"""Seller panel (#13) — sellers list and manage their own products and see the
orders placed for them. New listings are persisted to `seller_products` and
unioned into the live catalogue (see shared.load_cosmetics); editing a listing
flushes the cached catalogue so changes show immediately.

Reached only by the `seller` role (st.navigation routes sellers here exclusively).
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

import streamlit as st

from app import db, shared

AUDIENCES = ["Women", "Men", "Unisex", "Kids"]
QUALITIES = ["Standard", "Premium", "Luxury"]
FALLBACK_CATEGORIES = ["Skincare", "Makeup", "Fragrance", "Hair & body"]


def _category_options():
    try:
        cats = sorted({str(c) for c in shared.load_cosmetics()["category"].dropna()})
    except Exception:
        cats = []
    return cats or FALLBACK_CATEGORIES


def _product_form(key: str, defaults: dict | None = None, submit_label: str = "Save"):
    """Render a product form. Returns a validated data dict on submit, else None."""
    d = defaults or {}
    cats = _category_options()

    def _idx(options, value, fallback=0):
        return options.index(value) if value in options else fallback

    with st.form(key, clear_on_submit=(defaults is None)):
        c1, c2 = st.columns(2)
        with c1:
            prod_name = st.text_input("Product name *", value=d.get("prod_name", ""),
                                      key=f"{key}_name")
            brand = st.text_input("Brand", value=d.get("brand", ""), key=f"{key}_brand")
            category = st.selectbox("Category", cats,
                                    index=_idx(cats, d.get("category")), key=f"{key}_cat")
            product_type = st.text_input("Product type (e.g. Serum, Lipstick)",
                                         value=d.get("product_type_name", ""), key=f"{key}_type")
            audience = st.selectbox("For", AUDIENCES,
                                    index=_idx(AUDIENCES, d.get("index_group_name"), 2),
                                    key=f"{key}_aud")
        with c2:
            quality = st.selectbox("Quality", QUALITIES,
                                   index=_idx(QUALITIES, d.get("quality")), key=f"{key}_qual")
            shade = st.text_input("Shade / colour", value=d.get("colour_group_name", ""),
                                  key=f"{key}_shade")
            size = st.text_input("Size (e.g. 50ml)", value=str(d.get("size") or ""),
                                 key=f"{key}_size")
            made_in = st.text_input("Made in", value=d.get("made_in", ""), key=f"{key}_made")
        p1, p2 = st.columns(2)
        with p1:
            price = st.number_input("Price ($) *", min_value=0.0, step=1.0,
                                    value=float(d.get("price") or 0.0), key=f"{key}_price")
        with p2:
            sale_raw = d.get("sale_price")
            sale_price = st.number_input("Sale price ($) — 0 for none", min_value=0.0, step=1.0,
                                         value=float(sale_raw or 0.0), key=f"{key}_sale")
        image_url = st.text_input("Image URL (https://… or leave blank)",
                                  value=d.get("image_url") or "", key=f"{key}_img")
        detail_desc = st.text_area("Description", value=d.get("detail_desc", ""),
                                   key=f"{key}_desc", height=80)
        submitted = st.form_submit_button(submit_label, type="primary", use_container_width=True)

    if not submitted:
        return None
    if not prod_name.strip():
        st.error("Product name is required.")
        return None
    if price <= 0:
        st.error("Price must be greater than 0.")
        return None
    sale = float(sale_price) if sale_price and sale_price < price else None
    if sale_price and sale_price >= price:
        st.warning("Sale price must be below the regular price — ignored.")
    return {
        "prod_name": prod_name.strip(), "brand": brand.strip() or None,
        "category": category, "product_type_name": product_type.strip() or None,
        "index_group_name": audience, "colour_group_name": shade.strip() or None,
        "quality": quality, "size": size.strip() or None, "made_in": made_in.strip() or None,
        "price": round(float(price), 2), "sale_price": (round(sale, 2) if sale else None),
        "detail_desc": detail_desc.strip() or None,
        "image_url": image_url.strip() or None,
    }


def main():
    shared.check_session_timeout()
    user = st.session_state.get("user")
    shared.apply_css()
    shared.render_sidebar(user)

    if user is None or user.get("role") != "seller":
        st.markdown("<h1>Seller panel.</h1>", unsafe_allow_html=True)
        st.warning("This area is for seller accounts only.")
        return

    sid = user["id"]
    st.markdown('<div class="pill">Seller</div>', unsafe_allow_html=True)
    st.markdown("<h1>Your shop.</h1>", unsafe_allow_html=True)

    stats = db.seller_stats(sid)
    m = st.columns(4)
    m[0].metric("Products", stats["products"])
    m[1].metric("Active", stats["active"])
    m[2].metric("Units sold", stats["units_sold"])
    m[3].metric("Revenue", f"${stats['revenue']:,.2f}")

    tab_list, tab_add, tab_orders = st.tabs(["My products", "Add product", "Orders"])

    # ---------------- add ----------------
    with tab_add:
        st.markdown('<p class="muted">New listings appear in the catalogue immediately.</p>',
                    unsafe_allow_html=True)
        data = _product_form("seller_add", submit_label="Add product")
        if data:
            aid = db.add_seller_product(sid, data)
            shared.refresh_catalogue()
            st.success(f"Added “{data['prod_name']}” ({aid}).")
            st.rerun()

    # ---------------- list / edit ----------------
    with tab_list:
        products = db.list_seller_products(sid)
        if not products:
            st.markdown('<div class="card"><p class="muted">No products yet — add your first '
                        'in the “Add product” tab.</p></div>', unsafe_allow_html=True)
        for p in products:
            aid = p["article_id"]
            reg, sale = shared.catalogue_price(aid)
            # &#36; (HTML entity) not a literal `$` — two bare $ on a line trip LaTeX math.
            price_txt = (f"<s style='color:var(--muted)'>&#36;{reg:,.2f}</s> "
                         f"<b style='color:var(--accent-2)'>&#36;{sale:,.2f}</b>"
                         if sale else f"<b>&#36;{reg:,.2f}</b>")
            badge = "🟢 Active" if p["active"] else "⚪ Hidden"
            with st.container(border=True):
                top = st.columns([3, 1])
                top[0].markdown(f"<b>{p['prod_name']}</b> · {price_txt}<br>"
                                f"<span class='muted'>{aid} · {p.get('category') or '—'} · "
                                f"{p.get('brand') or '—'} · {badge}</span>",
                                unsafe_allow_html=True)
                with top[1]:
                    if st.button(("Hide" if p["active"] else "Show"),
                                 key=f"toggle_{aid}", use_container_width=True):
                        db.set_seller_product_active(aid, sid, not p["active"])
                        shared.refresh_catalogue()
                        st.rerun()
                with st.expander("Edit"):
                    edited = _product_form(f"edit_{aid}", defaults=p, submit_label="Save changes")
                    if edited:
                        db.update_seller_product(aid, sid, edited)
                        shared.refresh_catalogue()
                        st.success("Saved.")
                        st.rerun()
                    if st.button("🗑 Delete permanently", key=f"del_{aid}"):
                        db.delete_seller_product(aid, sid)
                        shared.refresh_catalogue()
                        st.rerun()

    # ---------------- orders ----------------
    with tab_orders:
        orders = db.seller_orders(sid)
        if not orders:
            st.markdown('<div class="card"><p class="muted">No orders for your products yet.</p>'
                        '</div>', unsafe_allow_html=True)
        else:
            import pandas as pd
            df = pd.DataFrame(orders)
            df["line total"] = (df["quantity"] * df["unit_price"]).round(2)
            df["kind"] = df["status"].map(lambda s: "Offline pickup" if s == "offline" else "Online")
            show = df.rename(columns={
                "order_id": "Order", "created_at": "Placed", "buyer": "Buyer",
                "prod_name": "Product", "quantity": "Qty", "unit_price": "Unit $",
            })[["Order", "Placed", "Buyer", "Product", "Qty", "Unit $", "line total", "kind"]]
            st.dataframe(show, use_container_width=True, hide_index=True)


main()
