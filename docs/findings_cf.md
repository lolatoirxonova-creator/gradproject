# Findings — Collaborative Filtering (ALS Matrix Factorisation)

> Fill this in after running `notebooks/03_collaborative_filtering.ipynb`. Pull from `outputs/collaborative_filtering/results.json`.

## Metrics (warm users, top-10)

| Metric | ALS | Content-Based (Notebook 02) | ALS uplift % |
|---|---|---|---|
| Precision@10 | [value] | [value] | [%] |
| Recall@10 | [value] | [value] | [%] |
| NDCG@10 | [value] | [value] | [%] |
| MAP@10 | [value] | [value] | [%] |
| HitRate@10 | [value] | [value] | [%] |

## Hyperparameters used

| Parameter | Value | Notes |
|---|---|---|
| `factors` | 64 | tried 32 / 128 — see hp_sweep.csv if attempted |
| `iterations` | 15 | loss plateaued — no benefit going higher |
| `regularization` | 0.01 | default; light tuning sufficient |
| `alpha` | 10.0 | confidence weight for implicit feedback |

## Discussion (3 short paragraphs)

**1. Headline result.** [Which model wins on each metric, by how much, and at what cost in compute. ALS typically wins NDCG; content-based may win HitRate.]

**2. Cold-start exposure.** [Cite §6 of the notebook. Quantify cold users + cold items. State plainly: ALS cannot personalise cold users and cannot score cold items.]

**3. What this tells us about hybrid design.** [Whichever metric ALS dominates suggests a low α (more weight on CF); whichever metric content-based dominates suggests a high α. Use this to predict what the α-sweep in Notebook 04 will find.]

## Spot-check evidence

[Pick one user from §9 of the notebook. Side-by-side: train history, ALS recommendations, actual test purchases. One-sentence comment.]

## Comparison figure

`outputs/collaborative_filtering/comparison_vs_content_based.png`
