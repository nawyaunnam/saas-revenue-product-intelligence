-- Full table rebuild deliberately handles arbitrarily late events in this bounded portfolio dataset.
select event_id, user_id, account_id, cast(occurred_at as date) as date_day,
    {{ month_start('occurred_at') }} as month, occurred_at, event_name
from {{ ref('stg_events') }}
