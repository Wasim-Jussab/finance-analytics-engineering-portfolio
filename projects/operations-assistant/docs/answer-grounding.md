# Answer grounding and evaluation

`POST /api/answers` validates an approved tool request, executes the read-only metric service and renders a fixed answer template. The answer carries the exact structured claims and evidence object returned by the tool. It does not accept SQL or free-form questions.

`make evaluate` runs four fixed cases: a populated summary, an empty summary, a full comparison and a region-filtered comparison. It checks claim equality, evidence identity, evidence-ID citation, synthetic-data disclosure, null-rate wording and a small list of prohibited causal phrases. The JSON result is written to `reports/answer-evaluation.json`.

This evaluates deterministic grounding rules only. It is not a language-model evaluation and does not measure usefulness, semantic equivalence or resistance to prompt injection. The purpose is to establish executable evidence before a local model adapter is introduced.
