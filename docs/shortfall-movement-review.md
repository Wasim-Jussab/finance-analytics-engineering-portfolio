# Account shortfall movement review

Run `make verify` from the repository root, then use the local Python environment:

```bash
python - <<'PY'
import duckdb
with duckdb.connect('data/finance.duckdb', read_only=True) as con:
    print(con.execute("""
        select snapshot_date, position_state, contribution_account_count,
            increasing_account_count, decreasing_account_count, unchanged_account_count,
            gross_shortfall_increase_amount, gross_shortfall_decrease_amount,
            scheduled_principal_shortfall_change
        from mart.agg_loan_shortfall_by_membership
        where snapshot_date = date '2025-12-31'
        order by position_state
    """).fetchall())
PY
```

The fixed seed returns 25 continuing contribution accounts: 11 increasing,
zero decreasing and 14 unchanged. Gross increase is 2,754.15, gross decrease
0.00 and net change 2,754.15. These are synthetic principal-only positions,
not contractual arrears, collections flows or causal attribution.

The account contribution report unions current and prior-calendar-month
membership so prior-only accounts are retained. Entered/Exited describe
observed membership, not origination, closure, default or recovery.
Direction counts and changes are null without a comparator, not zero.
Do not add position amounts across snapshot dates.

The controlled fixture separately demonstrates +5, -3 and zero in one
continuing group: gross 5/3, net +2, one account per direction. The observed
December result does not demonstrate offsetting decreases. dbt checks
reconcile amounts to portfolio totals, the direction partition to population,
and each direction count to individually filtered account contributions.
