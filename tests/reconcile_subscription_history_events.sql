with expected_events as (
    select
        concat('status_change:', status_change_id) as event_id,
        'Status Change' as event_type
    from {{ ref('fct_subscription_status_change') }}

    union all

    select
        concat('source_removal:', removal_id) as event_id,
        'Source Removal' as event_type
    from {{ ref('fct_subscription_source_removal') }}
),

actual_events as (
    select event_id, event_type
    from {{ ref('fct_subscription_history_event') }}
)

select
    coalesce(expected.event_id, actual.event_id) as event_id
from expected_events as expected
full outer join actual_events as actual
    on expected.event_id = actual.event_id
    and expected.event_type = actual.event_type
where
    expected.event_id is null
    or actual.event_id is null
