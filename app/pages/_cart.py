"""Shopping cart — review items, adjust quantities, proceed to checkout.

Hidden from the default nav (underscore prefix); registered in main.py's
st.navigation as "Cart" for shopping roles (customer / analyst).
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

    st.markdown('<div class="pill">Cart</div>', unsafe_allow_html=True)
    st.markdown("<h1>Your cart.</h1>", unsafe_allow_html=True)

    lines = db.get_cart(user["id"])
    if not lines:
        st.markdown('<p class="subtitle">Your cart is empty. Add items from the catalogue '
                    'or a product page to get started.</p>', unsafe_allow_html=True)
        if st.button("Browse catalogue", type="primary"):
            st.switch_page("pages/1_Catalogue.py")
        return

    articles = shared.load_articles()
    prices = shared.load_article_prices()
    by_id = articles.set_index("article_id")

    # prefetch images for cart items
    prefetch = [by_id.loc[l["article_id"]].to_dict() | {"article_id": l["article_id"]}
                for l in lines if l["article_id"] in by_id.index]
    if prefetch:
        with st.spinner("Loading your cart…"):
            shared.prefetch_images_sync(prefetch, timeout=12.0)

    st.markdown(f'<p class="subtitle">{len(lines)} '
                f'line{"s" if len(lines) != 1 else ""} in your cart.</p>', unsafe_allow_html=True)

    subtotal = 0.0
    for _i, line in enumerate(lines):
        aid, qty = line["article_id"], line["quantity"]
        if aid not in by_id.index:
            continue
        if _i:  # delicate separator between cart lines (they were too close)
            st.markdown('<div style="border-top:1px solid var(--border);margin:20px 0;"></div>',
                        unsafe_allow_html=True)
        item = by_id.loc[aid].to_dict()
        item["article_id"] = aid
        price = shared.display_price(aid, prices)
        line_total = round(price * qty, 2)
        subtotal += line_total

        c_img, c_name, c_qty, c_tot, c_rm = st.columns([1, 3.2, 2, 1.3, 0.8])
        with c_img:
            st.markdown(
                f'<img src="{shared._resolve_image_src(aid, item)}" '
                f'style="width:100%;aspect-ratio:1/1;object-fit:cover;border-radius:12px;">',
                unsafe_allow_html=True,
            )
        with c_name:
            st.markdown(
                f"**{item.get('prod_name') or aid}**  \n"
                f"<span class='muted'>{item.get('product_type_name') or ''} · "
                f"{item.get('colour_group_name') or ''}</span>  \n${price:,.2f} each",
                unsafe_allow_html=True,
            )
        with c_qty:
            m, qd, p = st.columns(3)
            if m.button("−", key=f"cart_minus_{aid}", use_container_width=True):
                db.set_cart_qty(user["id"], aid, qty - 1)
                st.rerun()
            qd.markdown(f"<div style='text-align:center;padding-top:6px;font-weight:600;'>{qty}</div>",
                        unsafe_allow_html=True)
            if p.button("+", key=f"cart_plus_{aid}", use_container_width=True):
                db.set_cart_qty(user["id"], aid, qty + 1)
                st.rerun()
        with c_tot:
            st.markdown(f"<div style='padding-top:6px;font-weight:600;'>${line_total:,.2f}</div>",
                        unsafe_allow_html=True)
        with c_rm:
            if st.button("", icon=":material/delete:", key=f"cart_rm_{aid}",
                         use_container_width=True, help="Remove"):
                db.remove_from_cart(user["id"], aid)
                st.rerun()

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    s1, s2 = st.columns([3, 2])
    with s2:
        st.markdown(f"<h2 style='margin-top:0 !important;'>Subtotal: ${subtotal:,.2f}</h2>",
                    unsafe_allow_html=True)
        st.markdown('<p class="muted">Shipping & taxes calculated at checkout.</p>',
                    unsafe_allow_html=True)
        if st.button("Proceed to checkout →", type="primary", use_container_width=True):
            st.switch_page("pages/_checkout.py")


main()
