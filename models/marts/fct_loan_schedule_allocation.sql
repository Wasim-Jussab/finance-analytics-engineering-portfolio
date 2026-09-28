with parameters as (
    select as_of_date
    from {{ source('raw', 'run_parameters') }}
),
completed_payments as (
    select
        account_id,
        sum(amount) as completed_payment_amount
    from {{ ref('fct_payment') }}
    cross join parameters
    where is_successful
        and payment_date <= parameters.as_of_date
    group by account_id
),
schedule_position as (
    select
        schedule.schedule_id,
        schedule.account_id,
        schedule.instalment_number,
        schedule.due_date,
        schedule.due_month,
        schedule.scheduled_principal_amount,
        parameters.as_of_date,
        schedule.due_date <= parameters.as_of_date as is_due_as_of_date,
        coalesce(payments.completed_payment_amount, 0.00) as completed_payment_amount,
        sum(
            case
                when schedule.due_date <= parameters.as_of_date
                    then schedule.scheduled_principal_amount
                else 0.00
            end
        ) over (
            partition by schedule.account_id
            order by schedule.instalment_number
            rows between unbounded preceding and current row
        ) as cumulative_scheduled_principal_due_amount
    from {{ ref('fct_loan_repayment_schedule') }} as schedule
    cross join parameters
    left join completed_payments as payments using (account_id)
),
allocated as (
    select
        *,
        case
            when is_due_as_of_date then least(
                greatest(
                    completed_payment_amount
                    - cumulative_scheduled_principal_due_amount
                    + scheduled_principal_amount,
                    0.00
                ),
                scheduled_principal_amount
            )
            else 0.00
        end as assumed_allocated_completed_payment_amount
    from schedule_position
)
select
    schedule_id,
    account_id,
    instalment_number,
    due_date,
    due_month,
    scheduled_principal_amount,
    as_of_date,
    is_due_as_of_date,
    cumulative_scheduled_principal_due_amount,
    assumed_allocated_completed_payment_amount,
    case
        when is_due_as_of_date then
            scheduled_principal_amount - assumed_allocated_completed_payment_amount
        else 0.00
    end as uncovered_scheduled_principal_amount,
    case
        when not is_due_as_of_date then 'Future'
        when assumed_allocated_completed_payment_amount = scheduled_principal_amount
            then 'Covered'
        when assumed_allocated_completed_payment_amount > 0.00
            then 'Partially Covered'
        else 'Uncovered'
    end as allocation_status
from allocated
