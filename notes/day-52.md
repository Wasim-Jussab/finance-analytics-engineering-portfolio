# Day 52 — summarise the delinquency proxy without hiding denominators

I added a product and observed-band aggregate over the account-level delinquency
proxy. The reporting grain is explicit, and the output keeps both the band account
count and full product account count so a reviewer can reconstruct the account
share. The due-principal coverage ratio uses summed money values rather than an
average of account percentages.

I considered generating all four bands for every product, including zero rows.
That would make a fixed matrix easier to chart, but it would also introduce a
separate band-spine rule that the current business question does not need. I kept
only observed combinations and documented that absence is not an explicit zero.

The aggregate inherits the same principal-only schedule and oldest-due-first
allocation assumptions as its parent fact. Product segmentation makes the proxy
more useful for portfolio review; it does not make it contractual arrears, default
or regulatory staging.
