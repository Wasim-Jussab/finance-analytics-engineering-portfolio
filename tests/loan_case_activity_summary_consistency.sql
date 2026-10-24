select
    account_id,
    'Activity state, counts or recency fields are inconsistent' as failure_reason
from {{ ref('rpt_loan_case_activity_summary') }}
where total_activity_count <> action_event_count + assignment_event_count
    or total_activity_count < 0
    or action_event_count < 0
    or assignment_event_count < 0
    or (
        has_recorded_activity
        and (
            total_activity_count = 0
            or first_activity_at is null
            or latest_activity_at is null
            or first_activity_at > latest_activity_at
            or cast(latest_activity_at as date) > as_of_date
            or days_since_latest_activity < 0
            or activity_state <> 'Activity recorded'
        )
    )
    or (
        not has_recorded_activity
        and (
            total_activity_count <> 0
            or action_event_count <> 0
            or assignment_event_count <> 0
            or first_activity_at is not null
            or latest_activity_at is not null
            or days_since_latest_activity is not null
            or activity_state <> 'No recorded activity'
        )
    )
