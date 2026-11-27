# Day 58 — separate diagnostics by business-question type

27 November 2026

I split the existing fixed routing diagnostics by expected intent, keeping
case denominators, raw/governed match counts and decision reasons together.
The four groups partition the same 18 cases; I did not create a new holdout.
The release evaluator is now 1.4.0 and recomputes these slices from rows,
refusing missing/extra groups, altered counts and float counters. Reports
from the previous evaluator must be regenerated. Training and thresholds
are unchanged.

Executed local classifier inference showed 5/5 raw matches for summary,
5/5 comparison and 3/3 exceptions, but only 2/5 for unsupported questions.
The unsupported group's governed outcomes were 5/5, with four guardrails
and one below-threshold refusal. This makes the dependence on policy visible;
it does not establish general accuracy, calibration or semantic novelty.
No generative model ran. All 20 focused diagnostic/CLI cases passed; Ruff
and diff checks passed.

Full `make verify` passed: 261 tests, 18/18 fixed routing, 27/27 adversarial,
6/6 grounding, 13/13 questions, runtime readiness, 18/18 proposal cases
and replay. An executed demo approved the actual reports and refused an
altered unsupported-intent count despite unchanged overall diagnostics.
The existing TestClient dependency warning remains non-failing. Metrics,
release verification and rendered answer text remain deterministic.
