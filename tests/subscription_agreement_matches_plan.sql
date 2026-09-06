select
    subscription.subscription_id
from {{ ref('dim_subscription') }} as subscription
inner join {{ ref('dim_subscription_plan') }} as plan
    on subscription.subscription_plan_id = plan.subscription_plan_id
where subscription.product_code != plan.product_code
   or subscription.billing_frequency != plan.billing_frequency
