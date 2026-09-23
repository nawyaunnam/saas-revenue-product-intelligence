-- Spine includes zero balances after cancellation: lag must not skip churned months.
with months as (select distinct month from {{ ref('dim_date') }}),
spine as (
    select a.account_id, m.month from {{ ref('dim_account') }} a
    cross join months m where m.month >= a.cohort_month
), balances as (
    select s.account_id, s.month,
        cast(coalesce(b.amount_cents / case when b.billing_period = 'annual' then 1200.0 else 100.0 end, 0)
             as decimal(18, 2)) as mrr
    from spine s left join {{ ref('stg_subscriptions') }} b
        on s.account_id = b.account_id and s.month = b.month
)
select *, coalesce(lag(mrr) over (partition by account_id order by month), 0) as beginning_mrr,
    coalesce(max(mrr) over (partition by account_id order by month rows between unbounded preceding and 1 preceding), 0) as historical_mrr
from balances
