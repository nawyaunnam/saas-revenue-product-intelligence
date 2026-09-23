# Power BI project

Open `SaaSIntelligence.pbip` in Power BI Desktop on Windows with Power BI Project/PBIR support enabled. This repository contains real PBIP, PBIR and TMSL semantic-model source, not a screenshot labeled as a report. **Desktop rendering, DAX engine execution and Service publishing are not verified in the macOS development environment.** CI checks JSON schemas and model references; complete the acceptance steps below in Desktop before calling it deployed.

1. Run the local pipeline (`saas demo`) and copy its `artifacts/` directory to your Windows machine if needed.
2. Open the PBIP; set DataFolder to the absolute artifacts path in Transform data → Manage parameters. Keep UseSnowflake=false for CSV inputs. Set RangeStart/RangeEnd to cover your generated dates; the default covers the 18-month sample.
3. Refresh. Mark Date as the date table using date_day. Import `theme.json` via View → Themes.
4. Review the six pages: executive overview, product, acquisition, cohort retention, account drill-through and hidden dynamic tooltip.
5. On the overview trend, use the Metric selector field parameter to change measure; use the Period comparison slicer for current/prior/MoM calculations. Do not sum MRR across months.
6. Right-click an account in the overview table and select Account detail. Hover the revenue chart for the context tooltip. Use the Bookmarks pane's Executive/Product bookmarks for navigation while preserving filters.

## Implemented capabilities

| Capability | Source |
|---|---|
| DAX | 34 explicit measures in model.bim, readable copies in measures.dax |
| Power Query/M | Typed CSV/Snowflake loading, parameters, half-open date filtering in Events |
| Star schema | Account/Date to Revenue/Events/Funnel; Date to Marketing; one-way relationships |
| Calculation group | Period comparison: current, previous month, MoM change % |
| Field parameter | Metric selector: MRR, ARR, NRR, MAU; extended ParameterMetadata |
| Drill-through | Account detail page binding to Account.account_id |
| Bookmarks | Executive/Product navigation bookmarks |
| Dynamic tooltip | Hidden Revenue context page and measure-based context text |
| RLS | Regional Analyst role maps USERPRINCIPALNAME to UserRegion; unknown users see no accounts |
| Incremental refresh | RangeStart/RangeEnd in M and an opt-in Snowflake policy in incremental-refresh.json |
| Optimization | Narrow facts, explicit measures, single-direction relationships, query-folding acceptance checks |

## RLS acceptance

The example UserRegion table contains only fake `*.analyst@example.com` identities. Replace with your governed entitlement source. In View as → Regional Analyst → Other user, test amer.analyst@example.com (AMER only), emea.analyst@example.com (EMEA only), and an unmapped identity (no account data). Marketing is denied to the regional role because it has no account/region attribution. Full-company analysts may access marketing without this role. Test with Power BI Service **Viewer** users; workspace edit permissions are not restricted by RLS in the same way. Hidden fields are not a security control.

## Incremental refresh and performance

For CSV the date predicate works but cannot fold; keep the demo as full refresh. For Snowflake, verify View Native Query/query diagnostics or Snowflake query history shows `occurred_at >= RangeStart AND occurred_at < RangeEnd`. Configure Events to store 36 months and refresh seven days using Desktop or apply `incremental-refresh.json`'s policy to the Events table via TOM/XMLA. An initial Service refresh creates partitions. Include older partitions when late events exceed seven days. This policy is supplied separately and is **not silently enabled** for local CSVs.

Use Performance Analyzer to export timings before and after changes. Run `queries/validation.dax`; the bridge residual must always equal zero and results must match exported mart CSVs. Check cohort and revenue totals under every slice. Use DAX Studio Server Timings and VertiPaq Analyzer to inspect cardinality, storage size and expensive scans. At larger volumes replace event-level visuals with an account-user-day-feature aggregate, retaining account keys for RLS and distinct-user semantics. Do not pre-sum DAU to derive MAU. There are no fabricated benchmark claims.

## Desktop acceptance checklist

- [ ] Project opens and Refresh succeeds without M errors.
- [ ] All visuals bind; field parameter, calculation group, bookmarks, tooltip and drill-through work.
- [ ] DAX monthly totals agree with dbt exports and bridge residual is zero.
- [ ] View as tests show correct regions and no data for unknown users.
- [ ] Snowflake folding and Service refresh partitions verified if cloud deployment is enabled.
- [ ] Performance Analyzer evidence saved for the actual machine/dataset.
