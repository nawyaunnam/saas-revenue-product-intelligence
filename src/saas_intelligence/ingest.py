"""Validate whole batches before publishing immutable, checksummed Parquet files."""

import hashlib
import json
import shutil
import tempfile
from pathlib import Path

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq

from .contracts import CONTRACTS, KEYS


def validate(data):
    if set(data) != set(CONTRACTS):
        raise ValueError("Batch must include every contracted dataset")
    parsed = {}
    for name, cls in CONTRACTS.items():
        rows = [cls.model_validate(row).model_dump() for row in data[name]]
        if not rows:
            raise ValueError(f"Empty required dataset: {name}")
        unique = {}
        for row in rows:
            key = tuple(row[k] for k in KEYS[name])
            if name != "events" and key in unique:
                raise ValueError(f"Duplicate {name} key: {key}")
            if name == "events" and key in unique and row["ingested_at"] <= unique[key]["ingested_at"]:
                continue
            unique[key] = row
        parsed[name] = list(unique.values())
    accounts = {r["account_id"]: r for r in parsed["accounts"]}
    users = {r["user_id"]: r for r in parsed["users"]}
    for name in ["users", "subscriptions", "opportunities", "events"]:
        for r in parsed[name]:
            if r["account_id"] not in accounts:
                raise ValueError(f"Orphan {name} account")
    for r in parsed["subscriptions"]:
        if r["month"].day != 1:
            raise ValueError("Subscription month must be the first day")
    for r in parsed["events"]:
        user = users.get(r["user_id"])
        if not user or user["account_id"] != r["account_id"]:
            raise ValueError("Event user/account mismatch")
        if r["occurred_at"].date() < user["created_date"] or r["ingested_at"] < r["occurred_at"]:
            raise ValueError("Invalid event chronology")
    for r in parsed["opportunities"]:
        dates = [r[k] for k in ["trial_date", "qualified_date", "paid_date"] if r[k]]
        if dates != sorted(dates) or (r["paid_date"] and not r["qualified_date"]):
            raise ValueError("Invalid funnel chronology")
    return parsed


def publish(data, landing):
    data = validate(data)
    landing = Path(landing)
    landing.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix=".batch-", dir=landing))
    try:
        manifest = {"contract_version": 1, "files": {}}
        for name, rows in data.items():
            path = temp / f"{name}.parquet"
            rows = sorted(rows, key=lambda r: tuple(r[k] for k in KEYS[name]))
            pq.write_table(pa.Table.from_pylist(rows), path, compression="zstd")
            manifest["files"][name] = {
                "rows": len(rows),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        batch_id = hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()[:24]
        manifest["batch_id"] = batch_id
        (temp / "manifest.json").write_text(json.dumps(manifest, indent=2))
        dest = landing / batch_id
        if dest.exists():
            verify(dest)
        else:
            temp.rename(dest)
        return dest
    finally:
        if temp.exists():
            shutil.rmtree(temp)


def verify(batch):
    batch = Path(batch)
    manifest = json.loads((batch / "manifest.json").read_text())
    if set(manifest["files"]) != set(CONTRACTS):
        raise ValueError("Incomplete manifest")
    for name, info in manifest["files"].items():
        path = batch / f"{name}.parquet"
        if hashlib.sha256(path.read_bytes()).hexdigest() != info["sha256"]:
            raise ValueError(f"Checksum mismatch: {name}")
    return manifest


def load_local(batch, database):
    batch = Path(batch)
    verify(batch)
    Path(database).parent.mkdir(parents=True, exist_ok=True)
    with duckdb.connect(str(database)) as con:
        con.execute("begin")
        con.execute("create schema if not exists raw")
        for name in CONTRACTS:
            # Names come only from the fixed contract registry, paths are bound parameters.
            con.execute(
                f"create or replace table raw.{name} as select * from read_parquet(?)",
                [str(batch / f"{name}.parquet")],
            )
        con.execute("commit")
