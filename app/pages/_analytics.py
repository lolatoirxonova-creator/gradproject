"""Analytics dashboard — simple at-a-glance KPI cards (admin / analyst).

Deliberately minimal: headline platform numbers in stat cards, no detailed
charts. Hidden from default nav (underscore prefix); reached via the "Analytics"
sidebar button.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

import streamlit as st

from app import db, shared

ROLE_LABEL = {"customer": "Customers", "seller": "Sellers",
              "analyst": "Analysts", "admin": "Admins"}

_KPI_CSS = """
<style>
  .st-key-kpi_grid [data-testid="stMetric"] {
    background: var(--bg); border: 1px solid var(--border);
    border-radius: 16px; padding: 18px 22px; box-shadow: var(--shadow-1);
  }
  .st-key-kpi_grid [data-testid="stMetricValue"] {
    font-family: var(--display); font-size: 32px !important; font-weight: 700 !important;
    color: var(--ink) !important; line-height: 1.1;
  }
  .st-key-kpi_grid [data-testid="stMetricLabel"] p {
    font-size: 13px !important; color: var(--muted) !important; font-weight: 500;
  }
  .mini-card {
    background: var(--bg); border: 1px solid var(--border); border-radius: 16px;
    padding: 18px 22px; box-shadow: var(--shadow-1); height: 100%;
  }
  .mini-card h3 { font-family: var(--display); font-size: 18px; margin: 0 0 12px !important; }
  .mini-row { display: flex; justify-content: space-between; align-items: center;
              padding: 9px 0; border-bottom: 1px solid var(--border); font-size: 14px; }
  .mini-row:last-child { border-bottom: none; }
  .mini-row .v { font-weight: 700; color: var(--ink); }
  .mini-row .pct { color: var(--muted); font-size: 12px; margin-left: 8px; }
  .mini-bar { height: 8px; border-radius: 6px; background: var(--accent-soft); overflow: hidden; margin-top: 2px; }
  .mini-bar > i { display: block; height: 100%; background: var(--accent); }
</style>
"""


def _query():
    """All the headline numbers in one place."""
    with db.get_conn() as c:
        def one(sql, *a):
            return c.execute(sql, a).fetchone()[0]
        data = {
            "total_users": one("SELECT COUNT(*) FROM users"),
            "customers": one("SELECT COUNT(*) FROM users WHERE role='customer'"),
            "sellers": one("SELECT COUNT(*) FROM users WHERE role='seller'"),
            "new_30d": one("SELECT COUNT(*) FROM users WHERE created_at >= datetime('now','-30 days')"),
            "orders": one("SELECT COUNT(*) FROM orders"),
            "revenue": one("SELECT COALESCE(SUM(total),0) FROM orders"),
            "reviews": one("SELECT COUNT(*) FROM reviews"),
            "avg_rating": one("SELECT COALESCE(AVG(rating),0) FROM reviews"),
            "wishlisted": one("SELECT COUNT(*) FROM interactions WHERE event_type='save'"),
        }
        roles = c.execute("SELECT role, COUNT(*) n FROM users GROUP BY role").fetchall()
    data["roles"] = {r["role"]: r["n"] for r in roles}
    return data


def main():
    shared.check_session_timeout()
    user = st.session_state.get("user")
    if user is None:
        st.warning("Please log in from the home page first.")
        st.stop()

    shared.apply_css()
    shared.render_sidebar(user)

    if user["role"] not in ("admin", "analyst"):
        st.markdown('<div class="pill">Access denied</div>', unsafe_allow_html=True)
        st.markdown("<h1>Analytics — admin or analyst only.</h1>", unsafe_allow_html=True)
        st.markdown('<p class="subtitle">This dashboard is restricted to administrators and analysts.</p>',
                    unsafe_allow_html=True)
        return

    st.markdown(_KPI_CSS, unsafe_allow_html=True)
    st.markdown('<div class="pill">Analytics</div>', unsafe_allow_html=True)
    st.markdown("<h1>Dashboard.</h1>", unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Headline numbers for the Barakaly marketplace.</p>',
                unsafe_allow_html=True)

    d = _query()
    articles = shared.load_articles()
    n_products = len(articles)

    # ---------------- KPI stat cards ----------------
    with st.container(key="kpi_grid"):
        r1 = st.columns(4)
        r1[0].metric("Customers", f"{d['customers']:,}")
        r1[1].metric("New (last 30 days)", f"{d['new_30d']:,}")
        r1[2].metric("Products", f"{n_products:,}")
        r1[3].metric("Orders", f"{d['orders']:,}")
        r2 = st.columns(4)
        r2[0].metric("Revenue", f"${d['revenue']:,.0f}")
        r2[1].metric("Reviews", f"{d['reviews']:,}")
        r2[2].metric("Avg rating", f"{d['avg_rating']:.1f} / 5")
        r2[3].metric("Sellers", f"{d['sellers']:,}")

    st.markdown('<div style="height:18px;"></div>', unsafe_allow_html=True)

    # ---------------- two simple breakdown cards ----------------
    left, right = st.columns(2)

    with left:
        cats = articles["category"].value_counts() if "category" in articles.columns else None
        rows = ""
        if cats is not None and len(cats):
            total = int(cats.sum())
            for name, n in cats.items():
                pct = round(100 * n / total)
                rows += (f'<div class="mini-row"><span>{name}</span>'
                         f'<span><span class="v">{int(n)}</span><span class="pct">{pct}%</span></span></div>'
                         f'<div class="mini-bar"><i style="width:{pct}%"></i></div>')
        st.markdown(f'<div class="mini-card"><h3>Catalogue by category</h3>{rows}</div>',
                    unsafe_allow_html=True)

    with right:
        order = ["customer", "seller", "analyst", "admin"]
        rows = ""
        for role in order:
            n = d["roles"].get(role, 0)
            if not n:
                continue
            pct = round(100 * n / max(1, d["total_users"]))
            rows += (f'<div class="mini-row"><span>{ROLE_LABEL.get(role, role.title())}</span>'
                     f'<span><span class="v">{n}</span><span class="pct">{pct}%</span></span></div>')
        st.markdown(f'<div class="mini-card"><h3>Accounts by role</h3>{rows}</div>',
                    unsafe_allow_html=True)


main()
