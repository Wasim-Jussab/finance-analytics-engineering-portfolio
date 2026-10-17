with product_risk as (
    select *
    from {{ ref('agg_loan_delinquency_product_risk') }}
),
ranked as (
    select
        *,
        row_number() over (
            partition by as_of_date
            order by loan_account_count desc, product_code
        ) as account_rank,
        row_number() over (
            partition by as_of_date
            order by scheduled_principal_shortfall_amount desc, product_code
        ) as shortfall_rank
    from product_risk
),
portfolio as (
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
        max(case when account_rank = 1 then product_code end)
            as largest_account_product_code,
        max(case when account_rank = 1 then loan_account_count end)
            as largest_account_product_count,
        max(case when shortfall_rank = 1 then product_code end)
            as largest_shortfall_product_code,
        max(
            case
                when shortfall_rank = 1
                    then scheduled_principal_shortfall_amount
            end
        ) as largest_product_shortfall_amount,
        sum(
            power(
                loan_account_count::decimal / portfolio_loan_account_count,
                2
            )
        ) as account_concentration_hhi,
        case
            when max(portfolio_scheduled_principal_shortfall_amount) = 0.00
                then null
            else sum(
                power(
                    scheduled_principal_shortfall_amount
                    / portfolio_scheduled_principal_shortfall_amount,
                    2
                )
            )
        end as shortfall_concentration_hhi
    from ranked
    group by as_of_date
)
select
    as_of_date,
    observed_product_count,
    portfolio_loan_account_count,
    severe_proxy_account_count,
    round(
        severe_proxy_account_count::decimal / portfolio_loan_account_count,
        4
    ) as severe_proxy_account_share,
    scheduled_principal_due_amount,
    assumed_allocated_completed_payment_amount,
    scheduled_principal_shortfall_amount,
    largest_account_product_code,
    largest_account_product_count,
    round(
        largest_account_product_count::decimal / portfolio_loan_account_count,
        4
    ) as largest_account_product_share,
    largest_shortfall_product_code,
    largest_product_shortfall_amount,
    case
        when scheduled_principal_shortfall_amount = 0.00 then null
        else round(
            largest_product_shortfall_amount
            / scheduled_principal_shortfall_amount,
            4
        )
    end as largest_product_shortfall_share,
    round(account_concentration_hhi, 4) as account_concentration_hhi,
    round(1 / account_concentration_hhi, 2) as account_effective_product_count,
    round(shortfall_concentration_hhi, 4) as shortfall_concentration_hhi,
    case
        when shortfall_concentration_hhi is null then null
        else round(1 / shortfall_concentration_hhi, 2)
    end as shortfall_effective_product_count
from portfolio
