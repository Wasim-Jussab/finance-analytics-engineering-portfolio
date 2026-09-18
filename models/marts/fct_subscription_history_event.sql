with status_changes as (
    select
        concat('status_change:', status_change_id) as event_id,
        status_change_id as source_version_id,
        subscription_id,
        'Status Change' as event_type,
        previous_status,
        new_status,
        business_event_date,
        observed_at,
        observation_delay_days,
        true as is_business_status_change
    from {{ ref('fct_subscription_status_change') }}
),

source_removals as (
    select
        concat('source_removal:', removal_id) as event_id,
        removal_id as source_version_id,
        subscription_id,
        'Source Removal' as event_type,
        last_observed_status as previous_status,
        cast(null as varchar) as new_status,
        cast(null as date) as business_event_date,
        removed_at as observed_at,
        cast(null as bigint) as observation_delay_days,
        false as is_business_status_change
    from {{ ref('fct_subscription_source_removal') }}
)

select * from status_changes
union all
select * from source_removals
