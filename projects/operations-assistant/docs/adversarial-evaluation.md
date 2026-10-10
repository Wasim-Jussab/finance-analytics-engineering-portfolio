# Adversarial intent evaluation

The local classifier is tested against 24 questions grouped into safe summary, safe comparison, write action, causal claim, forward-looking and out-of-domain slices. The report keeps the raw model label, confidence, confidence margin, applied guardrail and final routed outcome for every case.

Deterministic guardrails override the model for write actions, causal claims, forecasting and questions without a recognised delivery-metric term. This matters for mixed prompts: a question can contain strong comparison language while also asking the system to email a depot or predict a future result. In that case the raw model decision remains visible, but no approved tool is executed.

The first run failed four cases: one summary was misrouted as a comparison, and three unrelated questions were accepted as summaries. I added two summary paraphrases to the training fixture and required a recognised delivery-metric term before tool routing. The fixture is intentionally small and hand-authored. A perfect final result demonstrates that these named controls work on these cases; it is not a production accuracy estimate, red-team certification or evidence that unseen language is safe.
