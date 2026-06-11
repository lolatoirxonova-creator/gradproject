"""Catalogue browse — search, filters (in a modal), tags, paginated grid.

Cosmetics mode (Barakaly): all facet filters live behind one "Filters" button
that opens a modal (men/women/kids tags + category, brand, type, quality, size,
made-in, shade, price), with Clear / Apply / Close. Filter state is kept in
non-widget `f_*` session keys so it survives reruns and home shortcuts. H&M mode
keeps the original inline fashion filters. Clicking a card opens its detail page.
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

# Persistent (non-widget) filter state — survives reruns + set by home shortcuts.
FILTER_DEFAULTS = {
    "f_tag": "All", "f_category": "All", "f_brand": [], "f_type": [],
    "f_quality": [], "f_size": [], "f_made": [], "f_shade": [], "f_price": None,
}
TAGS = ["All", "Women", "Men", "Kids"]


def _opts(series):
    return sorted({str(v) for v in series.dropna() if str(v).strip() and str(v) != "—"})


def _multiselect(label, series, key):
    st.markdown(f'<div class="field-label">{label}</div>', unsafe_allow_html=True)
    return st.multiselect(label, _opts(series), label_visibility="collapsed",
                          placeholder=f"All {label.lower()}", key=key)


def _fget(key):
    return st.session_state.get(key, FILTER_DEFAULTS[key])


# ---------------------------------------------------------------- cosmetics
def _price_bounds(articles):
    eff = [shared.effective_price(a) for a in articles["article_id"].astype(str)]
    eff = [v for v in eff if v] or [0.0, 1.0]
    return float(int(min(eff))), float(int(max(eff)) + 1)


def _active_count():
    n = 0
    if _fget("f_tag") != "All":
        n += 1
    if _fget("f_category") != "All":
        n += 1
    for k in ("f_brand", "f_type", "f_quality", "f_size", "f_made", "f_shade"):
        if _fget(k):
            n += 1
    if _fget("f_price") is not None:
        n += 1
    return n


def _cosmetics_apply(articles):
    """Filter the catalogue from the persistent f_* state + inline search."""
    df = articles
    tag, cat = _fget("f_tag"), _fget("f_category")
    if tag == "Women":
        df = df[df["index_group_name"].isin(["Women", "Unisex"])]
    elif tag == "Men":
        df = df[df["index_group_name"].isin(["Men", "Unisex"])]
    elif tag == "Kids":
        df = df[df["index_group_name"] == "Kids"]
    if cat != "All":
        df = df[df["category"] == cat]
    for key, col in [("f_brand", "brand"), ("f_type", "product_type_name"),
                     ("f_quality", "quality"), ("f_made", "made_in"),
                     ("f_shade", "colour_group_name"), ("f_size", "size")]:
        vals = _fget(key)
        if vals:
            df = df[df[col].astype(str).isin([str(v) for v in vals])]
    q = st.session_state.get("cat_search", "").strip().lower()
    if q:
        df = df[df["prod_name"].fillna("").str.lower().str.contains(q, regex=False)
                | df["detail_desc"].fillna("").str.lower().str.contains(q, regex=False)
                | df["brand"].fillna("").str.lower().str.contains(q, regex=False)]
    price = _fget("f_price")
    if price is not None:
        eff = {a: shared.effective_price(a) for a in df["article_id"].astype(str)}
        df = df[df["article_id"].astype(str).map(eff).between(price[0], price[1])]
    return df


@st.dialog("Filters", width="large")
def _cosmetics_filter_dialog(articles, lo, hi):
    """All facet filters in one modal (#10). Widgets use w_* keys seeded from the
    persistent f_* state; Apply commits w_* → f_*."""
    # seed widget state from the committed filters (only when absent)
    seeds = {"w_tag": _fget("f_tag"), "w_category": _fget("f_category"),
             "w_brand": _fget("f_brand"), "w_type": _fget("f_type"),
             "w_quality": _fget("f_quality"), "w_size": _fget("f_size"),
             "w_made": _fget("f_made"), "w_shade": _fget("f_shade"),
             "w_price": _fget("f_price") or (lo, hi)}
    for k, v in seeds.items():
        st.session_state.setdefault(k, v)

    st.markdown('<div class="field-label">Shop for</div>', unsafe_allow_html=True)
    st.radio("Shop for", TAGS, horizontal=True, label_visibility="collapsed", key="w_tag")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="field-label">Category</div>', unsafe_allow_html=True)
        st.selectbox("Category", ["All", *_opts(articles["category"])],
                     label_visibility="collapsed", key="w_category")
    with c2:
        _multiselect("Brand", articles["brand"], "w_brand")

    cat = st.session_state.get("w_category", "All")
    scope = articles if cat == "All" else articles[articles["category"] == cat]
    f1, f2, f3 = st.columns(3)
    with f1:
        _multiselect("Type", scope["product_type_name"], "w_type")
    with f2:
        _multiselect("Quality", articles["quality"], "w_quality")
    with f3:
        _multiselect("Size", articles["size"], "w_size")
    g1, g2 = st.columns(2)
    with g1:
        _multiselect("Made in", articles["made_in"], "w_made")
    with g2:
        _multiselect("Shade", articles["colour_group_name"], "w_shade")

    st.markdown('<div class="field-label">Price ($)</div>', unsafe_allow_html=True)
    st.slider("Price", min_value=lo, max_value=hi, step=1.0,
              label_visibility="collapsed", key="w_price")

    st.markdown('<div class="divider" style="margin:1rem 0 !important;"></div>', unsafe_allow_html=True)
    b1, b2, b3 = st.columns(3)
    if b1.button("Clear all", use_container_width=True, key="flt_clear"):
        for k, v in FILTER_DEFAULTS.items():
            st.session_state[k] = v
        for wk in list(seeds):
            st.session_state.pop(wk, None)
        st.session_state["cat_page"] = 1
        st.rerun()
    if b2.button("Close", use_container_width=True, key="flt_close"):
        for wk in list(seeds):
            st.session_state.pop(wk, None)  # discard un-applied edits
        st.rerun()
    if b3.button("Apply filter", type="primary", use_container_width=True, key="flt_apply"):
        st.session_state["f_tag"] = st.session_state["w_tag"]
        st.session_state["f_category"] = st.session_state["w_category"]
        st.session_state["f_brand"] = st.session_state["w_brand"]
        st.session_state["f_type"] = st.session_state["w_type"]
        st.session_state["f_quality"] = st.session_state["w_quality"]
        st.session_state["f_size"] = st.session_state["w_size"]
        st.session_state["f_made"] = st.session_state["w_made"]
        st.session_state["f_shade"] = st.session_state["w_shade"]
        price = st.session_state["w_price"]
        st.session_state["f_price"] = None if tuple(price) == (lo, hi) else tuple(price)
        st.session_state["cat_page"] = 1
        st.rerun()


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
    shared.scroll_to_top_if_flagged()

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
    sub = ("Search, or open Filters for category, brand, quality, size, made-in, shade, "
           "price and audience." if cosmetics
           else "Search by name, filter by department / type / colour / price.")
    st.markdown(f'<p class="subtitle">{len(articles)} products. {sub}</p>', unsafe_allow_html=True)

    if cosmetics:
        lo, hi = _price_bounds(articles)
        # inline search + a single Filters button that opens the modal (#10)
        s1, s2 = st.columns([4, 1])
        with s1:
            st.text_input("Search", placeholder="Search — e.g. serum, lipstick, perfume",
                          label_visibility="collapsed", key="cat_search")
        with s2:
            n = _active_count()
            if st.button(f"⚙  Filters ({n})" if n else "⚙  Filters",
                         use_container_width=True, key="open_filters"):
                _cosmetics_filter_dialog(articles, lo, hi)
        if _active_count() or st.session_state.get("cat_search", "").strip():
            if st.button("✕  Clear filters", key="clear_inline"):
                for k, v in FILTER_DEFAULTS.items():
                    st.session_state[k] = v
                st.session_state["cat_search"] = ""
                st.session_state["cat_page"] = 1
                st.rerun()
        filtered = _cosmetics_apply(articles)
        sig = (_fget("f_tag"), _fget("f_category"), tuple(_fget("f_brand")), tuple(_fget("f_type")),
               tuple(_fget("f_quality")), tuple(_fget("f_size")), tuple(_fget("f_made")),
               tuple(_fget("f_shade")), _fget("f_price"), st.session_state.get("cat_search", ""))
    else:
        filtered, sig = _hm_filter_ui(articles)

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
