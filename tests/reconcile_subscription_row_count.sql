with subscription_counts as (
    select
        (select count(*) from {{ source('raw', 'subscriptions') }}) as raw_count,
        (select count(*) from {{ ref('dim_subscription') }}) as mart_count
)
select
    raw_count,
    mart_count
from subscription_counts
where raw_count <> mart_count
