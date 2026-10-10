# Day 10 — gate the complete question path

The routing release gate could approve the classifier while saying nothing about validated parameters, tool execution, grounded claims or decision traces. I added a second release decision over the executed eight-case question-path report.

The policy requires four answered and four blocked cases, all passing, zero tool executions for blocked requests, an unchanged DuckDB snapshot and eight distinct verified traces. Before applying it, the evaluator reconciles the case, outcome and tool totals and checks that answered cases identify both their approved tool and evidence. The release ID fingerprints the exact evaluation and policy.

This closes the five-day governed-routing milestone, but not the assistant as a production system. The evidence is eight fixed synthetic questions, not a representative accuracy estimate. The only learned component remains the local intent classifier; parameters, metrics, tools and prose remain deterministic. I would need independently labelled data and observed distribution-shift controls before widening the supported language or adding a generative layer.
