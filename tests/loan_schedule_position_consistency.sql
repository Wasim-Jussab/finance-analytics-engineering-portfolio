with invalid_rows as (
    select account_id, 'Amounts or counts are negative' as failure_reason
    from {{ ref('fct_loan_schedule_position') }}
    where scheduled_instalment_count < 0
        or due_instalment_count < 0
        or future_instalment_count < 0
        or uncovered_instalment_count < 0
        or scheduled_principal_due_amount < 0.00
        or assumed_allocated_completed_payment_amount < 0.00
        or scheduled_principal_shortfall_amount < 0.00
        or future_scheduled_principal_amount < 0.00
        or completed_payment_amount_as_of_date < 0.00
        or unallocated_completed_payment_amount < 0.00
        or days_past_due_proxy < 0
        or due_principal_coverage_ratio not between 0.00 and 1.00

    union all

    select account_id, 'Instalment counts do not reconcile' as failure_reason
    from {{ ref('fct_loan_schedule_position') }}
    where scheduled_instalment_count <> due_instalment_count + future_instalment_count

    union all

    select account_id, 'Principal due does not reconcile' as failure_reason
    from {{ ref('fct_loan_schedule_position') }}
    where scheduled_principal_due_amount
        <> assumed_allocated_completed_payment_amount
            + scheduled_principal_shortfall_amount

    union all

    select account_id, 'Scheduled principal does not reconcile to original balance'
        as failure_reason
    from {{ ref('fct_loan_schedule_position') }}
    where original_balance
        <> scheduled_principal_due_amount + future_scheduled_principal_amount

    union all

    select account_id, 'Completed payments do not reconcile' as failure_reason
    from {{ ref('fct_loan_schedule_position') }}
    where completed_payment_amount_as_of_date
        <> assumed_allocated_completed_payment_amount
            + unallocated_completed_payment_amount

    union all

    select account_id, 'Coverage ratio is inconsistent' as failure_reason
    from {{ ref('fct_loan_schedule_position') }}
    where due_principal_coverage_ratio is distinct from case
        when scheduled_principal_due_amount = 0.00 then null
        else round(
            assumed_allocated_completed_payment_amount
            / scheduled_principal_due_amount,
            4
        )
    end

    union all

    select account_id, 'Oldest uncovered date is inconsistent' as failure_reason
    from {{ ref('fct_loan_schedule_position') }}
    where (scheduled_principal_shortfall_amount = 0.00)
        <> (oldest_uncovered_due_date is null)

    union all

    select account_id, 'Days-past-due proxy is inconsistent' as failure_reason
    from {{ ref('fct_loan_schedule_position') }}
    where days_past_due_proxy <> case
        when oldest_uncovered_due_date is null then 0
        else date_diff('day', oldest_uncovered_due_date, as_of_date)
    end

    union all

    select account_id, 'Position status is inconsistent' as failure_reason
    from {{ ref('fct_loan_schedule_position') }}
    where schedule_position_status <> case
        when scheduled_principal_due_amount = 0.00 then 'Not Yet Due'
        when scheduled_principal_shortfall_amount = 0.00 then 'On Schedule'
        else 'Behind Schedule'
    end
)
select *
from invalid_rows
