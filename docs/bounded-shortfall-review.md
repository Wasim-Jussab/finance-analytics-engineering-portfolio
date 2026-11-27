# Bounded read-only shortfall review

After the root setup and `make verify`, run:

```bash
python -m finance_portfolio.shortfall_review --snapshot-date 2025-12-31 --direction Increase --limit 3
```

The JSON reports one direction and snapshot date, full contributing-account
count and gross denominator, a ranked prefix, selected gross magnitude/share
and whether further accounts remain. Amounts are decimal strings; shares
are unrounded fractions. For the fixed December example the first three
accounts cover 1,354.19 of 2,754.15 gross increases (49.17% displayed), with
11 contributing accounts and further rows remaining.

The limit is an integer from 1 to 50. Direction is Increase or Decrease,
not arbitrary SQL. Queries use bound parameters and a read-only DuckDB
connection. A direction absent from a comparable observed month returns
an empty page with null population/amount/share fields, not invented zeros.
An unavailable snapshot or missing comparator is refused instead.

This consumer trusts the reconciled dbt models; run verification first.
These are synthetic principal-position changes, not cash collections,
default/recovery evidence or a treatment recommendation. The selected
prefix never replaces the full direction denominator. No model is used.

The reader now uses one read-only transaction and reconciles summary grain,
account count and gross magnitude against the full ranked direction before
applying the row cap. Account IDs must be unique, ranks contiguous and
distinct, and signs consistent with the selected direction. Missing or
duplicate summary rows and inconsistent populations are refused rather
than returned as apparently valid JSON. This is a targeted consumer check,
not a replacement for the full dbt contract or proof of source authenticity.

Contiguous ranks alone do not prove that a capped page contains the largest
movements. The reader also recomputes full-direction order by absolute
movement descending, then account ID ascending for ties, and refuses ranks
that disagree before applying the cap. This mirrors the current mart's
ranking contract; changing that contract requires updating both checks.
