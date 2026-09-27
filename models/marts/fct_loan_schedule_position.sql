with payment_summary as (
    select
        payment.account_id,
        sum(payment.amount) as completed_payment_amount_as_of_date
    from {{ ref('fct_payment') }} as payment
    cross join {{ source('raw', 'run_parameters') }} as parameters
    where payment.is_successful
        and payment.payment_date <= parameters.as_of_date
    group by payment.account_id
),
schedule_summary as (
    select
        allocation.account_id,
        allocation.as_of_date,
        count(*) as scheduled_instalment_count,
        count(*) filter (where allocation.is_due_as_of_date) as due_instalment_count,
        count(*) filter (where not allocation.is_due_as_of_date) as future_instalment_count,
        count(*) filter (
            where allocation.uncovered_scheduled_principal_amount > 0.00
        ) as uncovered_instalment_count,
        sum(
            case
                when allocation.is_due_as_of_date
                    then allocation.scheduled_principal_amount
                else 0.00
            end
        ) as scheduled_principal_due_amount,
        sum(
            case
                when not allocation.is_due_as_of_date
                    then allocation.scheduled_principal_amount
                else 0.00
            end
        ) as future_scheduled_principal_amount,
        sum(
            allocation.assumed_allocated_completed_payment_amount
        ) as assumed_allocated_completed_payment_amount,
        sum(
            allocation.uncovered_scheduled_principal_amount
        ) as scheduled_principal_shortfall_amount,
        min(allocation.due_date) filter (
            where allocation.uncovered_scheduled_principal_amount > 0.00
        ) as oldest_uncovered_due_date
    from {{ ref('fct_loan_schedule_allocation') }} as allocation
    group by allocation.account_id, allocation.as_of_date
)
select
    loan.account_id,
    loan.customer_id,
    loan.product_code,
    loan.status as source_loan_status,
    loan.original_balance,
    summary.as_of_date,
    summary.scheduled_instalment_count,
    summary.due_instalment_count,
    summary.future_instalment_count,
    summary.uncovered_instalment_count,
    summary.scheduled_principal_due_amount,
    summary.assumed_allocated_completed_payment_amount,
    summary.scheduled_principal_shortfall_amount,
    summary.future_scheduled_principal_amount,
    coalesce(payments.completed_payment_amount_as_of_date, 0.00)
        as completed_payment_amount_as_of_date,
    greatest(
        coalesce(payments.completed_payment_amount_as_of_date, 0.00)
        - summary.assumed_allocated_completed_payment_amount,
        0.00
    ) as unallocated_completed_payment_amount,
    summary.oldest_uncovered_due_date,
    case
        when summary.oldest_uncovered_due_date is null then 0
        else date_diff(
            'day', summary.oldest_uncovered_due_date, summary.as_of_date
        )
    end as days_past_due_proxy,
    case
        when summary.scheduled_principal_due_amount = 0.00 then null
        else round(
            summary.assumed_allocated_completed_payment_amount
            / summary.scheduled_principal_due_amount,
            4
        )
    end as due_principal_coverage_ratio,
    case
        when summary.scheduled_principal_due_amount = 0.00 then 'Not Yet Due'
        when summary.scheduled_principal_shortfall_amount = 0.00 then 'On Schedule'
        else 'Behind Schedule'
    end as schedule_position_status
from schedule_summary as summary
inner join {{ ref('dim_loan') }} as loan using (account_id)
left join payment_summary as payments using (account_id)
