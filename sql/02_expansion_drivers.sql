-- Association, not causation: compare previous-month automation adoption to expansion.
with usage as (
  select account_id, month, max(case when event_name='automation' then 1 else 0 end) as used_automation
  from analytics.fct_product_event group by account_id,month
), lagged as (
  select r.*, lag(coalesce(u.used_automation,0)) over (partition by r.account_id order by r.month) as prior_automation
  from analytics.fct_account_month r left join usage u on r.account_id=u.account_id and r.month=u.month
)
select month,prior_automation,count(*) as eligible_accounts,
       avg(case when expansion_mrr>0 then 1.0 else 0.0 end) as expansion_incidence
from lagged where beginning_mrr>0 group by month,prior_automation order by month,prior_automation;
