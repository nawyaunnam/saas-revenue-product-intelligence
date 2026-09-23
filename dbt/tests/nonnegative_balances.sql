select * from {{ ref('fct_account_month') }} where mrr < 0 or beginning_mrr < 0
