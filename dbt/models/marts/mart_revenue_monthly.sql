with monthly as (
    select month, sum(mrr) as mrr, sum(beginning_mrr) as beginning_mrr,
        sum(new_mrr) as new_mrr, sum(reactivation_mrr) as reactivation_mrr,
        sum(expansion_mrr) as expansion_mrr, sum(contraction_mrr) as contraction_mrr,
        sum(churn_mrr) as churn_mrr, sum(paying_account) as paying_accounts,
        sum(beginning_account) as beginning_accounts, sum(churned_account) as churned_accounts
    from {{ ref('fct_account_month') }} group by month
)
select *, mrr * 12 as arr,
    (beginning_mrr + expansion_mrr - contraction_mrr - churn_mrr) / nullif(beginning_mrr, 0) as nrr,
    (beginning_mrr - contraction_mrr - churn_mrr) / nullif(beginning_mrr, 0) as grr,
    churned_accounts * 1.0 / nullif(beginning_accounts, 0) as logo_churn_rate,
    mrr / nullif(paying_accounts, 0) as arpa,
    -- Modeled LTV: 80% assumed gross margin, trailing 3-month weighted logo churn.
    (mrr / nullif(paying_accounts, 0)) * 0.8 /
        nullif(sum(churned_accounts) over (order by month rows between 2 preceding and current row) * 1.0 /
               nullif(sum(beginning_accounts) over (order by month rows between 2 preceding and current row), 0), 0) as modeled_ltv
from monthly
