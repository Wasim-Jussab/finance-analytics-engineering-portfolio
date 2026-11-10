# End-to-end question evaluation

The eleven-case evaluation starts from natural-language questions rather than preselected tools. Seven supported requests execute the local TF-IDF/logistic-regression router, validated request parameters, one approved read-only tool and the deterministic grounded-answer renderer. Four unsafe or unrelated questions must stop before tool execution.

The supported cases cover portfolio summaries, period comparisons, exception detail and pagination, empty denominators and conflicting question wording. In the conflicting case the question mentions London, while the request explicitly selects North and fixed dates. The claims must follow the structured parameters.

The empty-baseline comparison uses two equal, adjacent UTC windows with exclusive ends. The current cohort has 176 on-time out of 213 due; the baseline has zero due. Counts remain comparable, but the baseline rate and percentage-point change are null. The API regression checks the explanation as well as the structured value.

Every answered case must retain a tool name, model version and evidence ID, pass the independent grounding checks and match named synthetic fixture totals. Blocked write, causal, forecast and out-of-domain cases have no tool or evidence ID. A database fingerprint proves the evaluation did not alter the source snapshot.

This executes real local classifier inference. Tool execution, metric calculation and answer prose remain deterministic, and no generative model or LLM is used. The cases are bounded regression evidence, not a production accuracy estimate. The new denominator case reuses known comparison wording to isolate the metric edge case.
