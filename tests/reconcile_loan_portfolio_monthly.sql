with expected_account_month as (
    select
        snapshot.account_id,
        snapshot.snapshot_date,
        snapshot.product_code,
        snapshot.original_balance,
        snapshot.cumulative_completed_payment_amount,
        coalesce(sum(
            case
                when schedule.due_date <= snapshot.snapshot_date
                    then schedule.scheduled_principal_amount
                else 0.00
            end
        ), 0.00) as scheduled_principal_due_amount
    from {{ ref('fct_loan_monthly_snapshot') }} as snapshot
    left join {{ ref('fct_loan_repayment_schedule') }} as schedule
        on snapshot.account_id = schedule.account_id
    group by
        snapshot.account_id,
        snapshot.snapshot_date,
        snapshot.product_code,
        snapshot.original_balance,
        snapshot.cumulative_completed_payment_amount
),
expected as (
    select
        snapshot_date,
        product_code,
        count(*) as loan_account_count,
        sum(original_balance) as original_balance_amount,
        sum(cumulative_completed_payment_amount)
            as completed_payment_amount_as_of_month_end,
        sum(scheduled_principal_due_amount) as scheduled_principal_due_amount,
        sum(least(
            cumulative_completed_payment_amount,
            scheduled_principal_due_amount
        )) as assumed_allocated_completed_payment_amount,
        sum(scheduled_principal_due_amount - least(
            cumulative_completed_payment_amount,
            scheduled_principal_due_amount
        )) as scheduled_principal_shortfall_amount,
        sum(original_balance - scheduled_principal_due_amount)
            as future_scheduled_principal_amount,
        sum(greatest(
            cumulative_completed_payment_amount - scheduled_principal_due_amount,
            0.00
        )) as unallocated_completed_payment_amount,
        count(*) filter (
            where scheduled_principal_due_amount = 0.00
        ) as not_yet_due_account_count,
        count(*) filter (
            where scheduled_principal_due_amount > 0.00
                and scheduled_principal_due_amount
                    - least(
                        cumulative_completed_payment_amount,
                        scheduled_principal_due_amount
                    ) = 0.00
        ) as on_schedule_account_count,
        count(*) filter (
            where scheduled_principal_due_amount
                - least(
                    cumulative_completed_payment_amount,
                    scheduled_principal_due_amount
                ) > 0.00
        ) as behind_schedule_account_count
    from expected_account_month
    group by snapshot_date, product_code
)
select
    coalesce(expected.snapshot_date, actual.snapshot_date) as snapshot_date,
    coalesce(expected.product_code, actual.product_code) as product_code,
    'Monthly portfolio aggregate does not reconcile to account-month detail'
        as failure_reason
from expected
full outer join {{ ref('agg_loan_portfolio_monthly') }} as actual
    using (snapshot_date, product_code)
where expected.snapshot_date is null
    or actual.snapshot_date is null
    or expected.loan_account_count <> actual.loan_account_count
    or expected.original_balance_amount <> actual.original_balance_amount
    or expected.completed_payment_amount_as_of_month_end
        <> actual.completed_payment_amount_as_of_month_end
    or expected.scheduled_principal_due_amount
        <> actual.scheduled_principal_due_amount
    or expected.assumed_allocated_completed_payment_amount
        <> actual.assumed_allocated_completed_payment_amount
    or expected.scheduled_principal_shortfall_amount
        <> actual.scheduled_principal_shortfall_amount
    or expected.future_scheduled_principal_amount
        <> actual.future_scheduled_principal_amount
    or expected.unallocated_completed_payment_amount
        <> actual.unallocated_completed_payment_amount
    or expected.not_yet_due_account_count <> actual.not_yet_due_account_count
    or expected.on_schedule_account_count <> actual.on_schedule_account_count
    or expected.behind_schedule_account_count <> actual.behind_schedule_account_count
