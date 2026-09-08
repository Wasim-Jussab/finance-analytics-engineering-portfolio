with sequenced as (
    select
        reporting_month,
        product_code,
        billing_frequency,
        opening_agreement_count,
        lag(closing_agreement_count) over (
            partition by product_code, billing_frequency
            order by reporting_month
        ) as previous_closing_count
    from {{ ref('agg_subscription_movement_monthly') }}
)
select *
from sequenced
where previous_closing_count is not null
    and opening_agreement_count <> previous_closing_count
