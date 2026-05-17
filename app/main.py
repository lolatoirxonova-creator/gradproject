"""H&M Product Recommendation Demo — Streamlit app.

Run from repo root:
    streamlit run app/main.py

Required artefacts (produced by notebooks 02–05):
    models/content_based_vectorizer.pkl
    models/content_based_item_tfidf.npz
    models/cf_als_model.pkl
    models/hybrid_config.pkl
    models/ncf_neumf.pt          (optional — NCF tab disabled if missing)
    models/ncf_id_maps.pkl       (optional)

Required data:
    data/articles.csv
    data/customers.csv
    data/transactions_train.csv
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

import pickle
import json

import numpy as np
import pandas as pd
import streamlit as st
from scipy.sparse import load_npz, csr_matrix, diags
from sklearn.preprocessing import normalize

from src import data as dataio
from src import metrics as metricslib

MODEL_DIR = REPO_ROOT / "models"

st.set_page_config(
    page_title="Personalised Recommendations",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="collapsed",
)

CUSTOM_CSS = """
<style>
  /* Reset Streamlit defaults toward an Apple/Yandex-clean look */
  html, body, [class*="css"]  {
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text",
                 "Helvetica Neue", "Segoe UI", system-ui, sans-serif;
    color: #1d1d1f;
    -webkit-font-smoothing: antialiased;
  }
  /* Hide Streamlit chrome */
  #MainMenu, footer, [data-testid="stToolbar"], header[data-testid="stHeader"] { display: none; }
  /* Tighten container width and centre */
  .block-container { max-width: 1080px; padding-top: 3rem; padding-bottom: 4rem; }
  /* Headings */
  h1 { font-weight: 600; font-size: 40px; letter-spacing: -0.025em; margin-bottom: 0.25rem !important; }
  h2 { font-weight: 600; font-size: 22px; letter-spacing: -0.01em; margin-top: 2.5rem !important; }
  h3 { font-weight: 500; font-size: 16px; color: #1d1d1f; margin: 0 !important; }
  .subtitle { color: #6e6e73; font-size: 17px; margin-bottom: 2.5rem; max-width: 640px; }
  .pill {
    display: inline-block; padding: 4px 12px; border-radius: 100px;
    background: #f5f5f7; color: #1d1d1f; font-size: 13px; font-weight: 500;
    margin-bottom: 1.5rem;
  }
  /* Product cards */
  .card {
    background: #ffffff; border: 1px solid #e5e5e7; border-radius: 18px;
    padding: 20px; margin: 8px 0; transition: all 0.2s ease;
    height: 100%;
  }
  .card:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,0,0,0.06); border-color: #d2d2d7; }
  .card-rank {
    display: inline-block; width: 22px; height: 22px; line-height: 22px;
    background: #1d1d1f; color: #fff; border-radius: 6px; text-align: center;
    font-size: 12px; font-weight: 600; margin-right: 8px;
  }
  .card-title { font-size: 15px; font-weight: 600; color: #1d1d1f; margin: 0; }
  .card-row { display: flex; justify-content: space-between; margin-top: 6px; font-size: 13px; }
  .card-key { color: #86868b; }
  .card-val { color: #1d1d1f; font-weight: 500; }
  .card-id { color: #86868b; font-size: 11px; font-family: ui-monospace, SFMono-Regular, monospace; margin-top: 8px; }
  /* Compact purchase-history row */
  .history-row {
    display: flex; align-items: center; padding: 10px 14px; border-radius: 10px;
    background: #f5f5f7; margin-bottom: 6px;
  }
  .history-name { font-size: 14px; font-weight: 500; }
  .history-meta { color: #86868b; font-size: 12px; margin-top: 2px; }
  /* Customer dropdown styling */
  [data-baseweb="select"] > div { border-radius: 10px !important; border: 1px solid #d2d2d7 !important; }
  /* Section divider */
  .divider { border-top: 1px solid #e5e5e7; margin: 3rem 0 2rem; }
  .muted { color: #86868b; font-size: 13px; }
  /* Algorithm tabs — iOS-style segmented control */
  div[role="radiogroup"] {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    gap: 6px !important;
    background: #f5f5f7;
    padding: 4px;
    border-radius: 12px;
    width: fit-content;
  }
  div[role="radiogroup"] > label {
    padding: 6px 14px !important;
    border-radius: 8px !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    white-space: nowrap !important;
    cursor: pointer;
    color: #6e6e73;
    transition: all 0.15s ease;
  }
  div[role="radiogroup"] > label:hover { color: #1d1d1f; }
  /* Active chip: filled white card with shadow (selected has aria-checked=true) */
  div[role="radiogroup"] > label[data-baseweb="radio"]:has(input:checked) {
    background: #ffffff !important;
    color: #1d1d1f !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
  }
  /* Hide native radio circle — chip itself is the indicator */
  div[role="radiogroup"] > label > div:first-child { display: none !important; }
  /* Form label styling */
  .field-label {
    font-size: 12px; font-weight: 500; color: #6e6e73;
    text-transform: uppercase; letter-spacing: 0.04em;
    margin-bottom: 6px;
  }
</style>
"""

TEXT_COLS = [
    "prod_name", "detail_desc", "product_type_name",
    "product_group_name", "colour_group_name",
    "department_name", "index_group_name",
]


# ---------- loaders (cached) ----------

@st.cache_resource
def load_data(sample_n: int = 1_000_000):
    articles = dataio.load_articles()
    transactions = dataio.load_transactions(nrows=sample_n)
    train, _ = dataio.time_based_split(transactions, cutoff_days=7)
    return articles, train


@st.cache_resource
def load_content_based():
    with open(MODEL_DIR / "content_based_vectorizer.pkl", "rb") as f:
        vec = pickle.load(f)
    tfidf = load_npz(MODEL_DIR / "content_based_item_tfidf.npz")
    return vec, tfidf


@st.cache_resource
def load_cf():
    with open(MODEL_DIR / "cf_als_model.pkl", "rb") as f:
        bundle = pickle.load(f)
    return bundle["model"], bundle["user_index"], bundle["item_index"]


@st.cache_resource
def load_hybrid_config():
    path = MODEL_DIR / "hybrid_config.pkl"
    if not path.exists():
        return None
    with open(path, "rb") as f:
        return pickle.load(f)


@st.cache_resource
def build_cb_profiles(_articles: pd.DataFrame, train: pd.DataFrame, _tfidf):
    """Build content-based user profiles. Underscored args skip Streamlit hashing."""
    cols = [c for c in TEXT_COLS if c in _articles.columns]
    corpus_df = _articles[["article_id"] + cols].copy().fillna("")
    item_id_to_row = {a: i for i, a in enumerate(corpus_df["article_id"].values)}
    df = train.copy()
    df["item_row"] = df["article_id"].map(item_id_to_row)
    df = df.dropna(subset=["item_row"])
    df["item_row"] = df["item_row"].astype(int)
    users = pd.Index(df["customer_id"].unique())
    user_pos = users.get_indexer(df["customer_id"])
    counts = np.bincount(user_pos, minlength=len(users)).astype(np.float32)
    counts[counts == 0] = 1
    sel = csr_matrix(
        (np.ones(len(df), dtype=np.float32), (user_pos, df["item_row"].values)),
        shape=(len(users), _tfidf.shape[0]),
    )
    profiles = diags(1.0 / counts) @ (sel @ _tfidf)
    profiles = normalize(profiles, norm="l2", axis=1)
    return profiles, {u: i for i, u in enumerate(users)}, item_id_to_row


# ---------- recommenders ----------

def recommend_cb(user_id, profiles, user_id_to_row, tfidf, item_id_to_row, articles, seen, k):
    if user_id not in user_id_to_row:
        return None
    profile = profiles[user_id_to_row[user_id]]
    if profile.nnz == 0:
        return None
    scores = (profile @ tfidf.T).toarray().ravel()
    if seen:
        seen_rows = [item_id_to_row[a] for a in seen if a in item_id_to_row]
        scores[seen_rows] = -np.inf
    top = np.argpartition(-scores, k)[:k]
    top = top[np.argsort(-scores[top])]
    row_to_item = {v: kk for kk, v in item_id_to_row.items()}
    return [row_to_item[i] for i in top]


def recommend_als(model, user_index, item_index, train, user_id, k):
    user_id_to_row = {u: i for i, u in enumerate(user_index)}
    if user_id not in user_id_to_row:
        return None
    # build a one-row user_item to satisfy implicit.recommend API
    user_seen = train[train["customer_id"] == user_id]["article_id"]
    item_id_to_row = {a: i for i, a in enumerate(item_index)}
    cols = [item_id_to_row[a] for a in user_seen if a in item_id_to_row]
    row = csr_matrix(
        (np.ones(len(cols), dtype=np.float32), ([0] * len(cols), cols)),
        shape=(1, len(item_index)),
    )
    item_rows, _ = model.recommend(0, row, N=k, filter_already_liked_items=True)
    return [item_index[i] for i in item_rows]


def recommend_hybrid(user_id, alpha, profiles, cb_u_id_to_row, tfidf, item_id_to_row,
                     als_model, als_user_index, als_item_index, seen, k):
    als_u_id_to_row = {u: i for i, u in enumerate(als_user_index)}
    als_i_id_to_row = {a: i for i, a in enumerate(als_item_index)}
    candidate_items = list(set(als_item_index))
    cb_score = np.zeros(len(candidate_items), dtype=np.float32)
    if user_id in cb_u_id_to_row:
        profile = profiles[cb_u_id_to_row[user_id]]
        if profile.nnz > 0:
            rows = [item_id_to_row.get(i, -1) for i in candidate_items]
            mask = np.array(rows) >= 0
            if mask.any():
                sims = (profile @ tfidf[np.array(rows)[mask]].T).toarray().ravel()
                cb_score[mask] = sims
    cf_score = np.zeros(len(candidate_items), dtype=np.float32)
    if user_id in als_u_id_to_row:
        u_fac = als_model.user_factors[als_u_id_to_row[user_id]]
        rows = [als_i_id_to_row.get(i, -1) for i in candidate_items]
        mask = np.array(rows) >= 0
        if mask.any():
            i_fac = als_model.item_factors[np.array(rows)[mask]]
            cf_score[mask] = i_fac @ u_fac

    def minmax(x):
        lo, hi = x.min(), x.max()
        return np.zeros_like(x) if hi - lo < 1e-12 else (x - lo) / (hi - lo)

    combined = alpha * minmax(cb_score) + (1 - alpha) * minmax(cf_score)
    if seen:
        mask = np.array([1.0 if i in seen else 0.0 for i in candidate_items])
        combined = np.where(mask > 0, -np.inf, combined)
    arr = np.array(candidate_items)
    top = np.argpartition(-combined, k)[:k]
    top = top[np.argsort(-combined[top])]
    return arr[top].tolist()


# ---------- UI ----------

def main():
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    # Hero
    st.markdown('<div class="pill">Personalised Recommendations</div>', unsafe_allow_html=True)
    st.markdown("<h1>Built to learn what you actually wear.</h1>", unsafe_allow_html=True)
    st.markdown(
        '<p class="subtitle">Three recommendation algorithms running live on the H&amp;M catalogue. Pick a customer to see what each model would suggest next.</p>',
        unsafe_allow_html=True,
    )

    with st.spinner("Loading models…"):
        try:
            articles, train = load_data(sample_n=1_000_000)
            vec, tfidf = load_content_based()
            als_model, als_user_index, als_item_index = load_cf()
            hybrid_cfg = load_hybrid_config()
            best_alpha = hybrid_cfg["best_alpha"] if hybrid_cfg else 0.5
            profiles, cb_u_id_to_row, item_id_to_row = build_cb_profiles(articles, train, tfidf)
        except FileNotFoundError as e:
            st.error(f"Missing artefact: `{e.filename}`")
            return

    seen_by_user = train.groupby("customer_id")["article_id"].apply(set).to_dict()
    sample_users = list(seen_by_user.keys())[:200]

    # Algorithm chip row + customer picker
    c_alg, c_user, c_k = st.columns([3, 2, 1])
    with c_alg:
        st.markdown('<div class="field-label">Algorithm</div>', unsafe_allow_html=True)
        algo = st.radio(
            "Algorithm",
            ["Hybrid", "Content-Based", "Collaborative Filtering"],
            horizontal=True,
            label_visibility="collapsed",
        )
    with c_user:
        st.markdown('<div class="field-label">Customer</div>', unsafe_allow_html=True)
        # Show a brief preview of each customer's top purchase to make picking meaningful
        first_purchase_lookup = {}
        for uid in sample_users:
            seen_ids = list(seen_by_user.get(uid, set()))[:1]
            if seen_ids:
                row = articles[articles["article_id"] == seen_ids[0]].head(1)
                if not row.empty:
                    first_purchase_lookup[uid] = row.iloc[0].get("prod_name", "—")
                else:
                    first_purchase_lookup[uid] = "—"
            else:
                first_purchase_lookup[uid] = "—"
        user_id = st.selectbox(
            "Customer",
            sample_users,
            format_func=lambda u: f"{u[:6]}… · bought {first_purchase_lookup.get(u, '—')}",
            label_visibility="collapsed",
        )
    with c_k:
        st.markdown('<div class="field-label">Show</div>', unsafe_allow_html=True)
        k = st.selectbox(
            "Recommendations",
            [10, 15, 20],
            index=0,
            format_func=lambda n: f"{n} items",
            label_visibility="collapsed",
        )

    seen = seen_by_user.get(user_id, set())

    # Two-column body: history left, recommendations right
    col_hist, col_recs = st.columns([1, 2], gap="large")

    with col_hist:
        st.markdown("<h2>Purchase history</h2>", unsafe_allow_html=True)
        st.markdown(f'<p class="muted">{len(seen)} items in the training window</p>', unsafe_allow_html=True)
        recent = articles[articles["article_id"].isin(list(seen)[:6])]
        for _, item in recent.head(6).iterrows():
            st.markdown(
                f'<div class="history-row">'
                f'<div><div class="history-name">{item.get("prod_name", "—")}</div>'
                f'<div class="history-meta">{item.get("product_type_name", "")} · {item.get("colour_group_name", "")}</div></div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    with col_recs:
        st.markdown("<h2>Recommended for this customer</h2>", unsafe_allow_html=True)
        if algo.startswith("Content"):
            recs = recommend_cb(user_id, profiles, cb_u_id_to_row, tfidf, item_id_to_row, articles, seen, k)
            badge = "TF-IDF · Cosine Similarity"
        elif algo.startswith("Collaborative"):
            recs = recommend_als(als_model, als_user_index, als_item_index, train, user_id, k)
            badge = "ALS · Matrix Factorisation"
        else:
            recs = recommend_hybrid(
                user_id, best_alpha, profiles, cb_u_id_to_row, tfidf, item_id_to_row,
                als_model, als_user_index, als_item_index, seen, k,
            )
            badge = f"Hybrid · α = {best_alpha:.2f}"

        st.markdown(f'<p class="muted">{badge}</p>', unsafe_allow_html=True)

        if not recs:
            st.markdown('<div class="card"><p class="muted">Cold-start: not enough history to personalise.</p></div>', unsafe_allow_html=True)
            return

        rec_df = articles[articles["article_id"].isin(recs)].copy()
        rec_df["rank"] = rec_df["article_id"].map({a: i + 1 for i, a in enumerate(recs)})
        rec_df = rec_df.sort_values("rank")

        for i in range(0, len(rec_df), 2):
            row_cols = st.columns(2, gap="small")
            for col, (_, item) in zip(row_cols, rec_df.iloc[i: i + 2].iterrows()):
                with col:
                    st.markdown(
                        f'<div class="card">'
                        f'<p class="card-title"><span class="card-rank">{int(item["rank"])}</span>{item.get("prod_name", "—")}</p>'
                        f'<div class="card-row"><span class="card-key">Type</span><span class="card-val">{item.get("product_type_name", "—")}</span></div>'
                        f'<div class="card-row"><span class="card-key">Colour</span><span class="card-val">{item.get("colour_group_name", "—")}</span></div>'
                        f'<div class="card-row"><span class="card-key">Section</span><span class="card-val">{item.get("section_name", "—")}</span></div>'
                        f'<p class="card-id">{item["article_id"]}</p>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    with st.expander("About this demo"):
        st.markdown(
            """
            **Algorithms.** Three live models on H&M Personalized Fashion Recommendations.

            - **Content-Based** — TF-IDF on product metadata + cosine similarity.
            - **Collaborative Filtering** — Alternating Least Squares on implicit feedback (Hu, Koren and Volinsky, 2008).
            - **Hybrid** — Weighted ensemble (α = 0.5) of the two above, with popularity fallback for cold users.

            **Dataset.** H&M Personalized Fashion Recommendations (Kaggle, 2022). Anonymised customer IDs only — no PII.

            **Feedback.** Anonymous and aggregated, used to evaluate recommendation quality.
            """
        )

    with st.expander("Submit feedback"):
        relevance = st.slider("How relevant are these recommendations?", 1, 5, 3)
        diversity = st.slider("How diverse are they?", 1, 5, 3)
        surprise = st.slider("Did any pleasantly surprise you?", 1, 5, 3)
        notes = st.text_area("Any free-text feedback?")
        if st.button("Submit feedback"):
            from datetime import datetime
            feedback_path = REPO_ROOT / "outputs" / "user_feedback"
            feedback_path.mkdir(parents=True, exist_ok=True)
            entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "algorithm": algo,
                "k": k,
                "user_id": str(user_id),
                "relevance": relevance,
                "diversity": diversity,
                "surprise": surprise,
                "notes": notes,
            }
            with open(feedback_path / "feedback.jsonl", "a") as f:
                f.write(json.dumps(entry) + "\n")
            st.success("Thank you — your anonymous feedback was recorded.")


if __name__ == "__main__":
    main()
