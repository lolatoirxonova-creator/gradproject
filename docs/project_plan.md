# Chapter 3 — Project Plan and Methodology

**A Hybrid Product Recommendation System for Online Marketplaces Based on Customer Preferences**

Lola Toirxonova (ID: 220062) · Supervisor: Abdulaziz Gulomov · Submission: 1 June 2026

---

> **Criteria addressed by this chapter:** P3, P4, M2, D2
>
> - **P3** — Structured project plan with timelines, resource needs, risks and ethical considerations
> - **P4** — Implement key elements of the project plan to reach project outcomes
> - **M2** — Monitor progress and respond to emerging challenges
> - **D2** — Critically assess the effectiveness of the project planning (post-project, in reflection)
>
> **Target length:** 2,000–2,500 words

---

## 3.1 Research Philosophy and Approach

This project adopts a **pragmatist research philosophy** (Saunders, Lewis and Thornhill, 2023). Pragmatism is appropriate because the research question — *under what conditions does a hybrid recommendation model outperform single-algorithm baselines on a real fashion-marketplace dataset?* — is empirical, applied and concerned with what produces useful outcomes for users and businesses rather than with abstract truth claims.

The approach is **deductive**: established theory (latent factor models, content-based filtering, hybrid taxonomy, NCF) is operationalised on a real dataset, hypotheses about model performance are formulated, and the data is used to test them. The strategy combines **design science** (building the artefact) with **quantitative empirical evaluation** (measuring its performance under controlled conditions). This combination is referred to as a **capstone-style** project format under the BTEC L6 specification.

---

## 3.2 Methodological Choice

A **quantitative** methodology is used for the core evaluation: numeric metrics (Precision@K, Recall@K, NDCG, RMSE) calculated on held-out test data and analysed with statistical significance tests (paired t-test or Wilcoxon signed-rank). A small **qualitative** component is added in Phase 6 via thematic analysis of test-user feedback collected through the Streamlit demo, producing **mixed-methods** triangulation.

---

## 3.3 Project Management Methodology

**Agile with 2-week Scrum-style sprints** is the chosen methodology, justified over the two main alternatives:

| Option | Strength | Why not chosen |
|---|---|---|
| **Waterfall** | Predictable for linear, well-defined research | The build phase has many small iterations (model → measure → tune → re-measure); locking the design at the start would miss the value of cross-validation feedback |
| **PRINCE2** | Strong on governance and reporting | Excessive overhead for a single-student capstone with one supervisor |
| **Agile / Scrum (chosen)** | Supports incremental delivery, embraces measurement-driven iteration | Requires discipline to maintain the cadence — mitigated by a fixed weekly rhythm (see §3.8) |

**Sprint structure:** 2-week sprints, 7 sprints total over 14 weeks. Each sprint has a planning note, a sprint goal, a backlog and a retrospective entry in `logbook.md`.

---

## 3.4 Project Plan

### 3.4.1 Work Breakdown Structure (WBS)

```
1. Research & Proposal
   1.1 Read all four BTEC guide documents
   1.2 Choose dataset and tech stack
   1.3 Write Project Proposal (P1, P2, M1, D1)
   1.4 Supervisor approval — gate to Phase 2

2. Literature Review
   2.1 Search strategy and source collection (target: 25+)
   2.2 Thematic synthesis across 6 themes
   2.3 Gap statement (D1)
   2.4 Conceptual framework diagram

3. Project Plan & Ethics
   3.1 WBS + Gantt + Risk Register
   3.2 Ethics form (PDP University)
   3.3 Data Management Plan
   3.4 Supervisor sign-off — gate to Phase 4

4. Data & EDA
   4.1 Download H&M dataset from Kaggle
   4.2 EDA notebook (sparsity, long-tail, time range, cold-start prep)
   4.3 EDA findings write-up

5. Baseline Models
   5.1 Content-based filtering (TF-IDF + cosine)
   5.2 Collaborative filtering (matrix factorisation — SVD/ALS)
   5.3 Initial metrics on a held-out test fold

6. Advanced Models
   6.1 Hybrid (weighted ensemble of 5.1 + 5.2)
   6.2 Neural Collaborative Filtering (NCF) in PyTorch
   6.3 Hyperparameter tuning

7. Evaluation
   7.1 5-fold cross-validation across all four models
   7.2 Cold-start segmented metrics
   7.3 Statistical significance testing
   7.4 Evaluation report

8. Deployment
   8.1 Streamlit demo app
   8.2 Deploy to Streamlit Community Cloud
   8.3 Test-user recruitment (target ≥20)
   8.4 Feedback collection and thematic analysis

9. Reporting
   9.1 Final report draft (Chapters 1–7)
   9.2 Supervisor review and revision
   9.3 Reflective evaluation (Gibbs cycle)
   9.4 Presentation slides
   9.5 Rehearsal and oral defence
```

### 3.4.2 Gantt Chart and Timeline

| Sprint | Week | Phase | Deliverable | Owner |
|---|---|---|---|---|
| S1 | 1–2 | Research & Proposal (WBS 1) | Proposal approved, dataset chosen | Lola |
| S2 | 3–4 | Literature Review (WBS 2) | 25+ sources, thematic review draft | Lola |
| S3 | 5–6 | Plan & Data (WBS 3, 4) | Project Plan, ethics signed, EDA notebook | Lola |
| S4 | 7–8 | Baseline Models (WBS 5) | Content-based + CF working with first metrics | Lola |
| S5 | 9–10 | Advanced Models (WBS 6) | Hybrid + NCF trained, hyperparameters tuned | Lola |
| S6 | 11–12 | Evaluation + Demo (WBS 7, 8) | k-fold CV done, Streamlit deployed, user feedback | Lola |
| S7 | 13–14 | Reporting (WBS 9) | Final report, slides, oral defence, reflective evaluation | Lola |

**Milestones (M):**

| # | Milestone | Target | Status |
|---|---|---|---|
| M1 | Project proposal approved | end of W2 | ⚠ in progress |
| M2 | Literature review complete | end of W4 | ⌛ |
| M3 | Ethics approval obtained | end of W5 | ⌛ |
| M4 | EDA complete + dataset documented | end of W7 | ⌛ |
| M5 | Baseline models working with metrics | end of W9 | ⌛ |
| M6 | All 4 models trained + cross-validated | end of W11 | ⌛ |
| M7 | Streamlit demo deployed | end of W12 | ⌛ |
| M8 | Final report draft to supervisor | end of W13 | ⌛ |
| M9 | Final submission + oral defence | end of W14 | ⌛ |

Full visual Gantt chart will be produced in GanttProject or Excel and saved to `outputs/figures/gantt.png`. Reference it as **Figure 3.2** in the report.

### 3.4.3 Critical Path

The chain that cannot slip without delaying final submission:

**WBS 1 → 3 → 4 → 5 → 6 → 7 → 8 → 9**

The two most-likely critical-path bottlenecks:

1. **Dataset download + EDA (WBS 4)** — the H&M dataset is ~25 GB. Allow buffer for download and a sampling pass before full EDA.
2. **NCF training (WBS 6.2)** — deep-learning training on a laptop CPU is impractical; depends on Google Colab availability. **Mitigation:** train NCF early in the sprint, fall back to a smaller embedding dimension if compute is constrained.

**Contingency:** Sprint 7 (Reporting) includes one week of buffer. If any earlier sprint slips, this is the only safe sink — protect it.

---

## 3.5 Resource Plan

| Category | Resource | Source | Cost | Risk |
|---|---|---|---|---|
| **Human** | Student (Lola) — primary | self | — | sole point of failure → mitigated by logbook + Git |
| | Supervisor — bi-weekly review | PDP University | included | low |
| | 20+ test users for demo feedback | classmates, social network | — | low response rate (see Risk Register) |
| **Digital** | Python 3.11 + libraries | open source | free | — |
| | Jupyter / VS Code | open source | free | — |
| | Git + GitHub (private repo) | github.com | free | — |
| | Streamlit Community Cloud | streamlit.io | free tier | quota limits |
| | Google Colab | google.com | free tier (occasional Pro if needed) | GPU availability not guaranteed |
| | Kaggle | kaggle.com | free | — |
| **Technical** | Laptop (16 GB RAM) | personal | — | NCF training may exceed local RAM → Colab fallback |
| **Data** | H&M Personalized Fashion Recommendations | Kaggle competition | free (academic licence) | dataset is anonymised — no PII concerns |
| **Writing** | MS Word + Zotero (Harvard style) | university licence | included | — |
| **PM tools** | GitHub Projects (Kanban) | github.com | free | — |
| | GanttProject | open source | free | — |
| **Financial** | Printing & binding of final report | local copy shop | ≈ 100,000 UZS | budget set aside |

---

## 3.6 Risk Register

> M2 — Monitor progress and respond to emerging challenges

Likelihood and Impact scored 1–5; Score = L × I. Status: 🟢 OK · 🟡 monitor · 🔴 active.

| # | Risk | L | I | Score | Mitigation | Owner | Status |
|---|---|---|---|---|---|---|---|
| R01 | H&M dataset too large for local machine (16 GB RAM) | 5 | 4 | 20 | Use 1 M-row sample for development; full dataset only on Colab | Lola | 🟡 |
| R02 | NCF training too slow on free Colab GPU | 4 | 4 | 16 | Reduce embedding dim to 32; cache intermediate tensors; consider Colab Pro one-off if needed | Lola | 🟡 |
| R03 | Model accuracy below baseline expectations | 3 | 4 | 12 | Allocate Sprint 6 buffer for tuning; keep content-based as known-good baseline | Lola | 🟢 |
| R04 | Scope creep — adding extra algorithms / features | 4 | 4 | 16 | Freeze scope at end of Sprint 1; MoSCoW prioritisation in logbook | Lola | 🟡 |
| R05 | Supervisor unavailable for critical review | 2 | 4 | 8 | Book recurring bi-weekly slot; submit async written updates with 48 h notice | Lola | 🟢 |
| R06 | Ethics approval delayed | 2 | 5 | 10 | Submit signed form by W3, before any primary data collected | Lola | 🟢 |
| R07 | Test-user response rate too low (<20) | 4 | 3 | 12 | Recruit 30 to land 20; offer summary of findings as incentive; start outreach W10 | Lola | 🟡 |
| R08 | Final report rushed in last week | 4 | 5 | 20 | Lit Review and Methodology written by end of W7; full draft by W13 | Lola | 🔴 |
| R09 | Streamlit Community Cloud quota / outage during demo | 2 | 3 | 6 | Record a 3-min screen-capture as backup; have the app ready to run locally during defence | Lola | 🟢 |
| R10 | Personal illness or family event mid-project | 2 | 5 | 10 | Sprint 7 buffer absorbs ≤1 week loss; commit small + push often so work is recoverable from any device | Lola | 🟢 |
| R11 | Loss of laptop / data loss | 2 | 5 | 10 | Git push daily; cloud backup of `data/` and `outputs/`; second Google Drive copy of report | Lola | 🟢 |
| R12 | Academic integrity issue (plagiarism / unattributed sources) | 2 | 5 | 10 | Zotero for every source on first read; Turnitin self-check on draft before W13 submission | Lola | 🟢 |

**Review cadence:** update this register at the end of every sprint (every two weeks). Add new risks as they emerge.

---

## 3.7 Ethical Considerations

> P3 — Ethics

### 3.7.1 Dataset

- **Source:** H&M Personalized Fashion Recommendations, hosted on Kaggle as a public competition dataset.
- **Licence:** Kaggle competition rules grant academic and research use. The competition has ended (final scoreboard May 2022), so the data is freely usable for non-commercial academic work.
- **Anonymisation:** customer IDs are hashed in the dataset as released. No personally identifying information (names, addresses, payment details) is present. The dataset is therefore considered low-risk under GDPR and Uzbekistan Personal Data Law No. ZRU-547.
- **Attribution:** the dataset will be cited as H&M Group (2022) in all reports and the demo's "About" page.

### 3.7.2 Test Users (Streamlit Demo Feedback)

- **Informed consent:** a one-page consent form (English and Uzbek) will be presented before any feedback is recorded. Participation is voluntary and can be withdrawn at any time.
- **Anonymity:** no participant names or contact details are stored alongside responses. Each session is identified only by a randomly generated session ID held client-side.
- **Data collected:** Likert-scale ratings of recommendation relevance and diversity; optional free-text comments. No demographic data beyond a self-reported age band.
- **Storage:** responses written to a flat CSV in `outputs/user_feedback/` and deleted after the project's grade is finalised.
- **Right of access:** participants can request their session's data be deleted by contacting Lola via the email shown on the consent form.

### 3.7.3 Bias

The H&M dataset reflects the purchasing patterns of a single global retailer's customer base; it is geographically and demographically biased toward H&M's typical customer (predominantly European, female-skewed, age 18–45). Conclusions drawn from this dataset cannot be assumed to generalise to all e-commerce contexts, and particularly not to the demographic profile of Uzbek marketplace users. This limitation is acknowledged in the Discussion chapter and proposed as a future research direction.

### 3.7.4 Approval

Signed PDP University ethics form will be submitted before W5 and stored in `docs/ethics_approval.pdf` once signed.

---

## 3.8 Project Tracking and Documentation

> M2 audit trail

**Weekly rhythm:**

- 2 deep-work sessions per week, ≥3 hours each, in calendar
- 1 supervisor check-in every 2 weeks; agenda sent 24 h ahead
- 1 logbook entry every Friday: did / decided / changed / blocked / next
- 1 Kanban update on Sunday: move cards, assign next week's

**Artefacts that prove the audit trail (cited as evidence in M2 / D2):**

- `logbook.md` — dated weekly entries (gitignored — backed up to personal Drive)
- Git commit history — meaningful messages, small diffs
- GitHub Projects board — screenshots taken at end of each sprint, saved to `outputs/pm/`
- Supervisor meeting notes — `docs/supervisor_notes/YYYY-WW.md`
- Sprint retrospectives — appended to logbook at end of each sprint

---

## 3.9 Implementation of the Plan (P4 — populated as the project runs)

> P4 — *populated weekly from the logbook. Do not write this section at the end — that defeats the purpose.*

This section is updated each sprint with one or two paragraphs covering what was delivered, what was deferred, what was learned. Each entry should reference a specific commit, notebook or document by name to make the evidence concrete.

### Sprint 1 (W1–2) — Research & Proposal

[After Sprint 1: what was delivered, e.g. proposal first draft, dataset chosen, repo set up. Reference: `docs/proposal.md`, commit history.]

### Sprint 2 (W3–4) — Literature Review

[…]

### Sprint 3 (W5–6) — Plan & EDA

[…]

### Sprint 4 (W7–8) — Baseline Models

[…]

### Sprint 5 (W9–10) — Advanced Models

[…]

### Sprint 6 (W11–12) — Evaluation & Demo

[…]

### Sprint 7 (W13–14) — Reporting & Defence

[…]

---

## 3.10 Critical Assessment of Project Management

> **D2 — written after the project finishes, drawn from `logbook.md` evidence**

> Distinction-level evidence requires honest, evidence-based critical assessment — not a summary of what went well. Reference specific logbook entries.

This section will, on completion, cover:

- **What worked:** which planning decisions paid off (e.g. early dataset sampling, sprint discipline, choice of Streamlit over Flask).
- **What did not work:** which estimates were wrong, which risks materialised that were not in the register, which dependencies were under-specified.
- **What was learned:** concrete lessons applied during the project (mid-project plan revisions counted as evidence, not failures).
- **What would be done differently next time:** three or four specific changes with rationale.

[Lola — fill this in during Week 14 from logbook entries. Avoid generic phrases like "I learned time management"; cite specific incidents.]

---

## Self-Check Before Submission

- [ ] WBS covers all 9 work packages with sub-tasks
- [ ] Gantt chart figure exists at `outputs/figures/gantt.png`
- [ ] Risk register has ≥8 risks with L × I scores and mitigations
- [ ] Ethics section addresses dataset licence + user feedback consent + bias
- [ ] Resource plan covers human, digital, technical, data, financial
- [ ] §3.9 has at least one paragraph per sprint completed
- [ ] §3.10 critical assessment is written from logbook entries, not invented
- [ ] All cited frameworks (Saunders et al., Burke, He et al.) appear in the References list
