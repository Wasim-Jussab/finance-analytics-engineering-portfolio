# Day 29 — comparing consecutive payment runs

Yesterday's audit retained the output of each selected dbt run. I could inspect
one run at a time, but I still had to calculate the difference myself to see what
changed between runs. I added a view that puts those net differences alongside
each recorded state.

I kept the first run's differences null. There is no earlier record to subtract,
and showing zero would imply that the first run changed nothing. For later runs,
the view compares raw, physical and current payment counts, retained absent keys,
completed attempts and collected amount. A test checks every difference against
the two underlying audit rows, including the previous run ID.

The six-step scenario now checks the numbers rather than only the final state:
an unchanged rerun has zero differences; adding a late failed attempt and
correcting an existing failed one increases current keys by one and collected
attempts by one. When a completed payment disappears from the raw snapshot,
physical keys stay level, current keys fall by one and absent keys rise by one.
Restoration reverses that movement. The collected-amount differences use the
actual synthetic payment amount rather than a hard-coded price. All six selected
builds passed 55 results.

The first local scenario failed before it could reach those assertions. I ran it
against a custom database filename, but the shared copy helper renamed the file
to `finance.duckdb`. The new persisted DuckDB view still referenced the original
catalogue. Preserving the filename in the isolated copy fixed that, and the older
history scenarios also passed. This is a portability detail worth remembering
when I use persisted views in temporary databases.

These are net changes, not a row-level change log. Zero movement could conceal
offsetting corrections, and a negative collection difference does not by itself
mean a refund. For that, I would need payment-level event data and an agreed
business interpretation.
