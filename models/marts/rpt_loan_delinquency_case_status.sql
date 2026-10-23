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
        action_at,
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
)
select
    queue.account_id,
    queue.customer_id,
    queue.product_code,
    queue.as_of_date,
    queue.delinquency_band_proxy,
    queue.scheduled_principal_shortfall_amount,
    queue.portfolio_exception_rank,
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
