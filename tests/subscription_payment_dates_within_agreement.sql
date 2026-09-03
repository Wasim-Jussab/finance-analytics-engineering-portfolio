select
    payment.subscription_payment_id,
    payment.subscription_id,
    payment.billing_date,
    subscription.start_date,
    subscription.cancellation_date
from {{ ref('fct_subscription_payment') }} as payment
inner join {{ ref('dim_subscription') }} as subscription using (subscription_id)
where payment.billing_date < subscription.start_date
    or (
        subscription.cancellation_date is not null
        and payment.billing_date > subscription.cancellation_date
    )
