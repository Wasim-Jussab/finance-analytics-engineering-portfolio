# Day 8 — evaluate the complete question path

The router and answer layer each had tests, but they were evaluated separately. I added an eight-case suite that begins with natural-language questions and follows the complete path through local intent inference, validated parameters, approved read-only tools and grounded deterministic answers.

Four supported questions must produce the expected tool, claims and evidence ID. Four write, causal, forecast or unrelated questions must stop before tool execution. I included a deliberately conflicting wording case: the question mentions London, while the structured request selects North. The answer must follow the validated fields rather than letting the classifier invent scope.

My first wording also said “last month”. The classifier reasonably treated that as a comparison cue and selected the comparison tool, which then failed validation because I had supplied no baseline dates. That mixed two concerns in one case, so I narrowed this test to parameter authority. Missing comparison parameters remain covered by the request-contract tests rather than being disguised as a model failure.

The evaluation also fingerprints the DuckDB file before and after all cases to prove the path remained read-only. This is genuine local classifier inference, but the figures and prose are still deterministic. Eight passing cases are useful regression evidence, not a production accuracy estimate or a generative-model evaluation.

The first cross-project verification rerun was blocked before testing by the known DuckDB duplicate-schema WAL replay problem. I removed only the generated local database and recovery file, rebuilt from the synthetic sources and reran the unchanged gate successfully. I have not counted the failed recovery attempt as model or data-quality evidence.
