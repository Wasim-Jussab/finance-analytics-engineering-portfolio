# Local intent model

`POST /api/questions` accepts a natural-language question plus explicit dates and an optional region. A local TF-IDF logistic-regression classifier routes the question to `delivery_summary`, `compare_delivery_periods` or `unsupported`. Only the two approved labels can create a validated `ToolRequest`; the existing read-only tool and answer layers then run unchanged.

Dates are deliberately structured parameters. The classifier does not extract or invent them. Comparison requests still require two equal, non-overlapping periods, and unsupported, low-confidence, write, forecast and causal requests are rejected.

The model trains in process from 30 versioned examples with a fixed random state. `make evaluate` executes 15 separate examples and retains predicted label, confidence and result. This is real local intent-model inference, but it is not a language model, a generative answer model or evidence of production accuracy. The dataset is too small for that claim.
