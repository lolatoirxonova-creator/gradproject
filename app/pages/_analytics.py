"""Analytics dashboard — platform-wide metrics with Plotly charts.

Visible to users with role `admin` or `analyst`. Hidden from default page nav
(underscore prefix); reached via the "Analytics" sidebar button.

Honesty note: charts use real data from the platform's `interactions` log. CTR
and per-algorithm-funnel charts that would normally appear on a production
dashboard are deliberately not included — they would require impression
logging (recording which articles were shown to which user from which rail),
which is on the future-work roadmap (see report §5b.9).
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

import pandas as pd
import plotly.express as px
import streamlit as st

from app import db, shared


def _chart_layout(fig, height: int = 320):
    """Consistent layout tweaks across all charts."""
    fig.update_layout(
        height=height,
        margin=dict(l=20, r=20, t=30, b=20),
        font=dict(family="-apple-system, BlinkMacSystemFont, sans-serif", size=12),
        plot_bgcolor="#ffffff",
        paper_bgcolor="rgba(0,0,0,0)",
        hoverlabel=dict(bgcolor="#1d1d1f", font_color="#fff"),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.25),
    )
    fig.update_xaxes(showgrid=False, linecolor="#e5e5e7")
    fig.update_yaxes(showgrid=True, gridcolor="#f0f0f2", linecolor="#e5e5e7")
    return fig


def _section(title: str, caption: str = ""):
    st.markdown(f"<h2>{title}</h2>", unsafe_allow_html=True)
    if caption:
        st.markdown(f'<p class="muted">{caption}</p>', unsafe_allow_html=True)


def render_signups_and_active(days: int):
    signups = db.daily_signups(days)
    active = db.active_users(days=7)
    stats = db.interaction_stats()
    engage = db.engagement_rates()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total users", f"{stats['n_users']:,}")
    c2.metric("Active in 7 days", f"{active:,}")
    c3.metric("Total interactions", f"{stats['n_interactions']:,}")
    c4.metric("Save-rate (saves/views)", f"{engage['save_rate']:.1%}")

    if signups:
        df = pd.DataFrame(signups)
        fig = px.line(
            df, x="day", y="n",
            title=None,
            markers=True,
            line_shape="spline",
            labels={"day": "Date", "n": "Signups"},
            color_discrete_sequence=["#1d1d1f"],
        )
        fig.update_traces(line=dict(width=2.5))
        _chart_layout(fig, height=280)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.markdown(
            f'<p class="muted">No signups in the last {days} days yet.</p>',
            unsafe_allow_html=True,
        )


def render_events_breakdown(days: int):
    rows = db.daily_events(days)
    if not rows:
        st.markdown('<p class="muted">No interactions logged yet.</p>', unsafe_allow_html=True)
        return

    df = pd.DataFrame(rows)
    df["day"] = pd.to_datetime(df["day"])

    c1, c2 = st.columns([3, 2])

    with c1:
        fig = px.area(
            df, x="day", y="n", color="event_type",
            labels={"day": "Date", "n": "Events", "event_type": "Type"},
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        _chart_layout(fig, height=320)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        totals = df.groupby("event_type", as_index=False)["n"].sum().sort_values("n", ascending=True)
        fig = px.bar(
            totals, x="n", y="event_type", orientation="h",
            labels={"n": "Total events", "event_type": "Type"},
            color="event_type",
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig.update_layout(showlegend=False)
        _chart_layout(fig, height=320)
        st.plotly_chart(fig, use_container_width=True)


def render_product_analytics(articles: pd.DataFrame):
    name_by_id = articles.set_index("article_id")["prod_name"].to_dict()

    c1, c2 = st.columns(2)

    with c1:
        st.markdown('<p class="muted" style="margin-bottom:0;">Top 10 most-saved</p>', unsafe_allow_html=True)
        top_saved = db.top_articles("save", limit=10)
        if top_saved:
            df = pd.DataFrame(top_saved)
            df["label"] = df["article_id"].map(lambda a: f"{name_by_id.get(a, a)[:24]} · {a}")
            df = df.sort_values("n")
            fig = px.bar(
                df, x="n", y="label", orientation="h",
                labels={"n": "Saves", "label": ""},
                color="n",
                color_continuous_scale=["#d2d2d7", "#1d1d1f"],
            )
            fig.update_layout(showlegend=False, coloraxis_showscale=False)
            _chart_layout(fig, height=360)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.markdown('<p class="muted">No save events yet.</p>', unsafe_allow_html=True)

    with c2:
        st.markdown('<p class="muted" style="margin-bottom:0;">Top 10 most-viewed</p>', unsafe_allow_html=True)
        top_viewed = db.top_articles("view", limit=10)
        if top_viewed:
            df = pd.DataFrame(top_viewed)
            df["label"] = df["article_id"].map(lambda a: f"{name_by_id.get(a, a)[:24]} · {a}")
            df = df.sort_values("n")
            fig = px.bar(
                df, x="n", y="label", orientation="h",
                labels={"n": "Views", "label": ""},
                color="n",
                color_continuous_scale=["#d2d2d7", "#1d1d1f"],
            )
            fig.update_layout(showlegend=False, coloraxis_showscale=False)
            _chart_layout(fig, height=360)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.markdown('<p class="muted">No view events yet.</p>', unsafe_allow_html=True)


def render_cold_start():
    rows = db.cold_start_distribution()
    if not rows:
        st.markdown('<p class="muted">No users yet.</p>', unsafe_allow_html=True)
        return

    df = pd.DataFrame(rows)
    df["save_count"] = df["save_count"].astype(int).clip(lower=0)
    # Bucket into 0, 1, 2-4, 5-9, 10+ for a cleaner cold-start picture.
    def _bucket(n):
        if n <= 0:
            return "0 (cold)"
        if n == 1:
            return "1"
        if n <= 4:
            return "2-4"
        if n <= 9:
            return "5-9"
        return "10+"
    df["bucket"] = df["save_count"].map(_bucket)
    agg = df.groupby("bucket", as_index=False)["n_users"].sum()
    order = ["0 (cold)", "1", "2-4", "5-9", "10+"]
    agg["order"] = agg["bucket"].map({b: i for i, b in enumerate(order)})
    agg = agg.sort_values("order")
    fig = px.bar(
        agg, x="bucket", y="n_users",
        labels={"bucket": "Saved items", "n_users": "Users"},
        color="n_users",
        color_continuous_scale=["#d2d2d7", "#1d1d1f"],
    )
    fig.update_layout(showlegend=False, coloraxis_showscale=False)
    _chart_layout(fig, height=300)
    st.plotly_chart(fig, use_container_width=True)


def render_feedback_funnel():
    e = db.engagement_rates()
    df = pd.DataFrame([
        {"stage": "Views",    "count": e["n_views"]},
        {"stage": "Saves",    "count": e["n_saves"]},
        {"stage": "Likes",    "count": e["n_likes"]},
        {"stage": "Dislikes", "count": e["n_dislikes"]},
    ])
    fig = px.funnel(
        df, x="count", y="stage",
        color_discrete_sequence=["#1d1d1f"],
    )
    _chart_layout(fig, height=280)
    st.plotly_chart(fig, use_container_width=True)

    c1, c2 = st.columns(2)
    c1.metric("Save rate (saves/views)", f"{e['save_rate']:.1%}")
    c2.metric("Like ratio (likes / likes+dislikes)", f"{e['like_ratio']:.1%}")


def render_experiment():
    """A/B/n experiment results: users + engagement per assigned algorithm."""
    stats = db.algorithm_stats()
    df = pd.DataFrame(stats)
    if df.empty or int(df["n_users"].sum()) == 0:
        st.markdown('<p class="muted">No users assigned to the experiment yet.</p>', unsafe_allow_html=True)
        return

    df["saves_per_user"] = (df["n_saves"] / df["n_users"].where(df["n_users"] > 0)).fillna(0).round(2)
    df["likes_per_user"] = (df["n_likes"] / df["n_users"].where(df["n_users"] > 0)).fillna(0).round(2)

    leader = df.sort_values("saves_per_user", ascending=False).iloc[0]
    c1, c2, c3 = st.columns(3)
    c1.metric("Users in experiment", f"{int(df['n_users'].sum()):,}")
    c2.metric("Leading algorithm (saves/user)", leader["label"])
    c3.metric("Its saves/user", f"{leader['saves_per_user']:.2f}")

    cc1, cc2 = st.columns(2)
    with cc1:
        st.markdown('<p class="muted" style="margin-bottom:0;">Users per algorithm</p>', unsafe_allow_html=True)
        fig = px.bar(
            df.sort_values("n_users"), x="n_users", y="label", orientation="h",
            labels={"label": "", "n_users": "Users"},
            color="label",
            color_discrete_sequence=["#c19a3e", "#1d1d1f", "#a07e2c", "#8a8178"],
        )
        _chart_layout(fig, height=300)
        fig.update_layout(showlegend=False)  # after _chart_layout (which re-enables it)
        st.plotly_chart(fig, use_container_width=True)
    with cc2:
        st.markdown('<p class="muted" style="margin-bottom:0;">Engagement per user — effectiveness</p>', unsafe_allow_html=True)
        m = df.melt(id_vars="label", value_vars=["saves_per_user", "likes_per_user"],
                    var_name="metric", value_name="per_user")
        m["metric"] = m["metric"].map({"saves_per_user": "Saves/user", "likes_per_user": "Likes/user"})
        fig = px.bar(
            m, x="label", y="per_user", color="metric", barmode="group",
            labels={"label": "", "per_user": "Per user", "metric": ""},
            color_discrete_sequence=["#c19a3e", "#e2cb8e"],
        )
        _chart_layout(fig, height=300)
        st.plotly_chart(fig, use_container_width=True)

    show = df[["label", "n_users", "n_views", "n_saves", "n_likes", "n_dislikes",
               "n_purchases", "saves_per_user", "likes_per_user"]].rename(columns={
        "label": "Algorithm", "n_users": "Users", "n_views": "Views", "n_saves": "Saves",
        "n_likes": "Likes", "n_dislikes": "Dislikes", "n_purchases": "Purchases",
        "saves_per_user": "Saves/user", "likes_per_user": "Likes/user"})
    st.dataframe(show, hide_index=True, use_container_width=True)


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
        st.markdown(
            '<p class="subtitle">This dashboard is restricted to platform administrators and analysts. '
            'Ask an existing admin to promote your account.</p>',
            unsafe_allow_html=True,
        )
        return

    st.markdown('<div class="pill">Analytics</div>', unsafe_allow_html=True)
    st.markdown("<h1>Platform analytics.</h1>", unsafe_allow_html=True)
    st.markdown(
        '<p class="subtitle">Real-time view of user engagement and product '
        'analytics on the recommendation platform.</p>',
        unsafe_allow_html=True,
    )

    days = st.selectbox(
        "Time window", [7, 30, 90, 365], index=1,
        format_func=lambda d: f"Last {d} days",
        key="analytics_days",
    )

    _section("Platform health")
    render_signups_and_active(days)

    _section(
        "Algorithm experiment (A/B/n)",
        "Each customer is round-robin assigned one of the four algorithms and only ever "
        "sees that one, so engagement is attributable. ‘Saves/user’ is the headline "
        "effectiveness proxy.",
    )
    render_experiment()

    _section("Events over time", "Daily interaction volume broken down by event type.")
    render_events_breakdown(days)

    _section("Product analytics", "Most-saved and most-viewed articles across the platform.")
    articles = shared.load_articles()
    render_product_analytics(articles)

    _section("Cold-start distribution", "How warm is the user population? Most users with 0 saves means most recommendations rely on preference seeding.")
    render_cold_start()

    _section("Feedback funnel", "Views → Saves → Likes → Dislikes. Save-rate and like-ratio are proxies for recommendation relevance.")
    render_feedback_funnel()

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.caption(
        "Not shown (require impression logging — future work): "
        "per-algorithm CTR, recommendation→view conversion by rail, "
        "and per-user precision@k from offline evaluation."
    )


main()
