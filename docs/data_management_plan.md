# Data Management Plan

**Project:** A Hybrid Product Recommendation System for Online Marketplaces Based on Customer Preferences
**Student:** Lola Toirxonova (220062) · **Supervisor:** Abdulaziz Gulomov

---

## 1. Data inventory

| ID | Dataset / Artefact | Origin | Identifiable? | Storage location | Backup | Retention |
|---|---|---|---|---|---|---|
| D1 | `articles.csv` (105K products) | H&M / Kaggle | No | `data/` (gitignored) | personal Google Drive | end of academic year |
| D2 | `customers.csv` (1.3M users, hashed IDs) | H&M / Kaggle | No (hashed) | `data/` (gitignored) | personal Google Drive | end of academic year |
| D3 | `transactions_train.csv` (~31M rows) | H&M / Kaggle | No (hashed) | `data/` (gitignored) | personal Google Drive | end of academic year |
| D4 | Trained model artefacts (`*.pkl`, `*.npz`, `*.pt`) | Generated | No | `models/` (gitignored) | personal Google Drive | end of academic year |
| D5 | Test-user feedback (`feedback.jsonl`) | Streamlit demo | No (anonymous) | `outputs/user_feedback/` (gitignored) | personal Google Drive | end of academic year |
| D6 | Notebook outputs (figures, metrics CSVs/JSONs) | Generated | No | `outputs/` (gitignored except `.gitkeep`) | personal Google Drive | end of academic year |
| D7 | Final report (Word + PDF) | Lola | No | personal Google Drive + USB | OneDrive + email backup | indefinitely (academic archive) |
| D8 | Project logbook (`logbook.md`) | Lola | Contains personal reflections | local repo (gitignored) | personal Google Drive | indefinitely (personal) |
| D9 | Source code (notebooks, src/, app/) | Lola | No | public GitHub repo | repo clones, supervisor's machine | indefinitely (public) |

## 2. File-naming conventions

- Source files: `snake_case.py`
- Notebooks: `NN_short_name.ipynb` where NN is the order they are run
- Outputs: `outputs/<section>/<artefact>.csv|.png|.json`
- Models: `models/<algorithm>_<piece>.pkl|.npz|.pt`
- Report drafts: `docs/report_draft_v<NN>.docx`

## 3. Version control

- Git repository on GitHub: `https://github.com/lolatoirxonova-creator/gradproject`
- Commit early, commit often — at minimum one commit per meaningful change
- Public repo, but **everything sensitive is gitignored** (data, models, outputs, feedback, logbook, BTEC guide files)
- Tag each sprint completion with a Git tag (`sprint-01`, `sprint-02`, …) so the audit trail aligns with the project plan

## 4. Backup strategy

- **Daily:** anything in `outputs/` and `docs/` gets copied to personal Google Drive via Google Drive desktop sync
- **Weekly:** full repo zip + dataset zip to OneDrive as a redundant cloud copy
- **Pre-submission week (W14):** USB stick copy of the final report, slides and code given to a trusted peer

## 5. Access control

- The dataset and models exist only on Lola's primary laptop + cloud backups; not shared with anyone other than the supervisor on request
- The Streamlit Community Cloud deployment serves a public read-only demo; no upload mechanism beyond the anonymous feedback form
- Test-user feedback file (`outputs/user_feedback/feedback.jsonl`) is reviewed weekly during data collection; any inadvertent PII is redacted

## 6. Deletion plan

After the project grade is finalised (expected July 2026):

1. Delete the local copies of `data/`, `models/`, `outputs/user_feedback/` from laptop
2. Delete Google Drive copies of the same
3. Final report, slides and source code retained indefinitely as portfolio
4. GitHub repo kept public as portfolio; if the dataset were ever accidentally committed, it would be force-removed using `git filter-repo`

## 7. Compliance restatement

This Data Management Plan complies with:

- Uzbekistan Personal Data Law No. ZRU-547 (no processing of personal data as defined by the law, given complete anonymisation)
- GDPR principles (lawfulness, purpose limitation, data minimisation, retention)
- Kaggle competition academic-use licence (no commercial use; no redistribution)
- PDP University Code of Academic Integrity
