with action_summary as (
    select
        account_id,
        count(*) as recorded_action_count,
        min(action_at) as first_action_at,
        max(action_at) as latest_action_at
    from {{ ref('fct_loan_collection_action') }}
    group by account_id
),
latest_action as (
    select
        account_id,
        action_id as latest_action_id,
        action_type as latest_action_type,
        action_outcome as latest_action_outcome,
        agent_team as latest_agent_team
    from {{ ref('fct_loan_collection_action') }}
    qualify row_number() over (
        partition by account_id
        order by action_at desc, action_id desc
    ) = 1
),
assignment_summary as (
    select
        account_id,
        count(*) as assignment_event_count,
        min(assigned_at) as first_assigned_at,
        max(assigned_at) as latest_assigned_at
    from {{ ref('fct_loan_case_assignment') }}
    group by account_id
),
latest_assignment as (
    select
        account_id,
        assignment_id as current_assignment_id,
        assigned_team as current_assigned_team,
        assignment_reason as current_assignment_reason
    from {{ ref('fct_loan_case_assignment') }}
    qualify row_number() over (
        partition by account_id
        order by assigned_at desc, assignment_id desc
    ) = 1
),
expected as (
    select
        queue.account_id,
        queue.as_of_date,
        coalesce(action_summary.recorded_action_count, 0) as recorded_action_count,
        action_summary.recorded_action_count is not null as has_recorded_action,
        action_summary.first_action_at,
        action_summary.latest_action_at,
        latest_action.latest_action_id,
        latest_action.latest_action_type,
        latest_action.latest_action_outcome,
        latest_action.latest_agent_team,
        coalesce(assignment_summary.assignment_event_count, 0) as assignment_event_count,
        assignment_summary.assignment_event_count is not null as has_recorded_assignment,
        assignment_summary.first_assigned_at,
        assignment_summary.latest_assigned_at,
        latest_assignment.current_assignment_id,
        latest_assignment.current_assigned_team,
        latest_assignment.current_assignment_reason
    from {{ ref('rpt_loan_delinquency_exception_queue') }} as queue
    left join action_summary using (account_id)
    left join latest_action using (account_id)
    left join assignment_summary using (account_id)
    left join latest_assignment using (account_id)
)
select
    coalesce(expected.account_id, actual.account_id) as account_id,
    'Case status does not reconcile to queue, action and assignment events' as failure_reason
from expected
full outer join {{ ref('rpt_loan_delinquency_case_status') }} as actual
    using (account_id, as_of_date)
where expected.account_id is null
    or actual.account_id is null
    or expected.recorded_action_count <> actual.recorded_action_count
    or expected.has_recorded_action <> actual.has_recorded_action
    or expected.first_action_at is distinct from actual.first_action_at
    or expected.latest_action_at is distinct from actual.latest_action_at
    or expected.latest_action_id is distinct from actual.latest_action_id
    or expected.latest_action_type is distinct from actual.latest_action_type
    or expected.latest_action_outcome is distinct from actual.latest_action_outcome
    or expected.latest_agent_team is distinct from actual.latest_agent_team
    or expected.assignment_event_count <> actual.assignment_event_count
    or expected.has_recorded_assignment <> actual.has_recorded_assignment
    or expected.first_assigned_at is distinct from actual.first_assigned_at
    or expected.latest_assigned_at is distinct from actual.latest_assigned_at
    or expected.current_assignment_id is distinct from actual.current_assignment_id
    or expected.current_assigned_team is distinct from actual.current_assigned_team
    or expected.current_assignment_reason is distinct from actual.current_assignment_reason
