select * from {{ ref('fct_account_month') }}
where abs(mrr - (beginning_mrr + new_mrr + reactivation_mrr + expansion_mrr - contraction_mrr - churn_mrr)) > 0.01
