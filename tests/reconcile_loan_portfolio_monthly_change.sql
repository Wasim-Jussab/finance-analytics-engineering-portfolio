select coalesce(report.snapshot_date, current_position.snapshot_date) as snapshot_date
from {{ ref('rpt_loan_portfolio_monthly_change') }} as report
full outer join {{ ref('agg_loan_portfolio_total_monthly') }} as current_position
    on report.snapshot_date = current_position.snapshot_date
left join {{ ref('agg_loan_portfolio_total_monthly') }} as previous_position
    on previous_position.snapshot_date
        = date_trunc('month', current_position.snapshot_date) - interval '1 day'
where report.snapshot_date is null or current_position.snapshot_date is null
    or report.previous_snapshot_date is distinct from previous_position.snapshot_date
    or report.has_previous_month is distinct from (previous_position.snapshot_date is not null)
    or report.loan_account_count is distinct from current_position.loan_account_count
    or report.loan_account_count_change is distinct from
        (current_position.loan_account_count - previous_position.loan_account_count)
    or report.scheduled_principal_due_amount is distinct from
        current_position.scheduled_principal_due_amount
    or report.scheduled_principal_due_change is distinct from
        (current_position.scheduled_principal_due_amount - previous_position.scheduled_principal_due_amount)
    or report.assumed_allocated_completed_payment_amount is distinct from
        current_position.assumed_allocated_completed_payment_amount
    or report.assumed_allocated_completed_payment_change is distinct from
        (current_position.assumed_allocated_completed_payment_amount
            - previous_position.assumed_allocated_completed_payment_amount)
    or report.scheduled_principal_shortfall_amount is distinct from
        current_position.scheduled_principal_shortfall_amount
    or report.scheduled_principal_shortfall_change is distinct from
        (current_position.scheduled_principal_shortfall_amount
            - previous_position.scheduled_principal_shortfall_amount)
    or report.scheduled_principal_due_change <>
        report.assumed_allocated_completed_payment_change + report.scheduled_principal_shortfall_change
    or report.due_principal_coverage_ratio is distinct from round(
        current_position.assumed_allocated_completed_payment_amount
            / nullif(current_position.scheduled_principal_due_amount, 0), 4)
    or report.previous_due_principal_coverage_ratio is distinct from round(
        previous_position.assumed_allocated_completed_payment_amount
            / nullif(previous_position.scheduled_principal_due_amount, 0), 4)
    or report.coverage_change_percentage_points is distinct from round(100 * (
        current_position.assumed_allocated_completed_payment_amount
            / nullif(current_position.scheduled_principal_due_amount, 0)
        - previous_position.assumed_allocated_completed_payment_amount
            / nullif(previous_position.scheduled_principal_due_amount, 0)
    ), 6)
    or report.allocation_first_effect_percentage_points is distinct from case
        when current_position.scheduled_principal_due_amount > 0
            and previous_position.scheduled_principal_due_amount > 0
        then round(100 * (current_position.assumed_allocated_completed_payment_amount
            - previous_position.assumed_allocated_completed_payment_amount)
            / previous_position.scheduled_principal_due_amount, 6)
    end
    or report.due_second_effect_percentage_points is distinct from case
        when current_position.scheduled_principal_due_amount > 0
            and previous_position.scheduled_principal_due_amount > 0
        then round(100 * current_position.assumed_allocated_completed_payment_amount * (
            1.0 / current_position.scheduled_principal_due_amount
            - 1.0 / previous_position.scheduled_principal_due_amount), 6)
    end
    or abs(report.coverage_change_percentage_points
        - report.allocation_first_effect_percentage_points
        - report.due_second_effect_percentage_points) > 0.000002
