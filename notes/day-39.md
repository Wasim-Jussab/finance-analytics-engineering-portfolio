# Day 39 — retain each completed run

The latest-run report was useful for a quick status check, but the next invocation replaced it. That made it impossible to compare a failed load with a later successful rerun unless someone copied the file manually.

I now save each completed report under `reports/runs/<run-id>.json` before replacing the latest report. The archive uses exclusive creation: reusing a run ID fails rather than replacing existing evidence. Both successful and failed stage results are kept.

The tests run success followed by failure and verify the original bytes remain intact. A separate collision test checks that neither the archive nor the latest report changes.

This is local operational evidence, not tamper-proof storage. Abrupt process termination can still leave an unfinished run without a completed report, and archive retention is not implemented.
