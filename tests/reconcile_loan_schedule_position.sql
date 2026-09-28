with allocation_summary as (
    select
        account_id,
        count(*) as scheduled_instalment_count,
        count(*) filter (where is_due_as_of_date) as due_instalment_count,
        count(*) filter (where not is_due_as_of_date) as future_instalment_count,
        count(*) filter (
            where uncovered_scheduled_principal_amount > 0.00
        ) as uncovered_instalment_count,
        sum(
            case when is_due_as_of_date then scheduled_principal_amount else 0.00 end
        ) as scheduled_principal_due_amount,
        sum(
            case when not is_due_as_of_date then scheduled_principal_amount else 0.00 end
        ) as future_scheduled_principal_amount,
        sum(assumed_allocated_completed_payment_amount)
            as assumed_allocated_completed_payment_amount,
        sum(uncovered_scheduled_principal_amount)
            as scheduled_principal_shortfall_amount,
        min(due_date) filter (
            where uncovered_scheduled_principal_amount > 0.00
        ) as oldest_uncovered_due_date
    from {{ ref('fct_loan_schedule_allocation') }}
    group by account_id
),
payment_summary as (
    select
        payment.account_id,
        sum(payment.amount) as completed_payment_amount_as_of_date
    from {{ ref('fct_payment') }} as payment
    cross join {{ source('raw', 'run_parameters') }} as parameters
    where payment.is_successful
        and payment.payment_date <= parameters.as_of_date
    group by payment.account_id
),
expected as (
    select
        allocation.*,
        coalesce(payment.completed_payment_amount_as_of_date, 0.00)
            as completed_payment_amount_as_of_date
    from allocation_summary as allocation
    left join payment_summary as payment using (account_id)
)
select
    coalesce(expected.account_id, actual.account_id) as account_id,
    'Account summary does not reconcile to schedule allocation' as failure_reason
from expected
full outer join {{ ref('fct_loan_schedule_position') }} as actual using (account_id)
where expected.account_id is null
    or actual.account_id is null
    or expected.scheduled_instalment_count <> actual.scheduled_instalment_count
    or expected.due_instalment_count <> actual.due_instalment_count
    or expected.future_instalment_count <> actual.future_instalment_count
    or expected.uncovered_instalment_count <> actual.uncovered_instalment_count
    or expected.scheduled_principal_due_amount <> actual.scheduled_principal_due_amount
    or expected.future_scheduled_principal_amount
        <> actual.future_scheduled_principal_amount
    or expected.assumed_allocated_completed_payment_amount
        <> actual.assumed_allocated_completed_payment_amount
    or expected.scheduled_principal_shortfall_amount
        <> actual.scheduled_principal_shortfall_amount
    or expected.oldest_uncovered_due_date
        is distinct from actual.oldest_uncovered_due_date
    or expected.completed_payment_amount_as_of_date
        <> actual.completed_payment_amount_as_of_date
