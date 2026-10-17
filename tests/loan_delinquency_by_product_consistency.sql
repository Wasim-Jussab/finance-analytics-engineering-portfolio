with checked as (
    select
        *,
        sum(loan_account_count) over (
            partition by as_of_date, product_code
        ) as recalculated_product_loan_account_count,
        sum(product_account_share) over (
            partition by as_of_date, product_code
        ) as product_account_share_total
    from {{ ref('agg_loan_delinquency_by_product') }}
)
select
    as_of_date,
    product_code,
    delinquency_band_proxy,
    'Product-band metric or denominator is inconsistent' as failure_reason
from checked
where loan_account_count <= 0
    or product_loan_account_count <> recalculated_product_loan_account_count
    or product_account_share <> round(
        loan_account_count::decimal / product_loan_account_count,
        4
    )
    or abs(product_account_share_total - 1.0000) > 0.0001
    or scheduled_principal_due_amount < 0.00
    or assumed_allocated_completed_payment_amount < 0.00
    or scheduled_principal_shortfall_amount < 0.00
    or scheduled_principal_due_amount
        <> assumed_allocated_completed_payment_amount
            + scheduled_principal_shortfall_amount
    or due_principal_coverage_ratio is distinct from case
        when scheduled_principal_due_amount = 0.00 then null
        else round(
            assumed_allocated_completed_payment_amount
            / scheduled_principal_due_amount,
            4
        )
    end
