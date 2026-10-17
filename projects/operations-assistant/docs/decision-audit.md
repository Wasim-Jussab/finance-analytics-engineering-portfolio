# Local decision audit

Set `OPERATIONS_DECISION_AUDIT` to a local JSONL path to record every answered or
blocked `/api/questions` decision. Each row contains the privacy-conscious decision
trace, its sequence, the previous row's SHA-256 fingerprint and its own fingerprint.
The raw question is not retained. The trace now binds the outcome to the active
adapter, inference location and model-artifact fingerprint as well as the governed
parameters, tool and result evidence.

The ledger is verified before each append. Tests prove that edited content and a
missing middle row are rejected. This is useful local runtime evidence, not an
immutable audit system: there is no external timestamp, access control, concurrent-
writer lock or independently retained head fingerprint. A user with filesystem
access can replace or truncate the complete file. Approved metric tools continue
to open the DuckDB snapshot read-only; only the configured audit file is written.

`GET /api/audit/status` verifies the complete configured ledger on demand and
returns its record count, head fingerprint, record version and storage boundary.
It returns HTTP 409 when verification fails. It does not expose the configured
filesystem path, individual traces or raw questions; when no ledger is configured,
it says verification was not run rather than implying that an empty ledger passed.
