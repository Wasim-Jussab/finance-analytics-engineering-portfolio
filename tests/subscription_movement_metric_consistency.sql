select
    reporting_month,
    product_code,
    billing_frequency,
    opening_agreement_count,
    started_agreement_count,
    cancelled_agreement_count,
    net_agreement_change,
    closing_agreement_count
from {{ ref('agg_subscription_movement_monthly') }}
where opening_agreement_count < 0
    or started_agreement_count < 0
    or cancelled_agreement_count < 0
    or closing_agreement_count < 0
    or net_agreement_change <> started_agreement_count - cancelled_agreement_count
    or closing_agreement_count
        <> opening_agreement_count + started_agreement_count - cancelled_agreement_count
