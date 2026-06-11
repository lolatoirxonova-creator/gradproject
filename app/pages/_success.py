"""Order confirmation — shown after a successful (mock) checkout."""

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

    order_id = st.session_state.get("last_order_id")
    order = db.get_order(order_id) if order_id else None
    # only show the current user's order
    if order is None or order.get("user_id") != user["id"]:
        st.markdown('<div class="pill">Order</div>', unsafe_allow_html=True)
        st.markdown("<h1>No recent order.</h1>", unsafe_allow_html=True)
        if st.button("Browse catalogue", type="primary"):
            st.switch_page("pages/1_Catalogue.py")
        return

    articles = shared.load_articles()
    by_id = articles.set_index("article_id")

    # On-brand gold success animation: a gold checkmark that draws in, ringed by a
    # radiating sparkle burst that echoes the site's gold sparkle motif. (Replaces
    # Streamlit's off-brand red/green/blue st.balloons.)
    _sparkle_dirs = [(0, -62), (44, -44), (62, 0), (44, 44),
                     (0, 62), (-44, 44), (-62, 0), (-44, -44)]
    _sparkles = "".join(
        f'<i style="--dx:{dx}px;--dy:{dy}px;animation-delay:{0.28 + i * 0.02:.2f}s;">✦</i>'
        for i, (dx, dy) in enumerate(_sparkle_dirs)
    )
    st.markdown(
        """
<style>
  @keyframes pop  { 0%{transform:scale(0)} 70%{transform:scale(1.12)} 100%{transform:scale(1)} }
  @keyframes draw { to { stroke-dashoffset: 0; } }
  @keyframes sparkle {
    0%   { transform: translate(0,0) scale(0); opacity: 0; }
    35%  { opacity: 1; }
    100% { transform: translate(var(--dx), var(--dy)) scale(1); opacity: 0; }
  }
  .ok-wrap { position: relative; display:flex; justify-content:center; align-items:center;
             height: 116px; margin: 6px 0 16px; }
  .ok-circle {
    width:88px; height:88px; border-radius:50%; position: relative; z-index: 2;
    background: radial-gradient(120% 120% at 50% 30%, #e6c878 0%, #c19a3e 55%, #a07e2c 100%);
    display:flex; align-items:center; justify-content:center;
    animation: pop .5s cubic-bezier(.2,.8,.2,1) both;
    box-shadow: 0 16px 40px -10px rgba(193,154,62,.6);
  }
  .ok-circle svg path { stroke-dasharray: 48; stroke-dashoffset: 48; animation: draw .45s .3s ease forwards; }
  .ok-burst { position:absolute; inset:0; display:flex; align-items:center; justify-content:center;
              z-index:1; pointer-events:none; }
  .ok-burst i { position:absolute; color: var(--accent); font-size: 15px; opacity:0;
                animation: sparkle .95s ease-out forwards; }
</style>
<div class="ok-wrap">
  <div class="ok-burst">"""
        + _sparkles
        + """</div>
  <div class="ok-circle">
    <svg width="44" height="44" viewBox="0 0 24 24" fill="none">
      <path d="M5 13l4 4L19 7" stroke="#fff" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown('<div style="text-align:center;"><span class="pill">Payment successful</span></div>',
                unsafe_allow_html=True)
    st.markdown(f"<h1 class='hero-headline' style='text-align:center;'>Order #{order['id']} confirmed.</h1>",
                unsafe_allow_html=True)
    st.markdown(
        f'<p class="subtitle">Thanks, {user.get("display_name", "")}! Your order of '
        f'{order["n_items"]} item{"s" if order["n_items"] != 1 else ""} is placed. '
        f'A confirmation would be emailed in a real deployment (this is a demo).</p>',
        unsafe_allow_html=True,
    )

    st.markdown("<h2>Order summary</h2>", unsafe_allow_html=True)
    for it in order["items"]:
        aid, qty, price = it["article_id"], it["quantity"], it["unit_price"]
        name = by_id.loc[aid].get("prod_name") if aid in by_id.index else aid
        st.markdown(
            f'<div style="display:flex;justify-content:space-between;font-size:15px;margin-bottom:6px;">'
            f'<span>{name} × {qty}</span><span>${price * qty:,.2f}</span></div>',
            unsafe_allow_html=True,
        )
    st.markdown('<div class="divider" style="margin:10px 0 !important;"></div>', unsafe_allow_html=True)
    st.markdown(f"<h2 style='margin-top:0 !important;'>Total paid: ${order['total']:,.2f}</h2>",
                unsafe_allow_html=True)

    b1, b2, b3 = st.columns(3)
    if b1.button("Continue shopping", type="primary", use_container_width=True):
        st.session_state.pop("last_order_id", None)
        st.switch_page("pages/1_Catalogue.py")
    if b2.button("Payment history", use_container_width=True):
        st.session_state.pop("last_order_id", None)
        st.switch_page("pages/_orders.py")
    if b3.button("View wishlist", use_container_width=True):
        st.session_state.pop("last_order_id", None)
        st.switch_page("pages/2_Wishlist.py")


main()
