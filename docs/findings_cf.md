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

## Implementation note — online fold-in for platform users

During the platform build, the live ALS recommender in `app/shared.py` needs to recommend to users who **do not exist** in the ALS model's `user_index` (the H&M training IDs are anonymous hashes, unrelated to platform accounts). The `implicit` library supports this via **online fold-in**: pass the user's interaction sparse row as `user_items` and set `recalculate_user=True`, which solves a one-off ridge regression for the user's latent factor on demand.

```python
model.recommend(
    0,  # placeholder userid — recalculate_user overrides this
    user_items_csr,
    N=k,
    filter_already_liked_items=True,
    recalculate_user=True,
)
```

An earlier draft of `recommend_als` omitted `recalculate_user=True`, which silently used the trained factor for whichever H&M customer happened to occupy row 0 — producing identical recommendations for every platform user. This was caught during the multi-user smoke test of the auth-gated app; both `recommend_als` and the CF half of `recommend_hybrid` now set the flag explicitly. The same path is used by the admin "Retrain ALS now" button — after retraining, platform users with H&M-prefixed IDs `app:<id>` exist in `user_index` directly, but the fold-in path remains the canonical one because new signups never appear in the saved model until the next retrain.
