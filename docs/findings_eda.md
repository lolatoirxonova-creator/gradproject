# Findings — Exploratory Data Analysis

> Fill this in after running `notebooks/01_eda.ipynb`. The numbers should be copied from `outputs/eda/eda_summary.json` and the figures from `outputs/eda/*.png`.

## Dataset characteristics

| Metric | Value |
|---|---|
| Articles in catalogue | [N] |
| Customers (total in `customers.csv`) | [N] |
| Customers in sample | [N] |
| Items appearing in sample | [N] |
| Sample transaction count | [N] |
| Date range | [from] → [to] |
| Sparsity | [%] |

## Article (product) catalogue

[1 paragraph: which product groups dominate, depth of text metadata available for TF-IDF, missingness in `detail_desc`.]

Figure 4.1: Top 15 product groups (`outputs/eda/articles_top_groups.png`).

## Customer demographics

[1 paragraph: age distribution shape, missingness, any other demographic columns.]

Figure 4.2: Customer age distribution (`outputs/eda/customers_age_distribution.png`).

## Transaction patterns

[1 paragraph: daily volume, visible seasonality, any outliers.]

Figure 4.3: Daily transaction volume (`outputs/eda/transactions_daily_volume.png`).

## Long-tail analysis

[1 paragraph: what fraction of items account for 80% of transactions. Why this matters for recommendation algorithms — most CF activity concentrates on a small head; the rest is the long tail where personalisation can have outsized impact.]

Figure 4.4: Item popularity Pareto curve (`outputs/eda/transactions_long_tail.png`).

## Cold-start exposure

[1 paragraph: when the last 7 days are held out, how many test users / items are unseen in the training period. Why this matters — it is the primary motivation for the hybrid + popularity fallback design.]

## Implications for the algorithms

[1 paragraph mapping these findings to algorithm choice:]

- **Sparsity > 99.99%** → matrix factorisation and NCF are appropriate (kNN cosine would be infeasible).
- **Long-tail dominance** → top-popular fallback is a meaningful but limited baseline; personalisation matters for the tail.
- **Cold-start exposure of [N]%** → the hybrid model's popularity fallback is essential, not optional.
- **Rich text metadata** → TF-IDF content-based filtering has enough signal to be a competitive baseline and a useful hybrid contributor.
