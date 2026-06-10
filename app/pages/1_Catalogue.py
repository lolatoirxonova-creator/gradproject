"""Catalogue browse page — search + filter + paginated grid.

Filters: text search (prod_name + detail_desc), department, product type,
master colour, and price range (derived from H&M transactions, cached).

Clicking View on any card opens the hidden product detail page.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

import streamlit as st

from app import db, shared


PAGE_SIZE = 24
# H&M prices are normalised to ~[0, 0.6]. Multiplying by 1000 gives a familiar
# $1–$600 fashion-price range for the slider UX.
PRICE_DISPLAY_SCALE = 1000.0


def _filter_articles(articles, query: str, index_group: str, product_types: list[str],
                      colours: list[str], price_lo: float, price_hi: float,
                      price_series) -> "pd.DataFrame":
    df = articles
    if index_group != "All":
        df = df[df["index_group_name"] == index_group]
    if product_types:
        df = df[df["product_type_name"].isin(product_types)]
    if colours:
        df = df[df["perceived_colour_master_name"].isin(colours)]
    if query:
        q = query.strip().lower()
        if q:
            name_mask = df["prod_name"].fillna("").str.lower().str.contains(q, regex=False)
            desc_mask = df["detail_desc"].fillna("").str.lower().str.contains(q, regex=False)
            df = df[name_mask | desc_mask]
    # Price filter applies only to articles that actually have a price record;
    # articles with no transactions are kept (they have unknown price).
    if price_series is not None and len(price_series) and (price_lo > 0 or price_hi < 1.0):
        mapped = df["article_id"].map(price_series)
        in_range = mapped.between(price_lo, price_hi, inclusive="both")
        unknown = mapped.isna()
        df = df[in_range | unknown]
    return df


def main():
    shared.check_session_timeout()
    user = st.session_state.get("user")
    if user is None:
        st.warning("Please log in from the home page first.")
        st.stop()

    shared.apply_css()
    shared.render_sidebar(user)

    articles = shared.load_articles()
    # Curated demo: browse only the 50 curated products (matching photos).
    curated = shared.curated_set()
    if curated:
        articles = articles[articles["article_id"].isin(curated)]
    state = db.user_state(user["id"])
    saved_set = set(state["saved"])
    liked = state["liked"]
    disliked = state["disliked"]

    st.markdown('<div class="pill">Catalogue</div>', unsafe_allow_html=True)
    st.markdown("<h1>Browse the catalogue.</h1>", unsafe_allow_html=True)
    st.markdown(
        f'<p class="subtitle">A curated edit of {len(articles)} pieces. Search by name, filter '
        'by department / type / colour / price, then save items to shape your recommendations.</p>',
        unsafe_allow_html=True,
    )

    # ---------- search ----------
    st.markdown('<div class="field-label">Search</div>', unsafe_allow_html=True)
    query = st.text_input(
        "Search products by name or description",
        placeholder="e.g. denim, t-shirt, summer dress",
        label_visibility="collapsed",
        key="cat_query",
    )

    # ---------- primary filters (department + type) ----------
    index_groups = sorted({g for g in articles["index_group_name"].dropna() if g})
    col_f1, col_f2 = st.columns([1, 2])
    with col_f1:
        st.markdown('<div class="field-label">Department</div>', unsafe_allow_html=True)
        index_group = st.selectbox(
            "Department", ["All", *index_groups],
            label_visibility="collapsed",
            key="cat_index_group",
        )
    with col_f2:
        st.markdown('<div class="field-label">Product type</div>', unsafe_allow_html=True)
        scope = articles if index_group == "All" else articles[articles["index_group_name"] == index_group]
        type_options = sorted({t for t in scope["product_type_name"].dropna() if t})
        product_types = st.multiselect(
            "Product type", type_options,
            label_visibility="collapsed",
            placeholder="All types",
            key="cat_product_types",
        )

    # ---------- secondary filters (colour + price) ----------
    colour_options = sorted({
        c for c in articles["perceived_colour_master_name"].dropna()
        if c and c.lower() not in ("undefined", "unknown")
    })
    price_series = shared.load_article_prices()  # one-time precompute on first call
    # Display range = min/max in dataset, scaled to display dollars.
    if len(price_series):
        raw_lo = float(price_series.min())
        raw_hi = float(price_series.quantile(0.99))  # cap at 99th pctile — outliers
    else:
        raw_lo, raw_hi = 0.0, 1.0
    disp_lo = max(1.0, raw_lo * PRICE_DISPLAY_SCALE)
    disp_hi = max(disp_lo + 1.0, raw_hi * PRICE_DISPLAY_SCALE)

    col_f3, col_f4 = st.columns([1, 2])
    with col_f3:
        st.markdown('<div class="field-label">Colour</div>', unsafe_allow_html=True)
        colours = st.multiselect(
            "Colour", colour_options,
            label_visibility="collapsed",
            placeholder="All colours",
            key="cat_colours",
        )
    with col_f4:
        st.markdown(
            '<div class="field-label">Price (approx. $) — items with no transaction price are kept</div>',
            unsafe_allow_html=True,
        )
        price_range = st.slider(
            "Price",
            min_value=float(round(disp_lo, 0)),
            max_value=float(round(disp_hi, 0)),
            value=(float(round(disp_lo, 0)), float(round(disp_hi, 0))),
            step=1.0,
            label_visibility="collapsed",
            key="cat_price",
        )

    # Convert display dollars back to H&M-normalised range for filtering
    price_lo = price_range[0] / PRICE_DISPLAY_SCALE
    price_hi = price_range[1] / PRICE_DISPLAY_SCALE

    # Reset pagination when *any* filter changes
    filter_signature = (
        query.strip().lower(),
        index_group,
        tuple(product_types),
        tuple(colours),
        price_range,
    )
    if st.session_state.get("cat_filter_signature") != filter_signature:
        st.session_state["cat_filter_signature"] = filter_signature
        st.session_state["cat_page"] = 1

    filtered = _filter_articles(
        articles, query, index_group, product_types, colours,
        price_lo, price_hi, price_series,
    )

    total = len(filtered)
    total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    page = st.session_state.get("cat_page", 1)
    page = min(max(1, page), total_pages)
    st.session_state["cat_page"] = page

    st.markdown(
        f'<p class="muted">{total:,} item{"s" if total != 1 else ""} · page {page} of {total_pages}</p>',
        unsafe_allow_html=True,
    )

    if total == 0:
        st.markdown(
            '<div class="card"><p class="muted">No items match these filters. Try clearing them.</p></div>',
            unsafe_allow_html=True,
        )
        return

    # ---------- grid ----------
    start = (page - 1) * PAGE_SIZE
    chunk = filtered.iloc[start: start + PAGE_SIZE]

    # Prefetch images for everything we're about to render (~24 items max).
    # The disk cache means subsequent pages reuse images, so as the user
    # paginates the cache warms incrementally.
    prefetch_items = [chunk.iloc[i].to_dict() for i in range(len(chunk))]
    if prefetch_items:
        with st.spinner(f"Fetching product images ({len(prefetch_items)} items)…"):
            shared.prefetch_images_sync(prefetch_items, timeout=14.0)

    rows = (len(chunk) + 2) // 3
    for r in range(rows):
        cols = st.columns(3, gap="small")
        for ci, col in enumerate(cols):
            idx = r * 3 + ci
            if idx >= len(chunk):
                break
            item = chunk.iloc[idx].to_dict()
            with col:
                shared.render_catalogue_card(
                    item, key_prefix=f"cat_p{page}_r{r}_c{ci}",
                    user_id=user["id"], saved_set=saved_set,
                )

    # ---------- pagination controls ----------
    if total_pages > 1:
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        col_p1, _, col_p2 = st.columns([1, 2, 1])
        with col_p1:
            if st.button("← Previous", disabled=(page == 1), use_container_width=True, key="cat_prev"):
                st.session_state["cat_page"] = max(1, page - 1)
                st.rerun()
        with col_p2:
            if st.button("Next →", disabled=(page == total_pages), use_container_width=True, key="cat_next"):
                st.session_state["cat_page"] = min(total_pages, page + 1)
                st.rerun()


main()
