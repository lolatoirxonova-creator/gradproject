"""Wishlist page — items the user has saved.

Saved items are derived from the append-only `interactions` log
(`db.user_saved_articles`). Items are shown in reverse save order
(most-recent first).
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

import streamlit as st

from app import db, shared


def main():
    shared.check_session_timeout()
    user = st.session_state.get("user")
    if user is None:
        st.warning("Please log in from the home page first.")
        st.stop()

    shared.apply_css()
    shared.render_sidebar(user)

    st.markdown('<div class="pill">Wishlist</div>', unsafe_allow_html=True)
    st.markdown("<h1>Your saved items.</h1>", unsafe_allow_html=True)

    saved = db.user_state(user["id"])["saved"]

    if not saved:
        st.markdown(
            '<p class="subtitle">No saved items yet. Browse the catalogue and tap the heart '
            'on any product to add it here. The more you save, the better the algorithms '
            'tune to your taste.</p>',
            unsafe_allow_html=True,
        )
        if st.button("Browse catalogue", type="primary"):
            st.switch_page("views/1_Catalogue.py")
        return

    st.markdown(
        f'<p class="subtitle">{len(saved)} item{"s" if len(saved) != 1 else ""} saved. '
        'These shape your recommendations across content-based, collaborative filtering, '
        'and hybrid algorithms.</p>',
        unsafe_allow_html=True,
    )

    articles = shared.load_articles()
    saved_set = set(saved)
    cart_set = {l["article_id"] for l in db.get_cart(user["id"])}

    # Most-recent-first: db returns save order (oldest first), so reverse for index map
    order_map = {aid: i for i, aid in enumerate(reversed(saved))}
    saved_df = articles[articles["article_id"].isin(saved)].copy()
    saved_df["_order"] = saved_df["article_id"].map(order_map)
    saved_df = saved_df.sort_values("_order")

    # Prefetch images for the saved items
    prefetch_items = [saved_df.iloc[i].to_dict() for i in range(len(saved_df))]
    if prefetch_items:
        with st.spinner(f"Fetching product images ({len(prefetch_items)} items)…"):
            shared.prefetch_images_sync(prefetch_items, timeout=14.0)

    rows = (len(saved_df) + 2) // 3
    for r in range(rows):
        cols = st.columns(3, gap="small")
        for ci, col in enumerate(cols):
            idx = r * 3 + ci
            if idx >= len(saved_df):
                break
            item = saved_df.iloc[idx].to_dict()
            with col:
                shared.render_catalogue_card(
                    item, key_prefix=f"wish_r{r}_c{ci}",
                    user_id=user["id"], saved_set=saved_set, cart_set=cart_set,
                )


main()
