"""Hidden product detail page — accessed via View clicks from cards.

Reads `viewing_article_id` from session state. Shows full metadata,
similar-items (content-based), and a save/unsave button.

Filename starts with `_` so Streamlit's file-system page discovery hides it
from the sidebar nav. It's still reachable via st.switch_page(...).
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

import pandas as pd
import streamlit as st

from app import db, shared


def _format_value(value) -> str:
    if value is None:
        return "—"
    if isinstance(value, float) and pd.isna(value):
        return "—"
    s = str(value).strip()
    return s if s else "—"


def main():
    shared.check_session_timeout()
    user = st.session_state.get("user")
    if user is None:
        st.warning("Please log in from the home page first.")
        st.stop()

    shared.apply_css()
    shared.render_sidebar(user)

    article_id = st.session_state.get("viewing_article_id")

    if not article_id:
        st.markdown('<div class="pill">Product</div>', unsafe_allow_html=True)
        st.markdown("<h1>No product selected.</h1>", unsafe_allow_html=True)
        st.markdown(
            '<p class="subtitle">Open the catalogue and click <b>View</b> on any item to see its full '
            'details and similar items.</p>',
            unsafe_allow_html=True,
        )
        if st.button("Go to catalogue", type="primary"):
            st.switch_page("pages/1_Catalogue.py")
        return

    articles = shared.load_articles()
    cosmetics = shared.cosmetics_mode()
    if not cosmetics:
        _, tfidf = shared.load_content_based()
        item_id_to_row = shared.build_item_id_to_row(articles)

    row = articles[articles["article_id"] == article_id]
    if row.empty:
        st.error(f"Article `{article_id}` is not in the current catalogue.")
        st.session_state.pop("viewing_article_id", None)
        return

    item = row.iloc[0]

    # Log a view interaction (dedup per session per article)
    viewed = st.session_state.setdefault("viewed_articles", set())
    if article_id not in viewed:
        db.log_interaction(user["id"], article_id, "view")
        viewed.add(article_id)

    state = db.user_state(user["id"])
    saved = state["saved"]
    liked = state["liked"]
    disliked = state["disliked"]
    saved_set = set(saved)
    excluded = saved_set | disliked

    # ---------- hero (image left, details right) ----------
    item_dict = item.to_dict() if hasattr(item, "to_dict") else dict(item)
    # Prefetch the hero image and similar-items images server-side. Similar
    # items are computed below but we can warm the cache while the user reads.
    shared.prefetch_images_sync([item_dict])
    img_src = shared._resolve_image_src(article_id, item_dict, width=600, height=750)
    col_image, col_details = st.columns([1, 1], gap="large")

    with col_image:
        st.markdown(
            f'<div class="card" style="padding:0;">'
            f'  <div class="card-image-wrapper" style="aspect-ratio: 4/5;">'
            f'    <img class="card-image" src="{img_src}" alt="product image" />'
            f'  </div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    with col_details:
        st.markdown('<div class="pill">Product detail</div>', unsafe_allow_html=True)
        st.markdown(
            f"<h1 style='margin-top: 0;'>{_format_value(item.get('prod_name'))}</h1>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<p class="muted">{_format_value(item.get("product_type_name"))} · '
            f'{_format_value(item.get("colour_group_name"))} · ID {article_id}</p>',
            unsafe_allow_html=True,
        )

        # ---------- price + quantity + add to cart ----------
        price = shared.display_price(article_id)
        st.markdown(f"<h2 style='margin:4px 0 12px 0 !important;'>${price:,.2f}</h2>",
                    unsafe_allow_html=True)
        q_col, add_col = st.columns([1, 2])
        with q_col:
            qty = st.number_input("Quantity", min_value=1, max_value=20, value=1, step=1,
                                  key=f"prod_qty_{article_id}", label_visibility="collapsed")
        with add_col:
            if st.button("🛒  Add to cart", type="primary", use_container_width=True, key="prod_add_cart"):
                db.add_to_cart(user["id"], article_id, int(qty))
                st.toast(f"Added {int(qty)} to cart", icon="🛒")
                st.rerun()

        is_saved = article_id in saved_set
        if is_saved:
            if st.button("♥ Remove from wishlist", use_container_width=True, key="prod_unsave"):
                db.log_interaction(user["id"], article_id, "unsave")
                st.rerun()
        else:
            if st.button("♡ Add to wishlist", use_container_width=True, key="prod_save"):
                db.log_interaction(user["id"], article_id, "save")
                st.rerun()
        st.caption(f"{len(saved)} item{'s' if len(saved) != 1 else ''} in your wishlist")

        # ---------- 5-star rating ----------
        current_rating = db.user_rating(user["id"], article_id)
        st.markdown(
            '<div class="field-label" style="margin-top: 18px;">Your rating</div>',
            unsafe_allow_html=True,
        )
        star_cols = st.columns(5, gap="small")
        for i, col in enumerate(star_cols, start=1):
            with col:
                # Filled star if rating is at or above this slot.
                filled = current_rating is not None and current_rating >= i
                label = "★" if filled else "☆"
                if st.button(label, key=f"rate_{i}_{article_id}", use_container_width=True):
                    if current_rating == i:
                        # Clicking the current rating un-rates (no-op via "rate" event;
                        # we just don't have an inverse, so a 0 is captured as not-rated
                        # by not logging anything new). Simplest: log a 1-star to make
                        # the most-recent event explicitly the lowest possible.
                        # Cleaner UX choice: ignore — clicking the same star is a no-op.
                        pass
                    else:
                        db.log_rating(user["id"], article_id, i)
                    st.rerun()
        if current_rating is not None:
            st.caption(f"You rated this {current_rating}/5 stars")

        # Spec table
        st.markdown("<h2 style='font-size: 18px;'>Details</h2>", unsafe_allow_html=True)
        if cosmetics:
            spec_rows = [
                ("Brand", "brand"), ("Category", "category"), ("Type", "product_type_name"),
                ("For", "index_group_name"), ("Shade", "colour_group_name"),
                ("Size", "size"), ("Quality", "quality"), ("Made in", "made_in"),
            ]
        else:
            spec_rows = [
                ("Department", "department_name"),
                ("Section", "section_name"),
                ("Group", "product_group_name"),
                ("Type", "product_type_name"),
                ("Colour", "colour_group_name"),
                ("Perceived colour", "perceived_colour_master_name"),
                ("Garment group", "garment_group_name"),
            ]
        spec_html = "".join(
            f'<div style="display:flex; justify-content:space-between; padding: 8px 0; '
            f'border-bottom: 1px solid #f0f0f2; font-size: 13px;">'
            f'<span style="color:#86868b;">{label}</span>'
            f'<span style="color:#1d1d1f; font-weight: 500;">{_format_value(item.get(col))}</span></div>'
            for label, col in spec_rows
            if col in item.index
        )
        st.markdown(spec_html, unsafe_allow_html=True)

    # ---------- full description ----------
    detail = _format_value(item.get("detail_desc"))
    if detail and detail != "—":
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.markdown("<h2>Description</h2>", unsafe_allow_html=True)
        st.markdown(
            f'<p style="color:#1d1d1f; max-width: 700px; line-height: 1.6; font-size: 15px;">{detail}</p>',
            unsafe_allow_html=True,
        )

    # ---------- similar items ----------
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown("<h2>Similar items</h2>", unsafe_allow_html=True)
    st.markdown(
        '<p class="muted">Content-based · cosine similarity on product metadata</p>',
        unsafe_allow_html=True,
    )

    if cosmetics:
        similar_recs = shared.recommend_cosmetics(seed_ids=[article_id], k=8, exclude=excluded)
        reasons = None
    else:
        similar_recs = shared.recommend_similar(
            article_id, tfidf, item_id_to_row, k=8, exclude=excluded,
        )
        reasons = (shared.explain_similar_to(article_id, [a for a, _ in similar_recs], articles)
                   if similar_recs else None)
    if similar_recs:
        shared.render_rec_cards(
            similar_recs, articles, key_prefix=f"sim_{article_id}",
            user_id=user["id"], saved_set=saved_set,
            liked_set=liked, disliked_set=disliked,
            reasons=reasons, cart_set={l["article_id"] for l in db.get_cart(user["id"])},
        )
    else:
        st.markdown(
            '<div class="card" style="padding:24px;"><p class="muted">No similar items found for this article.</p></div>',
            unsafe_allow_html=True,
        )


main()
