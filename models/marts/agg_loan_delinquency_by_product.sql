with band_summary as (
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
),
product_totals as (
    select
        as_of_date,
        product_code,
        sum(loan_account_count) as product_loan_account_count
    from band_summary
    group by as_of_date, product_code
)
select
    summary.as_of_date,
    summary.product_code,
    summary.delinquency_band_proxy,
    summary.loan_account_count,
    totals.product_loan_account_count,
    round(
        summary.loan_account_count::decimal
        / totals.product_loan_account_count,
        4
    ) as product_account_share,
    summary.scheduled_principal_due_amount,
    summary.assumed_allocated_completed_payment_amount,
    summary.scheduled_principal_shortfall_amount,
    case
        when summary.scheduled_principal_due_amount = 0.00 then null
        else round(
            summary.assumed_allocated_completed_payment_amount
            / summary.scheduled_principal_due_amount,
            4
        )
    end as due_principal_coverage_ratio
from band_summary as summary
inner join product_totals as totals using (as_of_date, product_code)
