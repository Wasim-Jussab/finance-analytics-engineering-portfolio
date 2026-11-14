# Day 45 — enforce grounding before the API returns an answer

14 November 2026

I moved the existing grounding evaluator onto both answer-producing API
paths. The runtime now refuses an answer that fails those checks before
returning it. A renderer defect is an internal output failure, so I use
HTTP 500 rather than suggesting that the user's request was invalid.

The regression first checks a healthy 200, then substitutes a summary with
the wrong rate and unchanged claims. Both the question and direct-answer
endpoints must return only a generic grounding failure. I kept the raw
tool route unchanged and documented that the prose checks are specific
to the summary template, not a general model-safety claim.

The review closes this five-session metric-boundary milestone. The only
inference remains local intent classification; the checks are deterministic.

The full local gate passed: 165 tests, 6/6 grounding cases, 13/13 question
cases, routing/adversarial evaluation, readiness, replay and Ruff. The
runtime regressions passed on both answer-producing endpoints.
