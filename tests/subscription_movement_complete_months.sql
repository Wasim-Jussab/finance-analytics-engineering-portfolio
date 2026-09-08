with reporting_months as (
    select calendar_date as reporting_month
    from {{ ref('dim_date') }}
    where calendar_date = month_start_date
),
plan_start_months as (
    select
        subscription_plan_id,
        date_trunc('month', min(start_date)) as first_reporting_month
    from {{ ref('dim_subscription') }}
    group by subscription_plan_id
),
expected as (
    select
        month.reporting_month,
        plan.product_code,
        plan.billing_frequency
    from reporting_months as month
    inner join plan_start_months as start_month
        on month.reporting_month >= start_month.first_reporting_month
    inner join {{ ref('dim_subscription_plan') }} as plan using (subscription_plan_id)
),
actual as (
    select
        reporting_month,
        product_code,
        billing_frequency
    from {{ ref('agg_subscription_movement_monthly') }}
)
select
    coalesce(expected.reporting_month, actual.reporting_month) as reporting_month,
    coalesce(expected.product_code, actual.product_code) as product_code,
    coalesce(expected.billing_frequency, actual.billing_frequency) as billing_frequency
from expected
full outer join actual
    on expected.reporting_month = actual.reporting_month
    and expected.product_code = actual.product_code
    and expected.billing_frequency = actual.billing_frequency
where expected.reporting_month is null or actual.reporting_month is null
