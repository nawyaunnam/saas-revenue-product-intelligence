select month from {{ ref('mart_revenue_monthly') }} where grr < 0 or grr > 1 or nrr < grr
union all
select month from {{ ref('mart_product_monthly') }} where average_dau > mau or stickiness < 0 or stickiness > 1
union all
select month from {{ ref('mart_feature_adoption') }} where adoption_rate < 0 or adoption_rate > 1
