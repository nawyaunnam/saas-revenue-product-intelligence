with funnel as (
    select {{ month_start('f.signup_date') }} as month, a.channel, count(*) as signups,
        sum(f.qualified) as qualified, sum(f.converted) as paid_accounts,
        sum(f.activation_eligible) as eligible_accounts,
        sum(case when f.activation_eligible = 1 then f.activated else 0 end) as activated_accounts
    from {{ ref('fct_account_funnel') }} f join {{ ref('dim_account') }} a on f.account_id = a.account_id
    group by {{ month_start('f.signup_date') }}, a.channel
), spend as (
    select {{ month_start('date_day') }} as month, channel, sum(spend) as spend
    from {{ ref('fct_marketing_spend') }} group by {{ month_start('date_day') }}, channel
)
select s.month, s.channel, s.spend, coalesce(f.signups, 0) as signups,
    coalesce(f.qualified, 0) as qualified, coalesce(f.paid_accounts, 0) as paid_accounts,
    coalesce(f.activated_accounts, 0) as activated_accounts, coalesce(f.eligible_accounts, 0) as eligible_accounts,
    f.paid_accounts * 1.0 / nullif(f.signups, 0) as conversion_rate,
    f.activated_accounts * 1.0 / nullif(f.eligible_accounts, 0) as activation_rate,
    s.spend / nullif(f.paid_accounts, 0) as cohort_acquisition_cost
from spend s left join funnel f on s.month = f.month and s.channel = f.channel
