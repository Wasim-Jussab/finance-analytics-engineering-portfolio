# End-to-end question evaluation

The thirteen-case evaluation starts from natural-language questions rather than preselected tools. Nine supported requests execute the local TF-IDF/logistic-regression router, validated request parameters, one approved read-only tool and the deterministic grounded-answer renderer. Four unsafe or unrelated questions must stop before tool execution.

The supported cases cover portfolio summaries, period comparisons, exception detail and pagination, empty denominators and conflicting question wording. In the conflicting case the question mentions London, while the request explicitly selects North and fixed dates. The claims must follow the structured parameters.

The empty-baseline comparison uses two equal, adjacent UTC windows with exclusive ends. The current cohort has 176 on-time out of 213 due; the baseline has zero due. Counts remain comparable, but the baseline rate and percentage-point change are null. The API regression checks the explanation as well as the structured value.

The beyond-last-page case selects 21 overdue-open exceptions but requests
offset 25. It returns zero rows, no next page and the unchanged total of 21.
The answer states that this page is empty and that earlier rows were omitted;
it must not describe the exception population as empty.

The North-only comparison checks both denominators explicitly: 46/53 on time
in the baseline and 47/54 in the current period. The API regression verifies
the rate and percentage-point change, not just that the region label says North.
These fixture counts were checked with a direct grouped query of the synthetic
shipment source, independently of the reporting tool.

Summary grounding also checks the canonical renderer's labelled counts and
rate in prose against the approved result, including the null-rate wording.
Regression cases change each number while preserving claims and evidence.
These checks are intentionally tied to the deterministic template. They do
not validate arbitrary paraphrases, establish general factuality, or evaluate
a generative model. Comparison and exception prose are not covered by those
summary-specific checks.

Comparison grounding additionally verifies the canonical baseline/current
windows, due counts, rates and signed percentage-point change, including
null-rate wording. Mutation regressions preserve claims and evidence while
altering these headline values; both API answer paths refuse a reversed
change sign. Remaining comparison sentences and exception prose are not
covered by that comparison-specific numeric guard.

The comparison guard also verifies the canonical signed due-volume,
late-delivery and overdue-open changes against the approved result.
Three mutations retain claims/evidence while altering one volume value;
both API paths refuse each alteration. The regional-decrease narrative
remains outside these numeric prose checks. These are deterministic
template checks, not generative evaluation or a language holdout.

Exception prose grounding checks the canonical scope/population header,
returned count and offset, ordered shipment IDs (or empty-page statement),
and next-page/completeness statement against the approved tool result.
Six mutations preserve claims/evidence while changing those fields; both
API paths refuse an altered next offset. The existing empty-page release
case must still pass. This is template-specific grounding, not free-text
fact checking or a generative-model evaluation.

All three canonical answer types must also start with the selected region
(or all regions) and state the approved snapshot time. Scope mutation tests
retain claims/evidence; API regressions alter the displayed time on every
tool through both answer paths. These checks bind the displayed provenance
to the tool result, not to live data or an external freshness service.

Every answered case must retain a tool name, model version and evidence ID, pass the independent grounding checks and match named synthetic fixture totals. Blocked write, causal, forecast and out-of-domain cases have no tool or evidence ID. A database fingerprint proves the evaluation did not alter the source snapshot.

The comparison guard now also binds the regional-decrease sentence to
the selected region and signed on-time count contribution, or the exact
no-decrease statement. Regressions preserve claims/evidence while changing
region, count or that statement; both API paths refuse an incorrect region.
The no-decrease boundary is a controlled tool-result fixture, not a new
observed shipment scenario. Ties retain the renderer's first-in-order rule;
this is not unique causal attribution or arbitrary free-text validation.

This executes real local classifier inference. Tool execution, metric calculation and answer prose remain deterministic, and no generative model or LLM is used. The cases are bounded regression evidence, not a production accuracy estimate. The new denominator case reuses known comparison wording to isolate the metric edge case.
