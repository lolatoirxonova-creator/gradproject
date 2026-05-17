# Product Recommendation System for Online Marketplaces

**BTEC Level 6 — Unit 2: Independent Project (70726U)**
PDP Private University · BIT Department · Tashkent, Uzbekistan

A hybrid product recommendation system built on the H&M Personalized Fashion Recommendations dataset, deployed as a Streamlit web app.

## Algorithms Implemented

1. **Content-Based Filtering** — TF-IDF on product descriptions + cosine similarity
2. **Collaborative Filtering** — Matrix Factorisation (SVD / ALS)
3. **Hybrid Model** — weighted combination of (1) and (2)
4. **Neural Collaborative Filtering (NCF)** — deep learning baseline

## Evaluation Metrics

Precision@K, Recall@K, NDCG, RMSE — reported with k-fold cross-validation (k=5).

## Project Structure

```
gradproject/
├── data/           # H&M dataset (gitignored — download from Kaggle)
├── notebooks/      # EDA and model development notebooks
├── src/            # Reusable Python modules
├── app/            # Streamlit demo
├── models/         # Trained model artefacts (gitignored)
├── outputs/        # Figures, metrics, exports (gitignored)
└── docs/           # Report drafts, proposal, literature review
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Dataset

Download from Kaggle: https://www.kaggle.com/competitions/h-and-m-personalized-fashion-recommendations/data

Place the following three files inside `data/`:

- `articles.csv` — 105,000+ product catalogue items
- `customers.csv` — customer profiles
- `transactions_train.csv` — 31M purchase transactions

## Running the Demo

```bash
streamlit run app/main.py
```

## Author

Lola Toirxonova (ID: 220062) · BIT Department · PDP Private University
Supervisor: Abdulaziz Gulomov
Submission: 1 June 2026

Academic Year 2025–2026
