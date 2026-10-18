with checked as (
    select
        *,
        count(*) over (
            partition by as_of_date, product_code
        ) as band_row_count,
        sum(loan_account_count) over (
            partition by as_of_date, product_code
        ) as recalculated_product_account_count,
        sum(product_account_share) over (
            partition by as_of_date, product_code
        ) as product_account_share_total
    from {{ ref('agg_loan_delinquency_band_matrix') }}
)
select
    as_of_date,
    product_code,
    delinquency_band_proxy,
    'Complete delinquency matrix is internally inconsistent' as failure_reason
from checked
where band_row_count <> 4
    or product_loan_account_count <= 0
    or product_loan_account_count <> recalculated_product_account_count
    or abs(product_account_share_total - 1.0000) > 0.0001
    or loan_account_count < 0
    or scheduled_principal_due_amount < 0.00
    or assumed_allocated_completed_payment_amount < 0.00
    or scheduled_principal_shortfall_amount < 0.00
    or scheduled_principal_due_amount
        <> assumed_allocated_completed_payment_amount
            + scheduled_principal_shortfall_amount
    or is_observed_band <> (loan_account_count > 0)
    or (
        not is_observed_band
        and (
            loan_account_count <> 0
            or scheduled_principal_due_amount <> 0.00
            or assumed_allocated_completed_payment_amount <> 0.00
            or scheduled_principal_shortfall_amount <> 0.00
            or due_principal_coverage_ratio is not null
        )
    )
    or product_account_share <> round(
        loan_account_count::decimal / product_loan_account_count,
        4
    )
    or due_principal_coverage_ratio is distinct from case
        when scheduled_principal_due_amount = 0.00 then null
        else round(
            assumed_allocated_completed_payment_amount
            / scheduled_principal_due_amount,
            4
        )
    end
