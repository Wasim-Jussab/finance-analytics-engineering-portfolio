# Days 16–20 decision-evidence review

This milestone added local evidence around the assistant's runtime decisions. It
does not turn the application into an immutable audit platform.

| Control | Evidence | Remaining boundary |
|---|---|---|
| Append-only decision records | Hash-linked JSONL rows for answered and blocked requests | A filesystem owner can replace the entire file |
| Privacy-conscious traces | Question fingerprint, governed parameters, routing and result evidence | Dates and region remain visible because they define metric scope |
| On-demand status | Read-only API response with count and head fingerprint | The API is not authenticated |
| External expectations | Optional trusted head and record count supplied by the caller | Trust depends on retaining those values elsewhere |
| Writer serialization | Atomic local lock across verification and append | Crash recovery is manual; no distributed lock |
| Offline operation | Standalone verifier with machine-readable output and exit status | Local verification is not external attestation |

The strongest claim I can defend is narrower than "audit system": the project
creates tamper-evident local runtime evidence and can detect internal changes plus
whole-file replacement when an independent anchor is supplied. It has no access
control, immutable retention, external timestamp, digital signature or independent
approval workflow.

Model inference remains limited to the local TF-IDF/logistic intent classifier.
Safety rules, dates, approved tools, metric SQL and answer wording remain
deterministic application logic.
