select * from {{ ref('fct_account_funnel') }} where converted > qualified or qualified > 1 or (activation_date is not null and activation_date < signup_date)
