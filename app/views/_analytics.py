"""Admin control-room dashboard (admin only).

Renders a dark, self-contained control-room UI (matching the provided template)
inside an iframe via st.components.v1.html, injected with the marketplace's real
data. Streamlit's own sidebar is hidden on this page; the gold account avatar
stays pinned top-right for logout.
"""

from __future__ import annotations

import html as _html
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

import streamlit as st
import streamlit.components.v1 as components

from app import db, shared
from app.views import _admin_template

_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul",
           "Aug", "Sep", "Oct", "Nov", "Dec"]


def _pct_delta(curr, prev):
    """(class, label) describing curr vs prev — flat when prev is missing/zero."""
    if not prev:
        return ("flat", "tracking this period")
    change = 100 * (curr - prev) / prev
    cls = "up" if change >= 0 else "down"
    return (cls, f"{abs(change):.1f}% vs last month")


def _gather() -> dict:
    """Pull real numbers for the dashboard from the platform DB."""
    arts = shared.load_articles()
    name_by_id, cat_by_id = {}, {}
    if "article_id" in arts.columns:
        idx = arts.set_index(arts["article_id"].astype(str))
        name_by_id = idx["prod_name"].to_dict() if "prod_name" in arts.columns else {}
        cat_by_id = idx["category"].to_dict() if "category" in arts.columns else {}

    with db.get_conn() as c:
        def one(q, *a):
            return c.execute(q, a).fetchone()[0]

        gmv = float(one("SELECT COALESCE(SUM(total),0) FROM orders"))
        n_orders = int(one("SELECT COUNT(*) FROM orders"))
        buyers = int(one("SELECT COUNT(*) FROM users WHERE role='customer'"))
        admins = int(one("SELECT COUNT(*) FROM users WHERE role='admin'"))
        new_30 = int(one("SELECT COUNT(*) FROM users WHERE created_at>=datetime('now','-30 days')"))
        reviews = int(one("SELECT COUNT(*) FROM reviews"))
        avg_rating = float(one("SELECT COALESCE(AVG(rating),0) FROM reviews"))
        aov = (gmv / n_orders) if n_orders else 0.0

        m_rows = c.execute(
            "SELECT strftime('%Y-%m', created_at) m, COALESCE(SUM(total),0) t, COUNT(*) n "
            "FROM orders GROUP BY m ORDER BY m"
        ).fetchall()
        paid = int(one("SELECT COUNT(*) FROM orders WHERE status='paid'"))
        offline = int(one("SELECT COUNT(*) FROM orders WHERE status!='paid'"))

        top_rows = c.execute(
            "SELECT article_id, SUM(quantity) q FROM order_items "
            "GROUP BY article_id ORDER BY q DESC LIMIT 6"
        ).fetchall()
        oi_rows = c.execute(
            "SELECT article_id, SUM(quantity*unit_price) rev FROM order_items GROUP BY article_id"
        ).fetchall()
        units_sold = int(one("SELECT COALESCE(SUM(quantity),0) FROM order_items"))

        n_views = int(one("SELECT COUNT(*) FROM interactions WHERE event_type='view'"))
        n_saves = int(one("SELECT COUNT(*) FROM interactions WHERE event_type='save'"))
        n_cart = int(one("SELECT COALESCE(SUM(quantity),0) FROM cart"))

        buyers_1 = int(one("SELECT COUNT(DISTINCT user_id) FROM orders"))
        buyers_2 = int(one("SELECT COUNT(*) FROM "
                           "(SELECT user_id FROM orders GROUP BY user_id HAVING COUNT(*)>=2)"))

        gmv_today = float(one("SELECT COALESCE(SUM(total),0) FROM orders WHERE date(created_at)=date('now')"))
        orders_today = int(one("SELECT COUNT(*) FROM orders WHERE date(created_at)=date('now')"))

        order_logs = c.execute(
            "SELECT o.created_at, u.email, o.id, o.total, o.n_items, o.status "
            "FROM orders o JOIN users u ON u.id=o.user_id ORDER BY o.created_at DESC, o.id DESC LIMIT 10"
        ).fetchall()
        login_logs = c.execute(
            "SELECT created_at, email, success, ip FROM login_attempts ORDER BY id DESC LIMIT 10"
        ).fetchall()
        total_events = int(one("SELECT COUNT(*) FROM "
                               "(SELECT id FROM orders UNION ALL SELECT id FROM login_attempts)"))

    # ---- revenue / orders by month (last 6 buckets) ----
    rev_labels = [_MONTHS[int(r["m"][5:7]) - 1] for r in m_rows][-6:]
    rev_data = [round(float(r["t"]), 2) for r in m_rows][-6:]
    ord_by_month = [int(r["n"]) for r in m_rows][-6:]
    if not rev_labels:
        rev_labels, rev_data, ord_by_month = ["—"], [0], [0]

    # ---- month-over-month deltas (honest: flat when no prior month) ----
    if len(m_rows) >= 2:
        gmv_delta = _pct_delta(float(m_rows[-1]["t"]), float(m_rows[-2]["t"]))
        ord_delta = _pct_delta(int(m_rows[-1]["n"]), int(m_rows[-2]["n"]))
    else:
        gmv_delta = ord_delta = ("flat", "tracking this period")
    buyers_delta = ("up", f"+{new_30} new in 30 days") if new_30 else ("flat", "no new signups")
    aov_delta = ("flat", "per completed order")

    # ---- top products ----
    top_labels = [str(name_by_id.get(str(r["article_id"]), r["article_id"]))[:22] for r in top_rows]
    top_data = [int(r["q"]) for r in top_rows]
    if not top_labels:
        top_labels, top_data = ["No sales yet"], [0]

    # ---- sales by category (revenue share) ----
    cat_rev: dict[str, float] = {}
    for r in oi_rows:
        cat = str(cat_by_id.get(str(r["article_id"]), "Other"))
        cat_rev[cat] = cat_rev.get(cat, 0.0) + float(r["rev"] or 0)
    if not cat_rev and "category" in arts.columns:  # fall back to catalogue mix
        for cat, n in arts["category"].value_counts().items():
            cat_rev[str(cat)] = float(n)
    cat_sorted = sorted(cat_rev.items(), key=lambda x: -x[1])
    cat_total = sum(v for _, v in cat_sorted) or 1
    cat_labels = [k for k, _ in cat_sorted]
    cat_data = [round(100 * v / cat_total, 1) for _, v in cat_sorted]

    # ---- analytics behavioural cards ----
    repeat_rate = (100 * buyers_2 / buyers_1) if buyers_1 else 0.0
    clv = (gmv / buyers_1) if buyers_1 else 0.0
    denom = n_cart + units_sold
    cart_abandon = (100 * n_cart / denom) if denom else 0.0

    # ---- conversion funnel (real engagement) ----
    funnel = [("Product views", n_views), ("Saved to wishlist", n_saves),
              ("Added to cart", n_cart), ("Orders placed", n_orders)]

    # ---- merged activity log ----
    logs = []
    for r in order_logs:
        status = "Paid online" if r["status"] == "paid" else "Pay at store"
        badge = "success" if r["status"] == "paid" else "warning"
        logs.append((r["created_at"], r["email"], "Purchase",
                     f"Order #{r['id']} — {shared.money(r['total'])}, {r['n_items']} item(s)",
                     "—", status, badge))
    for r in login_logs:
        ok = r["success"]
        logs.append((r["created_at"], r["email"], "Sign-in",
                     "Logged in" if ok else "Failed login attempt",
                     r["ip"] or "—", "Success" if ok else "Failed",
                     "success" if ok else "danger"))
    logs.sort(key=lambda x: x[0] or "", reverse=True)
    logs = logs[:12]

    return dict(
        gmv=gmv, n_orders=n_orders, buyers=buyers, admins=admins, aov=aov,
        gmv_delta=gmv_delta, ord_delta=ord_delta, buyers_delta=buyers_delta, aov_delta=aov_delta,
        rev_labels=rev_labels, rev_data=rev_data, ord_by_month=ord_by_month,
        paid=paid, offline=offline,
        top_labels=top_labels, top_data=top_data,
        cat_labels=cat_labels, cat_data=cat_data,
        repeat_rate=repeat_rate, clv=clv, cart_abandon=cart_abandon,
        reviews=reviews, avg_rating=avg_rating, new_30=new_30,
        funnel=funnel, gmv_today=gmv_today, orders_today=orders_today,
        logs=logs, total_events=total_events,
    )


def main():
    shared.check_session_timeout()
    user = st.session_state.get("user")

    shared.apply_css()
    if user is None or user.get("role") != "admin":
        shared.render_sidebar(user)
        st.markdown('<div class="pill">Access denied</div>', unsafe_allow_html=True)
        st.markdown("<h1>Admin only.</h1>", unsafe_allow_html=True)
        st.markdown('<p class="subtitle">This console is restricted to administrators.</p>',
                    unsafe_allow_html=True)
        return

    # Hide Streamlit's sidebar + its st.logo (the iframe carries its own brand),
    # zero the padding so the console fills the viewport, and drop the gold account
    # avatar below the scrolling ticker so the two don't overlap.
    st.markdown(
        "<style>"
        "[data-testid='stSidebar'],[data-testid='stSidebarCollapsedControl'],"
        "[data-testid='stHeader'],[data-testid='stLogo'],[data-testid='stLogoLink']"
        "{display:none!important;}"
        "[data-testid='stAppViewContainer'],[data-testid='stMain']{padding-top:0!important;}"
        ".block-container,[data-testid='stMainBlockContainer']"
        "{padding:0!important;max-width:100%!important;min-height:0!important;}"
        ".block-container::after,[data-testid='stMainBlockContainer']::after{display:none!important;}"
        "[data-testid='stMain'] [data-testid='stVerticalBlock']{gap:0!important;}"
        "[data-testid='stElementContainer'],.stCustomComponentV1,"
        "[data-testid='stIFrame']{margin:0!important;}"
        ".st-key-account_menu{top:30px!important;right:26px!important;z-index:100001!important;}</style>",
        unsafe_allow_html=True,
    )
    shared.render_account_menu(user)

    html = _admin_template.render(_gather(), user, _html, json)
    components.html(html, height=1480, scrolling=True)


main()
