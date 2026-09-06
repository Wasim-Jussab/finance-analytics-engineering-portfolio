select
    subscription_plan_id,
    product_code,
    billing_frequency,
    billing_amount
from {{ source('raw', 'subscription_plans') }}
