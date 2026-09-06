with counts as (
    select
        (select count(*) from {{ source('raw', 'subscription_plans') }}) as raw_count,
        (select count(*) from {{ ref('dim_subscription_plan') }}) as mart_count
)
select
    raw_count,
    mart_count
from counts
where raw_count <> mart_count
