with checked as (
    select
        *,
        sum(loan_account_count) over (partition by as_of_date)
            as recalculated_portfolio_account_count,
        sum(scheduled_principal_shortfall_amount) over (partition by as_of_date)
            as recalculated_portfolio_shortfall_amount,
        sum(portfolio_account_share) over (partition by as_of_date)
            as portfolio_account_share_total,
        sum(portfolio_shortfall_share) over (partition by as_of_date)
            as portfolio_shortfall_share_total
    from {{ ref('agg_loan_delinquency_product_risk') }}
)
select
    as_of_date,
    product_code,
    'Product risk metric or denominator is inconsistent' as failure_reason
from checked
where loan_account_count <= 0
    or severe_proxy_account_count < 0
    or severe_proxy_account_count > loan_account_count
    or portfolio_loan_account_count <> recalculated_portfolio_account_count
    or portfolio_scheduled_principal_shortfall_amount
        <> recalculated_portfolio_shortfall_amount
    or portfolio_account_share <> round(
        loan_account_count::decimal / portfolio_loan_account_count,
        4
    )
    or severe_proxy_account_share <> round(
        severe_proxy_account_count::decimal / loan_account_count,
        4
    )
    or abs(portfolio_account_share_total - 1.0000) > 0.0001
    or (
        portfolio_scheduled_principal_shortfall_amount <> 0.00
        and abs(portfolio_shortfall_share_total - 1.0000) > 0.0001
    )
    or scheduled_principal_due_amount < 0.00
    or assumed_allocated_completed_payment_amount < 0.00
    or scheduled_principal_shortfall_amount < 0.00
    or scheduled_principal_due_amount
        <> assumed_allocated_completed_payment_amount
            + scheduled_principal_shortfall_amount
    or portfolio_shortfall_share is distinct from case
        when portfolio_scheduled_principal_shortfall_amount = 0.00 then null
        else round(
            scheduled_principal_shortfall_amount
            / portfolio_scheduled_principal_shortfall_amount,
            4
        )
    end
    or due_principal_coverage_ratio is distinct from case
        when scheduled_principal_due_amount = 0.00 then null
        else round(
            assumed_allocated_completed_payment_amount
            / scheduled_principal_due_amount,
            4
        )
    end
