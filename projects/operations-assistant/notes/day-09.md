# Day 9 — trace answered and blocked decisions

The question endpoint returned routing and metric evidence, but there was no single identifier binding the two. I added a deterministic decision trace for both answered questions and governed refusals.

The trace records the explicit dates and region, one model prediction, model version, selected tool, evidence ID and a fingerprint of the structured claims. It hashes the question instead of retaining the raw text, because an operational prompt could contain a person or customer reference even when the approved tool cannot use it. Repeating the same request produces the same ID; changing a governed parameter changes it.

Blocked write, causal, forecast and unrelated questions now return a trace without a tool or evidence ID. The eight-case end-to-end suite verifies every trace, and a separate tampering test proves a changed field no longer matches its ID. This improves auditability, but it is not immutable logging, encryption or proof of broad model accuracy.

My first targeted test run did not reach collection because the local DuckDB 1.5.6 native module raised a bus error on import. I reproduced the import failure, confirmed 1.4.1 was below this package's declared `duckdb>=1.5` requirement, and completed validation with a compatible 1.5.0 environment. I did not count that environment repair as product evidence or change the repository dependency range.
