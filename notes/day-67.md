# Day 67 — equal counts are not equal populations

30 October 2026

I tightened the direct-reader probe to compare account/date sets, reject null keys
or dates and detect duplicate account rows. Two reports can have identical counts
while referring to different loans or months. I kept account grain explicit rather
than allowing one account at multiple dates to pass as unique account/month rows.

All reads now share one transaction. Diagnostics expose counts, not identifiers.
The aggregate checks still reconcile totals only, not group membership. Matching
empty reports and a common wrong date remain outside this readiness decision;
neither is evidence of business completeness or freshness. I did not change WAL
recovery behaviour or the build gate.

## Local verification and actual failure

All 13 readiness cases passed. The first full run stopped at source freshness:
dbt reported that the raw schema was missing despite the loader printing its
expected counts. An explicit reload and read confirmed the tables existed; the
full retry passed without a code change. I have not established the cause of that
first failure and do not describe the reload as a repair.

The completed `make verify` retry passed 9/9 freshness checks, 613 dbt resources,
574 data tests, 95 Python tests, all controlled scenarios, Ruff and dbt docs.

The actual post-documentation direct-reader probe failed closed with
`wal_replay_error`: WAL present, original reader not opened, counts and account
checks both null. I left the original database and WAL untouched. Unlike Day 66,
today's successful build does not mean the original database is consumer-ready.
The new key checks passed on controlled databases, not on this unreadable file.
