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
checked as (
    select
        allocation.*,
        coalesce(payment.completed_payment_amount, 0.00) as completed_payment_amount,
        allocation.cumulative_scheduled_principal_due_amount
            - case
                when allocation.is_due_as_of_date
                    then allocation.scheduled_principal_amount
                else 0.00
            end as scheduled_principal_due_before_row
    from {{ ref('fct_loan_schedule_allocation') }} as allocation
    left join payment_totals as payment using (account_id)
)
select *
from checked
where is_due_as_of_date <> (due_date <= as_of_date)
    or cumulative_scheduled_principal_due_amount < 0.00
    or assumed_allocated_completed_payment_amount < 0.00
    or assumed_allocated_completed_payment_amount > scheduled_principal_amount
    or uncovered_scheduled_principal_amount < 0.00
    or (
        is_due_as_of_date
        and assumed_allocated_completed_payment_amount
            <> least(
                greatest(
                    completed_payment_amount - scheduled_principal_due_before_row,
                    0.00
                ),
                scheduled_principal_amount
            )
    )
    or (
        is_due_as_of_date
        and uncovered_scheduled_principal_amount
            <> scheduled_principal_amount
                - assumed_allocated_completed_payment_amount
    )
    or (
        not is_due_as_of_date
        and (
            assumed_allocated_completed_payment_amount <> 0.00
            or uncovered_scheduled_principal_amount <> 0.00
            or allocation_status <> 'Future'
        )
    )
    or (
        is_due_as_of_date
        and allocation_status <> case
            when assumed_allocated_completed_payment_amount
                = scheduled_principal_amount then 'Covered'
            when assumed_allocated_completed_payment_amount > 0.00
                then 'Partially Covered'
            else 'Uncovered'
        end
    )
