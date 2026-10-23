with expected as (
    select
        concat('Action:', action_id) as case_event_key,
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
        concat('Assignment:', assignment_id) as case_event_key,
        assignment_id as source_event_id,
        account_id,
        assigned_at as event_at,
        'Assignment' as event_type,
        'Case Assignment' as event_name,
        assignment_reason as event_detail,
        assigned_team as event_team
    from {{ ref('fct_loan_case_assignment') }}
)
select
    coalesce(expected.case_event_key, actual.case_event_key) as case_event_key,
    'Case activity does not reconcile to action and assignment facts' as failure_reason
from expected
full outer join {{ ref('fct_loan_case_activity') }} as actual
    using (case_event_key)
where expected.case_event_key is null
    or actual.case_event_key is null
    or expected.source_event_id <> actual.source_event_id
    or expected.account_id <> actual.account_id
    or expected.event_at <> actual.event_at
    or expected.event_type <> actual.event_type
    or expected.event_name <> actual.event_name
    or expected.event_detail <> actual.event_detail
    or expected.event_team <> actual.event_team
