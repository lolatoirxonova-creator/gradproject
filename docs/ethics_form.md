# Research Ethics Approval Form

**PDP Private University · BIT Department · BTEC Level 6 Unit 2 — Independent Project**

This form must be signed and approved by the supervisor **before** any primary data collection (test-user feedback through the Streamlit demo) begins. Place the signed copy in `docs/ethics_approval.pdf` and reference it in the Final Report.

---

## 1. Project identifiers

| Field | Detail |
|---|---|
| Project title | A Hybrid Product Recommendation System for Online Marketplaces Based on Customer Preferences |
| Student name | Lola Toirxonova |
| Student ID | 220062 |
| Programme / Group | BIT — [group] |
| Supervisor | Abdulaziz Gulomov |
| Submission date | 1 June 2026 |
| Date this form submitted | [day month 2026] |

## 2. Summary of the research

This project builds and evaluates four product recommendation algorithms (content-based filtering, ALS collaborative filtering, weighted hybrid, and Neural Collaborative Filtering) using the publicly available H&M Personalized Fashion Recommendations dataset (Kaggle, 2022). A Streamlit demo will be deployed and optional feedback collected from approximately 20 test users on the perceived relevance and diversity of the recommendations.

## 3. Data sources

### 3.1 Secondary data — H&M Kaggle dataset

| Aspect | Detail |
|---|---|
| Source | Kaggle competition "H&M Personalized Fashion Recommendations" (closed May 2022) |
| Licence | Kaggle competition rules grant academic and research use; no commercial use |
| URL | https://www.kaggle.com/competitions/h-and-m-personalized-fashion-recommendations |
| Personally identifying information | None. Customer IDs are pre-hashed by H&M. No names, addresses, contact details or payment information are present. |
| Sensitive attributes | The `age` column in `customers.csv` is self-reported and aggregated; no individual is identifiable. |
| Storage | Local copy in `data/` directory — gitignored. Not redistributed. |
| Retention | Deleted at the conclusion of the academic year (after the grade is finalised). |

### 3.2 Primary data — test-user feedback (optional)

Collected only if test-user feedback is included as a project deliverable. Collected through the Streamlit demo's optional feedback form.

| Aspect | Detail |
|---|---|
| Participants | Approximately 20 voluntary test users (classmates, peers, social network) |
| Information collected | (a) Likert ratings (1–5) of recommendation relevance, diversity and "pleasant surprise"; (b) optional free-text feedback; (c) the algorithm selected and customer-ID seed used during the session. |
| Personally identifying information | **None.** No names, emails, phone numbers, demographic details (other than the self-reported age band of the test user, kept optional). |
| Storage | Single JSONL file in `outputs/user_feedback/feedback.jsonl` — gitignored. |
| Retention | Deleted at the conclusion of the academic year. |
| Consent | Participants see a one-page consent statement (English and Uzbek) before they can submit feedback. Participation is voluntary, anonymous, and may be withdrawn before submission. |

## 4. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Re-identification of H&M customers from hashed IDs | Customer IDs are not displayed in any published output. Recommendations are illustrated only with product names and types, never with customer-level details. |
| Sensitive purchase content displayed in the demo | The H&M catalogue contains everyday fashion items; nothing sensitive. The "About" panel notes the public, academic nature of the data. |
| Test user gives personally identifying content in free-text feedback | Free-text box is labelled "do not include personal details". Submitted entries are reviewed and any inadvertent PII is redacted before inclusion in the report. |
| Bias in recommendations affecting test users' perceptions | The Findings chapter explicitly discusses dataset bias (geography, gender skew) and the limits of generalisation. Participants are debriefed via the "About" panel. |
| Algorithmic harm (filter bubbles, dark patterns) | Project is academic-only; no production deployment. Findings chapter discusses ethical risks (Pariser, 2011; Ekstrand et al., 2018) as required by D3 / D4. |

## 5. Compliance with regulations

- **Uzbekistan Personal Data Law No. ZRU-547** — primary data collection is anonymous; no personal data are processed under the law's definition.
- **GDPR principles** — even though the project is not in the EU, the principles of lawfulness, purpose limitation, data minimisation, accuracy, storage limitation, integrity and accountability are followed.
- **Kaggle competition rules** — the dataset is used for academic research only; no redistribution; results published only in this project's report.
- **PDP University Code of Academic Integrity** — all sources Harvard-referenced; no fabrication; supervisor consulted at each phase.

## 6. Consent statement (to be shown in the Streamlit demo)

> **Participation in this research project is voluntary and anonymous.**
>
> You are being asked to rate the recommendations produced by an academic recommendation system built for a BTEC Level 6 Independent Project at PDP Private University. No personal information (name, email, contact details) is collected. Your responses are stored only as aggregated counts and a free-text comment, identified by a random session ID.
>
> You may withdraw at any time before submitting the form by simply closing the page. Once submitted, your response cannot be retrieved or deleted individually because it is not linked to your identity.
>
> By clicking "Submit feedback" you confirm that you understand this statement and consent to your responses being used for the academic project, reported in aggregate, and deleted after the project's grade has been finalised.
>
> For questions, contact Lola Toirxonova (lolatoirxonova-creator@users.noreply.github.com) or supervisor Abdulaziz Gulomov.

## 7. Declarations

I confirm that:

- [ ] I have read PDP University's Code of Academic Integrity and will comply with it.
- [ ] No personally identifying information will be collected without explicit informed consent.
- [ ] Anonymised primary data will be stored locally only and deleted after grade finalisation.
- [ ] The H&M dataset will be used in accordance with the Kaggle competition's academic-use licence.
- [ ] Bias and limitations of the dataset will be explicitly discussed in the Final Report.
- [ ] Any incident involving accidental PII collection will be reported to the supervisor immediately.

---

**Student signature:** ________________________   **Date:** ____________

**Supervisor signature (approval):** ________________________   **Date:** ____________
