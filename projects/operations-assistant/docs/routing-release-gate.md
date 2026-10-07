# Routing release gate

The release gate consumes the executed held-out and adversarial evaluation reports. It does not invoke a generative model. It requires one model version across both reports, reconciles every case and applies the versioned policy in `config/routing-release-policy.json`.

A release is approved only when all 15 held-out and 24 adversarial cases pass, all six named risk slices are present and no request expected to be unsupported is accepted. Every breach is retained rather than stopping at the first failure.

`make evaluate` runs the local classifier before the gate. The output records exact SHA-256 fingerprints for both reports and the policy, an evaluator version and a stable release ID. These fixtures are small and hand-authored, and the adversarial set informed the router design. Approval is therefore regression evidence for this bounded interface, not a production accuracy estimate or broad safety certification.

The gate prevents a known bad evaluation from being published by the repository workflow. It does not secure the files against someone who can replace all inputs and regenerate the decision, and it does not approve answer content or metric correctness; those have separate deterministic evaluations.
