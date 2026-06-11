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


def _go_signin():
    """Send a guest to the sign-in page (object stashed by main.py's router)."""
    page = st.session_state.get("_signin_page")
    if page is not None:
        st.switch_page(page)
    else:
        st.toast("Please sign in to continue.", icon="🔒")


def main():
    shared.check_session_timeout()
    user = st.session_state.get("user")  # may be None — product detail is public (#2)
    guest = user is None

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

    if guest:
        saved, liked, disliked, saved_set, excluded = [], set(), set(), set(), set()
    else:
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

        # ---------- price + quantity + add to cart + order now ----------
        reg, sale = shared.catalogue_price(article_id)
        if sale is not None:
            price_html = (f"<s style='color:var(--muted);font-weight:400;font-size:21px;'>"
                          f"${reg:,.2f}</s> <span style='color:var(--accent-2);'>${sale:,.2f}</span>")
        else:
            price_html = f"${reg:,.2f}"
        st.markdown(f"<h2 style='margin:4px 0 12px 0 !important;'>{price_html}</h2>",
                    unsafe_allow_html=True)
        # compare toggle (public — guests can compare too)
        _in_cmp = shared.in_compare(article_id)
        if st.button("⚖  In compare" if _in_cmp else "⚖  Add to compare",
                     type=("primary" if _in_cmp else "secondary"),
                     use_container_width=True, key="prod_compare"):
            shared.toggle_compare(article_id)
            st.rerun()

        if guest:
            if st.button("🔒  Sign in to buy", type="primary", use_container_width=True, key="prod_signin"):
                _go_signin()
            st.caption("Browse freely — sign in to add to cart, order, or save.")
        else:
            q_col, add_col = st.columns([1, 2])
            with q_col:
                qty = st.number_input("Quantity", min_value=1, max_value=20, value=1, step=1,
                                      key=f"prod_qty_{article_id}", label_visibility="collapsed")
            with add_col:
                if st.button("🛒  Add to cart", type="primary", use_container_width=True, key="prod_add_cart"):
                    db.add_to_cart(user["id"], article_id, int(qty))
                    st.toast(f"Added {int(qty)} to cart", icon="🛒")
                    st.rerun()
            if st.button("⚡  Order now — pay at our store", use_container_width=True, key="prod_order_now"):
                db.order_now(user["id"], article_id, int(qty),
                             shared.effective_price(article_id), item.get("prod_name") or "")
                st.toast("Ordered! Check your notifications (top-right).", icon="🛍️")
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

        # ---------- review summary chip (full reviews section is below) ----------
        _sum = db.review_summary(article_id)
        if _sum["count"]:
            full = int(round(_sum["avg"]))
            st.markdown(
                f'<p style="margin-top:14px;"><span style="color:var(--accent);font-size:16px;">'
                f'{"★" * full}{"☆" * (5 - full)}</span> '
                f'<span class="muted">{_sum["avg"]} · {_sum["count"]} review'
                f'{"s" if _sum["count"] != 1 else ""}</span></p>',
                unsafe_allow_html=True,
            )

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

    # ---------- ratings & reviews (#11) ----------
    import html as _html
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    summary = db.review_summary(article_id)

    def _stars(n: float) -> str:
        f = int(round(n))
        return "★" * f + "☆" * (5 - f)

    if summary["count"]:
        st.markdown(
            f"<h2>Ratings &amp; reviews "
            f"<span style='color:var(--accent);'>{_stars(summary['avg'])}</span> "
            f"<span class='muted' style='font-size:15px;font-weight:400;'>{summary['avg']} · "
            f"{summary['count']} review{'s' if summary['count'] != 1 else ''}</span></h2>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown("<h2>Ratings &amp; reviews</h2>", unsafe_allow_html=True)
        st.markdown("<p class='muted'>No reviews yet — be the first to share yours.</p>",
                    unsafe_allow_html=True)

    if guest:
        if st.button("Sign in to write a review", key="rev_signin"):
            _go_signin()
    else:
        existing = db.user_review(user["id"], article_id)
        with st.expander("Edit your review" if existing else "Write a review",
                         expanded=not summary["count"]):
            with st.form(f"review_form_{article_id}"):
                rv_rating = st.slider("Your rating", 1, 5,
                                      value=(existing["rating"] if existing else 5),
                                      key=f"rev_rating_{article_id}")
                rv_comment = st.text_area("Your review (optional)",
                                          value=(existing["comment"] if existing else ""),
                                          placeholder="What did you think of this product?",
                                          key=f"rev_comment_{article_id}")
                if st.form_submit_button("Submit review", type="primary"):
                    db.add_review(user["id"], article_id, rv_rating, rv_comment)
                    db.log_rating(user["id"], article_id, rv_rating)  # recommender signal
                    st.toast("Thanks for your review!", icon="✅")
                    st.rerun()

    for rv in db.get_reviews(article_id):
        name = _html.escape(rv["display_name"] or "Anonymous")
        comment = _html.escape((rv["comment"] or "").strip())
        date = (rv["created_at"] or "")[:10]
        comment_html = (f'<p style="margin:6px 0 0;font-size:14px;line-height:1.5;">{comment}</p>'
                        if comment else "")
        st.markdown(
            f'<div class="card" style="padding:14px 16px;margin-bottom:8px;">'
            f'<div style="display:flex;justify-content:space-between;align-items:center;">'
            f'<span style="font-weight:600;">{name}</span>'
            f'<span style="color:var(--accent);">{_stars(rv["rating"])}</span></div>'
            f'{comment_html}'
            f'<p class="muted" style="margin:6px 0 0;font-size:12px;">{date}</p></div>',
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
            user_id=(None if guest else user["id"]),
            saved_set=(None if guest else saved_set),
            liked_set=(None if guest else liked), disliked_set=(None if guest else disliked),
            reasons=reasons,
            cart_set=(set() if guest else {l["article_id"] for l in db.get_cart(user["id"])}),
        )
    else:
        st.markdown(
            '<div class="card" style="padding:24px;"><p class="muted">No similar items found for this article.</p></div>',
            unsafe_allow_html=True,
        )


main()
