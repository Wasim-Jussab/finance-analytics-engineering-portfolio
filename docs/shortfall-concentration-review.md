# Ranked shortfall concentration review

Run `make verify` from the repository root, then use the same environment:

```bash
python - <<'PY'
import duckdb
with duckdb.connect('data/finance.duckdb', read_only=True) as con:
    print(con.execute("""
        select change_direction, contributing_account_count,
            accounts_to_review_threshold, direction_gross_change_amount,
            covered_gross_change_amount, covered_gross_change_share,
            previous_rank_gross_change_share
        from mart.agg_loan_shortfall_concentration
        where snapshot_date = date '2025-12-31'
        order by change_direction
    """).fetchall())
    print(con.execute("""
        select r.account_id, r.direction_rank,
            r.scheduled_principal_shortfall_change
        from mart.rpt_loan_shortfall_change_ranked r
        join mart.agg_loan_shortfall_concentration a
            on r.snapshot_date = a.snapshot_date
            and r.change_direction = a.change_direction
        where r.snapshot_date = date '2025-12-31'
            and r.direction_rank <= a.accounts_to_review_threshold
        order by r.change_direction, r.direction_rank
    """).fetchall())
PY
```

December has 11 increasing contribution accounts with gross increase
2,754.15. The first six cover 2,218.06, or 80.54% displayed; the preceding
five cover 70.95%. The stored shares are unrounded fractions. There is no
decrease row for this month, not a manufactured zero-population observation.

The 80% threshold is a fixed descriptive review choice, not treatment policy.
Ranks are ordinal: absolute change descending, account ID ascending for ties.
The tied-account fixture crosses exactly 80% at rank two and preserves that
order. Zero and unknown changes stay unranked; missing comparators stay null.
The [movement review](shortfall-movement-review.md) explains the underlying
membership union and gross/net reconciliation.

Use one snapshot date. Do not sum cumulative shares or positions across dates.
Keep increase/decrease gross denominators separate; net movement is not the
denominator. These are synthetic principal-only position changes, not cash
collections, contractual arrears, recovery/default events or causal evidence.
