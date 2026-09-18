select
    event_id,
    event_type,
    previous_status,
    new_status,
    business_event_date,
    observation_delay_days,
    is_business_status_change
from {{ ref('fct_subscription_history_event') }}
where
    (
        event_type = 'Status Change'
        and (
            new_status is null
            or previous_status = new_status
            or not is_business_status_change
        )
    )
    or (
        event_type = 'Source Removal'
        and (
            new_status is not null
            or business_event_date is not null
            or observation_delay_days is not null
            or is_business_status_change
        )
    )
