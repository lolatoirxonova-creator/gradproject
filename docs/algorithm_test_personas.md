# Algorithm Test Personas

Four engineered test accounts, one per core recommendation algorithm. Each
account's saved-item profile is deliberately shaped to expose that algorithm's
**strengths and weaknesses**. All saved items come from the curated-50 catalogue.

**Seed/refresh them with:** `python scripts/seed_test_personas.py`
**Password (all):** `Test2026!`

## How to evaluate

1. Log in as a persona.
2. Open the **Compare** page — it runs all four algorithms side-by-side for the
   logged-in user, with an Intra-List Diversity (ILD) chip per column and a live
   **α slider** for the hybrid.
3. Toggle **Show technical details** (sidebar) to see article IDs.
4. Read each algorithm's column against the persona's profile and the pros/cons below.

| Account | Targets | Saved profile | What to watch for |
|---|---|---|---|
| `test_content@example.com` | Content-Based (TF-IDF) | hoodie + sweater + cardigan (one tight knit/jersey style) | CB fills the rail with more knitwear; ALS/NCF wander off — shows CB's similarity strength **and** its filter-bubble weakness |
| `test_als@example.com` | ALS collaborative filtering | leggings + sneakers + tee (transaction-rich activewear) | ALS pulls co-bought items, often cross-category; CB can only echo the same item types |
| `test_hybrid@example.com` | Weighted Hybrid | 2 dresses (content) + popular leggings (collaborative) | The blend; slide α from 1.0→0.0 to watch it move from CB-like to CF-like |
| `test_neural@example.com` | Neural CF (NeuMF) | 4 items that all have NeuMF embeddings | NCF produces embedding-neighbours; items without embeddings (~13/50 curated) never surface — the coverage gap |

## Pros & cons per algorithm

### Content-Based (TF-IDF cosine on product metadata)
**Pros:** no item cold-start (works from metadata, so brand-new/niche items are recommendable); transparent/explainable ("shares: dress, jersey, black"); excellent for a user with a consistent, narrow taste.
**Cons:** over-specialisation / filter bubble — only ever surfaces *similar* items, so low serendipity and no cross-category discovery; blind to popularity and to what similar shoppers buy; quality is capped by the richness of the metadata.

### ALS Collaborative Filtering (`implicit`)
**Pros:** discovers cross-category items through co-purchase patterns (serendipity); needs no content/metadata; captures "wisdom of the crowd".
**Cons:** user **and** item cold-start (needs interaction history); popularity bias (head items dominate); items with little transaction history score poorly; not explainable from content.

### Weighted Hybrid (α·CB + (1−α)·CF)
**Pros:** each tower covers the other's blind spot — CB handles cold/niche items, CF adds discovery; tunable via α (notebook-tuned default); most robust across different user types.
**Cons:** needs both signals to be meaningful; α has to be tuned and is a single global compromise; more compute; a strong single-source signal can get diluted.

### Neural CF — NeuMF (GMF + MLP towers)
**Pros:** learns non-linear user–item interactions that linear matrix factorisation can miss; strong on dense interaction data.
**Cons:** data-hungry and heavier to train; cold-start for unseen users/items; **only items with learned embeddings are scoreable** (~37/50 curated here) — the rest can never be recommended; least explainable ("black box").

> Note: with the catalogue gated to the curated 50, every algorithm ranks within
> the same ~48 candidates, so differences are about *ordering and which items
> surface*, not catalogue size. The contrast is clearest on the Compare page.
