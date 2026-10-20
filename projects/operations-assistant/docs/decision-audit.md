# Local decision audit

Set `OPERATIONS_DECISION_AUDIT` to a local JSONL path to record every answered or
blocked `/api/questions` decision. Each row contains the privacy-conscious decision
trace, its sequence, the previous row's SHA-256 fingerprint and its own fingerprint.
The raw question is not retained. The trace now binds the outcome to the active
adapter, inference location and model-artifact fingerprint as well as the governed
parameters, tool and result evidence.

The ledger is verified before each append. Tests prove that edited content and a
missing middle row are rejected. This is useful local runtime evidence, not an
immutable audit system: there is no external timestamp, access control or
independently controlled storage. A user with filesystem
access can replace or truncate the complete file. Approved metric tools continue
to open the DuckDB snapshot read-only; only the configured audit file is written.

`GET /api/audit/status` verifies the complete configured ledger on demand and
returns its record count, head fingerprint, record version and storage boundary.
It returns HTTP 409 when verification fails. It does not expose the configured
filesystem path, individual traces or raw questions; when no ledger is configured,
it says verification was not run rather than implying that an empty ledger passed.


An operator that retains the last trusted head outside the ledger can call
`GET /api/audit/status?expected_head_sha256=<sha>&expected_record_count=<count>`.
The service first verifies the internal chain, then compares the supplied
expectations. A mismatch returns HTTP 409. This detects whole-file replacement or
truncation that leaves a shorter internally valid chain.

The expectation is request-supplied and is not written beside the ledger. Keeping
it in the same writable location would not improve the trust boundary. This still
does not provide immutable storage, an external timestamp or access control.

The append path creates a sibling `.lock` file atomically and holds it across
verification and append. A second local process fails before it can calculate a
sequence or change the ledger. Normal completion releases only the lock whose
random owner token matches the process that acquired it.

Abrupt process termination can leave a stale lock. Recovery is deliberately
manual because file age does not prove that a slow writer is dead. This is local
single-host coordination, not a distributed lock or a substitute for immutable
storage.

## Standalone verification

`python -m operations_assistant.audit_cli --path <ledger>` runs the same read-only
chain verification without starting FastAPI. Optional `--expected-head-sha256`
and `--expected-record-count` arguments apply the external-anchor checks. Success
prints integrity metadata as JSON and exits zero. A changed ledger or expectation
mismatch prints a path-free failure object and exits one; it never prints records,
decision traces or raw questions.
