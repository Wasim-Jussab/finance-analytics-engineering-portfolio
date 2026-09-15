with ordered_versions as (
    select
        subscription_plan_id,
        dbt_valid_from,
        dbt_valid_to,
        lead(dbt_valid_from) over (
            partition by subscription_plan_id
            order by dbt_valid_from
        ) as next_valid_from
    from {{ ref('subscription_plan_history') }}
)

select *
from ordered_versions
where
    (dbt_valid_to is not null and dbt_valid_to <= dbt_valid_from)
    or (next_valid_from is not null and dbt_valid_to > next_valid_from)
