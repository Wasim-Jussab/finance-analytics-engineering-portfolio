# Day 53 — separate product size from shortfall concentration

I added one product-level risk-prioritisation row for each synthetic loan product.
The output shows portfolio account share, the share of product accounts in the
project's 90+ day proxy band and the product's share of portfolio scheduled-
principal shortfall. Keeping those denominators visible matters because the
largest product is not automatically the largest monetary concentration.

I calculated the ratios from account counts and summed money values rather than
averaging the Day 52 band percentages. The model reconciles back to the account-
level proxy fact and retains the portfolio totals needed to reproduce each share.

I considered adding a composite risk score, but there is no governed weighting or
loss model in the source. A score would turn transparent descriptive measures into
an arbitrary ranking. The 90+ measure therefore remains a severe project proxy,
not default, probability of default or IFRS 9 staging.
