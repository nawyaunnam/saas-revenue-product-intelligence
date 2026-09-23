"""Golden business case executed through actual dbt models, not Python reimplementations."""

import os
import subprocess
from datetime import date
from pathlib import Path

import duckdb
import pytest

from saas_intelligence.generate import generate
from saas_intelligence.ingest import load_local, publish


@pytest.fixture(scope="module")
def warehouse(tmp_path_factory):
    root = Path(__file__).resolve().parents[1]
    tmp = tmp_path_factory.mktemp("golden")
    data = generate(accounts=12, months=6)
    # Force every account to exist from January; deterministic monthly balances.
    for account in data["accounts"]:
        account["signup_date"] = date(2024, 1, 1)
    data["subscriptions"] = []
    cases = {
        "A0000": [100, 150, 120, 0, 80, 80],
        "A0001": [200, 0, 0, 0, 0, 0],
        "A0002": [0, 50, 50, 50, 50, 50],
    }
    for aid, balances in cases.items():
        for i, amount in enumerate(balances):
            data["subscriptions"].append(
                dict(
                    account_id=aid,
                    month=date(2024, i + 1, 1),
                    amount_cents=amount * 1200,
                    billing_period="annual",
                    plan="Starter",
                )
            )
    batch = publish(data, tmp / "landing")
    db = tmp / "warehouse.duckdb"
    load_local(batch, db)
    subprocess.run(
        [
            "dbt",
            "build",
            "--project-dir",
            str(root / "dbt"),
            "--profiles-dir",
            str(root / "dbt"),
            "--target-path",
            str(tmp / "target"),
            "--log-path",
            str(tmp / "logs"),
        ],
        env={**os.environ, "DUCKDB_PATH": str(db)},
        check=True,
        capture_output=True,
        text=True,
    )
    return db


def test_golden_revenue_and_retention(warehouse):
    with duckdb.connect(str(warehouse)) as con:
        row = con.execute(
            "select mrr, beginning_mrr, new_mrr, expansion_mrr, churn_mrr, nrr, grr, arr from analytics.mart_revenue_monthly where month='2024-02-01'"
        ).fetchone()
        assert [float(x) for x in row[:5]] == [200, 300, 50, 50, 200]
        assert float(row[5]) == pytest.approx(0.5)  # New $50 excluded from NRR numerator.
        assert float(row[6]) == pytest.approx(1 / 3)
        assert float(row[7]) == 2400
        assert (
            con.execute(
                "select reactivation_mrr from analytics.fct_account_month where account_id='A0000' and month='2024-05-01'"
            ).fetchone()[0]
            == 80
        )
        assert (
            con.execute(
                "select contraction_mrr from analytics.fct_account_month where account_id='A0000' and month='2024-03-01'"
            ).fetchone()[0]
            == 30
        )
        assert (
            con.execute("select nrr from analytics.mart_revenue_monthly order by month limit 1").fetchone()[0]
            is None
        )


def test_product_distinct_users_and_cohort_denominator(warehouse):
    with duckdb.connect(str(warehouse)) as con:
        rows = con.execute(
            "select m.month,m.mau,count(distinct e.user_id) from analytics.mart_product_monthly m join analytics.fct_product_event e on m.month=e.month group by m.month,m.mau"
        ).fetchall()
        assert all(mau == expected for _, mau, expected in rows)
        assert con.execute(
            "select min(cohort_accounts),max(cohort_accounts) from analytics.mart_cohort_retention"
        ).fetchone() == (12, 12)
