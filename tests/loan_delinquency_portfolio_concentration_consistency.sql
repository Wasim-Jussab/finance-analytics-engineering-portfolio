with expected as (
    select
        as_of_date,
        count(*) as observed_product_count,
        max(portfolio_loan_account_count) as portfolio_loan_account_count,
        sum(severe_proxy_account_count) as severe_proxy_account_count,
        sum(scheduled_principal_due_amount) as scheduled_principal_due_amount,
        sum(assumed_allocated_completed_payment_amount)
            as assumed_allocated_completed_payment_amount,
        max(portfolio_scheduled_principal_shortfall_amount)
            as scheduled_principal_shortfall_amount,
        round(sum(power(
            loan_account_count::decimal / portfolio_loan_account_count, 2
        )), 4) as account_concentration_hhi,
        case
            when max(portfolio_scheduled_principal_shortfall_amount) = 0.00
                then null
            else round(sum(power(
                scheduled_principal_shortfall_amount
                / portfolio_scheduled_principal_shortfall_amount, 2
            )), 4)
        end as shortfall_concentration_hhi
    from {{ ref('agg_loan_delinquency_product_risk') }}
    group by as_of_date
)
select
    coalesce(expected.as_of_date, actual.as_of_date) as as_of_date,
    'Portfolio concentration summary is inconsistent' as failure_reason
from expected
full outer join {{ ref('agg_loan_delinquency_portfolio_concentration') }} as actual
    using (as_of_date)
where expected.as_of_date is null
    or actual.as_of_date is null
    or expected.observed_product_count <> actual.observed_product_count
    or expected.portfolio_loan_account_count <> actual.portfolio_loan_account_count
    or expected.severe_proxy_account_count <> actual.severe_proxy_account_count
    or expected.scheduled_principal_due_amount
        <> actual.scheduled_principal_due_amount
    or expected.assumed_allocated_completed_payment_amount
        <> actual.assumed_allocated_completed_payment_amount
    or expected.scheduled_principal_shortfall_amount
        <> actual.scheduled_principal_shortfall_amount
    or expected.account_concentration_hhi <> actual.account_concentration_hhi
    or expected.shortfall_concentration_hhi
        is distinct from actual.shortfall_concentration_hhi
    or actual.account_effective_product_count
        <> round(1 / actual.account_concentration_hhi, 2)
    or actual.shortfall_effective_product_count is distinct from case
        when actual.shortfall_concentration_hhi is null then null
        else round(1 / actual.shortfall_concentration_hhi, 2)
    end
