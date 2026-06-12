"""Checkout — shipping details + (mock) payment, then place the order.

Payment is SIMULATED: no real gateway, no charge. Fields are validated for
shape only. On submit we create an order, log purchases, clear the cart, and
route to the success page.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

import streamlit as st

from app import db, shared

SHIP_FLAT = 4.99  # flat demo shipping


def _validate(f: dict) -> dict:
    """Return {field_key: message} for invalid fields (empty dict = all valid)."""
    errs = {}
    for key, label in [("co_name", "Full name"), ("co_addr", "Address"),
                       ("co_city", "City"), ("co_postal", "Postal code"),
                       ("co_cardname", "Name on card")]:
        if not str(f.get(key, "")).strip():
            errs[key] = f"{label} is required"
    if not (12 <= len(re.sub(r"\D", "", f.get("co_card", ""))) <= 19):
        errs["co_card"] = "Enter a valid card number (12–19 digits)"
    if not re.fullmatch(r"(0[1-9]|1[0-2])\s*/\s*\d{2}", str(f.get("co_exp", "")).strip()):
        errs["co_exp"] = "Use MM/YY"
    if not re.fullmatch(r"\d{3,4}", str(f.get("co_cvc", "")).strip()):
        errs["co_cvc"] = "3–4 digits"
    return errs


def _field_err(key: str, errors: dict) -> None:
    if key in errors:
        st.markdown(f'<p class="field-err">{errors[key]}</p>', unsafe_allow_html=True)


def main():
    shared.check_session_timeout()
    user = st.session_state.get("user")
    if user is None:
        st.warning("Please log in from the home page first.")
        st.stop()

    shared.apply_css()
    shared.render_sidebar(user)

    lines = db.get_cart(user["id"])
    if not lines:
        st.markdown('<div class="pill">Checkout</div>', unsafe_allow_html=True)
        st.markdown("<h1>Your cart is empty.</h1>", unsafe_allow_html=True)
        if st.button("Browse catalogue", type="primary"):
            st.switch_page("views/1_Catalogue.py")
        return

    articles = shared.load_articles()
    prices = shared.load_article_prices()
    by_id = articles.set_index("article_id")

    items = []           # (article_id, qty, unit_price)
    subtotal = 0.0
    for line in lines:
        aid, qty = line["article_id"], line["quantity"]
        if aid not in by_id.index:
            continue
        price = shared.display_price(aid, prices)
        items.append((aid, qty, price))
        subtotal += price * qty
    total = round(subtotal + SHIP_FLAT, 2)

    st.markdown('<div class="pill">Checkout</div>', unsafe_allow_html=True)
    st.markdown("<h1>Checkout.</h1>", unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Demo checkout — payment is simulated, no card is charged.</p>',
                unsafe_allow_html=True)

    # seed name fields so we can key them (keyed widgets read from session_state)
    st.session_state.setdefault("co_name", user.get("display_name", ""))
    st.session_state.setdefault("co_cardname", user.get("display_name", ""))
    st.session_state.setdefault("co_country", "Uzbekistan")

    errors = st.session_state.get("checkout_errors", {})
    # Inline validation styling: red border + halo on each invalid field.
    border_css = "".join(
        f'.st-key-{k} [data-baseweb="input"], .st-key-{k} [data-baseweb="base-input"], .st-key-{k} input '
        f'{{ border-color:#e8462a !important; box-shadow:0 0 0 3px rgba(232,70,42,.14) !important; }}'
        for k in errors
    )
    st.markdown(f"<style>{border_css} .field-err{{color:#e8462a;font-size:12px;font-weight:500;"
                f"margin:-8px 0 10px 2px;}}</style>", unsafe_allow_html=True)

    left, right = st.columns([3, 2])

    with left:
        with st.form("checkout_form"):
            st.markdown("**Shipping**")
            st.text_input("Full name", key="co_name");                _field_err("co_name", errors)
            st.text_input("Address", key="co_addr");                  _field_err("co_addr", errors)
            cc1, cc2 = st.columns(2)
            with cc1:
                st.text_input("City", key="co_city");                 _field_err("co_city", errors)
            with cc2:
                st.text_input("Postal code", key="co_postal");        _field_err("co_postal", errors)
            st.text_input("Country", key="co_country")

            st.markdown("**Payment** · :grey[demo — not charged]")
            st.text_input("Name on card", key="co_cardname");         _field_err("co_cardname", errors)
            st.text_input("Card number", placeholder="4242 4242 4242 4242",
                          max_chars=23, key="co_card");               _field_err("co_card", errors)
            pc1, pc2 = st.columns(2)
            with pc1:
                st.text_input("Expiry (MM/YY)", placeholder="08/27",
                              max_chars=7, key="co_exp");             _field_err("co_exp", errors)
            with pc2:
                st.text_input("CVC", placeholder="123", max_chars=4,
                              type="password", key="co_cvc");         _field_err("co_cvc", errors)

            placed = st.form_submit_button(f"Pay ${total:,.2f} & place order",
                                           type="primary", use_container_width=True)

        if placed:
            errs = _validate({k: st.session_state.get(k, "") for k in
                              ("co_name", "co_addr", "co_city", "co_postal",
                               "co_cardname", "co_card", "co_exp", "co_cvc")})
            if errs:
                st.session_state["checkout_errors"] = errs
                st.rerun()
            else:
                st.session_state.pop("checkout_errors", None)
                order_id = db.create_order(user["id"], items)
                st.session_state["last_order_id"] = order_id
                st.switch_page("views/_success.py")

    with right:
        st.markdown("**Order summary**")
        for aid, qty, price in items:
            name = by_id.loc[aid].get("prod_name") if aid in by_id.index else aid
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;font-size:14px;margin-bottom:4px;">'
                f'<span>{name} × {qty}</span><span>${price * qty:,.2f}</span></div>',
                unsafe_allow_html=True,
            )
        st.markdown('<div class="divider" style="margin:10px 0 !important;"></div>', unsafe_allow_html=True)
        st.markdown(f'<div style="display:flex;justify-content:space-between;font-size:14px;">'
                    f'<span class="muted">Subtotal</span><span>${subtotal:,.2f}</span></div>',
                    unsafe_allow_html=True)
        st.markdown(f'<div style="display:flex;justify-content:space-between;font-size:14px;margin-bottom:6px;">'
                    f'<span class="muted">Shipping</span><span>${SHIP_FLAT:,.2f}</span></div>',
                    unsafe_allow_html=True)
        st.markdown(f"<h2 style='margin-top:6px !important;'>Total ${total:,.2f}</h2>",
                    unsafe_allow_html=True)
        if st.button("← Back to cart", use_container_width=True):
            st.switch_page("views/_cart.py")


main()
