with expected as (
    select
        as_of_date,
        product_code,
        delinquency_band_proxy,
        count(*) as loan_account_count,
        sum(scheduled_principal_due_amount) as scheduled_principal_due_amount,
        sum(assumed_allocated_completed_payment_amount)
            as assumed_allocated_completed_payment_amount,
        sum(scheduled_principal_shortfall_amount)
            as scheduled_principal_shortfall_amount
    from {{ ref('fct_loan_delinquency_position') }}
    group by as_of_date, product_code, delinquency_band_proxy
)
select
    coalesce(expected.as_of_date, actual.as_of_date) as as_of_date,
    coalesce(expected.product_code, actual.product_code) as product_code,
    coalesce(expected.delinquency_band_proxy, actual.delinquency_band_proxy)
        as delinquency_band_proxy,
    'Product-band summary does not reconcile to account-level positions'
        as failure_reason
from expected
full outer join {{ ref('agg_loan_delinquency_by_product') }} as actual
    using (as_of_date, product_code, delinquency_band_proxy)
where expected.as_of_date is null
    or actual.as_of_date is null
    or expected.loan_account_count <> actual.loan_account_count
    or expected.scheduled_principal_due_amount
        <> actual.scheduled_principal_due_amount
    or expected.assumed_allocated_completed_payment_amount
        <> actual.assumed_allocated_completed_payment_amount
    or expected.scheduled_principal_shortfall_amount
        <> actual.scheduled_principal_shortfall_amount
