"""Export model inputs plus a dependency-free, data-backed executive preview."""

import csv
import json
from decimal import Decimal
from pathlib import Path

import duckdb

TABLES = [
    "dim_account",
    "dim_user",
    "dim_date",
    "fct_account_month",
    "fct_product_event",
    "fct_account_funnel",
    "fct_marketing_spend",
    "mart_revenue_monthly",
    "mart_product_monthly",
    "mart_feature_adoption",
    "mart_cohort_retention",
    "mart_acquisition",
]


def export(database, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    result = {}
    with duckdb.connect(str(database), read_only=True) as con:
        for table in TABLES:
            cursor = con.execute(f"select * from analytics.{table}")
            fields = [c[0] for c in cursor.description]
            rows = cursor.fetchall()
            with (output / f"{table}.csv").open("w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(fields)
                writer.writerows(rows)
            result[table] = [dict(zip(fields, row, strict=True)) for row in rows]
    revenue = sorted(result["mart_revenue_monthly"], key=lambda r: r["month"])
    product = sorted(result["mart_product_monthly"], key=lambda r: r["month"])
    last = revenue[-1]
    summary = {
        "dataset": "synthetic",
        "latest_month": str(last["month"]),
        "accounts": len(result["dim_account"]),
        "events": len(result["fct_product_event"]),
        "latest_revenue": last,
        "latest_product": product[-1],
    }
    (output / "summary.json").write_text(
        json.dumps(summary, default=lambda x: float(x) if isinstance(x, Decimal) else str(x), indent=2)
    )
    peak = max(float(r["mrr"]) for r in revenue) or 1
    points = " ".join(
        f"{30 + i * 900 / (len(revenue) - 1):.1f},{225 - float(r['mrr']) / peak * 190:.1f}"
        for i, r in enumerate(revenue)
    )

    def pct(n):
        return "—" if n is None else f"{float(n):.1%}"

    cards = [
        ("Monthly recurring revenue", f"${last['mrr']:,.0f}"),
        ("Annual recurring revenue", f"${last['arr']:,.0f}"),
        ("Net revenue retention", pct(last["nrr"])),
        ("Monthly active users", str(product[-1]["mau"])),
    ]
    card_html = "".join(f"<article><span>{k}</span><strong>{v}</strong></article>" for k, v in cards)
    features = [r for r in result["mart_feature_adoption"] if r["month"] == last["month"]]
    bars = "".join(
        f'<div class="bar"><label>{r["feature"].replace("_", " ")}</label><progress max="1" value="{r["adoption_rate"] or 0}"></progress><b>{pct(r["adoption_rate"])}</b></div>'
        for r in features
    )
    cohorts = result["mart_cohort_retention"]
    heat = "<tr><th>Signup cohort</th>" + "".join(f"<th>M{i}</th>" for i in range(9)) + "</tr>"
    for cohort in sorted({r["cohort_month"] for r in cohorts})[-9:]:
        heat += f"<tr><th>{cohort:%b %Y}</th>"
        for age in range(9):
            cell = next((r for r in cohorts if r["cohort_month"] == cohort and r["cohort_age"] == age), None)
            heat += (
                "<td>—</td>"
                if cell is None
                else f'<td style="background:rgba(66,213,174,{float(cell["retention_rate"]) * 0.7:.2f})">{pct(cell["retention_rate"])}</td>'
            )
        heat += "</tr>"
    doc = f"""<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>SaaS Intelligence | Executive overview</title><style>
*{{box-sizing:border-box}}body{{margin:0;background:#0d1721;color:#e5edf4;font:15px system-ui,sans-serif}}main{{max-width:1200px;margin:0 auto;padding:40px 24px}}header{{display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #294050;padding-bottom:24px}}.eyebrow{{letter-spacing:3px;color:#42d5ae;font-size:12px}}h1{{font-size:34px;margin:12px 0}}.muted,span{{color:#a8b9c8}}.pill{{border:1px solid #365162;padding:10px;border-radius:6px}}.cards{{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin:28px 0}}article,.panel{{background:#152533;border:1px solid #294050;border-radius:10px;padding:22px}}strong{{display:block;font-size:32px;margin-top:14px}}h2{{font-size:18px;margin-top:0}}.grid{{display:grid;grid-template-columns:2fr 1fr;gap:20px;margin-bottom:20px}}svg{{width:100%;height:auto}}.bar{{margin:25px 0;display:grid;grid-template-columns:1fr 55px;gap:8px}}progress{{grid-column:1;width:100%;accent-color:#42d5ae}}.bar b{{grid-column:2;grid-row:2}}table{{width:100%;border-spacing:5px;font-size:12px}}th,td{{padding:9px;text-align:center;border-radius:3px}}th:first-child{{text-align:left;white-space:nowrap}}footer{{color:#a8b9c8;line-height:1.7;margin:24px 0}}@media(max-width:800px){{.cards{{grid-template-columns:repeat(2,1fr)}}.grid{{grid-template-columns:1fr}}.panel{{overflow-x:auto}}header{{display:block}}}}
</style><main><header><div><div class="eyebrow">SAAS INTELLIGENCE / EXECUTIVE VIEW</div><h1>Revenue meets product behavior.</h1><div class="muted">Billing · CRM · product events · marketing</div></div><div class="pill">Synthetic data · {last["month"]:%b %Y}</div></header>
<section class="cards">{card_html}</section><section class="grid"><div class="panel"><h2>Recurring revenue trajectory</h2><div class="muted">{revenue[0]["month"]:%b %Y} — {last["month"]:%b %Y} · USD · month-end balance</div><svg viewBox="0 0 960 250" role="img" aria-label="Monthly recurring revenue line chart"><line x1="30" x2="930" y1="225" y2="225" stroke="#365162"/><polyline points="{points}" fill="none" stroke="#42d5ae" stroke-width="4"/></svg><span>Latest GRR {pct(last["grr"])} · paying accounts {last["paying_accounts"]} · churn {pct(last["logo_churn_rate"])}</span></div><div class="panel"><h2>Feature adoption</h2><div class="muted">Distinct feature users / monthly active users</div>{bars}</div></section>
<section class="panel"><h2>Account cohort retention</h2><div class="muted">Accounts with product activity / original signup cohort · blank = unobserved</div><table>{heat}</table></section>
<footer>Generated from tested dbt marts. This HTML is a portable preview; the Power BI project contains the semantic model and report definitions.<br>NRR excludes new and reactivated accounts. LTV uses an explicit 80% gross-margin assumption and trailing three-month logo churn; it is a model, not realized customer value.</footer></main></html>"""
    (output / "dashboard.html").write_text(doc)
    print(
        json.dumps(
            {
                "dashboard": str(output / "dashboard.html"),
                "accounts": summary["accounts"],
                "events": summary["events"],
            }
        )
    )
