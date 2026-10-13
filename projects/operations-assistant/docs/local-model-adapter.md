# Local model adapter

The question router receives model-only predictions through `IntentModelAdapter`. The current implementation, `TfidfLogisticIntentAdapter`, fits and executes the existing scikit-learn classifier in local memory. Its version fingerprints the training examples, model settings and scikit-learn version.

The adapter returns only a label, confidence and confidence margin. It cannot select a tool, execute SQL, supply dates or write answer prose. The surrounding router validates the label and probabilities, applies deterministic write, causal, forecasting and domain guardrails, and only then constructs a validated request for an approved read-only tool.

Tests inject a fixed adapter to prove that a high-confidence supported label still cannot bypass the write guardrail. They also reject unknown labels and invalid probabilities. Every routing result records the adapter, model version, local inference location and that the adapter requires no network access.

This boundary makes a future local model replaceable without moving safety or business rules into model output. It does not make arbitrary models safe, prove broad language accuracy or add generative inference. Any replacement would still need the held-out, adversarial and complete question-path release gates.
