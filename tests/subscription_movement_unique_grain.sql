select
    reporting_month,
    product_code,
    billing_frequency,
    count(*) as row_count
from {{ ref('agg_subscription_movement_monthly') }}
group by reporting_month, product_code, billing_frequency
having count(*) != 1
