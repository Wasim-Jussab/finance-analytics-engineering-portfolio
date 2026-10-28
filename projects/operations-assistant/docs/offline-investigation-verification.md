# Offline investigation verification

The collector now includes complete page results alongside the existing evidence
references in version `investigation-v1`. Save its JSON output, then run:

```bash
python -m operations_assistant.investigation_verify investigation.json
```

Optionally supply `--expected-snapshot-id` from a separately retained record. The
verifier never connects to DuckDB. It checks the report version/cap, requested scope,
page pinning, ordered pagination, complete unique rows and each page's recomputed
`delivery-v1` evidence digest. Failed reports return nonzero and no verified summary.
Legacy collector reports without full pages must be regenerated, not assumed verified.

Tool digest calculation is shared without changing its established byte contract.
Tests include JSON round trips, empty populations, retained external expectations,
row/evidence/request/count/page tampering, removal of a pin with a recalculated
digest and command-line success/rejection.

This checks internal integrity, not authenticity, immutable storage or independent
business-rule correctness. Someone who controls all report contents can rewrite
and recalculate hashes. A matching snapshot ID is an identity check, not a trusted
signature. No model is invoked by the collector or verifier; local intent
classification remains separately tested and evaluated, with no generative inference.
