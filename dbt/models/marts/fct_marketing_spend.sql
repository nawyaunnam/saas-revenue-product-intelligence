select spend_date as date_day, channel, spend_cents / 100.0 as spend from {{ ref('stg_marketing') }}
