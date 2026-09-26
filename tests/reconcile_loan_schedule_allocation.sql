with payment_totals as (
    select
        payment.account_id,
        sum(payment.amount) as completed_payment_amount
    from {{ ref('fct_payment') }} as payment
    cross join {{ source('raw', 'run_parameters') }} as parameters
    where payment.is_successful
        and payment.payment_date <= parameters.as_of_date
    group by payment.account_id
),
allocation_totals as (
    select
        account_id,
        sum(
            case when is_due_as_of_date then scheduled_principal_amount else 0.00 end
        ) as scheduled_principal_due_amount,
        sum(assumed_allocated_completed_payment_amount) as allocated_payment_amount,
        sum(uncovered_scheduled_principal_amount) as uncovered_principal_amount
    from {{ ref('fct_loan_schedule_allocation') }}
    group by account_id
)
select
    allocation.account_id,
    allocation.scheduled_principal_due_amount,
    coalesce(payment.completed_payment_amount, 0.00) as completed_payment_amount,
    allocation.allocated_payment_amount,
    allocation.uncovered_principal_amount
from allocation_totals as allocation
left join payment_totals as payment using (account_id)
where allocation.allocated_payment_amount
        <> least(
            allocation.scheduled_principal_due_amount,
            coalesce(payment.completed_payment_amount, 0.00)
        )
    or allocation.uncovered_principal_amount
        <> allocation.scheduled_principal_due_amount
            - allocation.allocated_payment_amount
