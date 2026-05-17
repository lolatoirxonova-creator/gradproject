# Chapter 7 — Reflective Evaluation of Personal and Professional Development

**Lola Toirxonova · ID 220062 · BTEC L6 Unit 2 — Independent Project**

> **Criteria addressed:** P7, M5, D4
>
> - **P7** — Reflective review using a recognised model
> - **M5** — Communicate outcomes to a professional audience with citations
> - **D4** — Critically review personal/professional development; propose future strategies
>
> **Target length:** 1,500–2,000 words (Reflective Evaluation deliverable) or 800–1,200 words (Chapter 7 of the Final Report — choose one and reuse)

---

## 7.1 Choice of Reflective Model

**Gibbs' Reflective Cycle** (Gibbs, 1988) is chosen as the primary framework, with **Schön's reflection-in-action / reflection-on-action** distinction (Schön, 1983) applied where appropriate to in-sprint decisions.

**Justification.** Gibbs' six-stage cycle (Description → Feelings → Evaluation → Analysis → Conclusion → Action Plan) is well-suited to a year-long project punctuated by distinct events (sprint endings, model failures, supervisor disagreements). Kolb's experiential learning cycle was considered but rejected because it is better suited to short skill-acquisition cycles than to a single multi-phase project. Schön's distinction adds value when reflecting on real-time technical decisions — for example, mid-sprint choices about hyperparameter tuning where the reflection happened *in the moment*.

> Reference: Gibbs, G. (1988) *Learning by doing: a guide to teaching and learning methods*. Oxford: Further Education Unit; Schön, D. A. (1983) *The reflective practitioner*. New York: Basic Books.

---

## 7.2 Reflection Using Gibbs' Cycle

> Write one **substantive reflection** per significant event (3–4 events total). Each follows the six-stage cycle. **Cite specific dated logbook entries — generic reflection fails D4.**

### Reflection 1 — [Event name, e.g. "First model under-performed expectations"]

**Date / sprint:** [from logbook, e.g. "Sprint 4, Week 8, logbook entry 2026-XX-XX"]

#### Description — What happened?

[2–3 sentences. Concrete, factual: *"On 2026-XX-XX, I ran the first ALS model with default hyperparameters. Precision@10 was 0.014 — far below the 0.05 I had estimated from the literature."*]

#### Feelings — What were you thinking and feeling?

[2–3 sentences. Honest, but professional: *"Initially I was discouraged; my first thought was that the dataset was too sparse. After 24 hours I reconsidered: the literature numbers were on smaller, denser datasets, so my prior was wrong."*]

#### Evaluation — What was good and bad?

[2–3 sentences each side. **Good:** the early failure was caught in week 8, leaving time to adapt. **Bad:** I had not built a sanity-check baseline (popularity) before running ALS, so I had nothing to compare against.]

#### Analysis — Why did it happen this way?

[3–4 sentences. Reference the literature (Cremonesi, Koren and Turrin, 2010 — non-personalised baselines can be surprisingly competitive). Reference the project plan: I had skipped a popularity baseline because it was not explicitly required.]

#### Conclusion — What did you learn?

[2–3 sentences. **Specific** lesson, not generic. *"I learned to always implement the simplest possible baseline before any complex model. The popularity baseline I added afterwards revealed that ALS only marginally beat it on Precision@10, which sharpened the entire Discussion chapter."*]

#### Action Plan — What will you do differently?

[2–3 sentences. Concrete future commitment: *"In future data science projects I will commit, on day one, to implementing the random + popularity baselines before any model. I will add this as a 'definition of done' rule for sprint planning."*]

---

### Reflection 2 — [Event name, e.g. "NCF training on Colab GPU"]

[Six stages as above. Suggested topic: the first time you ran a deep-learning model. What surprised you about training time, memory, the gap between literature numbers and your own.]

---

### Reflection 3 — [Event name, e.g. "Supervisor feedback on literature review draft"]

[Six stages. Suggested topic: a moment where supervisor feedback forced a substantive revision. How did you feel? How did you act on it? Reference Schön's reflection-in-action if you adjusted mid-conversation.]

---

### Reflection 4 — [Event name, e.g. "Streamlit demo + test-user feedback"]

[Six stages. Suggested topic: the gap between offline metrics and what real users thought of the recommendations. This is the perfect place to discuss the validity D3 concept in personal-development terms — *I learned the offline–online gap is not just a theoretical concern.*]

---

## 7.3 SWOT Analysis of Personal Development

> **D4 evidence.** Fill in at project end, comparing skills at start of project to skills at end.

| | At project start (W1) | At project end (W14) |
|---|---|---|
| **Strengths** | [e.g. Python basics, pandas, basic Git] | [e.g. PyTorch, sparse matrix operations, Streamlit, Harvard referencing, MS Word long-document mastery] |
| **Weaknesses** | [e.g. unfamiliar with deep learning, no published writing experience, weak project planning] | [e.g. still need exposure to production deployment, distributed training, A/B testing methodology] |
| **Opportunities** | [e.g. growth of data-science roles in Uzbek tech sector; visibility from public GitHub portfolio] | [e.g. specific roles you could now apply for; certifications to deepen specialisation] |
| **Threats** | [e.g. self-taught gaps in fundamentals; lack of industry network] | [e.g. competition from Master's graduates; rapid framework churn — must commit to continuous learning] |

---

## 7.4 Skills Matrix — Self-Assessment

> Score each skill 1–5 (1 = no experience, 5 = could teach others) before and after the project. Honest scoring carries more weight than high scoring.

| Skill | Before (W1) | After (W14) | Δ |
|---|---|---|---|
| Python programming | | | |
| Pandas / NumPy data manipulation | | | |
| Sparse matrix operations (scipy.sparse) | | | |
| TF-IDF and text vectorisation | | | |
| Matrix factorisation (theory) | | | |
| PyTorch (model definition + training) | | | |
| GPU / Colab workflow | | | |
| Statistical testing (Wilcoxon, t-test) | | | |
| Cross-validation methodology | | | |
| Streamlit deployment | | | |
| Git + GitHub collaboration | | | |
| Project planning (WBS, Gantt, risk register) | | | |
| Agile / Scrum self-management | | | |
| Harvard academic referencing | | | |
| Long-form academic writing (8K+ words) | | | |
| Critical engagement with academic literature | | | |
| Reflective practice (Gibbs cycle) | | | |
| Oral presentation to a professional audience | | | |

---

## 7.5 360° Feedback

> **D4 evidence.** Collect short written feedback (2–3 sentences each) from your supervisor, two peers and one test user. Anonymise and quote 2–3 lines verbatim below. Acknowledge what you took on board and what you respectfully disagreed with.

**Supervisor (Abdulaziz Gulomov):** [quote 2–3 sentences from a written email or meeting note]

**Peer 1:** [quote]

**Peer 2:** [quote]

**Test user:** [quote from `outputs/user_feedback/feedback.jsonl` — pick a representative free-text comment]

[Closing paragraph: which pieces of feedback you acted on, which you weighed and chose not to act on, and why.]

---

## 7.6 Transferable Skills Gained

[1 paragraph each on the three most transferable skills:]

1. **Rigorous empirical evaluation.** Cross-validation + statistical testing + honest reporting of where the model loses, not just where it wins. Transferable to any quantitative role.

2. **Sprint discipline with documented audit trail.** Weekly logbook + Git + sprint retrospective. Transferable to any team-based engineering role.

3. **Reading academic literature critically, not just citing it.** Including the Rendle et al. (2020) caveat for NCF was a moment of intellectual courage I will carry forward.

---

## 7.7 Personal Development Plan (PDP)

> **D4 evidence — concrete future strategies.** Three to five specific actions with dates.

| # | Action | Why | By when | Evidence of completion |
|---|---|---|---|---|
| 1 | Complete the AWS Machine Learning Specialty certification | Solidify production-ML skills the project did not exercise | end of 2026 | certificate URL |
| 2 | Contribute one open-source pull request to a recommendation library (Surprise, LightFM or `implicit`) | Move from consumer to contributor; portfolio piece | within 6 months of graduation | merged PR link |
| 3 | Write a public blog post on "NCF vs MF revisited — replicating Rendle et al. (2020) on H&M data" | Long-tail outcome of this project; builds portfolio | within 3 months of graduation | published URL |
| 4 | Apply to data-science / ML-engineering roles at Uzum Market, Yandex Uzbekistan, EPAM, or similar | Direct industry entry | within 1 month of graduation | offer or written rejection log |
| 5 | Apply for a Master's programme in Data Science (consider TU Delft, KU Leuven, or domestic options) | Optional further study | application deadlines vary | submitted applications |

---

## Self-Check Before Submission

- [ ] At least one Gibbs cycle is fully written, with a quoted dated logbook entry
- [ ] SWOT comparing start vs end is concrete, not generic
- [ ] Skills matrix is scored honestly (some 2→4 jumps are believable; all 1→5 jumps are not)
- [ ] 360° feedback section quotes at least 3 sources verbatim
- [ ] PDP has dated, evidenced future actions
- [ ] Gibbs and Schön references appear in the bibliography
- [ ] Word count: 1,500–2,000 if standalone; 800–1,200 if integrated as Chapter 7 of the report
