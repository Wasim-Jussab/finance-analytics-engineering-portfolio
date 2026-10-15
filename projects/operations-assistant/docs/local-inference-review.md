# Days 11–15 local-inference review

This milestone replaced an implicit in-memory classifier boundary with a
reproducible local artifact and evidence chain. The adapter now has a versioned
training and estimator specification, the artifact records exact fitted bytes and
runtime compatibility, and every release evaluation can name the artifact it ran.
The API exposes read-only provenance without publishing training rows or weights.

The strongest part is the boundary, not the model sophistication. A local TF-IDF
logistic classifier selects one of two approved read-only tools or abstains.
Deterministic validation controls dates and regions; deterministic SQL calculates
the metrics; deterministic templates render evidence-cited answers. Held-out,
adversarial and end-to-end fixtures exercise that complete path. The final
readiness gate blocks deployment evidence when either release is not approved or
names different classifier bytes.

This is actual local classification inference. It is not an LLM or generative
assistant. The fixture sets are small and authored inside the project, so their
perfect scores are regression evidence rather than an unbiased accuracy estimate.
There is no authentication, concurrent model server, production data, live drift
monitoring, external red-team set or deployment. A recruiter should read this as
evidence of controlled AI integration and evaluation discipline, not production
scale or broad natural-language capability.

The next milestone should expand independently labelled questions and failure
analysis before adding more tools. A larger model would add cost and complexity
without first improving the quality of the evaluation population.
