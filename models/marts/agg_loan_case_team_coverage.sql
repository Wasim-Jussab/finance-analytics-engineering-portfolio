-- Current team ownership, not the team that recorded historical activity.
select
    as_of_date,
    current_assigned_team,
    count(*) as account_count,
    count(*) filter (where has_recorded_activity) as accounts_with_activity,
    count(*) filter (where not has_recorded_activity) as accounts_without_activity,
    sum(total_activity_count) as total_activity_count,
    sum(scheduled_principal_shortfall_amount) as scheduled_principal_shortfall_amount,
    sum(case when not has_recorded_activity
        then scheduled_principal_shortfall_amount else 0 end
    ) as shortfall_without_activity_amount,
    count(*) filter (where has_recorded_activity) * 1.0 / count(*) as activity_coverage_rate
from {{ ref('rpt_loan_case_activity_summary') }}
group by as_of_date, current_assigned_team
