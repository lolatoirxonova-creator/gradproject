# Findings — Content-Based Filtering (TF-IDF + Cosine)

> Fill this in after running `notebooks/02_content_based.ipynb`. Pull numbers from `outputs/content_based/results.json`.

## Metrics (warm users, top-10)

| Metric | Score |
|---|---|
| Precision@10 | [value] |
| Recall@10 | [value] |
| NDCG@10 | [value] |
| MAP@10 | [value] |
| HitRate@10 | [value] |
| Users evaluated | [N] |

## Discussion (3 short paragraphs)

**1. What worked.** [Where did the content-based model score well? Typical strength: high HitRate@10 because text metadata captures category and colour preferences.]

**2. Where it fell short.** [Typical weakness: low Recall@K because the model recommends near-duplicates of past purchases rather than novel items. Quote a number.]

**3. Cold-start behaviour.** [Cite §7 of the notebook — the model returns no recommendation for cold users. Quantify cold-user count in the test window. This is the bridge to the hybrid model's popularity fallback.]

## Spot-check evidence

[Pick one of the 3 spot-check users from §9 of the notebook. Tabulate: what they purchased, what was recommended, what they actually bought next. Comment in one sentence on whether the recommendations look reasonable.]

## Implications

[1 paragraph: where content-based sits in the four-model hierarchy. What weight (α) it deserves in the hybrid.]
