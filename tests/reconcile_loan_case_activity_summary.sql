with activity_summary as (
    select
        account_id,
        count(*) as total_activity_count,
        count(*) filter (where event_type = 'Action') as action_event_count,
        count(*) filter (where event_type = 'Assignment') as assignment_event_count,
        min(event_at) as first_activity_at,
        max(event_at) as latest_activity_at
    from {{ ref('fct_loan_case_activity') }}
    group by account_id
),
expected as (
    select
        status.account_id,
        status.as_of_date,
        status.current_assigned_team,
        coalesce(activity.total_activity_count, 0) as total_activity_count,
        coalesce(activity.action_event_count, 0) as action_event_count,
        coalesce(activity.assignment_event_count, 0) as assignment_event_count,
        activity.total_activity_count is not null as has_recorded_activity,
        activity.first_activity_at,
        activity.latest_activity_at,
        case
            when activity.latest_activity_at is null then null
            else date_diff(
                'day',
                cast(activity.latest_activity_at as date),
                status.as_of_date
            )
        end as days_since_latest_activity,
        case
            when activity.total_activity_count is null then 'No recorded activity'
            else 'Activity recorded'
        end as activity_state
    from {{ ref('rpt_loan_delinquency_case_status') }} as status
    left join activity_summary as activity using (account_id)
)
select
    coalesce(expected.account_id, actual.account_id) as account_id,
    'Activity summary does not reconcile to case status and event history' as failure_reason
from expected
full outer join {{ ref('rpt_loan_case_activity_summary') }} as actual
    using (account_id, as_of_date)
where expected.account_id is null
    or actual.account_id is null
    or expected.current_assigned_team is distinct from actual.current_assigned_team
    or expected.total_activity_count <> actual.total_activity_count
    or expected.action_event_count <> actual.action_event_count
    or expected.assignment_event_count <> actual.assignment_event_count
    or expected.has_recorded_activity <> actual.has_recorded_activity
    or expected.first_activity_at is distinct from actual.first_activity_at
    or expected.latest_activity_at is distinct from actual.latest_activity_at
    or expected.days_since_latest_activity is distinct from actual.days_since_latest_activity
    or expected.activity_state <> actual.activity_state
