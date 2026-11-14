# Portfolio coverage — Days 76–80

I built two month-end reports from the tested synthetic principal schedule:

- `agg_loan_portfolio_total_monthly`: account count, principal due, assumed
  allocation, shortfall and coverage. Coverage uses summed amounts, not
  the average of product rates.
- `rpt_loan_portfolio_monthly_change`: adjacent-calendar-month differences,
  current/prior coverage and an explicit allocation-first, due-second bridge.

Run `make verify` from the repository root. It builds the reports, checks
their grain and reconciliation, executes the isolated gap/rounding/zero-due
fixtures and runs the historical-change scenarios. Then inspect:

```sql
select snapshot_date, previous_snapshot_date, loan_account_count,
       scheduled_principal_due_amount, assumed_allocated_completed_payment_amount,
       scheduled_principal_shortfall_amount, due_principal_coverage_ratio,
       coverage_change_percentage_points,
       allocation_first_effect_percentage_points, due_second_effect_percentage_points
from mart.rpt_loan_portfolio_monthly_change
order by snapshot_date desc;
```

The fixed fixture has 24 observed month ends. At 31 December 2025 it has
25 accounts, 57,712.01 principal due and 6,025.00 allocated, leaving
51,687.01 shortfall. Coverage is 10.44%. The unrounded-input change from
November is -0.523177 percentage points, split into 0 allocation-first
and -0.523177 due-second under the documented sequence.

The reports expose amount inputs and comparator dates. Missing calendar
months do not become previous observations, and either zero denominator
makes the rate change and both effects null. The arithmetic components sum
within 0.000002 percentage points after rounding.

These positions use changing cohorts. They are not monthly cash receipts,
contractual arrears, migrations, default probabilities or IFRS 9 stages.
The bridge is order-dependent algebra, not causal attribution. A successful
build does not establish a permanent repair of the historical WAL failure.
The detailed [implementation contract](implementation-guide.md) records
the assumptions and formulas.
