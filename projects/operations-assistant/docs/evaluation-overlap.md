# Fixed routing regressions are not an independent holdout

The intent evaluation now compares each question with this repository's
reference training examples after lowercasing, replacing non-ASCII-alphanumeric
characters with spaces and collapsing whitespace. The report records the
per-case overlap flag and total overlapping/non-overlapping counts.

The 22 November 2026 execution found 5 overlapping and 13 non-overlapping
cases, with 18/18 fixed regressions passing. The 13 are not a newly sealed
holdout and must not be presented as independent accuracy evidence.

This check found reused training wording in the suite previously described
as held-out. That description overstated the evidence. A passing score over
these 18 fixed cases is a regression result, not independent generalisation
accuracy. Non-overlap does not prove semantic novelty or absence of tuning.
The audit describes the reference training specification, not arbitrary
third-party adapter training data.

The classifier, training examples, thresholds, expected labels and pass
requirements are unchanged. Existing `held_out_*` JSON fields and the
`require_all_held_out_cases_pass` policy key remain compatibility names;
they mean the fixed routing regression suite. The release output includes
an explicit evaluation-scope caveat and carries the overlap audit forward.

Run `make verify` locally. Inspect `reports/intent-evaluation.json` and
`reports/routing-release.json`. This executes the local classifier. It
does not execute or evaluate an LLM, and the answers remain deterministic.

Release evaluator 1.2.0 now requires this audit. It recomputes each case's
normalized reference-training membership, requires boolean flags and integer
totals, reconciles both cohort counts, checks the normalization contract and
rejects an independent-holdout claim. Even coherently edited flags/totals
must agree with reference membership. Old reports without the audit must be
regenerated; routing policy thresholds and training remain unchanged.
This is validation of supplied local evidence, not authentication of the
dataset's origin or proof that reported predictions were actually executed.
