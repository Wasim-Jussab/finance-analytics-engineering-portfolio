# Local model artifact

`make model-artifact` fits the existing TF-IDF/logistic-regression intent classifier and atomically writes two local files below `artifacts/local-intent-model/`: the fitted joblib pipeline and a JSON manifest. The manifest records the byte fingerprint, approved labels, training-example count, model version, scikit-learn version and local/no-network inference properties.

`make model-artifact-verify` requires exactly those two files, checks all compatible metadata and verifies the SHA-256 fingerprint before deserializing. The application can use the verified artifact through `create_app(model_artifact=...)` or `OPERATIONS_MODEL_ARTIFACT`. The same deterministic policy still controls domain, write, causal and forecasting blocks after model inference.

When the loaded artifact routes a question, its SHA-256 fingerprint is included in the routing decision trace. An in-memory development fit records a null artifact fingerprint instead of implying that persisted bytes were used.

The executable `make evaluate` path verifies and loads the artifact before running the 15 held-out and 24 adversarial routing cases. Both reports carry its fingerprint, and the release gate rejects evidence from different artifact bytes. This proves which local serialization was evaluated; it does not make the fixtures representative of production language.

Joblib uses pickle-compatible deserialization. The verifier therefore loads only an artifact generated locally by this project; the fingerprint catches changed bytes but does not make arbitrary downloaded serialization trustworthy. The generated files are deliberately not committed because the source examples and pinned training specification reproduce them locally.

This adds a reproducible deployment boundary for the real local intent classifier. It does not add an LLM, generative answers, remote inference or broader language capability.
