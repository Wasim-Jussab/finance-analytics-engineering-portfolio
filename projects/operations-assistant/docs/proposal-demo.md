# Weekly delivery comparison demo

From the operations package, run `make verify`, then `make proposal-demo` to
repeat the demonstration. The package gate also runs the demo with the release
decisions it just produced. Use only artifacts you generated locally; the
existing classifier loader uses joblib, and fingerprints do not authenticate
an untrusted artifact and manifest.

The demo asks how the current week compares with the prior week. The CLI fixes
both UTC promised-date windows, `[2026-09-14, 2026-09-21)` and
`[2026-09-21, 2026-09-28)`, across all regions. Dates are not inferred from text.
It checks readiness against the saved routing and question release decisions,
loads the verified classifier, then validates its proposal against typed scope
and the existing router. The router and proposal adapter use the same classifier;
their agreement is a policy check, not independent model confirmation.

Only the approved comparison runs, on a newly generated temporary synthetic
snapshot via the existing read-only executor. The JSON includes exact classifier
and release IDs, snapshot ID, typed request, evidence ID, claims and deterministic
answer. The prior cohort completed **176/213** on time (82.63%); the current
cohort completed **153/218** (70.18%), down **12.45 percentage points**. Current
due shipments reconcile to 153 on time + 44 delivered late + 21 overdue open;
six cancellations are excluded. Both cohorts are measured in one snapshot, not
as observed at two historical cutoffs. A region's change is not proof of cause.

This is a reproducible example, not a new holdout or approval for the proposal
path in production. It does not change the public API. Local classifier inference
executes; no generative inference is implemented or run.

The demo also emits the same core decision trace as the question API for the
same model, question, typed scope and synthetic snapshot. The trace binds the
claims and tool evidence; it omits raw question text. Proposal and release
details remain separate in the demo output, so matching decision IDs show
parity of the core decision, not identical execution paths. The digest is not
a signature or an immutable audit log.

The demo checks that its structured claims, evidence ID, contract version
and executed request match its decision trace before printing the answer.
This catches inconsistent pairing, such as claims edited after the trace
was built or evidence for a different region. It does not replay source
data, authenticate the bundle, or verify the free-text rendering by itself.

To replay the fixed synthetic comparison from a saved JSON report, run these
commands after the package gate:

```sh
python -m operations_assistant.proposal_demo > weekly-comparison.json
python -m operations_assistant.proposal_demo --verify-report weekly-comparison.json
```

Replay regenerates the synthetic data and recomputes the approved comparison.
It checks the claims, complete evidence and rendered answer; no report input
chooses the tool or windows. It neither loads a model nor revalidates routing
or release records. This verifies reproducibility, not authorship or
independent model accuracy.
