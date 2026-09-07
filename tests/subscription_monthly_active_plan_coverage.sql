with reporting_months as (
    select
        calendar_date as billing_month,
        month_end_date
    from {{ ref('dim_date') }}
    where calendar_date = month_start_date
),
expected as (
    select
        month.billing_month,
        plan.product_code,
        plan.billing_frequency,
        count(distinct subscription.subscription_id) as active_agreement_count
    from reporting_months as month
    inner join {{ ref('dim_subscription') }} as subscription
        on month.month_end_date >= subscription.start_date
        and month.billing_month <= date_trunc(
            'month',
            coalesce(
                subscription.cancellation_date,
                (select max(calendar_date) from {{ ref('dim_date') }})
            )
        )
    inner join {{ ref('dim_subscription_plan') }} as plan using (subscription_plan_id)
    group by month.billing_month, plan.product_code, plan.billing_frequency
),
actual as (
    select
        billing_month,
        product_code,
        billing_frequency,
        active_agreement_count
    from {{ ref('agg_subscription_monthly') }}
),
missing_or_extra as (
    select
        coalesce(expected.billing_month, actual.billing_month) as billing_month,
        coalesce(expected.product_code, actual.product_code) as product_code,
        coalesce(expected.billing_frequency, actual.billing_frequency) as billing_frequency,
        expected.active_agreement_count as expected_active_agreement_count,
        actual.active_agreement_count as actual_active_agreement_count
    from expected
    full outer join actual
        on expected.billing_month = actual.billing_month
        and expected.product_code = actual.product_code
        and expected.billing_frequency = actual.billing_frequency
    where expected.billing_month is null
        or actual.billing_month is null
        or expected.active_agreement_count <> actual.active_agreement_count
)
select * from missing_or_extra
