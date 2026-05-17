# Oral Presentation Outline

**A Hybrid Product Recommendation System for Online Marketplaces Based on Customer Preferences**

**Lola Toirxonova · BTEC L6 Unit 2 — Independent Project · PDP Private University**

> **Format:** 15–20 minutes speaking + 10 minutes Q&A
> **Slides:** 12–15 maximum — one main idea per slide
> **Audience:** professional academic panel + supervisor + classmates
> **Criteria:** P6 (presentation), M5 (communicate to professional audience), D4 (also includes oral reflection)
> **Backup:** record a 3-minute screen capture of the live Streamlit demo as fallback for connection failure during defence.

---

## Slide-by-slide structure

### Slide 1 — Title

- **Title:** A Hybrid Product Recommendation System for Online Marketplaces
- Lola Toirxonova · BIT Department · PDP Private University
- Supervisor: Abdulaziz Gulomov · 1 June 2026
- One image: hero shot of the Streamlit demo

**Speaker note (15s):** Greet, introduce yourself, state the project title.

---

### Slide 2 — The problem

- Global e-commerce + personalisation context (1 stat from Statista or McKinsey)
- The two failure modes that motivated the project: **cold-start** and **algorithm-choice opacity**
- Why H&M as the case study

**Speaker note (60s):** Frame the problem as something the audience already cares about; arrive at the gap.

---

### Slide 3 — Aim and research questions

- **Aim:** one clear sentence
- **RQ1 / RQ2 / RQ3** — the three questions you'll answer
- Mapped to BTEC LO1, LO3

**Speaker note (60s):** Read out the aim verbatim; explain that the rest of the talk works through each RQ.

---

### Slide 4 — Methodology overview

- Visual: pipeline diagram (Data → 4 Algorithms → Evaluation → Demo)
- Dataset: H&M Kaggle (31M transactions, 105K products)
- Four algorithms: Content-Based · ALS CF · Hybrid · NCF
- Evaluation: 5-fold CV + Wilcoxon

**Speaker note (90s):** Walk through the pipeline once. Promise that the next 4 slides go into each model.

---

### Slide 5 — Algorithm 1 — Content-Based (TF-IDF)

- One-line description + the cold-item strength
- 1 chart: per-user spot-check table OR Precision@10 result
- Cite: Lops, de Gemmis and Semeraro (2011)

**Speaker note (60s):** What it does, what it's good at, where it loses.

---

### Slide 6 — Algorithm 2 — Collaborative Filtering (ALS)

- One-line description + the cold-start weakness
- 1 chart: ALS vs content-based bar chart
- Cite: Hu, Koren and Volinsky (2008); Koren, Bell and Volinsky (2009)

**Speaker note (60s):** Same template — what / good at / loses where.

---

### Slide 7 — Algorithm 3 — Hybrid (the project's main contribution)

- The α-sweep curve from `outputs/hybrid/alpha_sweep.png` — this is the *visual centrepiece*
- Best α found and the uplift over the better single model
- Cite: Burke (2002) hybrid taxonomy

**Speaker note (90s):** Spend extra time here. This is the answer to RQ1.

---

### Slide 8 — Algorithm 4 — Neural Collaborative Filtering

- Architecture diagram (GMF + MLP merged)
- Honest result: did NCF win or not?
- Cite: He et al. (2017) and the critical caveat — Rendle et al. (2020)

**Speaker note (75s):** *This slide earns Distinction.* Even if NCF underperformed, present it as a finding consistent with Rendle et al. (2020), not as a failure.

---

### Slide 9 — Cross-validated comparison

- The headline chart: `outputs/figures/cv_metrics_with_error_bars.png`
- One Wilcoxon p-value to anchor the narrative
- Cold-start segmented metrics from `outputs/evaluation/cold_start_segments.csv`

**Speaker note (90s):** *This is the answer to RQ2 and the D3 evidence.* State plainly: which model wins, by how much, with what statistical confidence.

---

### Slide 10 — Live demo

- **Switch to Streamlit window.** If the cloud demo fails: play the 3-minute backup video.
- Walk through: pick a user → show their purchase history → run the hybrid → discuss one recommendation in detail.
- Submit one feedback form on the spot.

**Speaker note (120s):** Practiced demo path is essential. Rehearse with the panel's likely user-ID and have backup users ready in case the chosen one shows poor recommendations.

---

### Slide 11 — Limitations + future work

- **3 bullet limitations:** dataset bias (H&M Europe-centric); offline metrics only; NCF not cross-validated.
- **3 bullet future-work items:** A/B test on a real platform; sequential / transformer models (BERT4Rec); diversity / fairness metrics.

**Speaker note (60s):** Be brief but specific. The Q&A will dig in here.

---

### Slide 12 — Reflection + Personal Development Plan

- One concrete lesson from the year (drawn from Gibbs reflection 1)
- The three top items from your PDP
- Cite: Gibbs (1988); Schön (1983)

**Speaker note (60s):** Brief, sincere. Avoid generic "I learned time management" lines.

---

### Slide 13 — Conclusion + thanks

- One sentence: the headline finding
- Thanks: supervisor, family, classmates, test users
- Repo link: `github.com/lolatoirxonova-creator/gradproject`

**Speaker note (30s):** Close strong. Invite questions.

---

### (Optional) Slide 14–15 — Backup / appendix slides

Keep ready in case Q&A goes deep:

- Detailed hyperparameter table for all four models
- Time-based vs random k-fold trade-off
- The full Wilcoxon test results table
- The cold-start segmented table

---

## Rehearsal plan

| Pass | When | What |
|---|---|---|
| Pass 1 | W13 day 5 | Read through alone, slide by slide, time yourself |
| Pass 2 | W14 day 2 | Live, in front of a peer, with feedback |
| Pass 3 | W14 day 4 | Standing, out loud, with the actual demo running in the background |

**Target speaking pace:** 110–130 words per minute. If your script exceeds 2,000 words you will run over.

---

## Anticipated Q&A and prepared answers

> Distinction-level presentations *anticipate* the hard questions. Pre-write a one-sentence answer to each of these:

1. **"Why TF-IDF and not embeddings like BERT?"** → TF-IDF is the canonical baseline; BERT would be future work; reasoning about cost vs uplift on this dataset.
2. **"Why ALS over BPR or another implicit-feedback method?"** → ALS is the closer-to-MF-paper baseline; BPR was considered but rejected for budget reasons.
3. **"Why didn't you A/B test online?"** → No access to a production platform; explicitly listed as future work; cite Beel et al. (2013) on the offline–online gap.
4. **"What happens if H&M deploys this tomorrow?"** → They wouldn't — sample-vs-full data, no diversity guardrails, no production hardening. The project's value is the **methodology**, not a deployment-ready system.
5. **"Did NCF win?"** → [Yes / no — quote a number; if no, cite Rendle et al. 2020 and discuss cost–benefit].
6. **"What was the hardest part?"** → [One specific incident from the logbook, briefly, professionally.]
7. **"What would you do differently?"** → [Pick the strongest item from your PDP.]

---

## Slide-design rules

- One main idea per slide
- ≤ 20 words of text per slide (the audience reads or listens — not both)
- Every chart has axis labels, units, source, sample size
- Consistent colour scheme — one per algorithm — across all charts
- Backup slides hidden behind the conclusion slide for Q&A
- Footer on every slide: page number + Lola Toirxonova + date
