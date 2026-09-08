with source_totals as (
    select
        count(*) as started_agreement_count,
        count(*) filter (where cancellation_date is not null) as cancelled_agreement_count
    from {{ ref('dim_subscription') }}
),
movement_totals as (
    select
        sum(started_agreement_count) as started_agreement_count,
        sum(cancelled_agreement_count) as cancelled_agreement_count
    from {{ ref('agg_subscription_movement_monthly') }}
)
select
    source.started_agreement_count as source_started_count,
    movement.started_agreement_count as movement_started_count,
    source.cancelled_agreement_count as source_cancelled_count,
    movement.cancelled_agreement_count as movement_cancelled_count
from source_totals as source
cross join movement_totals as movement
where source.started_agreement_count <> movement.started_agreement_count
    or source.cancelled_agreement_count <> movement.cancelled_agreement_count
