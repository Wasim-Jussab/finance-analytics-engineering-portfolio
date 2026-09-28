with month_ends as (
    select calendar_date as snapshot_date
    from {{ ref('dim_date') }}
    where is_month_end
),
eligible_loan_months as (
    select
        loan.account_id,
        loan.customer_id,
        loan.product_code,
        loan.origination_date,
        loan.original_balance,
        month_ends.snapshot_date
    from {{ ref('dim_loan') }} as loan
    cross join month_ends
    where loan.origination_date <= month_ends.snapshot_date
),
payment_summary as (
    select
        loan_month.account_id,
        loan_month.customer_id,
        loan_month.product_code,
        loan_month.origination_date,
        loan_month.original_balance,
        loan_month.snapshot_date,
        count(payment.payment_id) filter (
            where payment.is_successful
                and payment.payment_date >= date_trunc('month', loan_month.snapshot_date)
        ) as completed_payment_count_in_month,
        coalesce(sum(payment.amount) filter (
            where payment.is_successful
                and payment.payment_date >= date_trunc('month', loan_month.snapshot_date)
        ), 0.00) as completed_payment_amount_in_month,
        count(payment.payment_id) filter (
            where payment.is_successful
        ) as cumulative_completed_payment_count,
        coalesce(sum(payment.amount) filter (
            where payment.is_successful
        ), 0.00) as cumulative_completed_payment_amount
    from eligible_loan_months as loan_month
    left join {{ ref('fct_payment') }} as payment
        on loan_month.account_id = payment.account_id
        and payment.payment_date <= loan_month.snapshot_date
    group by
        loan_month.account_id,
        loan_month.customer_id,
        loan_month.product_code,
        loan_month.origination_date,
        loan_month.original_balance,
        loan_month.snapshot_date
)
select
    account_id,
    customer_id,
    product_code,
    origination_date,
    snapshot_date,
    original_balance,
    completed_payment_count_in_month,
    completed_payment_amount_in_month,
    cumulative_completed_payment_count,
    cumulative_completed_payment_amount,
    greatest(original_balance - cumulative_completed_payment_amount, 0.00)
        as calculated_remaining_balance,
    greatest(cumulative_completed_payment_amount - original_balance, 0.00)
        as payments_above_original_balance
from payment_summary
