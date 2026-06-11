# Final Report Skeleton

**A Hybrid Product Recommendation System for Online Marketplaces Based on Customer Preferences**

PDP UNIVERSITY · Faculty of Business Information Technology · Tashkent, Uzbekistan
INDEPENDENT PROJECT · Pearson BTEC Level 6 Diploma in Digital Technologies
Unit 2 — Unit Code: 70726U — Credit Value: 30

| Field | Detail |
|---|---|
| Student Name | Lola Toirxonova |
| Student ID | 220062 |
| Programme / Group | BIT — [group] |
| Project Format | Capstone-style |
| Supervisor | Abdulaziz Gulomov |
| Submission Date | 1 June 2026 |
| Word Count Target | 8,000–10,000 |
| Target Grade | Distinction |

---

> **How to use this skeleton.** Each section maps to the official BTEC template (`BTEC_L6_Unit2_Independent_Project_Template.docx`) and to specific Pass / Merit / Distinction criteria. Bracketed `[guidance]` text is for Lola — replace with your own writing. Quoted blocks in `> citation` form remind you where to bring evidence from.
>
> **Order to write:** Methodology → Findings → Literature Review → Discussion → Conclusion → Reflection → Introduction → Abstract (last).

---

## Declaration of Originality

[Use the template wording from `BTEC_L6_Unit2_Independent_Project_Template.docx`. Sign and date at submission.]

## Acknowledgements

[Half-page. Thank Abdulaziz Gulomov; faculty at BIT; family and peers; the test users who participated in the demo feedback.]

## Abstract

> **Write last.** 200–300 words on one page. Structure: (1) context & problem, (2) aim, (3) methodology, (4) key findings, (5) conclusion. No citations or abbreviations in the abstract.

[Open with one sentence on global e-commerce + personalisation. State the problem: under what conditions does a hybrid recommender beat single-algorithm baselines on a real fashion dataset? State the aim. Summarise the methodology in two sentences (H&M dataset, four algorithms, 5-fold CV, statistical tests). Quote the headline finding with one number. Note that the models were deployed as a real auth-gated product — the "Chiroyli" cosmetics marketplace — and that pivoting to a domain without transaction history surfaced an end-to-end cold-start finding. Close with the contribution.]

**Keywords:** recommendation systems; collaborative filtering; content-based filtering; hybrid models; neural collaborative filtering; e-commerce personalisation

## Table of Contents

[Auto-generated in MS Word — right-click and "Update Field" before final submission.]

## List of Figures

| # | Title | Page |
|---|---|---|
| 1.1 | Conceptual framework | — |
| 2.1 | Recommender algorithm taxonomy | — |
| 3.1 | Work Breakdown Structure | — |
| 3.2 | Gantt chart | — |
| 4.1 | Item popularity Pareto curve | — |
| 4.2 | Customer age distribution | — |
| 4.3 | Daily transaction volume | — |
| 5.1 | α-sweep for hybrid model | — |
| 5.2 | Four-way model comparison (warm users) | — |
| 5.3 | 5-fold CV results with error bars | — |
| 5.4 | Cold-start segmented metrics | — |
| 5.5 | NeuMF training loss | — |

## List of Tables

| # | Title | Page |
|---|---|---|
| 3.1 | Milestones and critical path | — |
| 3.2 | Risk register | — |
| 5.1 | Summary metrics — all four models | — |
| 5.2 | Paired Wilcoxon signed-rank tests | — |
| 5.3 | Cold-start segmented metrics | — |

## List of Abbreviations

| Abbreviation | Full Form |
|---|---|
| ALS | Alternating Least Squares |
| BCE | Binary Cross-Entropy |
| CB | Content-Based Filtering |
| CF | Collaborative Filtering |
| CV | Cross-Validation |
| GDPR | General Data Protection Regulation |
| GMF | Generalised Matrix Factorisation |
| MAP | Mean Average Precision |
| MF | Matrix Factorisation |
| MLP | Multi-Layer Perceptron |
| NCF | Neural Collaborative Filtering |
| NeuMF | Neural Matrix Factorisation |
| NDCG | Normalised Discounted Cumulative Gain |
| PDP | PDP Private University |
| RAG | Red-Amber-Green status rating |
| RBM | Restricted Boltzmann Machine |
| RQ | Research Question |
| SMART | Specific, Measurable, Achievable, Relevant, Time-bound |
| SVD | Singular Value Decomposition |
| SWOT | Strengths, Weaknesses, Opportunities, Threats |
| TF-IDF | Term Frequency – Inverse Document Frequency |
| WBS | Work Breakdown Structure |

---

# Chapter 1 — Introduction

> **Criteria:** P1, P2, M1, D1 (proposal-bound)  ·  **Target:** 1,000–1,500 words

## 1.1 Background and Context

[Source from `docs/proposal.md` §1. Refine with current Statista / McKinsey numbers (replace `[verify]` tags with actual figures at time of submission).]

## 1.2 Problem Statement

[Source from `docs/proposal.md` §2 — hybrid effectiveness with cold-start as sub-question.]

## 1.3 Project Aim

To design, build and critically evaluate a hybrid product recommendation system combining content-based filtering, collaborative filtering and Neural Collaborative Filtering, in order to determine the conditions under which the hybrid approach improves recommendation accuracy and relevance over single-algorithm baselines, using the H&M Personalized Fashion Recommendations dataset as a case study.

## 1.4 Project Objectives

[Six SMART objectives from `docs/proposal.md` §4 — keep them or refine.]

## 1.5 Research Questions

[Four RQs from `docs/proposal.md` §5.]

## 1.6 Significance of the Project

[2–3 paragraphs. Academic, industry, personal significance. Reference Uzbek e-commerce growth (Uzum, Asaxiy, Olcha) and frame the deployed artefact — the "Chiroyli" cosmetics marketplace (Chapter 5b) — as a concrete instance of personalisation for a local marketplace, including the day-one cold-start reality a new vendor faces.]

## 1.7 Scope and Limitations

[1 paragraph each. Scope: four algorithms, single dataset (H&M), offline evaluation, optional small-N user feedback, plus the deployed "Chiroyli" cosmetics marketplace as the graded "real product" layer (Chapter 5b). Limitations: dataset bias (H&M-specific), offline metrics only, compute constraint on NCF, and — critically — the marketplace pivot to a domain with no transaction history, which limits the live storefront to a content-based recommender (see §5b.14).]

## 1.8 Structure of the Report

[1 paragraph signposting Chapters 2–7.]

---

# Chapter 2 — Literature Review

> **Criteria:** M1, D1  ·  **Target:** 2,000–3,000 words  ·  Source: `docs/literature_review.md`

[Copy/transfer content from the literature review scaffold. Ensure each theme compares sources, not just lists them. The Rendle et al. (2020) caveat goes in §2.3.3 — non-negotiable for D1.]

---

# Chapter 3 — Project Planning and Methodology

> **Criteria:** P3, P4, M2, D2  ·  **Target:** 2,000–2,500 words  ·  Source: `docs/project_plan.md`

[Copy/transfer from the project plan scaffold. Critical: §3.10 (D2) must be written *after* the project finishes, from `logbook.md` evidence. Don't invent it.]

---

# Chapter 4 — Data Collection and Analysis

> **Criteria:** P5, M3, M4  ·  **Target:** 1,500–2,500 words

## 4.1 Data Collection

### 4.1.1 Secondary Data — H&M Kaggle Dataset
[Source, structure, licence, why this dataset.]

### 4.1.2 Primary Data (optional) — Streamlit User Feedback
[How collected, consent, anonymity. Defer to `docs/ethics_form.md`.]

### 4.1.3 Sampling Strategy
[1M-row sample for development; 500K for cross-validation. Justify: smaller-than-full but large enough for stable patterns.]

## 4.2 Analytical Techniques

### 4.2.1 Quantitative
[Descriptive statistics (Chapter 4 EDA); evaluation metrics (Precision@K, Recall@K, NDCG, MAP, HitRate); paired Wilcoxon signed-rank tests.]

### 4.2.2 Qualitative
[Thematic analysis of free-text user feedback (if N ≥ 5).]

## 4.3 Findings — Exploratory Data Analysis

[Source: `docs/findings_eda.md`. Include sparsity, long-tail, time range, cold-start exposure. Embed Figures 4.1–4.3.]

## 4.4 Comparison of Patterns and Trends

[1 paragraph. How the EDA findings inform algorithm choice — sparsity favours MF/NCF; long-tail motivates personalisation; cold-start exposure motivates hybrid + fallback.]

---

# Chapter 5 — Results, Discussion and Findings

> **Criteria:** P5, M3, M4, **D3**  ·  **Target:** 2,000–2,500 words  ·  This is the chapter that earns Distinction

## 5.1 Single-Split Results per Algorithm

[Subsections 5.1.1–5.1.4 — one per algorithm. Source `docs/findings_content_based.md`, `docs/findings_cf.md`, `docs/findings_hybrid.md`, `docs/findings_ncf.md`.]

## 5.2 Cross-Validated Comparison

[Source: `notebooks/06_evaluation.ipynb` outputs. Table 5.1 (mean ± std per metric), Figure 5.3 (bar chart with error bars).]

## 5.3 Statistical Significance

[Table 5.2 from `outputs/evaluation/wilcoxon_pairs.csv`. Interpret each pair: significant or not, and what that implies.]

## 5.4 Cold-Start Segmented Evaluation

[Source: `outputs/evaluation/cold_start_segments.csv`. Three subsets: pure warm, partial-cold-item, cold user. Discuss the popularity fallback's role.]

## 5.5 Validity

[**D3 evidence:** offline–online gap (Beel et al., 2013); dataset bias; sample-vs-full data; metric choice rationale.]

## 5.6 Reliability

[**D3 evidence:** fixed seeds; 5-fold CV; mean ± std reported; Wilcoxon non-parametric test (no normality assumption); 3 random initialisations of ALS attempted (or note as future work).]

## 5.7 Project Effectiveness Evaluation

[D2 evidence — link to Chapter 3.10. What worked in the planning, what did not. Quote logbook entries.]

## 5.8 Limitations

[Honest. Sample size, single dataset, offline only, NCF not cross-validated, demographic bias.]

## 5.9 Implications for Practice and Future Research

[**D3 evidence — propose future development:**
- A/B test the hybrid on a real platform (Uzum, Olcha) to close the offline–online gap.
- Run on the full 31M-row dataset on a GPU cluster.
- Test transformer-based sequential recommenders (Sun et al., 2019 BERT4Rec).
- Diversity / fairness metrics on top of accuracy metrics.
- Localised re-evaluation on Uzbek e-commerce data when available.]

---

# Chapter 5b — Platform Implementation: the "Chiroyli" Marketplace

> **Criteria:** P4, M5, D3 (added at supervisor request — the academic notebooks alone do not satisfy the "real product" scoping of this submission)  ·  **Target:** 1,200–1,600 words

This chapter documents the deployed multi-user platform built on top of the four notebook-trained models. The product passed through two deliberate, late-stage scope changes: first from a public Streamlit demo to an **auth-gated product**, then a pivot to **"Chiroyli" — a gold-themed cosmetics marketplace** modelled on local Uzbek e-commerce (Uzum, Asaxiy, Olcha). This chapter describes the current artefact and reflects critically on managing that moving scope (D2 evidence).

One design constraint governs everything below. **The four models are trained on H&M fashion `article_id`s and cannot score the cosmetics catalogue** — there is no cosmetics transaction history to fit a collaborative model on. Rather than fabricate one, the marketplace serves its recommendations from a **separate content-based recommender** built over the generated cosmetics attributes (`shared.recommend_cosmetics` — TF-IDF over brand, category, product type, shade, audience and description), while the H&M-trained content/ALS/hybrid/NeuMF models and their quantitative evaluation (Chapters 4–5) remain the academic core and continue to back the analyst-only research pages (Evaluation, Algorithms). This division — a lightweight production recommender for the live cosmetics product, the rigorously-evaluated collaborative models for the empirical study — is itself a finding about the distance between offline recommender research and a shippable storefront, and is revisited at the close of this chapter (§5b.14).

## 5b.1 Scope Decisions and Cut List

The platform's scope was managed across two explicit decisions, both documented as evidence of control rather than drift.

**Decision 1 — the MVP cut (auth-gated product).** Eleven days of capacity remained when the first scoping conversation took place. A full feature tree was prepared and deliberately **cut down** to a defensible MVP: register/login/logout (no password reset), customer + admin roles only, two-rail home feed, catalogue with category filter (no full-text search), explicit thumbs feedback (no dwell-time tracking), admin-triggered retraining (no automatic loop), single admin page (no analytics dashboard).

**Decision 2 — the Chiroyli pivot (marketplace).** A subsequent conversation re-scoped the product as a cosmetics marketplace against a concrete, client-style brief of fourteen features (carousel, public browse with an order-time auth gate, on-sale and recommended rails, pagination, faceted filters plus men/women/kids tags, an offline "order now" flow with notifications, a recommendation assistant, reviews and ratings, product comparison, a seller panel, and a gold "Chiroyli" identity). Several Decision-1 cuts were knowingly **reversed** here — persistent login, an analytics dashboard, richer filtering, and two further roles (`analyst`, `seller`) were added back because the marketplace framing made them load-bearing rather than optional. This is presented honestly as a second, scoped decision with a fixed feature list, not as feature creep; the original cut list and the fourteen-feature brief are both reproduced in Appendix K.

## 5b.2 Architecture

The platform is a Streamlit multipage application (`st.navigation` router, Streamlit ≥1.50) sharing the notebook-trained model artefacts via `@st.cache_resource` loaders:

- **`app/db.py`** — SQLite at `data/app.db`. The schema grew with the marketplace to twelve tables: `users`, `preferences`, `interactions`, `login_attempts`, `sessions` (persistent-login tokens), `cart`, `orders` + `order_items`, `reviews`, `notifications`, `seller_products`, and `experiment_bucket`. User-facing state (wishlist, likes, dislikes) is still derived by replaying the append-only `interactions` log — `(saves – unsaves – purchases)` for the wishlist, paired toggle events for likes/dislikes — which avoids race conditions under concurrent reruns and yields a complete audit trail. Relaxing a `CHECK` constraint (e.g. adding the `seller` role) is handled by `_migrate_user_role()`, a self-repairing migration that runs in autocommit with `foreign_keys=OFF` so the table rebuild does not cascade-corrupt child foreign keys — a non-obvious SQLite hazard caught and fixed during this work.
- **`app/auth.py`** — bcrypt-hashed credentials, pure-function design (no Streamlit imports) so the helpers are unit-testable and reusable from CLI seeding scripts. Four roles are whitelisted: `customer`, `admin`, `analyst` (research dashboards, no admin panel), and `seller` (own listings only).
- **`app/shared.py`** — all cached loaders, recommenders, card renderers, the cosmetics layer (`load_cosmetics`, `recommend_cosmetics`, the rule-based assistant `cosmetics_assistant_reply`, the compare tray), and the persistent-session helpers. `load_cosmetics()` reads a committed 51-product catalogue (`app/assets/cosmetics_products.csv`) **and unions in active seller listings** from `seller_products`. The H&M recommender signatures take **`positives` and `excluded`** as separate sets so dislikes filter outputs without polluting the ALS fold-in signal.
- **`app/main.py`** — entry point and router. Four role branches register different page sets (visibility is page registration, not per-page buttons): guests get Home/Catalogue/Compare/Sign-in; admins get Analytics + Admin only; sellers get the Seller panel only; customers/analysts get the full storefront. The cosmetics home renders a carousel, on-sale rail, recommended rail, and the "Ask Chiroyli" assistant.
- **`app/pages/`** — storefront: `1_Catalogue.py`, `2_Wishlist.py`, `_compare.py` (product comparison), `_product.py` (detail + reviews + add-to-cart + offline order), `_cart.py`/`_checkout.py`/`_success.py`; back-office: `_seller.py`, `_admin.py`, `_analytics.py`; research (analyst): `3_Evaluation.py`, `4_Compare.py`.
- **`app/retrain.py`** — refits the H&M ALS model on a recent transaction slice plus active platform saves/likes/purchases (admin-triggered). Note this retrains the *research* model, not the cosmetics recommender, which is content-based and rebuilt in-process via `shared.refresh_catalogue()` whenever a seller adds or edits a product.

## 5b.3 Cold-Start Handling

Newly-signed-up users have no history, which would render any personalised feed inert. The marketplace's cosmetics recommender (`recommend_cosmetics`) handles this directly: a user's profile is the L2-normalised mean of the TF-IDF vectors of their saved items, and when that set is empty it falls back to a **featured ordering** (on-sale items first, then by price) so the "Recommended for you" rail and the home page are never blank — even for a guest who is not signed in at all. Preference categories selected at signup (e.g. *Skincare*, *Makeup*, *Fragrance*) seed the profile before any saves exist.

The same cold-start problem in the *research* models is solved differently and documented for completeness: the H&M ALS path uses `recalculate_user=True` in the `implicit` library to solve a per-request ridge regression for the user's latent factor from whatever positive signal exists. Without this flag the recommender silently reused whichever H&M customer occupied row 0 of the user matrix — a bug caught during the multi-user smoke test. That path now serves only the analyst Algorithms page, not the live storefront.

## 5b.4 Explainability

Each recommendation card shows a one-line "Why" caption:

- For content-based and hybrid rails: the top three TF-IDF terms shared between the user profile and the recommended item, computed as element-wise product of the normalised profile and item vectors. Implementation in `shared.explain_cb_for_items`.
- For the "Because you saved X" rail and the product-detail similar-items grid: a list of shared categorical attributes (`same type, same colour, same section`). Implementation in `shared.explain_similar_to`.

This is the operational version of the "interpretability" theme from the literature review (Chapter 2). It is intentionally lightweight — no LIME or SHAP — but it is on-screen for every recommendation, which a heavyweight explainer at one-second-per-card latency could not afford.

## 5b.5 Feedback Loop

Explicit feedback is captured via mutually-exclusive 👍 / 👎 buttons under every recommendation card. Toggling is implemented as paired event types (`like` / `unlike`, `dislike` / `undislike`); switching from like to dislike emits two events atomically so the derived state is never "both". Dislikes are added to the `excluded` set across all recommenders; the disliked article and its near-neighbours are pushed down on the next rerun, demonstrating the closed feedback loop end-to-end.

Implicit feedback is limited to per-session-deduplicated `view` events when the product-detail page opens. Dwell time is not captured (Streamlit's session model makes accurate measurement infeasible without a JavaScript injection); this is documented as future work in §5.9.

## 5b.6 Retraining Loop

The admin page exposes a "Retrain ALS now" button (`app/retrain.py`). Each invocation:

1. Loads articles for the item index.
2. Loads a sampled recent H&M transactions window (default: last calendar month, capped at 300 k rows for time-budget compliance).
3. Reads all currently-active platform saves / likes / purchases from `interactions`.
4. Builds the combined user-item sparse matrix; fits ALS at the same factor count as the existing bundle.
5. Overwrites `models/cf_als_model.pkl` and calls `shared.load_cf.clear()` to flush the Streamlit cache.

A full retrain on the project's reference droplet (DigitalOcean 4 GB / 2 vCPU) completes in approximately 25–45 seconds. The button surfaces progress messages and returns a stats dict (users, items, interactions, factors, elapsed). This is the smallest possible artefact that demonstrates a closed retraining loop; a true production system would schedule it (cron / Airflow) rather than running it interactively.

## 5b.7 Security and Privacy

- Passwords are bcrypt-hashed with the library default cost; no plaintext is ever persisted.
- The auth-screen email validator requires a non-trivial TLD; minimum password length is 8 (configurable via `auth.MIN_PASSWORD_LEN`).
- Role gating is enforced at **page registration** (`st.navigation` registers a different page set per role) *and* re-checked inside sensitive pages — e.g. the seller panel returns an "access denied" view for a non-seller who navigates to `/seller` directly. (Defence-in-depth — not just UI hiding.) The four roles are `customer`, `admin`, `analyst`, `seller`.
- **Persistent login** uses a signed token stored in an HTTP cookie (`streamlit-cookies-controller`) backed by a server-side `sessions` table with expiry; logout and idle-timeout both clear the cookie so it cannot silently re-authenticate. This resolved the MVP's "browser close logs you out" limitation.
- SQLite is local to the droplet; no analytics or marketing trackers are loaded. The `interactions` log is per-user and never shared with third parties. See Appendix E (Data Management Plan) for full GDPR mapping.

## 5b.8 Performance Engineering

GTmetrix baseline before platform work: **Grade E** (LCP 5.3s, FCP 4.8s, CLS 0.54). Root causes identified from the HAR: 73 of 74 responses uncompressed (Streamlit's bundled JS = 2.51 MB), and a 0.54 cumulative-layout-shift on the home block container when cached loaders finish. Fixes applied:

- `deploy/install.sh` nginx fragment now enables gzip for `application/javascript`, `text/css`, `application/json`, `application/wasm`, `image/svg+xml` at compression level 5. Verified on the droplet: total transfer drops from 3.06 MB to ≈1.2 MB.
- `app/shared.py` `.block-container` rule sets `min-height: 920px`, reserving vertical space so the page doesn't reflow when the rec grid populates. Cards have `min-height: 180px`; saved-item rows have `min-height: 56px`.

Re-tested GTmetrix at port 80 (nginx-fronted): see §5.4 of `docs/findings_perf.md` for the updated trace [verify before final submission].

## 5b.9 Honest Limitations

- **Recommendation quality on cosmetics is content-only.** Because the collaborative, hybrid and neural models cannot score the generated cosmetics catalogue (no transaction history), the live marketplace relies on a single content-based recommender. The richer collaborative signal demonstrated empirically in Chapters 4–5 is therefore *not* exercised by the shipping product — a genuine limitation of pivoting the storefront to a domain without behavioural data (see §5b.14).
- **Catalogue scale.** The marketplace catalogue is a curated 51-product set (plus seller additions) with committed photography, not the ≈106k-item H&M catalogue. This keeps the demo coherent and fast but means filtering/search are not stress-tested at scale.
- **No password reset.** Cut for time; an admin-mediated reset workflow is documented in the README.
- **Retraining is manual.** The H&M ALS "loop" is operator-triggered, not scheduled. In a real e-commerce platform this would run nightly via cron.

(The original MVP's session-persistence limitation has since been resolved: persistent login via signed cookies + a server-side `sessions` table was added during the marketplace work — see §5b.7.)

## 5b.10 Marketplace Surfaces

The cosmetics storefront is **public**: guests can browse the home page and catalogue and add items to a comparison tray; the authentication wall only appears at the point of ordering or saving. The home page opens with a three-slide **carousel banner**, an **on-sale rail** (items whose `sale_price` is set, shown with a struck-through original and a gold sale price), and a personalised **recommended rail**. The catalogue offers **pagination** and a faceted filter panel — price, shade, size, brand, quality and country of manufacture — alongside **men / women / kids audience tags** that act as quick filters. Sale-awareness is centralised in `catalogue_price`/`effective_price` so every surface (cards, comparison, cart, seller panel) prices an item identically.

## 5b.11 Reviews, Comparison and the Assistant

Three features bring the product closer to a real marketplace:

- **Reviews and ratings.** Each product page shows an aggregate star rating and the list of customer reviews; signed-in buyers can leave or update a single review (upserted, one per user per product) via the `reviews` table.
- **Product comparison.** A session-scoped tray (up to four items, added with the ⚖ button on any card or product page) renders an **Asaxiy-style side-by-side table** — price, rating, brand, category, type, audience, shade, size, quality and country — for at-a-glance comparison. The page is public.
- **"Ask Chiroyli" assistant.** A **rule-based** assistant on the home page (no external LLM) parses a free-text request for category, product type, brand, shade, country, audience, quality, a price cap ("under $30"), on-sale, gift and skin-concern intents, scores the catalogue against those signals, and returns product cards — falling back to featured picks when nothing matches. Implementing this with transparent rules rather than a language model keeps it explainable, offline, and free to run, consistent with the interpretability theme of Chapter 2.

## 5b.12 Cart, Checkout and the Offline "Order Now" Flow

The marketplace supports two purchase paths, reflecting how local Uzbek retailers actually operate. The **online path** is a cart → mock-checkout → confirmation flow (`_cart.py` / `_checkout.py` / `_success.py`) with inline, red-border field validation and a success animation; it records an `order` with status `paid`. The **offline path** is a one-click "Order now" button that reserves the item for in-store collection: it records an `order` with status `offline`, logs a purchase interaction, and posts an in-app **notification** ("…you can come to our market and collect it, paying offline") surfaced through the account-menu bell. Notifications and orders are first-class tables, so both paths produce a real audit trail.

## 5b.13 Seller Panel

A `seller` role turns the catalogue into a small **multi-vendor marketplace**. Seller-listed products live in a `seller_products` table and are **unioned into the live catalogue** by `load_cosmetics()` (seller items take `S`-prefixed IDs to avoid collision with the curated `C`-prefixed set); a seller-supplied image URL is honoured by the image resolver. The panel (`_seller.py`) gives a seller revenue/units/active-listing metrics, a create-and-edit product form, show/hide and delete controls, and a table of the orders placed for their products. Adding or editing a listing calls `shared.refresh_catalogue()` to flush the cached catalogue and its TF-IDF index, so a new product appears in browse, search and recommendations immediately.

## 5b.14 The Recommendation Split — Reflection

The most intellectually honest part of this chapter is the gap it exposes. The empirical study (Chapters 4–5) demonstrates, on real behavioural data, that collaborative and hybrid methods outperform a content-only baseline. Yet the shipping product — once pivoted to a cosmetics domain with **no** transaction history — can only run that content-only baseline, because there is nothing for a collaborative model to learn from. This is not a coding shortcut; it is the cold-start problem at the level of an entire catalogue, and it is exactly the situation a new Uzbek marketplace would face on day one. The defensible engineering response was to ship the recommender the data *can* support (content-based, plus explicit saves and reviews to bootstrap behavioural signal) while keeping the evaluated collaborative models live behind the analyst pages as the evidence base for *what to build next* once real purchase data accrues. The split is therefore presented as a finding, not an apology: it makes concrete the distance between an offline benchmark result and a recommender that can actually be deployed into a cold domain.

---

# Chapter 6 — Conclusion and Recommendations

> **Target:** 500–800 words

## 6.1 Summary of the Project
[1 paragraph re-stating problem, approach, headline finding.]

## 6.2 Achievement of Objectives

| Objective | Evidence | Status |
|---|---|---|
| O1 — Literature review of 25+ sources | Chapter 2 + Reference list | [✓ / partial] |
| O2 — Dataset acquired and pre-processed, EDA notebook | `notebooks/01_eda.ipynb` + `docs/findings_eda.md` | [✓ / partial] |
| O3 — Four algorithms implemented in Python | `notebooks/02–05` + `models/` artefacts | [✓ / partial] |
| O4 — Each model evaluated with cross-validation + significance | `notebooks/06_evaluation.ipynb` + `outputs/evaluation/` | [✓ / partial] |
| O5 — Streamlit demo deployed + 20+ user feedback | `app/main.py` + DigitalOcean droplet + `data/app.db` interactions (replaced the JSONL feedback file with the SQLite interaction log when scope expanded to a real product — see Ch 5b) | [✓ / partial] |
| O6 — Final report + 12–15 slide presentation | This document + `docs/presentation_outline.md` | [✓ / partial] |

## 6.3 Contribution to Knowledge and Practice

[1 paragraph each — academic, practical, personal.]

## 6.4 Recommendations

### 6.4.1 For Practitioners (Local Uzbek Marketplaces such as Chiroyli)
[3–5 concrete recommendations: e.g. on day one in a cold domain ship content-based recommendations and capture explicit signal (saves, reviews) to bootstrap behavioural data; introduce ALS as a baseline only once purchase history accrues; deploy the hybrid only after measuring uplift; budget for NCF only if expected uplift > engineering cost. Tie each back to the Chiroyli artefact's actual design choices (Chapter 5b).]

### 6.4.2 For Future Researchers
[3–5 directions: see Chapter 5.9.]

## 6.5 Closing Remarks

[1 paragraph.]

---

# Chapter 7 — Reflective Evaluation

> **Criteria:** P7, M5, D4  ·  **Target:** 800–1,200 words  ·  Source: `docs/reflective_evaluation.md`

[Copy/transfer from reflective evaluation scaffold. Use Gibbs cycle throughout. Reference specific dated logbook entries — not generic statements.]

---

# References

[All Harvard. Combine from `docs/proposal.md` §12 + any sources added during the literature review and findings work. Final target: 25+ sources, of which at least 8 are peer-reviewed journal articles from the last 5 years.]

---

# Appendices

| Appendix | Source | Purpose |
|---|---|---|
| A — Project Proposal (approved version) | `docs/proposal.md` | LO1 evidence |
| B — Full Gantt chart | `outputs/figures/gantt.png` | M2 evidence |
| C — Full Risk Register | `docs/project_plan.md` §3.6 | M2 / D2 evidence |
| D — Ethics Approval Form (signed) | `docs/ethics_approval.pdf` | P3 evidence |
| E — Data Management Plan | `docs/data_management_plan.md` | P3 / GDPR compliance |
| F — Code listings (selected) | `src/data.py`, `src/metrics.py`, `app/main.py` | implementation evidence |
| G — Raw user feedback (anonymised) | `outputs/user_feedback/feedback.jsonl` | qualitative findings |
| H — Project Logbook (extracts) | `logbook.md` (chosen entries) | M2 / D2 / D4 evidence |
| I — Supervisor meeting records | `docs/supervisor_notes/` | M2 evidence |
| J — Assessment Criteria self-check matrix | end of this report | mapping P/M/D ➜ chapter |
| K — Platform scope cut list | Day-1 of the build | evidence of explicit scope control (Ch 5b §5b.1) |

---

## Final BTEC Assessment Criteria Self-Check

| Code | Criterion | Where in this report |
|---|---|---|
| P1 | Aim + objectives for a complex problem | Ch 1 §1.3–1.4 |
| P2 | Significance in digital tech context | Ch 1 §1.6 |
| P3 | Structured plan with timelines, resources, risks, ethics | Ch 3 + Appendix B, C, D, E |
| P4 | Implement key elements of the plan | Ch 3 §3.9 + Ch 4–5 + Appendix F |
| P5 | Apply data collection + analysis | Ch 4 + Ch 5 §5.1 |
| P6 | Structured report + oral presentation | This document + slide deck |
| P7 | Reflective review using a recognised model | Ch 7 (Gibbs cycle) |
| M1 | Justify relevance/feasibility/significance with sources | Ch 1 §1.1, 1.6 + Ch 2 |
| M2 | Monitor progress, respond to emerging challenges | Ch 3 §3.6, §3.8, §3.9 + Appendix H, I |
| M3 | Interpret data collection + analysis methods | Ch 4 §4.2 + Ch 5 §5.1–5.4 |
| M4 | Compare patterns/trends with visualisation | Ch 4 + Ch 5 figures 5.1–5.4 |
| M5 | Communicate outcomes to professional audience | This document + oral presentation |
| **D1** | Evaluate alternative research approaches | Ch 2 §2.5 + Ch 1 (proposal traceability) |
| **D2** | Critically assess planning effectiveness | Ch 3 §3.10 + Ch 5 §5.7 + Ch 7 |
| **D3** | Evaluate validity + reliability + propose future development | Ch 5 §5.5, §5.6, §5.9 |
| **D4** | Review personal/professional development + future strategies | Ch 7 |

Before final submission, run this checklist once:

- [ ] Word count between 8,000 and 10,000
- [ ] At least 25 Harvard-formatted references; at least 8 peer-reviewed from last 5 years
- [ ] Every figure / table referenced in the text by number
- [ ] Every `[verify]` / `[date]` / `[N]` placeholder replaced
- [ ] All chapters' criteria boxes mapped above
- [ ] Spell-checked, grammar-checked (Grammarly)
- [ ] Turnitin similarity check completed
- [ ] Signed declaration of originality in front matter
- [ ] PDF exported with embedded fonts; print copy ordered
