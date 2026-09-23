with features as (
    select 'report_created' as feature union all select 'export' union all select 'automation' union all select 'invite_sent'
), counts as (
    select month, event_name, count(distinct user_id) as feature_users
    from {{ ref('fct_product_event') }} group by month, event_name
)
select m.month, f.feature, coalesce(c.feature_users, 0) as feature_users, m.mau,
    coalesce(c.feature_users, 0) * 1.0 / nullif(m.mau, 0) as adoption_rate
from {{ ref('mart_product_monthly') }} m cross join features f
left join counts c on c.month = m.month and c.event_name = f.feature
