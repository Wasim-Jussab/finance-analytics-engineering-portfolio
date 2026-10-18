with observed as (
    select *
    from {{ ref('agg_loan_delinquency_by_product') }}
),
reporting_scope as (
    select
        as_of_date,
        product_code,
        max(product_loan_account_count) as product_loan_account_count
    from observed
    group by as_of_date, product_code
),
bands as (
    select 'Current' as delinquency_band_proxy, 1 as band_sort
    union all
    select '1-29 days', 2
    union all
    select '30-89 days', 3
    union all
    select '90+ days', 4
),
matrix as (
    select
        scope.as_of_date,
        scope.product_code,
        bands.delinquency_band_proxy,
        bands.band_sort,
        scope.product_loan_account_count,
        coalesce(observed.loan_account_count, 0) as loan_account_count,
        coalesce(observed.scheduled_principal_due_amount, 0.00)
            as scheduled_principal_due_amount,
        coalesce(observed.assumed_allocated_completed_payment_amount, 0.00)
            as assumed_allocated_completed_payment_amount,
        coalesce(observed.scheduled_principal_shortfall_amount, 0.00)
            as scheduled_principal_shortfall_amount,
        observed.delinquency_band_proxy is not null as is_observed_band
    from reporting_scope as scope
    cross join bands
    left join observed
        on scope.as_of_date = observed.as_of_date
        and scope.product_code = observed.product_code
        and bands.delinquency_band_proxy = observed.delinquency_band_proxy
)
select
    as_of_date,
    product_code,
    delinquency_band_proxy,
    loan_account_count,
    product_loan_account_count,
    round(
        loan_account_count::decimal / product_loan_account_count,
        4
    ) as product_account_share,
    scheduled_principal_due_amount,
    assumed_allocated_completed_payment_amount,
    scheduled_principal_shortfall_amount,
    case
        when scheduled_principal_due_amount = 0.00 then null
        else round(
            assumed_allocated_completed_payment_amount
            / scheduled_principal_due_amount,
            4
        )
    end as due_principal_coverage_ratio,
    is_observed_band
from matrix
order by as_of_date, product_code, band_sort
