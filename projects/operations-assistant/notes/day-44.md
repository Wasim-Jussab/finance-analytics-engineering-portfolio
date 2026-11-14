# Day 44 — catch summary prose that disagrees with its claims

13 November 2026

The grounding evaluator already checked structured claims, evidence and
synthetic-data disclosure. That wasn't enough to reject a wrong number in
the text if the structured claims stayed correct. I added canonical summary
checks for due, on-time, late, overdue-open and cancelled counts and the rate.

The regression changes one number at a time while keeping claims and evidence
unchanged. Each pairing must fail for that labelled number. These checks
deliberately depend on our deterministic template. They are not a free-text
fact checker, and I haven't extended them to comparison or exception prose.
No generative model is introduced or evaluated.

The six focused mutation cases and the full local gate passed: 163 tests,
6/6 grounding cases, 13/13 question cases, classifier/adversarial checks,
readiness, saved-report replay and Ruff. Local intent classification ran
in the existing question evaluation; the new prose checks are deterministic.
