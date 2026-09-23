with activated as (
    select a.account_id, min(e.occurred_at) as activation_at
    from {{ ref('dim_account') }} a
    join {{ ref('fct_product_event') }} e on a.account_id = e.account_id
    where e.event_name = 'workspace_created'
      and e.occurred_at >= cast(a.signup_date as timestamp)
      and e.occurred_at < {{ add_days('cast(a.signup_date as timestamp)', 7) }}
    group by a.account_id
)
select a.account_id, a.signup_date, o.trial_date, o.qualified_date, o.paid_date,
    cast(v.activation_at as date) as activation_date,
    case when {{ add_days('a.signup_date', 7) }} <= (select max(date_day) from {{ ref('dim_date') }})
         then 1 else 0 end as activation_eligible,
    case when v.activation_at is not null then 1 else 0 end as activated,
    case when o.qualified_date is not null then 1 else 0 end as qualified,
    case when o.paid_date is not null then 1 else 0 end as converted
from {{ ref('dim_account') }} a
left join {{ ref('stg_opportunities') }} o on a.account_id = o.account_id
left join activated v on a.account_id = v.account_id
