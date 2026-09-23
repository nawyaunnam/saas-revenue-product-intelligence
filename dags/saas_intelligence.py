"""Daily synthetic batch demonstration; external feeds use the same contracts/loader."""

from datetime import timedelta

import pendulum
from airflow.providers.standard.operators.bash import BashOperator
from airflow.sdk import DAG

with DAG(
    dag_id="saas_revenue_product_intelligence",
    description="Validate sources, land immutable Parquet, load warehouse, test marts, export BI inputs",
    start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
    schedule="@daily",
    catchup=False,
    max_active_runs=1,
    default_args={
        "retries": 2,
        "retry_delay": timedelta(minutes=2),
        "execution_timeout": timedelta(minutes=20),
    },
    tags=["saas", "analytics-engineering", "dbt"],
) as dag:

    def command(task_id, action):
        return BashOperator(
            task_id=task_id,
            bash_command=f'cd /opt/project && /opt/airflow/pipeline/bin/saas {action} --target "$SAAS_TARGET"',
            append_env=True,
        )

    generate = command("extract_validate_land", "generate")
    load = command("load_warehouse", "load")
    build = command("dbt_build_and_test", "build")
    export = BashOperator(
        task_id="export_local_dashboard",
        bash_command='if [ "$SAAS_TARGET" = "local" ]; then cd /opt/project && /opt/airflow/pipeline/bin/saas export; else echo "Power BI connects directly to Snowflake marts"; fi',
        append_env=True,
    )
    generate >> load >> build >> export
