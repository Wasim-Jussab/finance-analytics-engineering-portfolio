# Day 48 — check the region and snapshot time shown to the reader

17 November 2026

Correct counts can still mislead if the answer labels another region or
an older snapshot. I added canonical prose checks for region and snapshot
time across summaries, comparisons and exception pages. The expected
scope comes from the approved result, not from the model's wording.

The regressions alter region or time while keeping claims and evidence
unchanged. Both answer API paths must refuse the wrong time for all
three tools. This checks displayed provenance, not external freshness,
authenticity or live operational state. The only inference remains the
local intent classifier; the guard itself is deterministic.

My first check lowercased the prose but not the expected ISO timestamp,
so the timestamp's uppercase T made healthy answers fail. The focused
tests caught this before publication. I normalized both sides and kept
the healthy-response assertions alongside the mutation cases.

After the correction, all 12 focused cases and the full gate passed:
192 tests, 6/6 grounding cases, 13/13 question cases, classifier/adversarial
evaluation, readiness, saved-report replay and Ruff. The live API checks
confirmed healthy 200s and refusal of incorrect displayed snapshot times.
