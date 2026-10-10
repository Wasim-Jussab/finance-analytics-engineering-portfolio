# Day 6 — test unsafe and mixed questions

The first milestone proved that the local classifier could route fifteen held-out questions, but that was too narrow to say much about risky phrasing. I added a separate 24-case evaluation covering safe paraphrases, write actions, causal claims, forecasts, mixed requests and unrelated questions.

Mixed prompts exposed the important design boundary: a model can notice strong comparison language while missing the unsafe action attached to it. I kept the raw model label in the evidence and added deterministic guardrails that force abstention before any tool executes. The report now shows results by risk slice, confidence margin and the guardrail applied.

The first run passed 20 of 24 cases. One plain summary was labelled as a comparison, while weather, stock and salary questions were incorrectly accepted as delivery summaries. I added two summary paraphrases to the training fixture and a narrow delivery-domain requirement, then reran both the original held-out suite and the adversarial suite. That improves this bounded interface but also means the adversarial fixture informed the design, so its final score is regression evidence rather than an unbiased accuracy estimate.

Passing this fixture proves only these named cases and controls. It is not a red-team certification or production accuracy estimate, and I have not added a generative model.
