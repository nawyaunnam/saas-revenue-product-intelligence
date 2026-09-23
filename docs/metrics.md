# Metric contracts

All source money is **USD cents**, excluding tax, credits and one-time services. Fixtures represent contracted month-end subscription balances, not cash receipts or GAAP revenue. Annual contracts are divided by 12. Do not treat ARR as recognized annual revenue.

| Metric | Definition and grain |
|---|---|
| MRR / ARR | Month-end contracted recurring revenue / MRR × 12. Balances are not additive across months. |
| New MRR | Positive balance following zero, with no earlier paid balance. |
| Reactivation | Positive balance following zero, with an earlier paid balance. Reported separately from new MRR. |
| Expansion / contraction | Increase/decrease in positive balances among accounts paying at both boundaries. |
| Churn MRR | Prior positive balance becoming zero. |
| NRR | (Beginning MRR + expansion − contraction − churn) / beginning MRR. New and reactivation excluded. |
| GRR | (Beginning MRR − contraction − churn) / beginning MRR; excludes expansion. |
| Logo churn | Churned accounts / accounts paying at beginning of month. |
| DAU / MAU | Distinct user IDs with any accepted product event per calendar day/month. Average DAU includes zero-activity calendar days. |
| Stickiness | Average DAU / MAU for the same calendar month. |
| Activation | A workspace_created event within [signup, signup + 7 days). Rate includes only accounts with a complete seven-day observation window. |
| Funnel | Signup → qualified → paid account, attributed to original signup month/channel. These are eventual cohort conversions, not same-month cash conversion. |
| Feature adoption | Distinct users using a feature / MAU in that month. |
| Cohort retention | Accounts in original signup cohort with any product activity in month n / original cohort size. Month zero may be below 100%; unobserved future months are blank. |
| Acquisition cost | Month/channel marketing spend divided by eventual paid accounts in that signup cohort. This is a cohort cost proxy, not fully loaded CAC or causal attribution. |
| Modeled LTV | Latest ARPA × assumed 80% gross margin / trailing 3-month weighted logo churn. Null when churn is zero/undefined. Not a forecast or realized LTV. |

## Star schema and grains

- `dim_account`: account ID; fixed segment/region/channel and signup cohort. This sample uses Type 1 dimensions; it does not implement historical SCD2 attribution.
- `dim_user`: user ID and account; `dim_date`: one uninterrupted calendar date.
- `fct_account_month`: account × month, including zeros after cancellation.
- `fct_product_event`: one deduplicated event ID. Timestamp filters are UTC with inclusive lower and exclusive upper boundaries.
- `fct_account_funnel`: one account and its lifecycle milestones.
- `fct_marketing_spend`: date × channel.

Never join events directly to revenue before aggregating: it multiplies MRR by event count. dbt marts aggregate each fact at its own grain. Power BI uses one-way dimension-to-fact relationships and explicit measures. Cohort and feature marts are intentionally not imported into the regional RLS model; otherwise disconnected aggregates could reveal totals from other regions.

## Tests that protect interpretation

Golden fixture February: opening $300, expansion $50, churn $200, new $50 → closing $200. NRR=50%, GRR=33.33%, ARR=$2,400. Later periods exercise contraction and reactivation. Zero-denominator ratios return NULL/BLANK, not zero. dbt asserts bridge equality, relationship integrity, calendar continuity, grain uniqueness and ratio bounds.
