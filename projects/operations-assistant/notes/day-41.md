# Day 41 — check the comparison when the baseline has no denominator

10 November 2026

I used the same comparison question with different typed windows. The
synthetic snapshot has no due shipments from 7–14 September, and 176 of
213 are on time in 14–21 September (UTC, exclusive ends). The volume
change can be reported, but the baseline rate and percentage-point change
must both remain null. The question API test checks that the answer says
why rather than inventing a percentage improvement.

I made this a required end-to-end release case. It tests the metric boundary
through actual local routing, not new language generalisation or generative
inference. The underlying calculation and deterministic renderer are unchanged.

The package gate passed: 155 tests, 11/11 end-to-end cases (seven answered,
four blocked), readiness, the saved-report replay and Ruff. The API test
returned HTTP 200 with a null change and the expected explanation.
