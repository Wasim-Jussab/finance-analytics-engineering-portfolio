# Day 87 — show concentration without netting the denominator

21 November 2026

I added full-direction gross amount, cumulative gross amount and cumulative
share to the ranked account report. Increase and decrease lists have
separate monthly denominators. A net movement can be small or negative,
so it would be a misleading denominator for either concentration curve.

The fixture uses +5/+5 and -9/-3: the first increase covers half of gross
increases, while the first decrease covers three quarters of gross
decreases. Another month resets the totals. Zero and unknown changes keep
null amounts/shares. These are unrounded fractions, not percentages.

All contribution accounts remain present. A top-N selection retains the
full direction denominator, and is descriptive movement, not a treatment
recommendation or causal explanation. Both focused fixtures and full
`make verify` passed: 666 dbt results, 129 Python tests, freshness,
history/incremental scenarios, degraded-path checks, Ruff and docs.
