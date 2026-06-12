"""Product comparison (Asaxiy-style) — selected products side-by-side by spec.

Items are added via the ⚖ button on cards / the product page (session-scoped,
up to shared.COMPARE_MAX). Public — works for guests too.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

import streamlit as st

from app import db, shared

# (label, dataframe column) — None column => computed (price / rating)
ATTRS = [
    ("Price", None), ("Rating", None), ("Brand", "brand"), ("Category", "category"),
    ("Type", "product_type_name"), ("For", "index_group_name"), ("Shade", "colour_group_name"),
    ("Size", "size"), ("Quality", "quality"), ("Made in", "made_in"),
]


def main():
    shared.check_session_timeout()
    user = st.session_state.get("user")  # public — guests can compare too

    shared.apply_css()
    shared.render_sidebar(user)

    st.markdown('<div class="pill">Compare</div>', unsafe_allow_html=True)
    st.markdown("<h1>Compare products.</h1>", unsafe_allow_html=True)

    ids = shared.compare_ids()
    if not ids:
        st.markdown('<p class="subtitle">Nothing to compare yet. Tap the compare button on any '
                    'product (catalogue, home, or a product page) to add it here — up to '
                    f'{shared.COMPARE_MAX} items.</p>', unsafe_allow_html=True)
        if st.button("Browse catalogue", type="primary"):
            st.switch_page("views/1_Catalogue.py")
        return

    articles = shared.load_articles()
    by_id = articles.set_index("article_id")
    ids = [a for a in ids if a in by_id.index]

    st.markdown(f'<p class="muted">{len(ids)} of {shared.COMPARE_MAX} items · scroll down for the full spec comparison.</p>',
                unsafe_allow_html=True)
    # Big product images filled horizontally across the page, centred (#11). A
    # narrow leading gutter keeps them aligned with the spec value columns below.
    gutter = 0.5
    head = st.columns([gutter] + [2] * len(ids), gap="large")
    for i, aid in enumerate(ids):
        item = by_id.loc[aid]
        with head[i + 1]:
            st.markdown(
                f'<img src="{shared._resolve_image_src(aid, item.to_dict())}" '
                f'style="width:100%;aspect-ratio:1/1;object-fit:cover;border-radius:16px;'
                f'box-shadow:var(--shadow-2);">',
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<p style='text-align:center;font-weight:600;font-size:16px;margin:12px 0 8px;'>"
                f"{item.get('prod_name') or aid}</p>",
                unsafe_allow_html=True,
            )
            if st.button("Remove", icon=":material/close:", key=f"cmp_rm_{aid}", use_container_width=True):
                shared.toggle_compare(aid)
                st.rerun()

    def _value(label, aid):
        item = by_id.loc[aid]
        if label == "Price":
            reg, sale = shared.catalogue_price(aid)
            return (f"<s style='color:var(--muted);'>{shared.money(reg)}</s> "
                    f"<b style='color:var(--accent-2);'>{shared.money(sale)}</b>") if sale else f"<b>{shared.money(reg)}</b>"
        if label == "Rating":
            s = db.review_summary(aid)
            if not s["count"]:
                return "—"
            full = int(round(s["avg"]))
            return f"<span style='color:var(--accent);'>{'★' * full}{'☆' * (5 - full)}</span> {s['avg']}"
        col = dict(ATTRS)[label]
        v = item.get(col)
        return "—" if v is None or str(v).strip() in ("", "nan", "—") else str(v)

    for label, _col in ATTRS:
        st.markdown('<div style="border-top:1px solid var(--border);"></div>', unsafe_allow_html=True)
        row = st.columns([0.5] + [2] * len(ids), gap="large")
        row[0].markdown(f'<p style="color:var(--muted);font-weight:600;font-size:12px;padding:10px 0;">{label}</p>',
                        unsafe_allow_html=True)
        for i, aid in enumerate(ids):
            row[i + 1].markdown(f'<p style="padding:10px 0;font-size:14px;text-align:center;">{_value(label, aid)}</p>',
                                unsafe_allow_html=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    if st.button("Clear comparison", key="cmp_clear"):
        shared.clear_compare()
        st.rerun()


main()
