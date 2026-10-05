# Day 42 — make pipeline health enforceable

Yesterday's summary described completed runs but could not change the outcome of a build. I added a small versioned policy for minimum evidence, failure rate, latest-run status and selected stage-duration budgets.

The command now records all breaches before returning a failure code. I chose that over stopping at the first breach because the JSON should still explain the whole decision. Threshold equality passes, and a missing stage is not invented as a zero-second success.

This remains a repository quality gate over completed reports. It does not detect a process killed before reporting, page an operator or establish a production availability objective.
