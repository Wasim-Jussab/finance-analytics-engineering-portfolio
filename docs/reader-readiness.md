# Direct-reader readiness

For stage-by-stage failure timing, use the [lifecycle diagnostic](reader-lifecycle.md).

After the normal pipeline, run:

```bash
python -m finance_portfolio.reader_readiness --database data/finance.duckdb
```

The probe opens the original database read-only and compares population counts in
the two case-account reports and both team aggregates. It returns `ready` only if
all four reads succeed, counts agree and account checks pass. Both account reports
must have non-null account IDs and reporting dates, exactly one row per account,
and identical `(account_id, as_of_date)` sets. Counts and key checks run in one
read transaction. Equal counts cannot conceal substituted accounts or dates.
`account_checks` reports invalid-row counts, duplicate surplus rows and the
two-way account/date set difference count; no account identifiers are exposed.

Empty, agreeing populations are readable; this is not a non-empty, freshness,
aggregate group-membership or business-rule certification. A common but wrong
reporting date still passes: the probe compares reports, not an external expected
date. Those wider controls remain in dbt. Missing databases are not created.

Missing files, failed reads and mismatched populations return nonzero. Errors are
classified without exposing local filesystem paths. No partial counts are returned
after a read failure. The probe never deletes a WAL, repairs a database, substitutes
a file-only copy or claims that a successful build proves downstream availability.

This is intentionally a separate downstream-consumer check. `make verify` retains
its existing build/scenario/documentation gate; it does not silently acquire a new
promise of direct-reader availability. The probe exposes the known post-docs WAL
limitation rather than treating a copied database as evidence that the original
opened. A failing direct probe is not a request to discard recovery evidence.
