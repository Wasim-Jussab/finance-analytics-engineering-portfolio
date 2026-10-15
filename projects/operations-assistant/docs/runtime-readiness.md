# Runtime readiness gate

The final local gate verifies the persisted model artifact before loading its
manifest, then requires both the routing release and end-to-end question release
to identify the same model name, model version and SHA-256 artifact fingerprint.
Both decisions must be approved with no breaches. Their release IDs are retained
in `reports/runtime-readiness.json` so the decision can be traced back to the exact
executed evidence.

The end-to-end question evaluation now loads the verified artifact rather than
fitting another classifier in memory. This closes a genuine evidence gap: a green
question-path test previously proved the same training specification, but not the
same serialized classifier bytes that the runtime would load.

`make evaluate` generates the synthetic snapshot, verifies the artifact, executes
the grounding, held-out, adversarial and end-to-end suites, applies both release
policies and runs the readiness gate. Any blocked release or identity mismatch
returns a non-zero exit code.

Readiness means only that this local package executed its named fixtures against
the exact approved intent-classifier artifact. It is not production deployment,
security review, broad language accuracy, drift monitoring or approval of a
generative model. Generative inference remains absent.
