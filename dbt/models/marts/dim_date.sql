-- Marketing has one row for every observation date, including zero-product-activity days.
select distinct spend_date as date_day, {{ month_start('spend_date') }} as month,
    extract(year from spend_date) as year, extract(month from spend_date) as month_number
from {{ ref('stg_marketing') }}
