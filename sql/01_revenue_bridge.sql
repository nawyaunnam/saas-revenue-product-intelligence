-- A bridge must balance for every segment/month, not only the company total.
select r.month, a.segment, sum(r.beginning_mrr) as opening,
       sum(r.new_mrr) as new, sum(r.expansion_mrr) as expansion,
       sum(r.reactivation_mrr) as reactivation, sum(r.contraction_mrr) as contraction,
       sum(r.churn_mrr) as churn, sum(r.mrr) as closing,
       sum(r.mrr - r.beginning_mrr - r.new_mrr - r.expansion_mrr
           - r.reactivation_mrr + r.contraction_mrr + r.churn_mrr) as residual
from analytics.fct_account_month r
join analytics.dim_account a on a.account_id=r.account_id
group by r.month,a.segment order by r.month,a.segment;
