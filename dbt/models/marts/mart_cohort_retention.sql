with activity as (select distinct account_id, month from {{ ref('fct_product_event') }}),
months as (select distinct month from {{ ref('dim_date') }})
select a.cohort_month, m.month, {{ month_diff('a.cohort_month', 'm.month') }} as cohort_age,
    count(*) as cohort_accounts, count(e.account_id) as retained_accounts,
    count(e.account_id) * 1.0 / count(*) as retention_rate
from {{ ref('dim_account') }} a join months m on m.month >= a.cohort_month
left join activity e on e.account_id = a.account_id and e.month = m.month
group by a.cohort_month, m.month
