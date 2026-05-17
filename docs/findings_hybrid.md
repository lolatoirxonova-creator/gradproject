# Findings — Weighted Hybrid Recommender

> Fill this in after running `notebooks/04_hybrid.ipynb`. Pull from `outputs/hybrid/results.json`.

## α-sweep results

| α | Precision@10 | Recall@10 | NDCG@10 | MAP@10 | HitRate@10 |
|---|---|---|---|---|---|
| 0.00 (pure CF) | [value] | | | | |
| 0.25 | | | | | |
| 0.50 | | | | | |
| 0.75 | | | | | |
| 1.00 (pure content) | | | | | |

**Best α by NDCG@10:** [value]

## Three-way comparison (warm users)

| Model | Precision@10 | Recall@10 | NDCG@10 | MAP@10 |
|---|---|---|---|---|
| Content-Based (α=1.00) | | | | |
| ALS CF (α=0.00) | | | | |
| **Hybrid (α=[best])** | | | | |

**Uplift over the better single model:** [%] on NDCG@10.

## Cold-user popularity fallback

| Metric | Value |
|---|---|
| Cold users evaluated | [N] |
| Precision@10 (popularity) | [value] |
| Recall@10 (popularity) | [value] |

[1 sentence: how does popularity compare to the warm-user hybrid? Is it useful as a temporary cold-start solution while the user warms up?]

## Discussion (3 paragraphs — answers RQ1)

**1. Does the hybrid beat single algorithms?** [Yes / no / partially — quote numbers. If yes, quote the % uplift. If no, explain on which metrics it failed to beat the best single model.]

**2. Why the chosen α won.** [Interpret the α-sweep curve. A flat-then-peak shape suggests one model dominates; a smooth curve suggests genuine complementarity. Cite Burke (2002) on weighted hybrids.]

**3. Cold-start: does the popularity fallback earn its place?** [Compare cold-user metrics to warm-hybrid metrics. Discuss whether popularity is acceptable for first-session users or whether a true content-based fallback should be tried in future work.]

## Distinction-level critical engagement

[1–2 sentences: where the hybrid is honestly worse than expected, or where the α-sweep was less informative than hoped. This kind of self-criticism is M5 / D3 evidence.]

## Figures

- `outputs/hybrid/alpha_sweep.png` — sweep curves (one line per metric)
- `outputs/hybrid/three_way_comparison.png` — bar chart, all 3 models
