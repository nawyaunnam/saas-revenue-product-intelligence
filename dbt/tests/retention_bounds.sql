select * from {{ ref('mart_cohort_retention') }} where retention_rate < 0 or retention_rate > 1 or cohort_age < 0
