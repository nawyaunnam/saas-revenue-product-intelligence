select *, {{ month_start('signup_date') }} as cohort_month from {{ ref('stg_accounts') }}
