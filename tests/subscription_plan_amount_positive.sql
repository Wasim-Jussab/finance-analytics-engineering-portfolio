select
    subscription_plan_id,
    billing_amount
from {{ ref('dim_subscription_plan') }}
where billing_amount <= 0
