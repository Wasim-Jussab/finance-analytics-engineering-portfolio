# Day 80 — close the coverage milestone with both zero-due boundaries

14 November 2026

I added an adjacent month with zero current due to the isolated fixture.
It now separately checks zero prior due, zero current due and a missing
calendar month. A previous coverage rate can still be shown when current
due is zero, but the change and both arithmetic effects must be null.

I wrote a short review with a runnable inspection query and the exact
December fixture. I also made the root overview point to this report.
The limits matter: changing cohorts and assumed principal allocation
don't support claims about cash flows or causal collections performance.

The focused boundary fixture and full local gate passed: 630 dbt results,
123 Python tests, controlled scenarios, Ruff, docs and lock cleanup.
The revised root overview remains 486 words.
