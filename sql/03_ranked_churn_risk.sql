-- Explainable analyst queue, not a trained churn prediction model.
with usage as (
  select account_id,month,count(distinct date_day) as active_days
  from analytics.fct_product_event group by account_id,month
), momentum as (
  select r.account_id,r.month,r.mrr,coalesce(u.active_days,0) as active_days,
     lag(coalesce(u.active_days,0)) over(partition by r.account_id order by r.month) as prior_active_days
  from analytics.fct_account_month r left join usage u on r.account_id=u.account_id and r.month=u.month
), scored as (
  select *, (prior_active_days-active_days)*1.0/nullif(prior_active_days,0) as activity_decline
  from momentum where mrr>0
)
select *,dense_rank() over(partition by month order by activity_decline desc nulls last,mrr desc) as review_priority
from scored order by month desc,review_priority;
