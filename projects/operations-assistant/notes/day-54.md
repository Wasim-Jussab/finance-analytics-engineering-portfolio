# Day 54 — validate the overlap evidence before release

23 November 2026

Yesterday's report disclosed reused training wording, but the release gate
only carried its audit metadata forward. I made that evidence mandatory
and recomputed each case's normalized membership in the reference training
examples. Counts, boolean flags, normalization and the no-independent-holdout
caveat must agree. Even consistently edited flags and totals must match
the reference question membership.

The controlled mutations preserve the 18 passing routing results while
changing the audit evidence. They are test inputs, not corruption found
in the generated report. Old reports without the audit need regeneration.
Release evaluator version is 1.2.0; training, router thresholds and expected
labels are unchanged. This validates supplied local evidence, not dataset
origin or proof of inference. The underlying suite remains fixed regression
evidence rather than independent generalisation accuracy.

All 17 focused overlap/release cases and full `make verify` passed:
241 Python tests, 18/18 fixed routing, 27/27 adversarial, 6/6 grounding,
13/13 question cases, readiness, 18/18 proposal cases and saved-report
replay. Ruff passed. A separate executed evidence demo approved the valid
report but refused a copied report with coherently edited flags/totals;
the 18 passing routing outcomes were unchanged. The real audit remains
5 overlapping and 13 non-overlapping cases. The existing TestClient
dependency warning remains non-failing. No generative inference ran.
