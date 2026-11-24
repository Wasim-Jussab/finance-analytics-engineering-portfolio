# Day 53 — correct the held-out claim

22 November 2026

While reviewing the evaluation and training examples, I found reused
wording in the suite described as held-out. The executed normalized
overlap audit found 5 of 18 cases overlap the reference training examples.
All 18 regressions still passed. That does not support the earlier
held-out description, and the 13 non-overlapping strings do not prove
independence, semantic novelty or absence of tuning either.

I added per-case overlap flags and report totals, carried the caveat into
release output, versioned the release evaluator and corrected current
documentation. Legacy held_out field and policy names remain compatibility
names for fixed regressions, not evidence of generalisation. The audit
refers to this repository's training specification, not arbitrary adapter
training data. Training, expected labels, thresholds and pass requirements
are unchanged. Historical learning notes are retained rather than rewritten.

Ruff sorted the new import. The focused audit/release tests passed.
This executes local classifier inference; there is still no generative
model. Full `make verify` passed: 231 tests, 18/18 fixed routing,
27/27 adversarial, 6/6 grounding, 13/13 question cases, readiness,
18/18 proposal cases and saved-report replay. The focused audit/release
tests were rerun after adding the release-scope assertions and passed.
The report and release output both retain the 5/13 overlap split.
Local HTTP checks returned a healthy summary and refused a delete request;
the server stopped. The existing TestClient warning remains non-failing.
