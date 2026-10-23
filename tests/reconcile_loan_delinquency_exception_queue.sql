with expected as (
    select *
    from {{ ref('fct_loan_delinquency_position') }}
    where scheduled_principal_shortfall_amount > 0.00
)
select
    coalesce(expected.account_id, actual.account_id) as account_id,
    coalesce(expected.as_of_date, actual.as_of_date) as as_of_date,
    'Exception queue does not reconcile to account-level proxy positions'
        as failure_reason
from expected
full outer join {{ ref('rpt_loan_delinquency_exception_queue') }} as actual
    using (account_id, as_of_date)
where expected.account_id is null
    or actual.account_id is null
    or expected.customer_id <> actual.customer_id
    or expected.product_code <> actual.product_code
    or expected.source_loan_status <> actual.source_loan_status
    or expected.scheduled_principal_due_amount
        <> actual.scheduled_principal_due_amount
    or expected.assumed_allocated_completed_payment_amount
        <> actual.assumed_allocated_completed_payment_amount
    or expected.scheduled_principal_shortfall_amount
        <> actual.scheduled_principal_shortfall_amount
    or expected.oldest_uncovered_due_date
        is distinct from actual.oldest_uncovered_due_date
    or expected.days_past_due_proxy <> actual.days_past_due_proxy
    or expected.schedule_position_status <> actual.schedule_position_status
    or expected.delinquency_band_proxy <> actual.delinquency_band_proxy
