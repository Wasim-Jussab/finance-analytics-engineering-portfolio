select
    billing_month,
    product_code,
    billing_frequency,
    count(*) as row_count
from {{ ref('agg_subscription_monthly') }}
group by billing_month, product_code, billing_frequency
having count(*) > 1
