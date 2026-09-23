select account_id, month, count(*) as n from {{ ref('fct_account_month') }} group by account_id, month having count(*) <> 1
