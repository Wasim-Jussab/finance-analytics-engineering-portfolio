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
)
select
    status.account_id,
    status.customer_id,
    status.product_code,
    status.as_of_date,
    status.delinquency_band_proxy,
    status.scheduled_principal_shortfall_amount,
    status.portfolio_exception_rank,
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
