"""Catalogue browse — search, filters, tags, paginated grid.

Cosmetics mode (Chiroyli): men/women/children tags + filters on category, brand,
quality, size, made-in, shade and price. H&M mode keeps the original fashion
filters. Clicking View on any card opens the product detail page.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

import streamlit as st

from app import db, shared

PAGE_SIZE = 24
PRICE_DISPLAY_SCALE = 1000.0  # H&M-normalised price → $ (fashion mode only)


def _opts(series):
    return sorted({str(v) for v in series.dropna() if str(v).strip() and str(v) != "—"})


def _multiselect(label, series, key):
    st.markdown(f'<div class="field-label">{label}</div>', unsafe_allow_html=True)
    return st.multiselect(label, _opts(series), label_visibility="collapsed",
                          placeholder=f"All {label.lower()}", key=key)


# ---------------------------------------------------------------- cosmetics
def _cosmetics_filter_ui(articles):
    """Render search + audience tags + cosmetics filters; return (filtered_df, signature)."""
    st.markdown('<div class="field-label">Search</div>', unsafe_allow_html=True)
    query = st.text_input("Search", placeholder="e.g. serum, lipstick, perfume",
                          label_visibility="collapsed", key="cat_query")

    # men / women / children tags (#8)
    st.markdown('<div class="field-label">Shop for</div>', unsafe_allow_html=True)
    tag = st.radio("Shop for", ["All", "Women", "Men", "Kids"], horizontal=True,
                   label_visibility="collapsed", key="cat_tag")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="field-label">Category</div>', unsafe_allow_html=True)
        category = st.selectbox("Category", ["All", *_opts(articles["category"])],
                                label_visibility="collapsed", key="cat_category")
    with c2:
        brands = _multiselect("Brand", articles["brand"], "cat_brand")

    with st.expander("More filters — type, quality, size, made-in, shade"):
        scope = articles if category == "All" else articles[articles["category"] == category]
        f1, f2, f3 = st.columns(3)
        with f1:
            types = _multiselect("Type", scope["product_type_name"], "cat_type")
        with f2:
            qualities = _multiselect("Quality", articles["quality"], "cat_quality")
        with f3:
            sizes = _multiselect("Size", articles["size"], "cat_size")
        g1, g2 = st.columns(2)
        with g1:
            made_ins = _multiselect("Made in", articles["made_in"], "cat_made")
        with g2:
            shades = _multiselect("Shade", articles["colour_group_name"], "cat_shade")

    # price slider over effective (sale-aware) prices
    eff = {a: shared.effective_price(a) for a in articles["article_id"].astype(str)}
    vals = [v for v in eff.values() if v] or [0.0, 1.0]
    lo_v, hi_v = float(min(vals)), float(max(vals))
    st.markdown('<div class="field-label">Price ($)</div>', unsafe_allow_html=True)
    price_range = st.slider("Price", min_value=float(int(lo_v)), max_value=float(int(hi_v) + 1),
                            value=(float(int(lo_v)), float(int(hi_v) + 1)), step=1.0,
                            label_visibility="collapsed", key="cat_price")

    # ---- filter ----
    df = articles
    if tag == "Women":
        df = df[df["index_group_name"].isin(["Women", "Unisex"])]
    elif tag == "Men":
        df = df[df["index_group_name"].isin(["Men", "Unisex"])]
    elif tag == "Kids":
        df = df[df["index_group_name"] == "Kids"]
    if category != "All":
        df = df[df["category"] == category]
    if types:
        df = df[df["product_type_name"].isin(types)]
    if brands:
        df = df[df["brand"].isin(brands)]
    if qualities:
        df = df[df["quality"].isin(qualities)]
    if sizes:
        df = df[df["size"].astype(str).isin(sizes)]
    if made_ins:
        df = df[df["made_in"].isin(made_ins)]
    if shades:
        df = df[df["colour_group_name"].isin(shades)]
    if query.strip():
        q = query.strip().lower()
        df = df[df["prod_name"].fillna("").str.lower().str.contains(q, regex=False)
                | df["detail_desc"].fillna("").str.lower().str.contains(q, regex=False)
                | df["brand"].fillna("").str.lower().str.contains(q, regex=False)]
    df = df[df["article_id"].astype(str).map(eff).between(price_range[0], price_range[1])]

    sig = (query.strip().lower(), tag, category, tuple(types), tuple(brands),
           tuple(qualities), tuple(sizes), tuple(made_ins), tuple(shades), price_range)
    return df, sig


# ---------------------------------------------------------------- H&M (legacy)
def _hm_filter_ui(articles):
    st.markdown('<div class="field-label">Search</div>', unsafe_allow_html=True)
    query = st.text_input("Search", placeholder="e.g. denim, t-shirt, summer dress",
                          label_visibility="collapsed", key="cat_query")
    index_groups = _opts(articles["index_group_name"])
    c1, c2 = st.columns([1, 2])
    with c1:
        st.markdown('<div class="field-label">Department</div>', unsafe_allow_html=True)
        index_group = st.selectbox("Department", ["All", *index_groups],
                                   label_visibility="collapsed", key="cat_index_group")
    with c2:
        scope = articles if index_group == "All" else articles[articles["index_group_name"] == index_group]
        types = _multiselect("Product type", scope["product_type_name"], "cat_product_types")
    colours = _multiselect("Colour", articles["perceived_colour_master_name"], "cat_colours")
    price_series = shared.load_article_prices()
    raw_lo = float(price_series.min()) if len(price_series) else 0.0
    raw_hi = float(price_series.quantile(0.99)) if len(price_series) else 1.0
    disp_lo = max(1.0, raw_lo * PRICE_DISPLAY_SCALE)
    disp_hi = max(disp_lo + 1.0, raw_hi * PRICE_DISPLAY_SCALE)
    st.markdown('<div class="field-label">Price (approx. $)</div>', unsafe_allow_html=True)
    price_range = st.slider("Price", min_value=float(round(disp_lo)), max_value=float(round(disp_hi)),
                            value=(float(round(disp_lo)), float(round(disp_hi))), step=1.0,
                            label_visibility="collapsed", key="cat_price")
    df = articles
    if index_group != "All":
        df = df[df["index_group_name"] == index_group]
    if types:
        df = df[df["product_type_name"].isin(types)]
    if colours:
        df = df[df["perceived_colour_master_name"].isin(colours)]
    if query.strip():
        q = query.strip().lower()
        df = df[df["prod_name"].fillna("").str.lower().str.contains(q, regex=False)
                | df["detail_desc"].fillna("").str.lower().str.contains(q, regex=False)]
    lo, hi = price_range[0] / PRICE_DISPLAY_SCALE, price_range[1] / PRICE_DISPLAY_SCALE
    mapped = df["article_id"].map(price_series)
    df = df[mapped.between(lo, hi, inclusive="both") | mapped.isna()]
    sig = (query.strip().lower(), index_group, tuple(types), tuple(colours), price_range)
    return df, sig


def main():
    shared.check_session_timeout()
    user = st.session_state.get("user")  # may be None — catalogue is public (#2)

    shared.apply_css()
    shared.render_sidebar(user)

    cosmetics = shared.cosmetics_mode()
    articles = shared.load_articles()
    curated = shared.curated_set()
    if curated:
        articles = articles[articles["article_id"].isin(curated)]
    if user is not None:
        state = db.user_state(user["id"])
        saved_set = set(state["saved"])
        cart_set = {l["article_id"] for l in db.get_cart(user["id"])}
        uid = user["id"]
    else:
        saved_set, cart_set, uid = set(), set(), None

    st.markdown('<div class="pill">Catalogue</div>', unsafe_allow_html=True)
    st.markdown("<h1>Browse the catalogue.</h1>", unsafe_allow_html=True)
    sub = ("Filter by category, brand, quality, size, made-in, shade and price — "
           "and shop for women, men or kids." if cosmetics
           else "Search by name, filter by department / type / colour / price.")
    st.markdown(f'<p class="subtitle">{len(articles)} products. {sub}</p>', unsafe_allow_html=True)

    filtered, sig = (_cosmetics_filter_ui(articles) if cosmetics else _hm_filter_ui(articles))

    if st.session_state.get("cat_filter_signature") != sig:
        st.session_state["cat_filter_signature"] = sig
        st.session_state["cat_page"] = 1

    total = len(filtered)
    total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    page = min(max(1, st.session_state.get("cat_page", 1)), total_pages)
    st.session_state["cat_page"] = page

    st.markdown(f'<p class="muted">{total:,} item{"s" if total != 1 else ""} · '
                f'page {page} of {total_pages}</p>', unsafe_allow_html=True)
    if total == 0:
        st.markdown('<div class="card"><p class="muted">No items match these filters. '
                    'Try clearing them.</p></div>', unsafe_allow_html=True)
        return

    chunk = filtered.iloc[(page - 1) * PAGE_SIZE: (page - 1) * PAGE_SIZE + PAGE_SIZE]
    if not cosmetics:  # cosmetics images are local (Tier 0) — no remote prefetch
        items = [chunk.iloc[i].to_dict() for i in range(len(chunk))]
        if items:
            with st.spinner(f"Fetching product images ({len(items)} items)…"):
                shared.prefetch_images_sync(items, timeout=14.0)

    rows = (len(chunk) + 2) // 3
    for r in range(rows):
        cols = st.columns(3, gap="small")
        for ci, col in enumerate(cols):
            idx = r * 3 + ci
            if idx >= len(chunk):
                break
            with col:
                shared.render_catalogue_card(
                    chunk.iloc[idx].to_dict(), key_prefix=f"cat_p{page}_r{r}_c{ci}",
                    user_id=uid, saved_set=(saved_set if uid else None), cart_set=cart_set,
                )

    if total_pages > 1:
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        p1, _, p2 = st.columns([1, 2, 1])
        with p1:
            if st.button("← Previous", disabled=(page == 1), use_container_width=True, key="cat_prev"):
                st.session_state["cat_page"] = max(1, page - 1)
                st.rerun()
        with p2:
            if st.button("Next →", disabled=(page == total_pages), use_container_width=True, key="cat_next"):
                st.session_state["cat_page"] = min(total_pages, page + 1)
                st.rerun()


main()
