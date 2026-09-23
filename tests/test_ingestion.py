import copy
from datetime import timedelta

import duckdb
import pytest

from saas_intelligence.generate import generate
from saas_intelligence.ingest import load_local, publish, validate, verify


@pytest.fixture
def data():
    return generate(accounts=12, months=6)


def test_deterministic_and_idempotent(data, tmp_path):
    assert data == generate(accounts=12, months=6)
    batch = publish(data, tmp_path / "landing")
    assert publish(data, tmp_path / "landing") == batch
    manifest = verify(batch)
    assert manifest["files"]["events"]["rows"] < len(data["events"])
    db = tmp_path / "test.duckdb"
    load_local(batch, db)
    load_local(batch, db)
    with duckdb.connect(str(db)) as con:
        assert (
            con.execute("select count(*) from raw.events").fetchone()[0]
            == manifest["files"]["events"]["rows"]
        )


def test_latest_event_wins(data):
    event = copy.deepcopy(data["events"][0])
    event["ingested_at"] += timedelta(days=1)
    event["event_name"] = "export"
    data["events"].append(event)
    assert (
        next(r for r in validate(data)["events"] if r["event_id"] == event["event_id"])["event_name"]
        == "export"
    )


@pytest.mark.parametrize("fault", ["orphan", "negative", "duplicate", "chronology", "user_mismatch"])
def test_reject_bad_batch_before_publish(data, tmp_path, fault):
    if fault == "orphan":
        data["events"][0]["account_id"] = "MISSING"
    elif fault == "negative":
        data["subscriptions"][0]["amount_cents"] = -1
    elif fault == "duplicate":
        data["accounts"].append(data["accounts"][0])
    elif fault == "chronology":
        data["opportunities"][1]["paid_date"] = data["opportunities"][1]["trial_date"] - timedelta(days=1)
    else:
        data["events"][0]["user_id"] = "MISSING"
    with pytest.raises(ValueError):
        publish(data, tmp_path / "landing")
    assert not (tmp_path / "landing").exists()


def test_tampered_batch_rejected(data, tmp_path):
    batch = publish(data, tmp_path / "landing")
    (batch / "accounts.parquet").write_bytes(b"corrupt")
    with pytest.raises(ValueError, match="Checksum"):
        load_local(batch, tmp_path / "test.duckdb")
    assert not (tmp_path / "test.duckdb").exists()


def test_json_import_uses_same_contracts(data, tmp_path, monkeypatch):
    import json

    from saas_intelligence.cli import main

    source = tmp_path / "sources"
    source.mkdir()
    for name, rows in data.items():
        (source / f"{name}.json").write_text(json.dumps(rows, default=str))
    monkeypatch.setattr("sys.argv", ["saas", "ingest", "--root", str(tmp_path), "--source-dir", str(source)])
    main()
    batch = (tmp_path / "data/latest_batch.txt").read_text()
    assert verify(batch)["files"]["accounts"]["rows"] == 12


def test_timezone_normalization():
    from saas_intelligence.contracts import Event

    row = Event(
        event_id="e",
        user_id="u",
        account_id="a",
        event_name="login",
        occurred_at="2024-01-02T00:30:00+02:00",
        ingested_at="2024-01-02T02:00:00+02:00",
    )
    assert row.occurred_at.isoformat() == "2024-01-01T22:30:00"
    assert row.ingested_at.tzinfo is None
