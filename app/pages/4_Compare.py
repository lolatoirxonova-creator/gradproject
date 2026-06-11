"""Side-by-side algorithm comparison.

Renders the same user's top-K recommendations from all four implemented
algorithms in parallel columns: Content-Based, ALS, Hybrid (with a live α
slider), and Neural CF. Per-column ILD scores let the user see directly how
the four families differ in diversity, not just relevance.

This is the "answer" to supervisor feedback §3.4 — the algorithms operating
on the same customer simultaneously, not switched via a radio button.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

import streamlit as st

from app import auth, db, shared


K_DEFAULT = 6
POOL_MULT = 4
LAMBDA_MMR = 0.7


def _algo_column(col, title: str, badge: str, recs, articles, ild: float,
                 user, saved_set, liked, disliked, empty_msg: str | None,
                 key_prefix: str, reasons: dict | None = None):
    """Render one of the four parallel algorithm columns."""
    with col:
        st.markdown(f"<h3 style='margin-top: 0;'>{title}</h3>", unsafe_allow_html=True)
        st.markdown(f'<p class="muted" style="font-size:12px; margin-top: 4px;">{badge}</p>',
                    unsafe_allow_html=True)
        # ILD chip — green-tinted for high diversity, neutral for low
        klass = "high" if ild >= 0.4 else "mid"
        st.markdown(
            f'<span class="card-match {klass}" style="position: static; '
            f'display:inline-block; margin: 8px 0 16px;">ILD {ild:.2f}</span>',
            unsafe_allow_html=True,
        )
        if not recs:
            if empty_msg:
                st.markdown(
                    f'<div class="card" style="padding:16px;"><p class="muted">{empty_msg}</p></div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    '<div class="card" style="padding:16px;">'
                    '<p class="muted">No recommendations.</p></div>',
                    unsafe_allow_html=True,
                )
            return
        rec_df = articles[articles["article_id"].isin([a for a, _ in recs])].copy()
        order_map = {aid: i for i, (aid, _) in enumerate(recs)}
        score_map = {aid: s for aid, s in recs}
        rec_df["_order"] = rec_df["article_id"].map(order_map)
        rec_df = rec_df.sort_values("_order")
        for i, (_, row) in enumerate(rec_df.iterrows()):
            item = row.to_dict()
            aid = item["article_id"]
            shared.render_catalogue_card(
                item,
                key_prefix=f"{key_prefix}_{i}",
                user_id=user["id"], saved_set=saved_set,
                liked_set=liked, disliked_set=disliked,
                score=score_map.get(aid),
                reason=(reasons or {}).get(aid),
            )


def main():
    shared.check_session_timeout()
    user = st.session_state.get("user")
    if user is None:
        st.warning("Please log in from the home page first.")
        st.stop()

    shared.apply_css()
    shared.render_sidebar(user)

    st.markdown('<div class="pill">Compare</div>', unsafe_allow_html=True)
    st.markdown("<h1>Side-by-side algorithm comparison.</h1>", unsafe_allow_html=True)
    st.markdown(
        '<p class="subtitle">Same user, same time, four algorithms. Drag the α '
        'slider to watch the Hybrid column re-rank in real time.</p>',
        unsafe_allow_html=True,
    )

    # ---------- load models + state ----------
    try:
        articles = shared.load_hm_articles()  # Compare runs the trained H&M models
        vectorizer, tfidf = shared.load_content_based()
        als_model, _, als_item_index = shared.load_cf()
        hybrid_cfg = shared.load_hybrid_config()
        tuned_alpha = float(hybrid_cfg["best_alpha"]) if hybrid_cfg else 0.5
    except FileNotFoundError as e:
        st.error(f"Missing artefact: `{e.filename}`")
        return

    item_id_to_row = shared.build_item_id_to_row(articles)
    als_item_to_row, candidate_items = shared.als_lookups(als_item_index)

    include = shared.curated_set() or None  # gate to curated demo catalogue

    state = db.user_state(user["id"])
    saved = state["saved"]
    liked = state["liked"]
    disliked = state["disliked"]
    preferences = auth.get_preferences(user["id"])
    saved_set = set(saved)
    excluded = saved_set | disliked

    # ---------- controls ----------
    c_alpha, c_k = st.columns([3, 1])
    with c_alpha:
        st.markdown(
            f'<div class="field-label">Hybrid α — CB weight (1.0) ↔ CF weight (0.0). '
            f'Tuned default from notebook 04: <b>α = {tuned_alpha:.2f}</b></div>',
            unsafe_allow_html=True,
        )
        alpha = st.slider(
            "alpha", min_value=0.0, max_value=1.0, value=tuned_alpha, step=0.05,
            format="%.2f", label_visibility="collapsed", key="cmp_alpha",
        )
    with c_k:
        st.markdown('<div class="field-label">Show</div>', unsafe_allow_html=True)
        k = st.selectbox(
            "k", [6, 8, 10, 15, 20], index=0,
            format_func=lambda n: f"Top {n}",
            label_visibility="collapsed", key="cmp_k",
        )

    mmr_on = bool(st.session_state.get("mmr_enabled", True))
    pool_size = k * (POOL_MULT if mmr_on else 1)

    def _apply_mmr(recs):
        if not mmr_on or not recs:
            return list(recs or [])[:k]
        return shared.mmr_rerank(
            recs, tfidf, item_id_to_row, k=k, lambda_param=LAMBDA_MMR,
        )

    # ---------- compute all four algorithms ----------
    profile = shared.build_user_profile(saved, preferences, articles, tfidf, item_id_to_row)

    with st.spinner("Computing all four algorithms…"):
        cb_pool = shared.recommend_cb(profile, tfidf, item_id_to_row, excluded, pool_size,
                                      include=include)
        als_pool = shared.recommend_als(als_model, als_item_index, als_item_to_row,
                                         saved_set, excluded, pool_size, include=include)
        hyb_pool = shared.recommend_hybrid(
            profile, tfidf, item_id_to_row,
            als_model, als_item_index, als_item_to_row,
            candidate_items, saved_set, excluded, alpha, pool_size,
            include=include,
        )
        ncf_pool = shared.recommend_ncf(saved_set, excluded, pool_size, include=include)

    cb_recs  = _apply_mmr(cb_pool)
    als_recs = _apply_mmr(als_pool)
    hyb_recs = _apply_mmr(hyb_pool)
    ncf_recs = _apply_mmr(ncf_pool)

    # ILD per column
    ild_cb  = shared.intra_list_diversity(cb_recs,  tfidf, item_id_to_row)
    ild_als = shared.intra_list_diversity(als_recs, tfidf, item_id_to_row)
    ild_hyb = shared.intra_list_diversity(hyb_recs, tfidf, item_id_to_row)
    ild_ncf = shared.intra_list_diversity(ncf_recs, tfidf, item_id_to_row)

    # Per-column reasons in the rail-appropriate style (CB / CF / Hybrid / NCF)
    cb_ids  = [a for a, _ in (cb_recs  or [])]
    als_ids = [a for a, _ in (als_recs or [])]
    hyb_ids = [a for a, _ in (hyb_recs or [])]
    ncf_ids = [a for a, _ in (ncf_recs or [])]
    cb_reasons  = shared.explain_cb_for_items(profile, cb_ids, tfidf, item_id_to_row, vectorizer)
    als_reasons = shared.explain_cf_for_items(als_ids)
    hyb_reasons = shared.explain_hybrid_for_items(profile, hyb_ids, tfidf, item_id_to_row, vectorizer, alpha)
    # NCF reuses the CF-style explanation (it's a neural collaborative model)
    ncf_reasons = shared.explain_cf_for_items(ncf_ids)

    # Prefetch every article we're about to render (one parallel batch)
    all_recs = (cb_recs or []) + (als_recs or []) + (hyb_recs or []) + (ncf_recs or [])
    seen_aids = set()
    prefetch_items = []
    for aid, _ in all_recs:
        if aid in seen_aids:
            continue
        seen_aids.add(aid)
        row = articles[articles["article_id"] == aid]
        if not row.empty:
            prefetch_items.append(row.iloc[0].to_dict())
    if prefetch_items:
        with st.spinner(f"Fetching product images ({len(prefetch_items)} items)…"):
            shared.prefetch_images_sync(prefetch_items, timeout=14.0)

    st.markdown('<div class="divider" style="margin: 1.5rem 0;"></div>', unsafe_allow_html=True)

    # ---------- four parallel columns ----------
    col_cb, col_als, col_hyb, col_ncf = st.columns(4, gap="small")
    _algo_column(
        col_cb, "Content-Based",
        "TF-IDF cosine",
        cb_recs, articles, ild_cb,
        user, saved_set, liked, disliked,
        empty_msg="No CB profile yet — pick preferences or save items.",
        key_prefix="cmp_cb", reasons=cb_reasons,
    )
    _algo_column(
        col_als, "ALS CF",
        "Matrix factorisation",
        als_recs, articles, ild_als,
        user, saved_set, liked, disliked,
        empty_msg="ALS needs ≥1 saved item to fold you in.",
        key_prefix="cmp_als", reasons=als_reasons,
    )
    _algo_column(
        col_hyb, "Hybrid",
        f"α = {alpha:.2f}",
        hyb_recs, articles, ild_hyb,
        user, saved_set, liked, disliked,
        empty_msg="Cold start.",
        key_prefix="cmp_hyb", reasons=hyb_reasons,
    )
    _algo_column(
        col_ncf, "Neural CF",
        "NeuMF · 48-d embeddings",
        ncf_recs, articles, ild_ncf,
        user, saved_set, liked, disliked,
        empty_msg="NeuMF needs ≥1 saved item with NCF coverage (~40% of catalogue).",
        key_prefix="cmp_ncf", reasons=ncf_reasons,
    )

    # ---------- footer commentary ----------
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        **How to read this view.** All four algorithms see the same user state at the
        same instant. The **ILD chips** under each header show the diversity of that
        column's output — high (green) means the algorithm spreads across categories,
        low (grey) means it concentrates on similar items. The {'MMR re-ranking layer is **on**' if mmr_on else 'MMR re-ranking layer is **off**'}
        (toggle in the sidebar).

        **What to look for at the viva.** Move the **α slider** to 0.0 — the Hybrid
        column collapses onto ALS. Move it to 1.0 — it collapses onto Content-Based.
        Somewhere in between (typically α ≈ {tuned_alpha:.2f}) the Hybrid column shows
        items that *neither* CB nor ALS picked alone — this is the
        ensemble effect, and is the central claim of the project's hybrid approach.

        See **Evaluation** in the sidebar for the cross-validated quantitative
        comparison (5-fold Precision / Recall / NDCG / MAP / Hit Rate + Wilcoxon
        significance tests).
        """
    )


main()
