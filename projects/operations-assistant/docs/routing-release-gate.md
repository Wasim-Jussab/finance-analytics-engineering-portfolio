# Routing release gate

The release gate consumes the executed fixed-routing and adversarial regression reports. It does not invoke a generative model. It requires one model version across both reports, reconciles every case and applies the versioned policy in `config/routing-release-policy.json`. See the [overlap audit](evaluation-overlap.md): this suite is not an independent holdout; legacy held-out field/policy names are retained for compatibility.

A release is approved only when all 18 fixed-routing and 27 adversarial cases pass, all required named risk slices are present and no request expected to be unsupported is accepted. Every breach is retained rather than stopping at the first failure.

`make evaluate` runs the local classifier before the gate. The output records exact SHA-256 fingerprints for both reports and the policy, an evaluator version and a stable release ID. These fixtures are small and hand-authored, and the adversarial set informed the router design. Approval is therefore regression evidence for this bounded interface, not a production accuracy estimate or broad safety certification.

The gate prevents a known bad evaluation from being published by the repository workflow. It does not secure the files against someone who can replace all inputs and regenerate the decision, and it does not approve answer content or metric correctness; those have separate deterministic evaluations.
