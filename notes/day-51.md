# Day 51 — add a bounded delinquency proxy

I started the next finance milestone by making the existing days-past-due proxy
usable as a governed reporting dimension. The new fact keeps one row per loan at
the fixed reporting date and assigns four mutually exclusive bands, while
reconciling every amount and date back to the tested schedule-position fact.

I did not call the bands arrears, default or IFRS 9 stages. They inherit a
principal-only schedule and an assumed oldest-due-first allocation, so those
stronger labels would imply source evidence and policy that the project does not
have. The useful result is a repeatable segmentation rule with an explicit
boundary, not a claim that the synthetic model reproduces a lender ledger.

The main trade-off is that `Current` combines accounts not yet due with accounts
whose due principal is covered. That is appropriate for a delinquency view, while
the retained `schedule_position_status` still separates those two populations.
