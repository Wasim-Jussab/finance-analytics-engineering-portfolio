# Day 55 — complete the reporting matrix without hiding missing combinations

The observed-band aggregate is the right source of truth, but a BI table that omits
unobserved combinations can be misread as incomplete data. I added a separate
reporting matrix containing every governed proxy band for every observed product
and reporting date. The eight combinations absent from this fixture are explicit
zero rows and carry an observation flag.

I kept the sparse aggregate rather than replacing it. That preserves the distinction
between a combination observed in source and a row manufactured for presentation.
The complete matrix reconciles every non-zero row to the sparse aggregate and each
product population back to the account-level fact.

The execution environment was unavailable today, so I could not run the local
`make verify` gate before publishing. I used the repository's exact-head GitHub
Actions gate as the independent executable check and will not merge the milestone
unless that commit passes. The proxy boundary remains unchanged: these bands are
not contractual arrears, default or IFRS 9 stages.
