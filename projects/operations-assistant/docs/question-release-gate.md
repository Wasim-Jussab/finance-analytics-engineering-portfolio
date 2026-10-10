# Question-path release gate

`make evaluate` executes the eight fixed end-to-end question cases, then applies `config/question-release-policy.json`. A release is approved only when all four answered and four blocked cases pass, blocked cases execute no tool, the DuckDB snapshot is unchanged and all eight decision traces are distinct.

The gate independently reconciles case totals, outcomes, failures, tools, evidence IDs and tool-execution totals before applying policy. Its release ID fingerprints the exact evaluation file, policy and decision. A failed decision exits non-zero and remains inspectable rather than hiding its breaches.

This is a release decision over named synthetic fixtures. It does not estimate production accuracy, prove general language safety or evaluate a generative model. The only learned inference is the local intent classifier; metrics, approved tools and answer wording remain deterministic.
