"""S3 landing -> Snowflake staging -> transactional key-based MERGE.
Provision objects with warehouse/bootstrap.sql. No password literals or arbitrary identifiers.
"""

import os
import re
from pathlib import Path

from .contracts import KEYS
from .ingest import verify


def identifier(value):
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*){0,2}", value):
        raise ValueError("Invalid SQL identifier")
    return value.upper()


def load_snowflake(batch):
    import boto3
    import pyarrow.parquet as pq
    import snowflake.connector

    batch = Path(batch)
    manifest = verify(batch)
    batch_id = manifest["batch_id"]
    if not re.fullmatch(r"[a-f0-9]{24}", batch_id):
        raise ValueError("Invalid batch identifier")
    bucket = os.environ["S3_BUCKET"]
    stage = identifier(os.environ["SNOWFLAKE_STAGE"])
    database = identifier(os.environ.get("SNOWFLAKE_DATABASE", "SAAS_ANALYTICS"))
    s3 = boto3.client("s3")
    prefix = f"saas/batch={batch_id}"
    for path in sorted(batch.glob("*.parquet")):
        s3.upload_file(
            str(path), bucket, f"{prefix}/{path.name}", ExtraArgs={"ServerSideEncryption": "AES256"}
        )
    # Manifest acts as the completion marker; never upload it before the data files.
    s3.upload_file(
        str(batch / "manifest.json"),
        bucket,
        f"{prefix}/manifest.json",
        ExtraArgs={"ServerSideEncryption": "AES256"},
    )
    with snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        private_key_file=os.environ["SNOWFLAKE_PRIVATE_KEY_PATH"],
        role=os.environ.get("SNOWFLAKE_ROLE", "SAAS_TRANSFORMER"),
        warehouse=os.environ.get("SNOWFLAKE_WAREHOUSE", "SAAS_ETL_WH"),
        database=database,
        schema="RAW",
    ) as con:
        with con.cursor() as cur:
            # DDL is outside the transaction because Snowflake DDL implicitly commits.
            for name in KEYS:
                table = identifier(name)
                cur.execute(f"CREATE TEMPORARY TABLE LOAD_{table} LIKE {table}")
                cur.execute(
                    f"COPY INTO LOAD_{table} FROM @{stage}/{prefix}/{name}.parquet "
                    "FILE_FORMAT=(TYPE=PARQUET USE_LOGICAL_TYPE=TRUE) "
                    "MATCH_BY_COLUMN_NAME=CASE_INSENSITIVE ON_ERROR=ABORT_STATEMENT FORCE=TRUE"
                )
            cur.execute("BEGIN")
            try:
                for name, keys in KEYS.items():
                    table = identifier(name)
                    cols = [identifier(c) for c in pq.read_schema(batch / f"{name}.parquet").names]
                    join = " AND ".join(f"t.{identifier(k)}=s.{identifier(k)}" for k in keys)
                    updates = ", ".join(f"t.{c}=s.{c}" for c in cols if c.lower() not in keys)
                    # Do not regress a corrected event when an older batch is replayed.
                    guard = " AND s.INGESTED_AT >= t.INGESTED_AT" if name == "events" else ""
                    cur.execute(
                        f"MERGE INTO {table} t USING LOAD_{table} s ON {join} "
                        f"WHEN MATCHED{guard} THEN UPDATE SET {updates} "
                        f"WHEN NOT MATCHED THEN INSERT ({', '.join(cols)}) "
                        f"VALUES ({', '.join('s.' + c for c in cols)})"
                    )
                cur.execute(
                    "MERGE INTO LOAD_AUDIT t USING (SELECT %s AS BATCH_ID) s "
                    "ON t.BATCH_ID=s.BATCH_ID WHEN NOT MATCHED THEN INSERT (BATCH_ID, LOADED_AT) "
                    "VALUES (s.BATCH_ID, CURRENT_TIMESTAMP())",
                    (batch_id,),
                )
                cur.execute("COMMIT")
            except Exception:
                cur.execute("ROLLBACK")
                raise
