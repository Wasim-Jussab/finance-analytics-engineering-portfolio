{% snapshot subscription_plan_history %}
{{
    config(
        target_schema='history',
        unique_key='subscription_plan_id',
        strategy='check',
        check_cols=['product_code', 'billing_frequency', 'billing_amount'],
        invalidate_hard_deletes=True
    )
}}

select
    subscription_plan_id,
    product_code,
    billing_frequency,
    billing_amount,
    load_id,
    loaded_at
from {{ source('raw', 'subscription_plans') }}

{% endsnapshot %}
