with sequenced as (
    select
        account_id,
        snapshot_date,
        original_balance,
        completed_payment_count_in_month,
        completed_payment_amount_in_month,
        cumulative_completed_payment_count,
        cumulative_completed_payment_amount,
        calculated_remaining_balance,
        payments_above_original_balance,
        lag(cumulative_completed_payment_count, 1, 0) over (
            partition by account_id order by snapshot_date
        ) as previous_completed_payment_count,
        lag(cumulative_completed_payment_amount, 1, 0.00) over (
            partition by account_id order by snapshot_date
        ) as previous_completed_payment_amount
    from {{ ref('fct_loan_monthly_snapshot') }}
)
select *
from sequenced
where cumulative_completed_payment_count
        <> previous_completed_payment_count + completed_payment_count_in_month
    or cumulative_completed_payment_amount
        <> previous_completed_payment_amount + completed_payment_amount_in_month
    or calculated_remaining_balance
        <> greatest(original_balance - cumulative_completed_payment_amount, 0.00)
    or payments_above_original_balance
        <> greatest(cumulative_completed_payment_amount - original_balance, 0.00)
    or completed_payment_count_in_month < 0
    or completed_payment_amount_in_month < 0
