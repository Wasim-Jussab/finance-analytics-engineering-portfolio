select
    subscription.subscription_id,
    subscription.customer_id,
    subscription.product_code,
    subscription.start_date,
    date_diff('month', subscription.start_date, parameters.as_of_date)
        - case
            when day(parameters.as_of_date) < day(subscription.start_date) then 1
            else 0
          end as months_since_start,
    subscription.billing_frequency,
    subscription.status,
    subscription.status = 'Active' as is_active
from {{ source('raw', 'subscriptions') }} as subscription
cross join {{ source('raw', 'run_parameters') }} as parameters
