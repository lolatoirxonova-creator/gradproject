# Chapter 2 — Literature Review

**Recommendation Systems for Online Marketplaces: From Classical Collaborative Filtering to Neural Approaches**

---

> **Criteria addressed by this chapter:** M1, D1
>
> - **M1** — Justify relevance, feasibility and significance with academic/industry sources
> - **D1** — Evaluate alternative approaches with reference to wider contexts
>
> **Target length:** 2,500–3,500 words
> **Target sources:** 15–25 high-quality references (peer-reviewed journals, books, white papers, industry reports). At least 8 from the last 5 years.

---

## 2.1 Introduction to the Literature Review

[Open with 1 paragraph stating: (a) the scope of the review (what algorithm families, what evaluation methods, what ethical concerns), (b) the search strategy you used, (c) the structure of the chapter (six themes below).]

**Search strategy used (Lola — fill in honestly):**

- **Databases:** ACM Digital Library, IEEE Xplore, ScienceDirect, SpringerLink, Google Scholar
- **Search terms:** "recommendation system" OR "recommender system"; combined with "collaborative filtering", "content-based", "hybrid", "neural collaborative filtering", "matrix factorisation", "cold-start", "fashion e-commerce", "deep learning"
- **Inclusion criteria:** English-language; peer-reviewed (or top-tier conference, e.g. RecSys, KDD, WWW); 2018–2026 prioritised; foundational pre-2018 works included when seminal
- **Exclusion criteria:** non-peer-reviewed blog posts (except official company engineering blogs cited as industry evidence); duplicate publications; non-English without translation
- **Total sources reviewed:** [N] / **Total cited in this chapter:** [N]

---

## 2.2 Theoretical Framework

[1–2 paragraphs. Identify the theoretical lenses that frame your study. Suggested options for this topic:]

- **Information Filtering Theory** (Belkin and Croft, 1992) — frames recommendation as a personalised filtering problem, distinguishing pull-based search from push-based recommendation.
- **Latent Factor Models** (Koren, Bell and Volinsky, 2009) — the mathematical foundation behind matrix factorisation and modern embeddings.
- **Hybrid Recommender Taxonomy** (Burke, 2002) — a typology of seven hybrid strategies (weighted, switching, mixed, feature combination, cascade, feature augmentation, meta-level) used to position the chosen hybrid design.

[Pick 2 frameworks above (or alternatives) and justify why they fit. Cite each with Harvard.]

---

## 2.3 Thematic Review

### 2.3.1 Theme 1 — Foundational Algorithms: Content-Based and Collaborative Filtering

[3–4 paragraphs. Compare and contrast — do not summarise paper by paper.]

**Sub-points to cover:**

- The original GroupLens system (Resnick et al., 1994) and the birth of automated collaborative filtering.
- User-based vs. item-based CF: the Amazon item-to-item shift (Linden, Smith and York, 2003) and why it scaled where user-based did not.
- Content-based filtering using TF-IDF and other text features (Lops, de Gemmis and Semeraro, 2011): strengths (cold-start for new items, interpretability) and weaknesses (no serendipity, requires good metadata).
- The fundamental trade-off: CF needs interactions, CB needs features. Neither alone is sufficient — this motivates Theme 4 (hybrids).

**Critical move (for M1):** Quote at least one comparison study (e.g. Cremonesi, Koren and Turrin, 2010) showing that simple non-personalised baselines (e.g. TopPop, ItemKNN) can be surprisingly competitive against more complex methods — and discuss what this implies for algorithm selection.

### 2.3.2 Theme 2 — Matrix Factorisation and the Netflix Era

[3–4 paragraphs.]

**Sub-points:**

- Why latent factor models won the Netflix Prize: Koren, Bell and Volinsky (2009); Bell and Koren (2007).
- SVD, regularised SVD, SVD++ — what each adds.
- Implicit feedback variants: ALS (Hu, Koren and Volinsky, 2008) and BPR (Rendle et al., 2009) — relevant because the H&M dataset is purchase data, i.e. implicit feedback.
- Factorisation Machines (Rendle, 2010) as a generalisation.

**Critical move:** Discuss the shift from explicit ratings (Netflix 1–5 stars) to implicit feedback (purchases, clicks). The H&M dataset is implicit-only — discuss which algorithms are appropriate as a result and which are not.

### 2.3.3 Theme 3 — Deep Learning for Recommendation

[4–5 paragraphs — this theme is the most relevant to your D1 justification.]

**Sub-points:**

- The 2016–2017 turning point: He et al. (2017) on Neural Collaborative Filtering; Cheng et al. (2016) Wide & Deep at Google; Covington, Adams and Sargin (2016) for YouTube.
- Why NCF: replaces the dot product of MF with a learned non-linear function; can model higher-order interactions; provides a clean experimental contrast to MF on the same data.
- Sequential / session-based models: Hidasi et al. (2016); Kang and McAuley (2018) SASRec; Sun et al. (2019) BERT4Rec — note that sequential models exploit the order of interactions, which is relevant for H&M but adds significant complexity.
- The Zhang et al. (2019) survey: scope of deep-learning approaches in the field.
- **Honest caveat:** Rendle et al. (2020) "Neural Collaborative Filtering vs. Matrix Factorization Revisited" — showed that a well-tuned MF can match or beat NCF on some benchmarks. **This is critical for D1**: a Distinction-level argument must acknowledge that "deeper is not automatically better".

### 2.3.4 Theme 4 — Hybrid Systems

[3 paragraphs.]

**Sub-points:**

- Burke (2002) taxonomy of seven hybrid strategies — pick which one you use (weighted, switching, cascade…) and justify.
- Industry hybrids: Netflix's blend of dozens of algorithms (Gomez-Uribe and Hunt, 2015); Wide & Deep at Google (Cheng et al., 2016).
- Cold-start: hybrid systems can mitigate user-side cold-start by falling back to content features for new users — connect to your D1 cold-start sub-question.

### 2.3.5 Theme 5 — Evaluation Methodology

[2–3 paragraphs. This theme directly feeds D3.]

**Sub-points:**

- Offline metrics: RMSE/MAE vs. ranking metrics (Precision@K, Recall@K, NDCG, MAP). The shift from rating-prediction to top-N recommendation (Cremonesi, Koren and Turrin, 2010).
- The offline–online gap (Beel et al., 2013; Gomez-Uribe and Hunt, 2015): why A/B tests sometimes disagree with offline metrics. You must acknowledge this limitation as part of D3.
- Statistical reliability: Herlocker et al. (2004) on evaluating CF systems; the use of cross-validation, multiple seeds, and significance testing.

### 2.3.6 Theme 6 — Ethics: Bias, Filter Bubbles, Privacy

[2 paragraphs.]

**Sub-points:**

- Filter bubbles and echo chambers (Pariser, 2011).
- Algorithmic bias and fairness in recommendation (Ekstrand et al., 2018; Mehrabi et al., 2021).
- Data privacy: GDPR principles, anonymisation, Uzbekistan Personal Data Law No. ZRU-547.
- Dark patterns and "engagement-maximising" recommenders.

---

## 2.4 Industry and Practice Review

[1–2 paragraphs. Use the major industry case studies to show that hybrid + deep learning is the production-grade direction.]

- Amazon item-to-item CF (Linden, Smith and York, 2003) — still the canonical industry reference.
- Netflix recommender stack (Gomez-Uribe and Hunt, 2015) — emphasises the blend of many models.
- YouTube DNN (Covington, Adams and Sargin, 2016) — two-stage candidate generation + ranking.
- Optional: any local industry write-ups from Uzum/Olcha engineering blogs, if available (cite specifically; if none, acknowledge as a gap).

---

## 2.5 Identification of the Gap

> **D1 — Evaluate alternative approaches**

[2 paragraphs that synthesise the review into a single gap statement.]

**The gap (working draft for Lola to refine):**

> Despite a mature literature on individual recommendation algorithms and several large industrial deployments, three gaps persist for a practitioner choosing an approach for a real fashion-marketplace problem.
>
> First, comparative evaluations of classical hybrid approaches against modern Neural Collaborative Filtering on the H&M Personalized Fashion dataset specifically remain limited in peer-reviewed literature, despite the dataset's scale and industry realism.
>
> Second, recent work (Rendle et al., 2020) has called into question the assumption that deep-learning recommenders consistently outperform well-tuned matrix factorisation — meaning a controlled, transparent comparison on a single dataset with shared evaluation protocol is genuinely valuable.
>
> Third, the cold-start problem is widely acknowledged but rarely isolated in evaluation; most reported metrics aggregate over warm and cold users/items, obscuring algorithm behaviour where it matters most for new users and new catalogue items.
>
> This project addresses all three gaps by building four algorithms (content-based, CF via matrix factorisation, hybrid, NCF) on the H&M dataset under one evaluation protocol, with explicit cold-start segmentation in the reported metrics.

[Then 1 paragraph evaluating two or three alternative directions you considered and rejected — link back to proposal §7. This is the D1 evidence point.]

---

## 2.6 Conceptual Framework

[1 paragraph + a diagram. The diagram should show:]

- **Inputs:** customer profile (demographics, implicit feedback history) + item catalogue (TF-IDF features, metadata)
- **Algorithms:** Content-Based → Collaborative Filtering → Hybrid → NCF
- **Evaluation layer:** Precision@K, Recall@K, NDCG, RMSE, cold-start-segmented metrics
- **Output:** ranked Top-N recommendations + comparative analysis

Save the diagram as `outputs/figures/conceptual_framework.png` and reference it as **Figure 2.1**.

---

## 2.7 Summary of the Literature Review

[Half-page summary covering:]

- The two main algorithmic families and their complementary weaknesses.
- The state of deep learning for recommendation, including the honest caveat that it does not always win.
- The evaluation challenges that motivate this project's reliability strategy.
- The ethical concerns that the project must address.
- The specific gap this project will fill.
- The bridge to Chapter 3 (Methodology).

---

## Sources Cited in This Chapter

*(Mirror to References list in final report. Cite using Harvard. Track which of these are also in the proposal references so you can keep them in sync.)*

### Foundational and survey

- Adomavicius, G. and Tuzhilin, A. (2005)
- Aggarwal, C. C. (2016)
- Belkin, N. J. and Croft, W. B. (1992) 'Information filtering and information retrieval: two sides of the same coin?', *Communications of the ACM*, 35(12), pp. 29–38.
- Burke, R. (2002)
- Lops, P., de Gemmis, M. and Semeraro, G. (2011)
- Resnick, P. et al. (1994)
- Ricci, F., Rokach, L. and Shapira, B. (eds) (2015)
- Sarwar, B. et al. (2001)
- Su, X. and Khoshgoftaar, T. M. (2009)

### Matrix factorisation and implicit feedback

- Bell, R. M. and Koren, Y. (2007)
- Hu, Y., Koren, Y. and Volinsky, C. (2008) 'Collaborative filtering for implicit feedback datasets', *Proceedings of the 2008 IEEE International Conference on Data Mining*, pp. 263–272.
- Koren, Y., Bell, R. and Volinsky, C. (2009)
- Rendle, S. (2010)
- Rendle, S. et al. (2009) 'BPR: Bayesian personalized ranking from implicit feedback', *Proceedings of the 25th Conference on Uncertainty in Artificial Intelligence*, pp. 452–461.

### Deep learning and modern approaches

- Cheng, H.-T. et al. (2016)
- He, X. et al. (2017)
- Hidasi, B. et al. (2016)
- Kang, W.-C. and McAuley, J. (2018)
- Sun, F. et al. (2019)
- Zhang, S. et al. (2019)

### Critical engagement / replicability (essential for D1)

- Anelli, V. W., Bellogín, A., Di Noia, T. and Pomo, C. (2021) 'Reenvisioning the comparison between Neural Collaborative Filtering and Matrix Factorization', *Proceedings of the 15th ACM Conference on Recommender Systems*, pp. 521–529.
- Petrov, A. and Macdonald, C. (2022) 'A systematic review and replicability study of BERT4Rec for sequential recommendation', *Proceedings of the 16th ACM Conference on Recommender Systems*, pp. 436–447.
- Rendle, S., Krichene, W., Zhang, L. and Anderson, J. (2020) 'Neural collaborative filtering vs. matrix factorization revisited', *Proceedings of the 14th ACM Conference on Recommender Systems*, pp. 240–248.

### Modern surveys (2022–2024)

- Chen, J., Dong, H., Wang, X., Feng, F., Wang, M. and He, X. (2023) 'Bias and debias in recommender system: a survey and future directions', *ACM Transactions on Information Systems*, 41(3), pp. 1–39.
- Gao, C., Zheng, Y., Li, N., Li, Y., Qin, Y., Piao, J., Quan, Y., Chang, J., Jin, D., He, X. and Li, Y. (2023) 'A survey of graph neural networks for recommender systems: challenges, methods, and directions', *ACM Transactions on Recommender Systems*, 1(1), pp. 1–51.
- Wang, Y., Ma, W., Zhang, M., Liu, Y. and Ma, S. (2023) 'A survey on the fairness of recommender systems', *ACM Transactions on Information Systems*, 41(3), pp. 1–43.
- Wu, S., Sun, F., Zhang, W., Xie, X. and Cui, B. (2022) 'Graph neural networks in recommender systems: a survey', *ACM Computing Surveys*, 55(5), pp. 1–37.
- Zhao, Y., Wang, Y., Liu, Y., Cheng, X., Aggarwal, C. and Derr, T. (2024) 'Fairness and diversity in recommender systems: a survey', *ACM Transactions on Intelligent Systems and Technology*.

### Evaluation methodology

- Beel, J. et al. (2013)
- Cremonesi, P., Koren, Y. and Turrin, R. (2010)
- Herlocker, J. L. et al. (2004)

### Industry case studies

- Covington, P., Adams, J. and Sargin, E. (2016)
- Gomez-Uribe, C. A. and Hunt, N. (2015)
- Linden, G., Smith, B. and York, J. (2003)

### Ethics

- Ekstrand, M. D. et al. (2018)
- Mehrabi, N. et al. (2021) 'A survey on bias and fairness in machine learning', *ACM Computing Surveys*, 54(6), pp. 1–35.
- Pariser, E. (2011)

---

## Writing Order Recommendation

1. **Read first** (Week 3): the three surveys — Adomavicius & Tuzhilin (2005), Zhang et al. (2019), Ricci et al. (2015) handbook. These give you the map of the territory.
2. **Read next** (Week 3): the foundational papers — Resnick (GroupLens), Sarwar (item-based CF), Linden (Amazon), Koren (MF), Burke (hybrids).
3. **Read next** (Week 3–4): the deep-learning core — He et al. (NCF), Cheng et al. (Wide & Deep), Rendle et al. (2020) (the honest caveat).
4. **Read next** (Week 4): evaluation — Cremonesi et al., Herlocker et al., Beel et al.
5. **Read last** (Week 4): ethics — Pariser, Ekstrand, Mehrabi.
6. **Write themes in this order:** 2.3.1 → 2.3.2 → 2.3.4 (hybrids) → 2.3.3 (deep) → 2.3.5 → 2.3.6 → 2.5 (gap) → 2.6 → 2.7 → 2.4 → 2.2 → 2.1.

---

## Self-Check Before Submission

- [ ] At least 25 references cited (proposal target was 15; final report target is 25+)
- [ ] At least 8 peer-reviewed journal articles from 2020 or later
- [ ] Every claim has a citation OR is presented as your interpretation
- [ ] Each theme **compares** sources — does not just list them
- [ ] D1 gap statement evaluates ≥3 alternative directions
- [ ] Rendle et al. (2020) "NCF vs MF revisited" is included and addressed — this is the strongest single signal of critical engagement
- [ ] Conceptual framework diagram is in `outputs/figures/` and referenced as Figure 2.1
- [ ] No verbatim copying — paraphrase every borrowed argument with citation
