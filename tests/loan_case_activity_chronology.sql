select
    case_event_key,
    account_id,
    event_sequence,
    prior_event_at,
    event_at,
    minutes_since_prior_event
from {{ ref('fct_loan_case_activity') }}
where event_sequence < 1
    or (event_sequence = 1 and prior_event_at is not null)
    or (event_sequence > 1 and prior_event_at is null)
    or prior_event_at > event_at
    or minutes_since_prior_event < 0
