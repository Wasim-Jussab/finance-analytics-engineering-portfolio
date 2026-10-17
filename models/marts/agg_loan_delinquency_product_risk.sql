with product_summary as (
    select
        as_of_date,
        product_code,
        count(*) as loan_account_count,
        sum(
            case when delinquency_band_proxy = '90+ days' then 1 else 0 end
        ) as severe_proxy_account_count,
        sum(scheduled_principal_due_amount) as scheduled_principal_due_amount,
        sum(assumed_allocated_completed_payment_amount)
            as assumed_allocated_completed_payment_amount,
        sum(scheduled_principal_shortfall_amount)
            as scheduled_principal_shortfall_amount
    from {{ ref('fct_loan_delinquency_position') }}
    group by as_of_date, product_code
),
with_portfolio_denominators as (
    select
        *,
        sum(loan_account_count) over (partition by as_of_date)
            as portfolio_loan_account_count,
        sum(scheduled_principal_shortfall_amount) over (partition by as_of_date)
            as portfolio_scheduled_principal_shortfall_amount
    from product_summary
)
select
    as_of_date,
    product_code,
    loan_account_count,
    portfolio_loan_account_count,
    round(
        loan_account_count::decimal / portfolio_loan_account_count,
        4
    ) as portfolio_account_share,
    severe_proxy_account_count,
    round(
        severe_proxy_account_count::decimal / loan_account_count,
        4
    ) as severe_proxy_account_share,
    scheduled_principal_due_amount,
    assumed_allocated_completed_payment_amount,
    scheduled_principal_shortfall_amount,
    portfolio_scheduled_principal_shortfall_amount,
    case
        when portfolio_scheduled_principal_shortfall_amount = 0.00 then null
        else round(
            scheduled_principal_shortfall_amount
            / portfolio_scheduled_principal_shortfall_amount,
            4
        )
    end as portfolio_shortfall_share,
    case
        when scheduled_principal_due_amount = 0.00 then null
        else round(
            assumed_allocated_completed_payment_amount
            / scheduled_principal_due_amount,
            4
        )
    end as due_principal_coverage_ratio
from with_portfolio_denominators
