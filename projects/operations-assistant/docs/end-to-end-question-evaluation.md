# End-to-end question evaluation

The eight-case evaluation starts from natural-language questions rather than preselected tools. Four supported questions execute the local TF-IDF/logistic-regression router, validated request parameters, one approved read-only tool and the deterministic grounded-answer renderer. Four unsafe or unrelated questions must stop before tool execution.

The supported cases cover a portfolio summary, period comparison, empty denominator and conflicting question wording. In the conflicting case, the question mentions London and “last month”, while the validated request explicitly selects North and fixed dates. The claims must follow the structured parameters; the classifier is not allowed to infer or overwrite metric scope.

Every answered case must retain a tool name, model version and evidence ID, pass the independent grounding checks and match named synthetic fixture totals. Blocked write, causal, forecast and out-of-domain cases have no tool or evidence ID. A database fingerprint proves the evaluation did not alter the source snapshot.

This executes real local classifier inference. Tool execution, metric calculation and answer prose remain deterministic, and no generative model or LLM is used. Eight passing cases are bounded regression evidence, not a production accuracy estimate.
