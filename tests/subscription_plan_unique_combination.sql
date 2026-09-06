select
    product_code,
    billing_frequency,
    count(*) as row_count
from {{ ref('dim_subscription_plan') }}
group by product_code, billing_frequency
having count(*) != 1
