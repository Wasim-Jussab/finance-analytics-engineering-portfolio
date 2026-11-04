# Days 31–35: bounded proposal production, authorisation and evidence

The delivered business boundary is narrow: a caller supplies governed dates and
filters; a local classifier proposes one of three approved reporting tools; the
request is checked before any application execution. The proposed call is not
permission to run arbitrary SQL, change data, invent dates or bypass release policy.

## Delivered components

- JSON validation rejects duplicate keys, non-finite constants, unknown arguments,
  changed scope, dropped snapshot expectations and oversized output.
- Existing classifier/policy agreement vetoes wrong tools and blocked questions.
- A swappable producer interface has one executed classifier-backed implementation.
- An artifact-bound planning evaluation runs 18 **reused routing fixtures** through
  the adapter and validation path; it is not a new independent model holdout.
- The CLI handoff regression verifies that the report names the exact verified
  artifact, then corrupts a locally generated fixture and confirms rejection before
  a new report can replace the prior result.

## Reproduce

From this independently installable package directory:

```bash
python -m pip install -e ".[dev]"
make verify
python -m operations_assistant.proposal_evaluation \
  --model-artifact artifacts/local-intent-model
```

The planning report is `reports/proposal-evaluation.json`. It distinguishes model
artifact identity, adapter, model version, per-case outcomes and explicit false
flags for generative inference and tool execution. A retained old report after a
failed invocation is not a new passing result: always check the CLI exit status.
The normal grounding and question-path gates remain separate checks of executed
metrics, evidence and answer templates; this report does not replace them.

## Honest limits

The only implemented inference is local TF-IDF/logistic intent classification.
No generative model or LLM evaluation has been executed. The baseline classifier
runs twice for proposal and veto, preserving its own limitations and adding cost.
The interface is trusted Python application code, not a sandbox. Hash matching
is not authenticity, and verified serialization must still come from trusted local
generation. No new public endpoint or automatic execution authority is introduced.

See [proposal scope](tool-proposals.md), [authorisation](proposal-authorization.md),
[adapter](proposal-adapter.md) and [evaluation](proposal-evaluation.md) contracts.
