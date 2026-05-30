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

[Open with one sentence on global e-commerce + personalisation. State the problem: under what conditions does a hybrid recommender beat single-algorithm baselines on a real fashion dataset? State the aim. Summarise the methodology in two sentences (H&M dataset, four algorithms, 5-fold CV, statistical tests). Quote the headline finding with one number. Close with the contribution.]

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

[2–3 paragraphs. Academic, industry, personal significance. Reference Uzbek e-commerce growth (Uzum, Olcha).]

## 1.7 Scope and Limitations

[1 paragraph each. Scope: four algorithms, single dataset, offline evaluation, optional small-N user feedback. Limitations: dataset bias (H&M-specific), offline metrics only, compute constraint on NCF.]

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

# Chapter 5b — Platform Implementation: Auth-Gated Product

> **Criteria:** P4, M5, D3 (added at supervisor request — the academic notebooks alone do not satisfy the "real product" scoping of this submission)  ·  **Target:** 800–1,200 words

This chapter documents the deployed multi-user platform built on top of the four notebook-trained models. The decision to deliver an auth-gated product (rather than the original public Streamlit demo) was taken late in the project at the supervisor's direction; this chapter therefore both describes the artefact and reflects critically on the late-stage scope expansion (D2 evidence).

## 5b.1 Scope Decision and Cut List

Eleven days of capacity remained when the scoping conversation took place. A full feature tree was prepared (auth + RBAC + four-rail home + catalogue with search + per-card explicit/implicit feedback + retraining loop + analytics dashboard + admin panel) and explicitly **cut down** to a defensible MVP: register/login/logout (no password reset), customer + admin roles only, two-rail home feed, catalogue with category filter (no full-text search), explicit thumbs feedback (no dwell-time tracking), admin-triggered retraining (no automatic loop), single admin page (no analytics dashboard). The cut list is reproduced verbatim in Appendix K as evidence of explicit scope control, not feature inflation.

## 5b.2 Architecture

The platform is a Streamlit multipage application sharing the notebook-trained model artefacts via `@st.cache_resource` loaders:

- **`app/db.py`** — SQLite at `data/app.db`. Three tables (`users`, `preferences`, `interactions`). All state is derived from the append-only `interactions` log: the current wishlist is `(saves – unsaves – purchases)` replayed; likes / dislikes are similarly derived. This avoids race conditions on toggle state under concurrent reruns and produces a complete audit trail.
- **`app/auth.py`** — bcrypt-hashed credentials, pure-function design (no Streamlit imports) so the helpers are unit-testable and reusable from CLI seeding scripts.
- **`app/shared.py`** — all cached loaders, recommenders, and card-rendering helpers. Recommender signatures take **`positives` and `excluded`** as separate sets, so dislikes filter outputs without polluting the ALS fold-in signal.
- **`app/main.py`** — entry point and home page (two product rails plus a "Compare algorithms" expander that preserves the academic switcher for viva demos).
- **`app/pages/`** — `1_Catalogue.py`, `2_Wishlist.py` (visible nav), `_product.py`, `_admin.py` (hidden, reached via in-app navigation).
- **`app/retrain.py`** — refits ALS on a recent slice of H&M transactions plus currently-active platform saves/likes/purchases. Platform users are keyed `"app:<id>"` to avoid collision with H&M customer hashes; platform interactions are weighted 3× to reflect their explicit-feedback character.

## 5b.3 Cold-Start Handling

Newly-signed-up users have no purchase history, which would render both ALS and the content-based profile inert. Two mechanisms address this:

1. **Preference seeding at signup.** Users select at least three product-type categories (e.g. *dress*, *jeans*, *t-shirt*). The first build of their content-based profile is the L2-normalised mean of TF-IDF vectors of up to 80 catalogue exemplars from those categories.
2. **Online ALS fold-in.** ALS recommendations use `recalculate_user=True` in the `implicit` library, solving a per-request ridge regression for the user's latent factor from whatever positive signal they have so far. Without this flag, the recommender silently uses whichever H&M customer happened to occupy row 0 of the user matrix — a bug caught during the multi-user smoke test.

The "Picked for you" rail is therefore non-empty for fresh accounts (CB profile from preferences seeds the hybrid), while the "Because you saved X" rail is gated on at least one save. The collaborative-filtering-only tab in the compare expander explicitly tells the user it requires at least one save to fold them in — a design choice favouring legibility over silent fallback.

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
- Admin actions are gated server-side on `user["role"] == "admin"` — the sidebar "Admin panel" button is only rendered for admins, but the page itself re-checks the role and returns an "access denied" view for non-admins who navigate directly. (Defence-in-depth — not just UI hiding.)
- SQLite is local to the droplet; no analytics or marketing trackers are loaded. The `interactions` log is per-user and never shared with third parties. See Appendix E (Data Management Plan) for full GDPR mapping.

## 5b.8 Performance Engineering

GTmetrix baseline before platform work: **Grade E** (LCP 5.3s, FCP 4.8s, CLS 0.54). Root causes identified from the HAR: 73 of 74 responses uncompressed (Streamlit's bundled JS = 2.51 MB), and a 0.54 cumulative-layout-shift on the home block container when cached loaders finish. Fixes applied:

- `deploy/install.sh` nginx fragment now enables gzip for `application/javascript`, `text/css`, `application/json`, `application/wasm`, `image/svg+xml` at compression level 5. Verified on the droplet: total transfer drops from 3.06 MB to ≈1.2 MB.
- `app/shared.py` `.block-container` rule sets `min-height: 920px`, reserving vertical space so the page doesn't reflow when the rec grid populates. Cards have `min-height: 180px`; saved-item rows have `min-height: 56px`.

Re-tested GTmetrix at port 80 (nginx-fronted): see §5.4 of `docs/findings_perf.md` for the updated trace [verify before final submission].

## 5b.9 Honest Limitations

- **Session persistence.** Closing the browser logs the user out — the current implementation does not use signed cookies for session resumption. A cookie-manager bolt-on would be a half-day extension.
- **No password reset.** Cut for time; an admin-mediated reset workflow is documented in the README.
- **Search.** Catalogue browse is filter-only, not full-text search. The H&M catalogue has ≈106k items; a real-search implementation would need an inverted index, which is out of scope for this submission.
- **Retraining is manual.** The "loop" is operator-triggered, not scheduled. In a real e-commerce platform this would run nightly via cron.

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

### 6.4.1 For Practitioners (Local Uzbek Marketplaces)
[3–5 concrete recommendations: e.g. start with ALS as baseline; deploy hybrid only after measuring; budget for NCF only if expected uplift > engineering cost.]

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
