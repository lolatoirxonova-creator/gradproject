"""Payment / order history — the user's placed orders (online + offline).

Hidden page (filename `_`-prefixed, nav link hidden in CSS); reached from the
top-right account menu's "Payment history" entry. Reads `db.user_orders`.
"""

from __future__ import annotations

import html
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

import streamlit as st

from app import db, shared


def _status_badge(status: str) -> str:
    """Gold (online paid) / outline (offline pickup) status chip."""
    if status == "offline":
        return ('<span style="display:inline-block;padding:3px 11px;border-radius:100px;'
                'font-size:11px;font-weight:600;background:transparent;color:var(--accent-2);'
                'border:1px solid var(--accent);">Pay at store</span>')
    return ('<span style="display:inline-block;padding:3px 11px;border-radius:100px;'
            'font-size:11px;font-weight:600;background:var(--accent-soft);'
            'color:var(--accent-2);">Paid online</span>')


def main():
    shared.check_session_timeout()
    user = st.session_state.get("user")
    shared.apply_css()
    shared.render_sidebar(user)

    if user is None:
        st.markdown('<div class="pill">Payment history</div>', unsafe_allow_html=True)
        st.markdown("<h1>Sign in to view your orders.</h1>", unsafe_allow_html=True)
        return

    st.markdown('<div class="pill">Your account</div>', unsafe_allow_html=True)
    st.markdown("<h1>Payment history.</h1>", unsafe_allow_html=True)

    # back to home (#14)
    _bh, _ = st.columns([1, 4])
    with _bh:
        if st.button("Back to home", icon=":material/home:", key="orders_home",
                     use_container_width=True):
            _home = st.session_state.get("_home_page")
            st.switch_page(_home) if _home is not None else st.switch_page("views/1_Catalogue.py")

    orders = db.user_orders(user["id"])
    if not orders:
        st.markdown(
            '<p class="subtitle">No orders yet. When you check out or place an in-store order, '
            'it will appear here.</p>', unsafe_allow_html=True)
        if st.button("Browse catalogue", type="primary"):
            st.switch_page("views/1_Catalogue.py")
        return

    total_spent = sum(o["total"] for o in orders)
    m1, m2, m3 = st.columns(3)
    m1.metric("Orders", len(orders))
    m2.metric("Items bought", sum(o["n_items"] for o in orders))
    m3.metric("Total spent", shared.money(total_spent))
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    by_id = shared.load_articles().set_index("article_id")

    def _name(aid: str) -> str:
        try:
            return str(by_id.loc[aid].get("prod_name") or aid)
        except Exception:
            return str(aid)

    for o in orders:
        date = (o.get("created_at") or "")[:16]
        lines = "".join(
            f'<div style="display:flex;justify-content:space-between;font-size:13px;'
            f'padding:5px 0;color:var(--ink-2);">'
            f'<span>{html.escape(_name(it["article_id"]))} &times; {it["quantity"]}</span>'
            f'<span>{html.escape(shared.money(it["unit_price"] * it["quantity"]))}</span></div>'
            for it in o["items"]
        )
        st.markdown(
            f'<div class="card" style="padding:16px 18px;margin-bottom:12px;">'
            f'  <div style="display:flex;justify-content:space-between;align-items:center;'
            f'margin-bottom:8px;">'
            f'    <span style="font-weight:700;font-size:15px;">Order #{o["id"]}'
            f'      <span class="muted" style="font-weight:400;margin-left:8px;">{date}</span></span>'
            f'    {_status_badge(o.get("status", "paid"))}'
            f'  </div>'
            f'  <div style="border-top:1px solid var(--border);padding-top:6px;">{lines}</div>'
            f'  <div style="display:flex;justify-content:space-between;border-top:1px solid var(--border);'
            f'margin-top:6px;padding-top:8px;font-weight:700;">'
            f'    <span>Total</span><span>{html.escape(shared.money(o["total"]))}</span></div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div style="height:48px;"></div>', unsafe_allow_html=True)


main()
