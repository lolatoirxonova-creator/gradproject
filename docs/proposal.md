# Project Proposal

**A Hybrid Product Recommendation System for Online Marketplaces Based on Customer Preferences**

---

| Field | Detail |
|---|---|
| Student Name | Lola Toirxonova |
| Student ID | 220062 |
| Programme / Group | BIT — [group] |
| Project Format | Capstone-style |
| Supervisor | Abdulaziz Gulomov |
| Submission Date | 1 June 2026 |
| Target Grade | Distinction |
| Word Count Target | 2,500–3,500 words |

---

> **Criteria addressed by this document:** P1, P2, M1, D1
>
> - **P1** — Clear aim and objectives for a complex problem
> - **P2** — Significance of the project in its digital technologies context
> - **M1** — Justify relevance, feasibility and significance with academic/industry sources
> - **D1** — Evaluate alternative research approaches with reference to wider contexts

---

## Abstract

*(One paragraph, 200–250 words. Write LAST, after every other section is drafted.)*

[Open with the problem and its context (1–2 sentences). State the aim (1 sentence). Summarise the methodology (2 sentences: dataset, algorithms, evaluation). Mention key expected contribution (1–2 sentences). Close with the wider significance to industry / academia / the local Uzbek e-commerce context (1 sentence).]

**Keywords:** recommendation systems; collaborative filtering; content-based filtering; hybrid models; neural collaborative filtering; e-commerce personalisation

---

## 1. Background and Context

> P2 — Significance in digital technologies context

The global e-commerce sector has continued its post-pandemic expansion, with worldwide retail e-commerce sales reaching an estimated USD 6.86 trillion in 2025 — approximately one fifth of all retail spending worldwide — and forecast to approach USD 9 trillion by 2030 (Statista, 2025a). Fashion is the largest single category within this market: global fashion e-commerce revenue is forecast at approximately USD 920 billion in 2025, and the fashion segment now accounts for an estimated 31.2 per cent of all online retail (Statista, 2025b). Within this market, personalisation has shifted from competitive advantage to baseline expectation: McKinsey & Company reports that personalisation typically lifts revenue by 10–15 per cent (with sector-specific lifts in a 5–25 per cent range), and that companies excelling at personalisation generate 40 per cent more revenue from those activities than average players (McKinsey, 2021). Recommendation engines account for an estimated 35 per cent of Amazon's purchases and over 75 per cent of viewing on Netflix (Linden, Smith and York, 2003; Gomez-Uribe and Hunt, 2015). For fashion specifically, where product catalogues routinely exceed 100,000 items and customer taste is intrinsically subjective, recommendation quality is now a direct lever on conversion rate, average order value and customer lifetime value.

Recommendation systems address a problem that classical search cannot: helping users discover items they would not have known to look for. They reduce search cost on the user side and surface long-tail inventory on the business side. Foundational algorithmic families — content-based filtering, collaborative filtering and hybrid combinations — have been studied since the early 1990s (Resnick et al., 1994; Sarwar et al., 2001; Burke, 2002). The last decade has added matrix factorisation at scale (Koren, Bell and Volinsky, 2009) and deep-learning approaches, notably Neural Collaborative Filtering (He et al., 2017) and sequential transformer-based models (Sun et al., 2019; Kang and McAuley, 2018). Despite this progress, two open questions persist in practice: when does the additional complexity of a deep-learning recommender justify its compute cost, and how do these models handle the chronic cold-start problem that all real-world platforms face?

The Uzbek and Central Asian digital economy is undergoing a comparable transformation. Uzbekistan's e-commerce market grew approximately fivefold between 2018 and 2022, reaching over USD 500 million by 2023, and is estimated to lie between USD 1.2 billion and USD 2.27 billion in 2024 depending on methodology (KPMG, 2023; World Bank, 2024; Statista, 2025c). KPMG forecasts that domestic e-commerce penetration of total retail will reach 9–11 per cent by 2027, with the market reaching USD 1.8–2.2 billion. Growth has been driven by the emergence of domestic marketplaces — Uzum Market (Uzbekistan's first technology unicorn), Olcha and Texnomart — alongside regional players such as Yandex Market. Mobile-first shopping behaviour, a young population and increasing penetration of digital payments make recommendation quality a strategic concern for local platforms. Yet personalisation maturity in the region lags global leaders, and there is little peer-reviewed empirical work comparing recommendation algorithms on either local or large-scale fashion datasets with explicit attention to the cold-start problem. This project addresses that gap by building and rigorously evaluating four recommendation algorithms — content-based, collaborative filtering, hybrid and Neural Collaborative Filtering — on the H&M Personalized Fashion Recommendations dataset, producing reusable code, transparent metrics and Distinction-level evidence that can inform both academic discussion and local industry practice.

---

## 2. Problem Statement

> P1 — Complex problem

Online fashion marketplaces such as H&M, Zara, ASOS and — in the Uzbek market — Uzum Market and Olcha must recommend products to millions of customers from catalogues containing hundreds of thousands of items. Two failure modes dominate:

1. **Cold-start** — new users with no purchase history and new products with no transaction signal receive low-quality recommendations, directly hurting first-session conversion and the time-to-value for new catalogue items.
2. **Algorithm-choice opacity** — practitioners face an ever-growing menu of algorithms (content-based, collaborative filtering, matrix factorisation, hybrid ensembles, neural collaborative filtering, transformer-based sequential models), yet most published comparisons are run on heterogeneous datasets and metrics, making it difficult to know when a more complex model is actually justified for a given business context.

The **complex problem** this project addresses is therefore: *under what conditions does a hybrid recommendation model — and the modern Neural Collaborative Filtering approach — meaningfully outperform classical single-algorithm baselines on a large real-world fashion e-commerce dataset, and how do these approaches behave specifically under cold-start conditions?* This is multi-variable (model architecture, evaluation metric, user/item coldness, computational cost), uncertain (offline metrics are imperfect proxies for online utility), real-world (every e-commerce platform faces these trade-offs), and reveals a clear gap: comparative cold-start-aware evaluations of classical hybrid and NCF approaches on the H&M dataset, at the scale and depth required for evidence-based industry adoption, remain limited in the peer-reviewed literature.

---

## 3. Aim

> P1

**Aim:** *To design, build and critically evaluate a hybrid product recommendation system, combining content-based filtering, collaborative filtering and neural collaborative filtering, in order to improve recommendation accuracy and relevance for users of large online fashion marketplaces, using the H&M Personalized Fashion Recommendations dataset as a case study.*

[Refine the sentence above so it reflects the exact problem framing you chose in Section 2.]

---

## 4. Project Objectives

> P1 — SMART objectives

[3–5 SMART objectives. Each must be **S**pecific, **M**easurable, **A**chievable, **R**elevant, **T**ime-bound. Use action verbs. Numbers and dates are required.]

1. **Review** at least 25 peer-reviewed and industry sources on recommendation systems (content-based, collaborative filtering, hybrid, deep learning) by Week 4, producing a thematic literature review of 2,500–3,500 words.

2. **Acquire and pre-process** the H&M Personalized Fashion dataset (~31M transactions, 105K+ articles, customer profiles) and produce an Exploratory Data Analysis notebook by Week 7.

3. **Implement four recommendation algorithms** — Content-Based (TF-IDF + cosine), Collaborative Filtering (matrix factorisation via SVD/ALS), Hybrid (weighted ensemble), and Neural Collaborative Filtering (NCF) — in Python by Week 11.

4. **Evaluate each model** using Precision@10, Recall@10, NDCG@10 and RMSE under 5-fold cross-validation, with statistical significance testing, by Week 12.

5. **Deploy a working demonstrator** using Streamlit and collect feedback from at least 20 test users by Week 13.

6. **Produce a final report** of 8,000–10,000 words with Harvard referencing and a professional presentation of 12–15 slides by Week 14.

---

## 5. Research Questions

[Choose 2–4 focused research questions. Match them to your aim and objectives.]

- **RQ1** — To what extent does a hybrid recommendation model outperform standalone content-based and collaborative filtering baselines on the H&M dataset, as measured by Precision@K, Recall@K and NDCG?
- **RQ2** — How does Neural Collaborative Filtering compare to classical matrix factorisation in terms of accuracy and computational cost?
- **RQ3** — How does the cold-start problem affect each algorithm's performance, and which approach mitigates it most effectively?
- **RQ4** — *(optional)* — How do test users perceive the relevance, diversity and explainability of recommendations from each model in a Streamlit demo?

---

## 6. Literature Review (Summary)

> M1 — Justify relevance, feasibility, significance with sources

[2–3 pages here in the proposal; full review goes into Chapter 2 of the final report. Organise by **themes**, not by author. Compare and critique — do not summarise paper by paper. Cover the five themes below.]

### 6.1 Foundational Techniques

[Content-based filtering; user-based and item-based collaborative filtering; matrix factorisation (SVD, ALS). Cite seminal works: Resnick et al. (1994), Sarwar et al. (2001), Koren et al. (2009).]

### 6.2 Modern Approaches

[Hybrid systems (Burke, 2002); deep learning for recommendation — Neural Collaborative Filtering (He et al., 2017); autoencoder-based recommenders; sequential / transformer-based recommendation.]

### 6.3 Industry Case Studies

[Amazon item-to-item (Linden et al., 2003); Netflix Prize and post-Prize lessons (Bell & Koren, 2007); YouTube deep network (Covington et al., 2016); Spotify; Alibaba/Taobao. Use these to make the case for hybrid + deep learning being industry-standard.]

### 6.4 Evaluation Methodology

[Offline metrics: Precision@K, Recall@K, NDCG, MAP, RMSE, MAE. Cross-validation. The offline–online evaluation gap (Beel et al., 2013). Why offline-only evaluation has limits.]

### 6.5 Ethical Concerns

[Filter bubbles (Pariser, 2011); algorithmic bias and fairness in recommendation (Ekstrand et al., 2018); data privacy and GDPR / Uzbekistan Personal Data Law No. ZRU-547; dark patterns.]

### 6.6 The Gap

[Synthesise. Make the gap explicit. Example framing: *"While hybrid systems are well-established in literature and industry, comparative evaluations of classical hybrid approaches against modern Neural Collaborative Filtering on large fashion e-commerce datasets remain limited, particularly with attention to cold-start performance and computational trade-offs."*]

---

## 7. Justifying the Research Direction

> **D1 — Evaluate alternative approaches**

[This section is what separates Merit from Distinction at LO1. Compare at least **three** alternative directions you considered and explain why you chose the hybrid + NCF route.]

### 7.1 Alternative 1 — Pure Collaborative Filtering Only

[Strengths: simple, strong baseline, well-understood. Weaknesses: cold-start, sparsity, no use of rich product metadata. Cite e.g. Sarwar et al. (2001). Why rejected as the sole approach.]

### 7.2 Alternative 2 — Pure Content-Based Filtering

[Strengths: handles cold-start for new items, interpretable. Weaknesses: limited serendipity, requires good textual metadata, struggles with user-side cold-start. Why rejected as the sole approach.]

### 7.3 Alternative 3 — End-to-End Deep Learning (e.g. Transformer-based Sequential Recommender)

[Strengths: state of the art on some benchmarks. Weaknesses: heavy compute requirement, less interpretable, harder to deploy in a one-semester capstone with no GPU cluster. Why rejected.]

### 7.4 Chosen Direction — Hybrid + NCF

[Combines complementary strengths of CF and content-based; NCF adds a modern deep-learning baseline for a meaningful comparison; feasible on a single laptop + Google Colab GPU; supports all four BTEC distinction criteria. Cite Burke (2002), He et al. (2017).]

---

## 8. Methodology Outline

> P3 (preview — full plan in Phase 3 / Chapter 3)

### 8.1 Research Philosophy and Approach

[Pragmatist philosophy; design-science / capstone approach; quantitative empirical evaluation. Reference Saunders, Lewis & Thornhill (2023) "research onion".]

### 8.2 Dataset

H&M Personalized Fashion Recommendations (Kaggle):

- `articles.csv` — 105K+ product catalogue items with descriptions and metadata
- `customers.csv` — customer demographic profiles
- `transactions_train.csv` — ~31M purchase transactions

Licence: research/academic use under Kaggle competition terms.

### 8.3 Tech Stack

| Layer | Tool |
|---|---|
| Language | Python 3.11+ |
| Data | pandas, NumPy |
| Classical ML | scikit-learn, Surprise, implicit |
| Deep Learning | PyTorch (Neural Collaborative Filtering) |
| NLP | scikit-learn TF-IDF, NLTK |
| Demo | Streamlit |
| Notebooks | Jupyter, Google Colab (GPU) |
| Version Control | Git + GitHub |
| Visualisation | matplotlib, seaborn, Plotly |
| Project Management | GitHub Projects (Kanban) + GanttProject |

### 8.4 Evaluation Plan

> Supports D3

- **Metrics:** Precision@10, Recall@10, NDCG@10, RMSE, MAE
- **Validation:** 5-fold cross-validation; train/validation/test split with held-out final test set
- **Reliability:** fixed random seeds; 3 runs per experiment; report mean ± standard deviation
- **Statistical testing:** paired t-test (or Wilcoxon signed-rank) between model pairs
- **Cold-start analysis:** isolate cold users and cold items, report metrics separately
- **Qualitative:** thematic analysis of test-user feedback on relevance, diversity, surprise

### 8.5 Project Management Methodology

Agile / Scrum with 2-week sprints. Kanban board on GitHub Projects. Weekly supervisor meetings. Git commit history serves as part of the M2 audit trail.

---

## 9. Ethics and Feasibility

### 9.1 Ethics

- **Dataset licence** — H&M Kaggle dataset is licensed for academic/research use; cited and credited.
- **Data privacy** — dataset is already anonymised (no PII); customer IDs are hashed.
- **Primary data (optional)** — if test-user feedback is collected via Streamlit demo, informed consent will be obtained; survey responses will be anonymous; no personal data stored beyond aggregated feedback.
- **Compliance** — GDPR principles and Uzbekistan Personal Data Law No. ZRU-547 followed.
- **Bias** — fashion dataset is geographically and demographically biased toward H&M's customer base; this limitation will be acknowledged and discussed in the Discussion chapter.
- **Ethics form** — signed PDP University ethics approval form will be submitted before any primary data collection (Week 5 target).

### 9.2 Feasibility

| Dimension | Assessment |
|---|---|
| Skills | Python, pandas, scikit-learn (held); PyTorch + Streamlit (basic, will deepen during project) |
| Time | One semester (14 weeks) — sufficient if scope is held to the four algorithms |
| Compute | Local laptop (16GB RAM) for CF/content-based; Google Colab free GPU for NCF training |
| Data | Already publicly available; ~25GB total, requires a sampling strategy for prototyping |
| Cost | Zero — all tools, datasets and platforms used are free for students |

---

## 10. Initial Timeline (14 Weeks)

| Week | Phase | Deliverable |
|---|---|---|
| 1–2 | Proposal & scoping | This proposal, supervisor approval |
| 3–4 | Literature review | 25+ sources, annotated bibliography, full review draft |
| 5 | Project plan & ethics | Gantt, WBS, risk register (≥8 risks), signed ethics form |
| 6–7 | Data acquisition & EDA | H&M data loaded, cleaned, EDA notebook complete |
| 8–9 | Baseline models | Content-based + Collaborative Filtering working with first metrics |
| 10–11 | Hybrid + NCF | Hybrid model + NCF built, cross-validation run, metrics table |
| 12 | Demo & user testing | Streamlit demo deployed, 20+ test users give feedback |
| 13 | Final report draft | Full draft submitted to supervisor for review |
| 14 | Revision & defence | Final report, slides, reflective evaluation, oral defence |

(Full Gantt with dependencies and contingency buffers will be produced in Week 5 — see Project Plan.)

---

## 11. Expected Contribution

[1–2 paragraphs. Cover:]

- **Academic:** a controlled comparison of four recommendation paradigms (content-based, classical CF, hybrid, NCF) on a large real-world fashion dataset, with explicit cold-start analysis.
- **Practical:** a working, deployable Streamlit demo and reusable Python codebase that local Uzbek marketplaces (Uzum, Olcha) could adapt as a baseline implementation.
- **Personal:** demonstrable Distinction-level evidence across all four BTEC learning outcomes; portfolio piece for industry roles in data science / ML engineering.

---

## 12. References

*(Harvard author–date format. Final report target: 25+ sources, of which at least 8 are peer-reviewed journal articles from the last 5 years. Verify every URL and DOI before final submission.)*

### Foundational & survey

- Adomavicius, G. and Tuzhilin, A. (2005) 'Toward the next generation of recommender systems: a survey of the state-of-the-art and possible extensions', *IEEE Transactions on Knowledge and Data Engineering*, 17(6), pp. 734–749.
- Aggarwal, C. C. (2016) *Recommender systems: the textbook*. Cham: Springer.
- Burke, R. (2002) 'Hybrid recommender systems: survey and experiments', *User Modeling and User-Adapted Interaction*, 12(4), pp. 331–370.
- Lops, P., de Gemmis, M. and Semeraro, G. (2011) 'Content-based recommender systems: state of the art and trends', in Ricci, F. et al. (eds) *Recommender systems handbook*. Boston: Springer, pp. 73–105.
- Resnick, P. et al. (1994) 'GroupLens: an open architecture for collaborative filtering of netnews', *Proceedings of the 1994 ACM Conference on Computer Supported Cooperative Work*, pp. 175–186.
- Ricci, F., Rokach, L. and Shapira, B. (eds) (2015) *Recommender systems handbook*. 2nd edn. New York: Springer.
- Sarwar, B. et al. (2001) 'Item-based collaborative filtering recommendation algorithms', *Proceedings of the 10th International Conference on World Wide Web*, pp. 285–295.
- Su, X. and Khoshgoftaar, T. M. (2009) 'A survey of collaborative filtering techniques', *Advances in Artificial Intelligence*, 2009, pp. 1–19.

### Matrix factorisation & classical models

- Bell, R. M. and Koren, Y. (2007) 'Lessons from the Netflix prize challenge', *ACM SIGKDD Explorations Newsletter*, 9(2), pp. 75–79.
- Koren, Y., Bell, R. and Volinsky, C. (2009) 'Matrix factorization techniques for recommender systems', *Computer*, 42(8), pp. 30–37.
- Rendle, S. (2010) 'Factorization machines', *Proceedings of the 2010 IEEE International Conference on Data Mining*, pp. 995–1000.

### Deep learning & modern approaches

- Cheng, H.-T. et al. (2016) 'Wide & deep learning for recommender systems', *Proceedings of the 1st Workshop on Deep Learning for Recommender Systems*, pp. 7–10.
- He, X. et al. (2017) 'Neural collaborative filtering', *Proceedings of the 26th International Conference on World Wide Web*, pp. 173–182.
- Hidasi, B. et al. (2016) 'Session-based recommendations with recurrent neural networks', *Proceedings of the 4th International Conference on Learning Representations (ICLR)*.
- Kang, W.-C. and McAuley, J. (2018) 'Self-attentive sequential recommendation', *Proceedings of the 2018 IEEE International Conference on Data Mining*, pp. 197–206.
- Sun, F. et al. (2019) 'BERT4Rec: sequential recommendation with bidirectional encoder representations from transformer', *Proceedings of the 28th ACM International Conference on Information and Knowledge Management*, pp. 1441–1450.
- Zhang, S. et al. (2019) 'Deep learning based recommender system: a survey and new perspectives', *ACM Computing Surveys*, 52(1), pp. 1–38.

### Industry case studies

- Covington, P., Adams, J. and Sargin, E. (2016) 'Deep neural networks for YouTube recommendations', *Proceedings of the 10th ACM Conference on Recommender Systems*, pp. 191–198.
- Gomez-Uribe, C. A. and Hunt, N. (2015) 'The Netflix recommender system: algorithms, business value, and innovation', *ACM Transactions on Management Information Systems*, 6(4), pp. 1–19.
- Linden, G., Smith, B. and York, J. (2003) 'Amazon.com recommendations: item-to-item collaborative filtering', *IEEE Internet Computing*, 7(1), pp. 76–80.

### Evaluation methodology

- Beel, J. et al. (2013) 'A comparative analysis of offline and online evaluations and discussion of research paper recommender system evaluation', *Proceedings of the International Workshop on Reproducibility and Replication in Recommender Systems Evaluation*, pp. 7–14.
- Cremonesi, P., Koren, Y. and Turrin, R. (2010) 'Performance of recommender algorithms on top-N recommendation tasks', *Proceedings of the 4th ACM Conference on Recommender Systems*, pp. 39–46.
- Herlocker, J. L. et al. (2004) 'Evaluating collaborative filtering recommender systems', *ACM Transactions on Information Systems*, 22(1), pp. 5–53.

### Ethics, bias, fairness

- Ekstrand, M. D. et al. (2018) 'Exploring author gender in book rating and recommendation', *Proceedings of the 12th ACM Conference on Recommender Systems*, pp. 242–250.
- Pariser, E. (2011) *The filter bubble: what the internet is hiding from you*. New York: Penguin Press.

### Recent surveys and replicability studies (2020–2024) — verified

- Anelli, V. W., Bellogín, A., Di Noia, T. and Pomo, C. (2021) 'Reenvisioning the comparison between Neural Collaborative Filtering and Matrix Factorization', *Proceedings of the 15th ACM Conference on Recommender Systems*, pp. 521–529. arXiv: 2107.13472.
- Chen, J., Dong, H., Wang, X., Feng, F., Wang, M. and He, X. (2023) 'Bias and debias in recommender system: a survey and future directions', *ACM Transactions on Information Systems*, 41(3), pp. 1–39. DOI: 10.1145/3564284.
- Gao, C., Zheng, Y., Li, N., Li, Y., Qin, Y., Piao, J., Quan, Y., Chang, J., Jin, D., He, X. and Li, Y. (2023) 'A survey of graph neural networks for recommender systems: challenges, methods, and directions', *ACM Transactions on Recommender Systems*, 1(1), pp. 1–51. arXiv: 2109.12843.
- Petrov, A. and Macdonald, C. (2022) 'A systematic review and replicability study of BERT4Rec for sequential recommendation', *Proceedings of the 16th ACM Conference on Recommender Systems*, pp. 436–447. arXiv: 2207.07483.
- Rendle, S., Krichene, W., Zhang, L. and Anderson, J. (2020) 'Neural collaborative filtering vs. matrix factorization revisited', *Proceedings of the 14th ACM Conference on Recommender Systems*, pp. 240–248. arXiv: 2005.09683.
- Wang, Y., Ma, W., Zhang, M., Liu, Y. and Ma, S. (2023) 'A survey on the fairness of recommender systems', *ACM Transactions on Information Systems*, 41(3), pp. 1–43. DOI: 10.1145/3547333.
- Wu, S., Sun, F., Zhang, W., Xie, X. and Cui, B. (2022) 'Graph neural networks in recommender systems: a survey', *ACM Computing Surveys*, 55(5), pp. 1–37. DOI: 10.1145/3535101.
- Zhao, Y., Wang, Y., Liu, Y., Cheng, X., Aggarwal, C. and Derr, T. (2024) 'Fairness and diversity in recommender systems: a survey', *ACM Transactions on Intelligent Systems and Technology*. arXiv: 2307.04644.

### Research methods

- Saunders, M., Lewis, P. and Thornhill, A. (2023) *Research methods for business students*. 9th edn. Harlow: Pearson.

### Industry / market reports

- KPMG (2023) *E-commerce in Uzbekistan*. KPMG Caucasus and Central Asia, August 2023. Available at: https://assets.kpmg.com/content/dam/kpmg/uz/pdf/2023/E-commerce%20in%20Uzbekistan_to-upload.pdf (Accessed: [date]).
- McKinsey & Company (2021) *The value of getting personalization right — or wrong — is multiplying*. Available at: https://www.mckinsey.com/capabilities/growth-marketing-and-sales/our-insights/the-value-of-getting-personalization-right-or-wrong-is-multiplying (Accessed: [date]).
- Statista (2025a) *Global retail e-commerce sales 2022–2030*. Available at: https://www.statista.com/statistics/379046/worldwide-retail-e-commerce-sales/ (Accessed: [date]).
- Statista (2025b) *Fashion e-commerce worldwide — statistics and facts*. Available at: https://www.statista.com/topics/9288/fashion-e-commerce-worldwide/ (Accessed: [date]).
- Statista (2025c) *eCommerce — Uzbekistan*. Statista Market Forecast. Available at: https://www.statista.com/outlook/emo/ecommerce/uzbekistan (Accessed: [date]).
- World Bank (2024) *From local bazaars to global markets: unlocking e-commerce through regional integration in Central Asia*. World Bank Blogs. Available at: https://blogs.worldbank.org/en/psd/unlocking-e-commerce-through-regional-integration-in-central-asi (Accessed: [date]).

### Dataset

- H&M Group (2022) *H&M Personalized Fashion Recommendations*, Kaggle competition. Available at: https://www.kaggle.com/competitions/h-and-m-personalized-fashion-recommendations [accessed [date]].

---

**Reference-collection tips for Lola:**

- Use **Zotero** (free, integrates with MS Word) with the citation style *"Cite Them Right - Harvard"*.
- For each source, save the PDF + Zotero record on the day you read it — do not leave bibliography work to Week 13.
- Target the **last 5 years** for at least 8 of your 25+ sources. Search ACM Digital Library, IEEE Xplore, ScienceDirect and Google Scholar.
- For Uzbek/Central Asia statistics, prefer **Statistics Agency of the Republic of Uzbekistan**, **Ministry of Digital Technologies**, **Central Bank of Uzbekistan**, **World Bank** and **Asian Development Bank** reports over news articles.
- Replace every `[verify]` tag in this document with a specific year/figure + matching citation before submission.

---

## Self-Check Before Submission

Before submitting this proposal to your supervisor, verify:

- [ ] Aim is one clear sentence, starting with an action verb
- [ ] Objectives are SMART (numbered, dated, measurable)
- [ ] Problem is explicitly framed as **complex** (multi-variable, real-world, gap)
- [ ] At least 15 Harvard-formatted references
- [ ] D1 section evaluates **at least 3** alternative approaches and justifies the chosen one
- [ ] Ethics section addresses dataset licence + data privacy + bias
- [ ] Feasibility section honestly addresses skills, time, compute, cost
- [ ] Initial timeline aligns with the supervisor's expected calendar
- [ ] Word count between 2,500 and 3,500 words
- [ ] Spell-checked and grammar-checked (Grammarly or equivalent)
