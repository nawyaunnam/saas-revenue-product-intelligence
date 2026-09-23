import argparse
import json
import os
import subprocess
from pathlib import Path

from .contracts import CONTRACTS
from .generate import generate
from .ingest import load_local, publish


def main():
    parser = argparse.ArgumentParser(description="SaaS intelligence pipeline")
    parser.add_argument("command", choices=["generate", "ingest", "load", "build", "export", "demo"])
    parser.add_argument("--root", type=Path, default=Path(os.environ.get("SAAS_ROOT", ".")))
    parser.add_argument("--target", choices=["local", "snowflake"], default="local")
    parser.add_argument("--batch", type=Path)
    parser.add_argument("--source-dir", type=Path)
    parser.add_argument("--months", type=int, default=18)
    parser.add_argument("--accounts", type=int, default=120)
    args = parser.parse_args()
    if args.command == "ingest" and args.source_dir is None:
        parser.error("ingest requires --source-dir containing six contracted JSON arrays")
    root = args.root.resolve()
    data = root / "data"
    data.mkdir(exist_ok=True)
    if args.command in ["generate", "ingest", "demo"]:
        records = (
            {name: json.loads((args.source_dir / f"{name}.json").read_text()) for name in CONTRACTS}
            if args.command == "ingest"
            else generate(args.accounts, args.months)
        )
        batch = publish(records, data / "landing")
        (data / "latest_batch.txt").write_text(str(batch))
        print(json.dumps({"batch": str(batch)}))
    if args.command in ["load", "demo"]:
        batch = args.batch or Path((data / "latest_batch.txt").read_text())
        if args.target == "local":
            load_local(batch, data / "warehouse.duckdb")
        else:
            from .cloud import load_snowflake

            load_snowflake(batch)
    if args.command in ["build", "demo"]:
        subprocess.run(
            [
                "dbt",
                "build",
                "--project-dir",
                str(root / "dbt"),
                "--profiles-dir",
                str(root / "dbt"),
                "--target",
                args.target,
            ],
            check=True,
            env={**os.environ, "DUCKDB_PATH": str(data / "warehouse.duckdb")},
        )
    if args.command in ["export", "demo"]:
        if args.target != "local":
            print("Connect Power BI directly to Snowflake for cloud results")
            return
        from .report import export

        export(data / "warehouse.duckdb", root / "artifacts")


if __name__ == "__main__":
    main()
