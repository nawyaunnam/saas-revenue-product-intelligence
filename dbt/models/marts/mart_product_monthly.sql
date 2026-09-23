with daily as (
    select d.date_day, d.month, count(distinct e.user_id) as dau
    from {{ ref('dim_date') }} d left join {{ ref('fct_product_event') }} e on d.date_day = e.date_day
    group by d.date_day, d.month
), monthly as (
    select month, count(distinct user_id) as mau, count(distinct account_id) as active_accounts
    from {{ ref('fct_product_event') }} group by month
)
select d.month, avg(d.dau * 1.0) as average_dau, coalesce(m.mau, 0) as mau,
    coalesce(m.active_accounts, 0) as active_accounts,
    avg(d.dau * 1.0) / nullif(m.mau, 0) as stickiness
from daily d left join monthly m on d.month = m.month
group by d.month, m.mau, m.active_accounts
