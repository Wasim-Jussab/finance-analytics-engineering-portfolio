{% snapshot subscription_agreement_history %}
{{
    config(
        target_schema='history',
        unique_key='subscription_id',
        strategy='check',
        check_cols=[
            'customer_id',
            'product_code',
            'subscription_plan_id',
            'start_date',
            'cancellation_date',
            'billing_frequency',
            'status'
        ],
        invalidate_hard_deletes=True
    )
}}

select
    subscription_id,
    customer_id,
    product_code,
    subscription_plan_id,
    start_date,
    cancellation_date,
    billing_frequency,
    status,
    load_id,
    loaded_at
from {{ source('raw', 'subscriptions') }}

{% endsnapshot %}
