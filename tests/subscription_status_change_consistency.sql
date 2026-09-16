select
    status_change_id,
    subscription_id,
    start_date,
    previous_status,
    new_status,
    business_event_date,
    observed_at,
    observation_delay_days
from {{ ref('fct_subscription_status_change') }}
where
    previous_status = new_status
    or (new_status = 'Cancelled' and business_event_date is null)
    or business_event_date < start_date
    or observation_delay_days is distinct from
        date_diff('day', business_event_date, cast(observed_at as date))
