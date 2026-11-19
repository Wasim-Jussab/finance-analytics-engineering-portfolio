with invalid_grain as (
    select account_id, snapshot_date
    from {{ ref('fct_loan_monthly_schedule_position') }}
    group by account_id, snapshot_date having count(*) <> 1
),
missing_or_extra as (
    (select account_id, snapshot_date from {{ ref('fct_loan_monthly_snapshot') }}
     except select account_id, snapshot_date from {{ ref('fct_loan_monthly_schedule_position') }})
    union all
    (select account_id, snapshot_date from {{ ref('fct_loan_monthly_schedule_position') }}
     except select account_id, snapshot_date from {{ ref('fct_loan_monthly_snapshot') }})
)
select account_id, snapshot_date from invalid_grain
union all
select account_id, snapshot_date from missing_or_extra
union all
select account_id, snapshot_date from {{ ref('fct_loan_monthly_schedule_position') }}
where scheduled_principal_due_amount < 0
    or assumed_allocated_completed_payment_amount < 0
    or scheduled_principal_shortfall_amount < 0
    or future_scheduled_principal_amount < 0
    or unallocated_completed_payment_amount < 0
    or scheduled_principal_due_amount <>
        assumed_allocated_completed_payment_amount + scheduled_principal_shortfall_amount
    or original_balance <> scheduled_principal_due_amount + future_scheduled_principal_amount
    or cumulative_completed_payment_amount <>
        assumed_allocated_completed_payment_amount + unallocated_completed_payment_amount
