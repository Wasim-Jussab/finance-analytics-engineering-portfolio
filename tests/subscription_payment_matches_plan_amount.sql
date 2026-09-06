select
    payment.subscription_payment_id,
    payment.amount as payment_amount,
    plan.billing_amount as expected_amount
from {{ ref('fct_subscription_payment') }} as payment
inner join {{ ref('dim_subscription') }} as subscription using (subscription_id)
inner join {{ ref('dim_subscription_plan') }} as plan using (subscription_plan_id)
where payment.amount <> plan.billing_amount
