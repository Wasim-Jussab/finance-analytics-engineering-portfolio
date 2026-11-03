# Executed proposal-planning integration evaluation

The package `make verify` gate now executes:

```bash
python -m operations_assistant.proposal_evaluation \
  --model-artifact artifacts/local-intent-model
```

The report at `reports/proposal-evaluation.json` names the verified artifact bytes,
adapter and model version. Every existing routing fixture runs through proposal
production, JSON/scope validation and governed-router authorisation. Correct tool
selection or required abstention is checked; any failed case makes the CLI nonzero.
The report retains case IDs rather than raw question text.

This **reuses the existing 18 routing fixtures**; it is not a new independent
holdout, an expanded accuracy claim or LLM evaluation. Comparison fixtures provide
explicit equal-length baseline dates, as the API already requires. Those typed
arguments are test inputs, not model-extracted dates. No tool or metric service is
executed by this evaluation; the existing grounding/end-to-end gates cover those
separate boundaries.

The actual implementation executes the classifier-backed proposal adapter and
the classifier veto. An intentionally wrong test-double producer must generate
a failing report, proving the harness does not simply count executed cases as
successes. No generative model was loaded. This report is an integration check,
not an additional production release approval or a substitute for existing gates.
