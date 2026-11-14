# Day 43 — keep both comparison denominators inside the region

12 November 2026

I added a required North-only comparison. A region label alone doesn't
prove a filter was applied to both numerator and denominator. I first ran
a direct grouped source query: North has 46 on time out of 53 due in the
baseline week and 47 out of 54 in the current week.

The API regression checks those counts, both rates and their percentage-point
change, and confirms North is retained in the evidence request. The release
case checks the two filtered cohorts too. I reused the known comparison
wording to isolate scope handling; this isn't a new language holdout or a
generative-model evaluation. All inference is still local classification.

The local gate passed: 157 tests, 13/13 question cases (nine answered,
four blocked), routing/adversarial checks, readiness, saved-report replay
and Ruff. The API returned HTTP 200 and the regional rate change matched
the calculation from 46/53 and 47/54.
