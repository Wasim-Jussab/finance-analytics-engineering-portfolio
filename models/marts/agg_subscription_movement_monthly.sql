with reporting_months as (
    select
        calendar_date as reporting_month,
        month_end_date
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
plan_months as (
    select
        month.reporting_month,
        month.month_end_date,
        plan.subscription_plan_id
    from reporting_months as month
    inner join plan_start_months as plan
        on month.reporting_month >= plan.first_reporting_month
),
movement_metrics as (
    select
        plan_month.reporting_month,
        plan_month.subscription_plan_id,
        count(*) filter (
            where subscription.start_date < plan_month.reporting_month
                and (
                    subscription.cancellation_date is null
                    or subscription.cancellation_date >= plan_month.reporting_month
                )
        ) as opening_agreement_count,
        count(*) filter (
            where subscription.start_date between
                plan_month.reporting_month and plan_month.month_end_date
        ) as started_agreement_count,
        count(*) filter (
            where subscription.cancellation_date between
                plan_month.reporting_month and plan_month.month_end_date
        ) as cancelled_agreement_count,
        count(*) filter (
            where subscription.start_date <= plan_month.month_end_date
                and (
                    subscription.cancellation_date is null
                    or subscription.cancellation_date > plan_month.month_end_date
                )
        ) as closing_agreement_count
    from plan_months as plan_month
    inner join {{ ref('dim_subscription') }} as subscription
        on plan_month.subscription_plan_id = subscription.subscription_plan_id
    group by plan_month.reporting_month, plan_month.subscription_plan_id
)
select
    movement.reporting_month,
    plan.product_code,
    plan.billing_frequency,
    movement.opening_agreement_count,
    movement.started_agreement_count,
    movement.cancelled_agreement_count,
    movement.started_agreement_count
        - movement.cancelled_agreement_count as net_agreement_change,
    movement.closing_agreement_count
from movement_metrics as movement
inner join {{ ref('dim_subscription_plan') }} as plan using (subscription_plan_id)
