with source_events as (
    select
        action_id as source_event_id,
        account_id,
        action_at as event_at,
        'Action' as event_type,
        action_type as event_name,
        action_outcome as event_detail,
        agent_team as event_team
    from {{ ref('fct_loan_collection_action') }}

    union all

    select
        assignment_id as source_event_id,
        account_id,
        assigned_at as event_at,
        'Assignment' as event_type,
        'Case Assignment' as event_name,
        assignment_reason as event_detail,
        assigned_team as event_team
    from {{ ref('fct_loan_case_assignment') }}
),
sequenced as (
    select
        concat(event_type, ':', source_event_id) as case_event_key,
        *,
        row_number() over (
            partition by account_id
            order by event_at, event_type, source_event_id
        ) as event_sequence,
        lag(event_at) over (
            partition by account_id
            order by event_at, event_type, source_event_id
        ) as prior_event_at
    from source_events
)
select
    case_event_key,
    source_event_id,
    account_id,
    event_at,
    event_type,
    event_name,
    event_detail,
    event_team,
    event_sequence,
    prior_event_at,
    case
        when prior_event_at is null then null
        else date_diff('minute', prior_event_at, event_at)
    end as minutes_since_prior_event
from sequenced
