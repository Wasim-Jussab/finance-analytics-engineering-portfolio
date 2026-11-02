# Day 70 — close the reader-control milestone without overstating reliability

2 November 2026

I added cross-module regressions demonstrating the distinction between readable
raw data, correct case membership and safe lock handling. Equal row counts can
hide different accounts; a completed run report cannot grant permission to bypass
the pipeline lock. The tests exercise the actual controls together.

I consolidated the five-session review and linked it from the concise root README.
The milestone delivers diagnostic and readiness controls, not a repair of the
historical WAL or local lock-retention behaviour. I have not deleted old locks
or treated a successful fresh run as proof that either issue is permanently fixed.

## Local verification and actual readiness result

`make verify` passed: 613 dbt results, 574 data tests, 116 Python tests, all
controlled scenarios, Ruff and dbt docs. All three targeted integration cases
passed separately. The root README is 486 words and links both projects.

After the standard run, the actual original-database probe returned unavailable
with `wal_replay_error`: reader not opened, WAL present, both count and account
results null. Lock status matched a successful completed run but still returned
`safe_to_remove: false`. I left the database, WAL and lock untouched.

The milestone's delivered scope is tested fail-closed controls and diagnostic
evidence, not a ready consumer database or WAL repair. The build passing is not
reported as successful original-reader availability. The review records this
current failure as well as yesterday's successful independent lifecycle.
