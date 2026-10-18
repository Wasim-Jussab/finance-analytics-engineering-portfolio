with expected as (
    select *
    from {{ ref('agg_loan_delinquency_by_product') }}
),
actual as (
    select *
    from {{ ref('agg_loan_delinquency_band_matrix') }}
    where is_observed_band
)
select
    coalesce(expected.as_of_date, actual.as_of_date) as as_of_date,
    coalesce(expected.product_code, actual.product_code) as product_code,
    coalesce(
        expected.delinquency_band_proxy,
        actual.delinquency_band_proxy
    ) as delinquency_band_proxy,
    'Observed matrix rows do not reconcile to the source aggregate'
        as failure_reason
from expected
full outer join actual
    on expected.as_of_date = actual.as_of_date
    and expected.product_code = actual.product_code
    and expected.delinquency_band_proxy = actual.delinquency_band_proxy
where expected.as_of_date is null
    or actual.as_of_date is null
    or expected.loan_account_count <> actual.loan_account_count
    or expected.product_loan_account_count
        <> actual.product_loan_account_count
    or expected.product_account_share <> actual.product_account_share
    or expected.scheduled_principal_due_amount
        <> actual.scheduled_principal_due_amount
    or expected.assumed_allocated_completed_payment_amount
        <> actual.assumed_allocated_completed_payment_amount
    or expected.scheduled_principal_shortfall_amount
        <> actual.scheduled_principal_shortfall_amount
    or expected.due_principal_coverage_ratio
        is distinct from actual.due_principal_coverage_ratio
