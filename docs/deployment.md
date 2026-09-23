# Deployment

## Local Python

Python 3.11–3.13 is supported. Use a virtual environment and activate it so `dbt` is on PATH:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
saas demo
pytest -q
python -m http.server 8081 --directory artifacts
```

Open http://localhost:8081/dashboard.html. `saas generate`, `saas load`, `saas build`, and `saas export` also run independently. A completed manifest and latest_batch pointer are in `data/`. Regenerating identical inputs produces the same batch ID; changing `--accounts` or `--months` creates a new one. Do not run simultaneous writers against DuckDB.

## Docker and Airflow

```bash
docker compose up --build pipeline preview
# Airflow uses a separate volume and its own isolated dbt virtual environment:
docker compose --profile airflow up --build airflow
```

Preview: localhost:8081/dashboard.html. Airflow: localhost:8080. The Airflow standalone command generates local development credentials; retrieve them from container logs/generated password file. Unpause and trigger `saas_revenue_product_intelligence`. The DAG is paused initially to prevent unexpected runs. This standalone setup is for local demonstration, not an HA Airflow deployment. For production, use an external metadata database, a supported executor and secret backend, and the official Helm deployment.

## Snowflake + S3 (requires your accounts; not exercised by local CI)

1. Create a private S3 bucket with public access blocked, encryption and versioning. Give the uploader write/read permissions only on `saas/`; use the AWS default credential chain (workload role preferred).
2. Create a Snowflake AWS storage integration, restrict its allowed location to that bucket, and configure the AWS trust relationship using `DESC INTEGRATION`. Follow the linked Snowflake guide below. Substitute the bucket URL and integration name in `warehouse/bootstrap.sql`; have a provisioning admin run it. The loader assumes the external stage points to the **bucket root**.
3. Create dedicated key-pair-authenticated Snowflake service users. Grant SAAS_TRANSFORMER to the pipeline user and SAAS_BI_READER to the Power BI user. Never use ACCOUNTADMIN for scheduled loads. Store the private key outside the repository, with restricted file permissions.
4. Install `pip install -e '.[cloud]'`. Export the variables shown in `.env.example` to the shell or your secret manager; the CLI does not automatically source `.env`. Use an unencrypted PEM private key protected by the secret store/file permissions for this example, or extend both connector and dbt profiles with a passphrase parameter.
5. Run `saas generate`, `saas load --target snowflake`, then `saas build --target snowflake`. These commands write synthetic data only. Do not run the provisioning SQL against unrelated objects.
6. In Power BI, set UseSnowflake=true and the server/warehouse/database parameters. Authenticate with the BI read-only role. Validate query folding before enabling the included Events refresh policy.

Cloud code deliberately fails on missing configuration. CI validates its identifier guard and structure but does not claim a Snowflake/S3 integration test. To orchestrate cloud runs, inject environment variables and mount the private key into the Airflow container; change SAAS_TARGET to snowflake. No credentials are checked into Compose.

## Official references

- [Airflow Docker quickstart](https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html)
- [dbt DuckDB profile](https://docs.getdbt.com/docs/local/connect-data-platform/duckdb-setup)
- [Snowflake storage integrations for S3](https://docs.snowflake.com/en/user-guide/data-load-s3-config-storage-integration)
- [Power BI project semantic models](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-dataset)
- [Power BI field parameters](https://learn.microsoft.com/en-us/power-bi/create-reports/power-bi-field-parameters)
- [Power BI incremental refresh](https://learn.microsoft.com/en-us/power-bi/connect-data/incremental-refresh-configure)
