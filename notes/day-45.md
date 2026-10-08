# Day 45 — prove the degraded health path

The healthy pipeline path was well covered, but the milestone still needed executable evidence that a failed run produces the intended operational decision. I added an isolated scenario with one successful run and one failed load, followed by a blocked dbt build.

A strict temporary policy must record four breaches: too few completed runs, excessive failure rate, a failed latest run and excessive generate duration. The scenario also reconciles the failed and blocked stages, then uses the separate Day 44 verifier to confirm the degraded artifact exactly matches its source evidence.

I kept the scenario out of the live run archive and real policy. Its own command returns success only when the expected degraded decision is observed, so CI can test the negative path without manufacturing a failed workflow. This closes the five-day pipeline-health milestone, but it still demonstrates repository controls rather than uptime monitoring or immutable external audit storage.
