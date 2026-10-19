# Day 19 — serialize decision-audit writers

The ledger verifier and hash chain were already deterministic, but two processes
could both verify the same head and calculate the same next sequence. I closed that
gap with an atomic sibling lock held across verification and append.

The lock has a random owner token. Cleanup removes it only when that token still
matches, so one process cannot delete a replacement lock. Tests hold the lock while
a second append is attempted, confirm that the ledger is unchanged, and confirm
that a successful append releases its lock.

I did not add automatic stale-lock deletion. A process crash can leave a lock, but
age alone cannot distinguish a dead writer from a slow valid one. Manual inspection
is the honest local-tooling trade-off. This control is single-host only; the audit
remains mutable local JSONL rather than an immutable or externally controlled log.

The package gate passed 70 tests. Grounding passed 4/4 cases, held-out intent
routing 15/15, adversarial routing 24/24 and end-to-end questions 8/8. The local
TF-IDF/logistic intent classifier remains the only model inference; metric queries
and answer wording are still deterministic.
