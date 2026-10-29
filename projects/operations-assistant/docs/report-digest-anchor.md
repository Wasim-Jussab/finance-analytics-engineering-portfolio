# Whole-report digest and external expectation

New collector output uses `investigation-v2` and carries `report_sha256`. The
digest covers canonical JSON values for the entire report, excluding only its own
digest field. Key ordering and whitespace do not matter; non-finite numbers are
rejected. The existing page-level `delivery-v1` digests are unchanged.

Retain the original report digest independently, then verify a saved report with:

```bash
python -m operations_assistant.investigation_verify investigation.json \
  --expected-report-sha256 <independently-retained-lowercase-SHA-256>
```

The verifier checks the embedded v2 digest and, when supplied, the external digest
before its existing page/scope/reconciliation controls. Its summary separately
reports `embedded_report_digest_checked` and `external_report_anchor_checked`.
Legacy `investigation-v1` reports remain structurally verifiable and explicitly
report no embedded digest check. A missing external expectation is not an anchored
verification, even when internal hashes agree.

Tests deliberately rewrite a valid cap and recalculate all necessary report hashes:
unanchored verification still succeeds, while the independently retained original
digest rejects the replacement. This demonstrates the boundary rather than claiming
the embedded hash prevents a malicious whole-report rewrite.

This is not a signature, access control or immutable storage. The external value is
only as trustworthy as how it was retained; putting it beside a mutable report does
not make it independent. No credentials, secrets, model inference or paid services
are required. Snapshot identity expectations remain a separate supported check.
