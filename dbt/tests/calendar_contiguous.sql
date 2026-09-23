select 1 as failed from {{ ref('dim_date') }} having count(*) <> {{ day_diff('min(date_day)', 'max(date_day)') }} + 1
