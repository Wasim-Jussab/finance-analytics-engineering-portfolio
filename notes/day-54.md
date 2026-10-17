# Day 54 — summarise concentration without inventing a risk score

I added one portfolio-level row that separates product concentration by account
count from concentration by scheduled-principal shortfall. It identifies the
largest product under each denominator and reports the Herfindahl concentration
index with its reciprocal effective-product count.

I calculate the indices from unrounded counts and amounts, then round only the
published measures. This avoids summing yesterday's displayed shares and makes
the output independently reproducible from the product-level mart.

I did not attach high/medium/low labels or regulatory thresholds. There are only
three synthetic products, no governed concentration appetite and no loss model.
The measures describe how this fixture is distributed; they do not estimate
default, capital or expected credit loss.
