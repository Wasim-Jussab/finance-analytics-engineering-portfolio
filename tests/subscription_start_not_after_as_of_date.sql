select
    subscription_id,
    start_date
from {{ ref('dim_subscription') }}
where start_date > (
    select as_of_date
    from {{ source('raw', 'run_parameters') }}
)
