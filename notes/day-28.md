# Day 28 — retaining evidence for each incremental run

Day 27 proved the final payment state was correct after each source change. What I
could not see afterwards was the sequence of runs that produced it. The dbt output
showed that tests passed, but the database retained only the latest fact state.

I added an append-only audit model with one row per selected dbt invocation. It
records raw payment count, physical fact count, current fact count, retained absent
rows, collection totals and two exception counts. The row is reconciled only when
the current raw snapshot agrees with current reporting and the physical fact also
accounts for any retained absent rows.

I extended the existing temporary-database scenario rather than inventing a second
test. Its six builds now leave six audit rows: unchanged baseline, insert and
correction, unchanged rerun, source absence, restoration and a final unchanged
rerun. Each selected build passed 50 results, and Python also checked that exactly
six rows were appended and that the latest metrics matched the expected state after
every step.

The first scenario launch hit the same DuckDB recovery-file replay problem seen on
earlier days, before any of these assertions ran. I preserved the recovery file
outside the repository and reran against the checkpointed database. I have kept
that separate from the evidence for the new control.

This is useful run evidence, but it is not full observability. The audit lives in
the same DuckDB file, has no alerting and is appended only when the downstream model
is selected. It also records the resulting population and totals rather than a
row-by-row change set. A production version would normally write run results to an
independent control store and connect failures to monitoring.
