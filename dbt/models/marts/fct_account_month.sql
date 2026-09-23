select account_id, month, mrr, beginning_mrr,
    case when beginning_mrr = 0 and mrr > 0 and historical_mrr = 0 then mrr else 0 end as new_mrr,
    case when beginning_mrr = 0 and mrr > 0 and historical_mrr > 0 then mrr else 0 end as reactivation_mrr,
    case when beginning_mrr > 0 and mrr > beginning_mrr then mrr - beginning_mrr else 0 end as expansion_mrr,
    case when mrr > 0 and mrr < beginning_mrr then beginning_mrr - mrr else 0 end as contraction_mrr,
    case when beginning_mrr > 0 and mrr = 0 then beginning_mrr else 0 end as churn_mrr,
    case when mrr > 0 then 1 else 0 end as paying_account,
    case when beginning_mrr > 0 then 1 else 0 end as beginning_account,
    case when beginning_mrr > 0 and mrr = 0 then 1 else 0 end as churned_account
from {{ ref('int_account_month') }}
