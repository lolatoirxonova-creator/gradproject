"""Admin page — platform stats, user table, and ALS retrain trigger.

Hidden from default page nav (underscore prefix). Reached via the "Admin"
button in the sidebar, which only renders for users with role='admin'.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

import pandas as pd
import streamlit as st

from app import auth, db, retrain, shared


def main():
    shared.check_session_timeout()
    user = st.session_state.get("user")
    if user is None:
        st.warning("Please log in from the home page first.")
        st.stop()

    shared.apply_css()
    shared.render_sidebar(user)

    if user["role"] != "admin":
        st.markdown('<div class="pill">Access denied</div>', unsafe_allow_html=True)
        st.markdown("<h1>Admin only.</h1>", unsafe_allow_html=True)
        st.markdown(
            '<p class="subtitle">This page is reserved for platform administrators. '
            'If you should have access, ask an existing admin to promote your account.</p>',
            unsafe_allow_html=True,
        )
        return

    st.markdown('<div class="pill">Admin</div>', unsafe_allow_html=True)
    st.markdown("<h1>Platform administration.</h1>", unsafe_allow_html=True)
    st.markdown(
        '<p class="subtitle">User management, interaction telemetry, and on-demand '
        'retraining of the collaborative-filtering model.</p>',
        unsafe_allow_html=True,
    )

    # ---------- Aggregate stats ----------
    stats = db.interaction_stats()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Users", stats["n_users"])
    c2.metric("Admins", stats["n_admins"])
    c3.metric("Interactions", stats["n_interactions"])
    by = stats["by_event_type"]
    c4.metric("Saves (active)", by.get("save", 0) - by.get("unsave", 0))

    if by:
        breakdown = ", ".join(f"{k}={v}" for k, v in sorted(by.items()))
        st.caption(f"By event type: {breakdown}")

    # ---------- User table ----------
    st.markdown("<h2>Users</h2>", unsafe_allow_html=True)
    users = db.admin_user_table()
    if users:
        users_df = pd.DataFrame(users)[
            ["id", "email", "display_name", "role", "n_interactions", "created_at"]
        ]
        users_df.columns = ["ID", "Email", "Display name", "Role", "Interactions", "Created at"]
        st.dataframe(users_df, use_container_width=True, hide_index=True)
    else:
        st.markdown('<p class="muted">No users yet.</p>', unsafe_allow_html=True)

    # ---------- Login audit log ----------
    st.markdown("<h2>Login audit log</h2>", unsafe_allow_html=True)
    st.markdown(
        f'<p class="muted">Every login attempt is recorded. Failed-attempt '
        f'lockout: ≥{auth.MAX_FAILED_ATTEMPTS} failures within '
        f'{auth.LOCKOUT_WINDOW_MINUTES} minutes blocks the account for that window. '
        f'Session timeout: {shared.SESSION_TIMEOUT_SECONDS // 60} min idle → logout.</p>',
        unsafe_allow_html=True,
    )
    events = db.recent_login_events(limit=100)
    if events:
        ev_df = pd.DataFrame(events)
        ev_df["result"] = ev_df["success"].map({1: "✓ success", 0: "✗ failure"})
        ev_df = ev_df[["created_at", "email", "result", "ip", "user_agent"]]
        ev_df.columns = ["When", "Email", "Result", "IP", "User-Agent"]
        st.dataframe(ev_df, use_container_width=True, hide_index=True)
        n_failures_24h = sum(
            1 for r in events
            if r["success"] == 0
            and r["created_at"] > (pd.Timestamp.utcnow() - pd.Timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
        )
        if n_failures_24h:
            st.caption(f"{n_failures_24h} failed attempt(s) in the last 24 hours.")
    else:
        st.markdown('<p class="muted">No login attempts logged yet.</p>', unsafe_allow_html=True)

    # ---------- Retrain ----------
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown("<h2>Retrain collaborative-filtering model</h2>", unsafe_allow_html=True)
    st.markdown(
        '<p class="muted">Refits ALS on a recent slice of H&amp;M transactions combined '
        'with all currently-active platform saves/likes/purchases. The new bundle '
        'overwrites <code>models/cf_als_model.pkl</code> and is picked up after a cache clear.</p>',
        unsafe_allow_html=True,
    )

    last_stats = st.session_state.get("last_retrain_stats")
    if last_stats:
        st.success(
            f"Last retrain: {last_stats['n_users']:,} users · "
            f"{last_stats['n_items']:,} items · "
            f"{last_stats['n_interactions']:,} interactions · "
            f"{last_stats['n_platform_users']} platform user(s) · "
            f"completed in {last_stats['elapsed_seconds']}s."
        )

    if st.button("Retrain ALS now", type="primary"):
        progress = st.empty()

        def _cb(msg: str):
            progress.info(msg)

        try:
            with st.spinner("Retraining ALS — keep this tab open…"):
                result = retrain.retrain_als(progress_cb=_cb)
        except Exception as e:
            progress.empty()
            st.error(f"Retrain failed: {type(e).__name__}: {e}")
            return

        progress.empty()
        # Refresh the cached model so the rest of the app sees it on next interaction.
        try:
            shared.load_cf.clear()
        except Exception:
            pass
        st.session_state["last_retrain_stats"] = result
        st.success(
            f"Done in {result['elapsed_seconds']}s — "
            f"{result['n_users']:,} users, {result['n_interactions']:,} interactions, "
            f"factors={result['factors']}."
        )


main()
