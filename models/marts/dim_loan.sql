with payment_summary as (
    select
        account_id,
        count(*) filter (where payment_status = 'Completed') as completed_payment_count,
        coalesce(sum(amount) filter (where payment_status = 'Completed'), 0.00)
            as completed_payment_amount,
        max(payment_date) filter (where payment_status = 'Completed')
            as last_completed_payment_date
    from {{ source('raw', 'payments') }}
    group by account_id
)
select
    loan.account_id,
    loan.customer_id,
    loan.product_code,
    loan.origination_date,
    loan.original_balance,
    loan.status,
    coalesce(payment_summary.completed_payment_count, 0) as completed_payment_count,
    coalesce(payment_summary.completed_payment_amount, 0.00) as completed_payment_amount,
    payment_summary.last_completed_payment_date
from {{ source('raw', 'loans') }} as loan
left join payment_summary using (account_id)
