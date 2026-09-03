with subscription_base as (
    select
        subscription.*,
        parameters.as_of_date,
        coalesce(subscription.cancellation_date, parameters.as_of_date) as active_end_date
    from {{ source('raw', 'subscriptions') }} as subscription
    cross join {{ source('raw', 'run_parameters') }} as parameters
)
select
    subscription_id,
    customer_id,
    product_code,
    start_date,
    date_diff('month', start_date, as_of_date)
        - case
            when day(as_of_date) < day(start_date) then 1
            else 0
          end as months_since_start,
    cancellation_date,
    date_diff('month', start_date, active_end_date)
        - case
            when day(active_end_date) < day(start_date) then 1
            else 0
          end as active_months,
    billing_frequency,
    status,
    status = 'Active' as is_active
from subscription_base
