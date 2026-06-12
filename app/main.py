"""H&M Product Recommendation Platform — entry point.

Auth-gated home page. Catalogue, product detail, and (later) wishlist/admin
live under app/views/.

Run from repo root:
    streamlit run app/main.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

import streamlit as st

from app import auth, db, shared

st.set_page_config(
    page_title="Barakaly",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------- auth screen (rendered when not logged in) ----------

def _on_login(email, password):
    try:
        user = auth.authenticate(email, password)
        st.session_state["user"] = user
        shared.establish_session(user)  # persist across refreshes
        st.session_state["_scroll_top"] = True  # land at the top, not mid-list (#17)
        return None
    except auth.LockedError as e:
        return f"{e}"
    except auth.AuthError as e:
        # Show remaining-attempts hint so legitimate users don't trip the lockout blind
        n_failed = db.failed_attempts_in_window(email)
        remaining = max(0, auth.MAX_FAILED_ATTEMPTS - n_failed)
        if 0 < remaining < auth.MAX_FAILED_ATTEMPTS:
            return f"{e}  ({remaining} attempt{'s' if remaining != 1 else ''} remaining before lockout.)"
        return str(e)


def _on_signup(email, password, display_name, prefs):
    if len(prefs) < 3:
        return "Please pick at least 3 categories so we can personalise your feed."
    try:
        user = auth.register(email, password, display_name)
        auth.set_preferences(user["id"], prefs)
        st.session_state["user"] = user
        shared.establish_session(user)  # persist across refreshes
        st.session_state["_scroll_top"] = True  # land at the top, not mid-list (#17)
        return None
    except auth.AuthError as e:
        return str(e)


def render_auth_screen():
    shared.apply_css()
    # No sidebar pre-login (st.navigation position="hidden"). Split-screen layout:
    # the form sits on the left, a decorative branded panel fills the right — the
    # conventional fix for auth-page whitespace. This CSS only renders while
    # logged out, so it's effectively scoped to the auth screen.
    shared.render_auth_panel()

    # Mode is session-state driven (a radio reruns on change) so the hero copy can
    # react to it — st.tabs switches client-side only and can't change the heading.
    is_signup = st.session_state.get("auth_mode", "Log in") == "Create account"

    if st.button("Back to browsing", key="auth_back", icon=":material/arrow_back:"):
        shared.leave_signin()
    st.markdown('<div class="pill">Barakaly — beauty, curated</div>', unsafe_allow_html=True)
    if is_signup:
        st.markdown("<h1 class='hero-headline'>Create your account.</h1>", unsafe_allow_html=True)
        st.markdown(
            '<p class="subtitle">Pick a few categories you love and we’ll tailor recommendations from '
            'four learned models — content-based, collaborative filtering, hybrid, and neural — from '
            'your very first visit.</p>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown("<h1 class='hero-headline'>Beauty, curated for you.</h1>", unsafe_allow_html=True)
        st.markdown(
            '<p class="subtitle">Log in to get personalised cosmetics picks — skincare, makeup, '
            'fragrance and more — tuned to your taste and saved items.</p>',
            unsafe_allow_html=True,
        )

    # Tab-style selector that drives the mode (and reruns).
    st.radio(
        "Authentication mode", ["Log in", "Create account"],
        horizontal=True, label_visibility="collapsed", key="auth_mode",
    )

    if not is_signup:
        with st.form("login_form", clear_on_submit=False):
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            submitted = st.form_submit_button("Log in", type="primary", use_container_width=True)
        if submitted:
            err = _on_login(email, password)
            if err:
                st.error(err)
            else:
                st.rerun()
    else:
        articles = shared.load_articles()
        categories = sorted({c for c in articles["product_type_name"].dropna() if c})
        with st.form("signup_form", clear_on_submit=False):
            email = st.text_input("Email", key="signup_email")
            password = st.text_input(
                "Password", type="password", key="signup_password",
                help=f"At least {auth.MIN_PASSWORD_LEN} characters",
            )
            display_name = st.text_input("Display name", key="signup_name")
            prefs = st.multiselect(
                "What kinds of items interest you? (pick at least 3)",
                categories,
                key="signup_prefs",
            )
            submitted = st.form_submit_button("Create account", type="primary", use_container_width=True)
        if submitted:
            err = _on_signup(email, password, display_name, prefs)
            if err:
                st.error(err)
            else:
                st.rerun()


# ---------- home (logged-in) ----------

RAIL_SIZE = 6   # items per rail (3 columns x 2 rows)
POOL_MULT = 4   # request POOL_MULT × RAIL_SIZE candidates so MMR can diversify
LAMBDA_MMR = 0.7  # 1.0 = pure relevance; 0.0 = pure diversity
ALGO_HOME_SIZE = 12  # fuller single-rail grid for A/B/n-bucketed users


def _render_single_algo_home(algo, user, articles, tfidf, vectorizer,
                             als_model, als_item_index, als_item_to_row, candidate_items,
                             item_id_to_row, saved, saved_set, liked, disliked, preferences,
                             excluded, best_alpha, include, mmr_on, cart_set=None):
    """Render a home driven by ONE algorithm for an A/B/n-bucketed customer.

    All of the user's engagement is therefore attributable to `algo`. Cold-start
    algorithms (ALS/NeuMF need saved items) show an empty-state prompt.
    """
    pool_n = ALGO_HOME_SIZE * (POOL_MULT if mmr_on else 1)
    reasons: dict = {}
    profile = None
    if algo in ("content", "hybrid"):
        profile = shared.build_user_profile(saved, preferences, articles, tfidf, item_id_to_row)

    if algo == "content":
        pool = shared.recommend_cb(profile, tfidf, item_id_to_row, excluded, pool_n, include=include) or []
        if profile is not None:
            reasons = shared.explain_cb_for_items(profile, [a for a, _ in pool], tfidf, item_id_to_row, vectorizer)
        empty_msg = "Set a few style preferences in your profile (or save items) to get content-based picks."
    elif algo == "als":
        pool = shared.recommend_customers_like_you(als_model, als_item_index, als_item_to_row,
                                                   saved_set, excluded, k=pool_n, include=include)
        reasons = shared.explain_cf_for_items([a for a, _ in pool])
        empty_msg = "Save a few items so collaborative filtering can find shoppers like you."
    elif algo == "hybrid":
        pool = shared.recommend_hybrid(profile, tfidf, item_id_to_row, als_model, als_item_index,
                                       als_item_to_row, candidate_items, saved_set, excluded,
                                       best_alpha, pool_n, include=include) or []
        reasons = shared.explain_hybrid_for_items(profile, [a for a, _ in pool], tfidf,
                                                  item_id_to_row, vectorizer, best_alpha)
        empty_msg = "Save items or set preferences to get hybrid picks."
    else:  # neural
        pool = shared.recommend_ncf(saved_set, excluded, k=pool_n, include=include) or []
        empty_msg = "Save a few items so the neural model can learn and match your taste."

    if mmr_on and pool:
        recs = shared.mmr_rerank(pool, tfidf, item_id_to_row, k=ALGO_HOME_SIZE, lambda_param=LAMBDA_MMR)
    else:
        recs = list(pool or [])[:ALGO_HOME_SIZE]

    prefetch = []
    for aid, _ in recs:
        row = articles[articles["article_id"] == aid]
        if not row.empty:
            prefetch.append(row.iloc[0].to_dict())
    if prefetch:
        with st.spinner(f"Fetching product images ({len(prefetch)} items)…"):
            shared.prefetch_images_sync(prefetch, timeout=14.0)

    if not recs:
        st.info(empty_msg)
        return

    caption = "Personalised picks, just for you"
    if st.session_state.get("show_tech_details"):
        caption += f" · algorithm: {db.ALGORITHM_LABELS.get(algo, algo)}"
    shared.render_rail(
        "Picked for you", caption, recs, articles,
        key_prefix=f"algo_{algo}", user_id=user["id"],
        saved_set=saved_set, liked_set=liked, disliked_set=disliked, reasons=reasons,
        cart_set=cart_set,
    )


def _render_cosmetics_home(user):
    """Cosmetics home: carousel → 'Recommended for you' (first) → shop-by
    shortcuts → on-sale rail. Recs use shared.recommend_cosmetics (the trained
    H&M models don't apply to generated cosmetics)."""
    catalogue = shared.load_articles()  # cosmetics df in cosmetics mode
    guest = user is None
    if guest:
        saved, liked, disliked, saved_set, excluded, prefs, cart_set, uid = [], set(), set(), set(), set(), [], set(), None
    else:
        state = db.user_state(user["id"])
        saved, liked, disliked = state["saved"], state["liked"], state["disliked"]
        saved_set = set(saved)
        excluded = saved_set | disliked
        prefs = auth.get_preferences(user["id"])
        cart_set = {l["article_id"] for l in db.get_cart(user["id"])}
        uid = user["id"]

    if guest:
        st.markdown('<div class="pill">Barakaly — beauty, curated</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="pill">Welcome back, {user["display_name"]}</div>', unsafe_allow_html=True)

    # ---------- carousel banner with product images (#1) ----------
    shared.render_carousel(catalogue)

    # ---------- recommended for you — FIRST section (#5) ----------
    recs = shared.recommend_cosmetics(seed_ids=saved, prefs=prefs, k=9, exclude=excluded)
    caption = ("Based on your saved items." if saved
               else ("Sign in to tailor these to your taste." if guest
                     else "Popular picks — save items to personalise this."))
    shared.render_rail(
        "Recommended for you", caption, recs, catalogue, key_prefix="cos_home",
        user_id=uid, saved_set=saved_set, liked_set=liked, disliked_set=disliked,
        cart_set=cart_set,
    )

    # ---------- shop-by category / occasion shortcuts (#6) ----------
    _render_shortcuts()

    # ---------- on sale ----------
    sale_df = catalogue[catalogue["sale_price"].notna()]
    sale_ids = [a for a in sale_df["article_id"].astype(str).tolist() if a not in excluded][:9]
    if sale_ids:
        shared.render_rail(
            "On sale", "Limited-time prices — grab them while they last.", sale_ids, catalogue,
            key_prefix="cos_sale", user_id=uid, saved_set=saved_set,
            liked_set=liked, disliked_set=disliked, cart_set=cart_set,
        )


# Home shop-by shortcuts → jump to the catalogue pre-filtered (#6).
_SHORTCUTS = [
    ("Gifts for her", ":material/redeem:", {"f_tag": "Women", "f_quality": ["Luxury", "Premium"]}),
    ("Gifts for him", ":material/card_giftcard:", {"f_tag": "Men"}),
    ("Skincare", ":material/spa:", {"f_category": "Skincare"}),
    ("Fragrance", ":material/local_florist:", {"f_category": "Fragrance"}),
]
# All catalogue filter keys (persistent f_* + modal w_* + bookkeeping) — cleared
# before applying a shortcut so the preset starts from a clean slate.
_CAT_FILTER_KEYS = ("f_tag", "f_category", "f_brand", "f_type", "f_quality",
                    "f_size", "f_made", "f_shade", "f_price", "cat_search",
                    "cat_page", "cat_filter_signature",
                    "w_tag", "w_category", "w_brand", "w_type", "w_quality",
                    "w_size", "w_made", "w_shade", "w_price")


def _apply_shortcut(preset: dict):
    for k in _CAT_FILTER_KEYS:
        st.session_state.pop(k, None)
    st.session_state.update(preset)
    st.session_state["cat_page"] = 1
    st.session_state["_scroll_top"] = True
    st.switch_page("views/1_Catalogue.py")


def _render_shortcuts():
    st.markdown("<h2>Shop by</h2>", unsafe_allow_html=True)
    st.markdown('<p class="muted">Jump straight to a curated edit.</p>', unsafe_allow_html=True)
    cols = st.columns(len(_SHORTCUTS))
    for col, (label, icon, preset) in zip(cols, _SHORTCUTS):
        if col.button(label, icon=icon, key=f"sc_{label}", use_container_width=True):
            _apply_shortcut(preset)


def render_home(user):
    shared.apply_css()
    shared.render_sidebar(user)
    shared.scroll_to_top_if_flagged()

    if shared.cosmetics_mode():
        _render_cosmetics_home(user)
        return

    st.markdown(
        f'<div class="pill">Welcome back, {user["display_name"]}</div>',
        unsafe_allow_html=True,
    )
    st.markdown("<h1>Recommended for you.</h1>", unsafe_allow_html=True)
    st.markdown(
        '<p class="subtitle">Personalised rails powered by content-based, collaborative-filtering, '
        'and hybrid models — shaped by your saved items and preferences.</p>',
        unsafe_allow_html=True,
    )

    try:
        articles = shared.load_articles()
        vectorizer, tfidf = shared.load_content_based()
        als_model, _, als_item_index = shared.load_cf()
        hybrid_cfg = shared.load_hybrid_config()
        best_alpha = hybrid_cfg["best_alpha"] if hybrid_cfg else 0.5
    except FileNotFoundError as e:
        st.error(f"Missing artefact: `{e.filename}`")
        return

    item_id_to_row = shared.build_item_id_to_row(articles)
    als_item_to_row, candidate_items = shared.als_lookups(als_item_index)

    # Curated demo: gate all rails to the 50 curated products (matching photos)
    # via an `include` filter on each recommender. candidate_items MUST stay the
    # full ALS index — recommend_hybrid indexes its CF-score array by ALS row
    # position. Falls back to the full catalogue when no curated set is present.
    curated = shared.curated_set()
    curated_articles = articles[articles["article_id"].isin(curated)] if curated else articles
    include = curated or None

    # Single DB call replaces 3 separate connections.
    state = db.user_state(user["id"])
    saved = state["saved"]
    liked = state["liked"]
    disliked = state["disliked"]
    preferences = auth.get_preferences(user["id"])
    saved_set = set(saved)
    excluded = saved_set | disliked  # don't recommend saved-or-disliked
    cart_set = {l["article_id"] for l in db.get_cart(user["id"])}  # for in-cart ✓ on cards

    mmr_on = bool(st.session_state.get("mmr_enabled", True))
    # When MMR is on we ask each recommender for POOL_MULT × RAIL_SIZE
    # candidates and let MMR thin them down to RAIL_SIZE. When off, we just ask
    # for the exact rail size and skip the re-rank.
    pool_size = RAIL_SIZE * (POOL_MULT if mmr_on else 1)

    def _apply_mmr(recs):
        if not mmr_on or not recs:
            return list(recs or [])[:RAIL_SIZE]
        return shared.mmr_rerank(
            recs, tfidf, item_id_to_row, k=RAIL_SIZE, lambda_param=LAMBDA_MMR,
        )

    # ---------- A/B/n experiment: bucketed customers see ONE algorithm ----------
    # Each customer is assigned a single algorithm (db.experiment_bucket) so their
    # engagement is attributable to it. Admins/analysts are unbucketed → merged rails.
    assigned_algo = db.get_algorithm(user["id"])
    if assigned_algo:
        _render_single_algo_home(
            assigned_algo, user, articles, tfidf, vectorizer,
            als_model, als_item_index, als_item_to_row, candidate_items,
            item_id_to_row, saved, saved_set, liked, disliked, preferences,
            excluded, best_alpha, include, mmr_on, cart_set,
        )
        return

    # Session-state memoization keyed on (user_id, interactions sig, alpha, mmr_on).
    cache_key = ("home_rails_v3", user["id"], state["signature"], best_alpha, RAIL_SIZE, mmr_on)
    cached = st.session_state.get("rail_cache")
    if cached and cached.get("key") == cache_key:
        picked_recs = cached["picked_recs"]
        rail1_reasons = cached["rail1_reasons"]
        latest_similar = cached["latest_similar"]
        customers_recs = cached["customers_recs"]
        customers_reasons = cached["customers_reasons"]
        trending_recs = cached["trending_recs"]
        trending_reasons = cached["trending_reasons"]
        new_arrivals_recs = cached["new_arrivals_recs"]
        new_arrivals_reasons = cached["new_arrivals_reasons"]
        rail_ild = cached["rail_ild"]
        profile = cached["profile"]
    else:
        profile = shared.build_user_profile(saved, preferences, articles, tfidf, item_id_to_row)
        # Picked-for-you: hybrid, MMR re-ranked → hybrid-style "both models agree" reason
        hybrid_pool = shared.recommend_hybrid(
            profile, tfidf, item_id_to_row,
            als_model, als_item_index, als_item_to_row,
            candidate_items, saved_set, excluded, best_alpha, pool_size,
            include=include,
        ) or []
        picked_recs = _apply_mmr(hybrid_pool)
        picked_ids = [a for a, _ in picked_recs]
        rail1_reasons = shared.explain_hybrid_for_items(
            profile, picked_ids, tfidf, item_id_to_row, vectorizer, best_alpha,
        )
        # Because-you-saved-X: CB similar items
        if saved:
            latest_aid = saved[-1]
            sim_pool = shared.recommend_similar(
                latest_aid, tfidf, item_id_to_row, k=pool_size, exclude=excluded,
                include=include,
            ) or []
            similar_recs = _apply_mmr(sim_pool)
            latest_similar = {"aid": latest_aid, "recs": similar_recs}
        else:
            latest_similar = None
        # Customers like you also liked: pure ALS
        cust_pool = shared.recommend_customers_like_you(
            als_model, als_item_index, als_item_to_row,
            saved_set, excluded, k=pool_size, include=include,
        )
        customers_recs = _apply_mmr(cust_pool)
        # Trending: pure popularity
        trend_pool = shared.recommend_trending(excluded, k=pool_size, include=include)
        trending_recs = _apply_mmr(trend_pool)
        # New arrivals: recency-filtered by preferences (within the curated set)
        new_pool = shared.recommend_new_arrivals(curated_articles, preferences, excluded, k=pool_size)
        new_arrivals_recs = _apply_mmr(new_pool)

        # Per-rail explanation maps (rail-appropriate framing per supervisor §3.5)
        customers_reasons = shared.explain_cf_for_items([a for a, _ in customers_recs])
        trending_reasons = shared.explain_trending(
            [a for a, _ in trending_recs], shared.load_trending(),
        )
        new_arrivals_reasons = shared.explain_new_arrivals(
            [a for a, _ in new_arrivals_recs], preferences,
        )

        # ILD score per rail — measured on the *post-MMR* list (what the user sees)
        rail_ild = {
            "picked":   shared.intra_list_diversity(picked_recs, tfidf, item_id_to_row),
            "similar":  (shared.intra_list_diversity(latest_similar["recs"], tfidf, item_id_to_row)
                         if latest_similar else 0.0),
            "customers": shared.intra_list_diversity(customers_recs, tfidf, item_id_to_row),
            "trending":  shared.intra_list_diversity(trending_recs, tfidf, item_id_to_row),
            "new":       shared.intra_list_diversity(new_arrivals_recs, tfidf, item_id_to_row),
        }

        st.session_state["rail_cache"] = {
            "key": cache_key,
            "picked_recs": picked_recs,
            "rail1_reasons": rail1_reasons,
            "latest_similar": latest_similar,
            "customers_recs": customers_recs,
            "customers_reasons": customers_reasons,
            "trending_recs": trending_recs,
            "trending_reasons": trending_reasons,
            "new_arrivals_recs": new_arrivals_recs,
            "new_arrivals_reasons": new_arrivals_reasons,
            "rail_ild": rail_ild,
            "profile": profile,
        }

    # Prefetch images for everything that will be rendered, in parallel. The
    # disk cache is shared across users so successive page loads are instant
    # for any article that's been displayed before.
    prefetch_items = []
    seen_aids = set()
    def _collect(rec_list):
        for entry in rec_list or []:
            aid = entry[0] if isinstance(entry, tuple) else entry
            if aid in seen_aids:
                continue
            seen_aids.add(aid)
            row = articles[articles["article_id"] == aid]
            if not row.empty:
                prefetch_items.append(row.iloc[0].to_dict())
    _collect(picked_recs)
    if latest_similar:
        _collect(latest_similar.get("recs"))
    _collect(customers_recs)
    _collect(trending_recs)
    _collect(new_arrivals_recs)
    if prefetch_items:
        with st.spinner(f"Fetching product images ({len(prefetch_items)} items)…"):
            shared.prefetch_images_sync(prefetch_items, timeout=14.0)

    def _ild_suffix(score: float) -> str:
        if not mmr_on:
            return f" · ILD {score:.2f} (no MMR)"
        return f" · ILD {score:.2f} · MMR λ={LAMBDA_MMR}"

    # ---------- Rail 1: Picked for you (Hybrid) ----------
    if saved:
        rail1_caption = (
            f"Hybrid · {len(saved)} saved item{'s' if len(saved) != 1 else ''} shape this rail · "
            f"α = {best_alpha:.2f}"
        )
    elif preferences:
        prefs_str = ", ".join(preferences[:3]) + ("…" if len(preferences) > 3 else "")
        rail1_caption = f"Seeded from your preferences: {prefs_str}"
    else:
        rail1_caption = "Cold start — pick preferences or save items to personalise."
    rail1_caption += _ild_suffix(rail_ild["picked"])
    shared.render_rail(
        "Picked for you", rail1_caption, picked_recs, articles,
        key_prefix="rail_picked", user_id=user["id"],
        saved_set=saved_set, liked_set=liked, disliked_set=disliked,
        reasons=rail1_reasons, cart_set=cart_set,
    )

    # ---------- Rail 2: Because you saved X (Content-Based) ----------
    if latest_similar:
        latest_aid = latest_similar["aid"]
        latest_row = articles[articles["article_id"] == latest_aid]
        latest_name = latest_row.iloc[0]["prod_name"] if not latest_row.empty else latest_aid
        similar_recs = latest_similar["recs"]
        similar_ids = [a for a, _ in similar_recs]
        rail2_reasons = shared.explain_similar_to(latest_aid, similar_ids, articles)
        shared.render_rail(
            f"Because you saved {latest_name}",
            "Content-based · TF-IDF cosine on product metadata"
            + _ild_suffix(rail_ild["similar"]),
            similar_recs, articles,
            key_prefix=f"rail_similar_{latest_aid}",
            user_id=user["id"], saved_set=saved_set,
            liked_set=liked, disliked_set=disliked,
            reasons=rail2_reasons, cart_set=cart_set,
        )

    # ---------- Rail 3: Customers like you also liked (pure ALS / CF) ----------
    if saved_set:
        shared.render_rail(
            "Customers like you also liked",
            "Collaborative filtering · ALS latent-factor neighbours of your saved items"
            + _ild_suffix(rail_ild["customers"]),
            customers_recs, articles,
            key_prefix="rail_customers",
            user_id=user["id"], saved_set=saved_set,
            liked_set=liked, disliked_set=disliked,
            reasons=customers_reasons, cart_set=cart_set,
        )

    # ---------- Rail 4: Trending this week (popularity) ----------
    shared.render_rail(
        "Trending this week",
        "Most-purchased items across the catalogue" + _ild_suffix(rail_ild["trending"]),
        trending_recs, articles,
        key_prefix="rail_trending",
        user_id=user["id"], saved_set=saved_set,
        liked_set=liked, disliked_set=disliked,
        reasons=trending_reasons, cart_set=cart_set,
    )

    # ---------- Rail 5: New arrivals in your style ----------
    if preferences:
        new_caption = f"Newest arrivals in your preferred categories: {', '.join(preferences[:3])}"
    else:
        new_caption = "Latest catalogue additions — pick preferences in your profile to refine"
    new_caption += _ild_suffix(rail_ild["new"])
    shared.render_rail(
        "New arrivals in your style",
        new_caption,
        new_arrivals_recs, articles,
        key_prefix="rail_new",
        user_id=user["id"], saved_set=saved_set,
        liked_set=liked, disliked_set=disliked,
        reasons=new_arrivals_reasons, cart_set=cart_set,
    )

    # The old "Compare algorithms (research view)" expander has been promoted to
    # a dedicated page at `app/pages/4_Compare.py` — see the sidebar nav for
    # the parallel-columns view with the live α slider.


def _home_page():
    """Home — works for both logged-in users and guests (user may be None)."""
    render_home(st.session_state.get("user"))


def main():
    db.init_db()
    shared.mount_cookie_controller()   # mount once per run so set/remove work
    shared.restore_session()           # rehydrate user from cookie (no flash)
    shared.ensure_session_cookie()     # self-heal the cookie if a login set was lost
    shared.check_session_timeout()
    user = st.session_state.get("user")

    shared.render_brand()  # project logo, top-left above the sidebar nav

    if user is None:
        # Sign-in screen renders with NO sidebar (position="hidden") so submitting
        # the login form never flashes the nav — it completes on the sign-in page,
        # then the next run (user set) routes to the main app (#4). Entered via the
        # guest Sign-in button / "sign in to buy" actions, which set `auth_view`.
        if st.session_state.get("auth_view"):
            st.navigation(
                [st.Page(render_auth_screen, title="Sign in", url_path="signin")],
                position="hidden",
            ).run()
            return
        # Public browsing (#2): guests browse the Catalogue (their landing page —
        # no Home section until they sign in, #1) + Compare + product detail;
        # ordering / saving requires sign-in.
        cmp_n = len(shared.compare_ids())
        st.navigation([
            st.Page("views/1_Catalogue.py", title="Catalogue",
                    icon=":material/storefront:", url_path="catalogue", default=True),
            st.Page("views/_compare.py", title=f"Compare ({cmp_n})" if cmp_n else "Compare",
                    icon=":material/balance:", url_path="compare"),
            st.Page("views/_product.py", title="Product", url_path="product"),
        ], position="sidebar").run()
        return

    role = user.get("role")
    if role == "admin":
        # Admin is a back-office role only — the control-room dashboard (its own
        # dark UI is rendered inside the page; Streamlit's sidebar is hidden there).
        pages = [
            st.Page("views/_analytics.py", title="Dashboard",
                    icon=":material/dashboard:", url_path="dashboard", default=True),
        ]
    else:
        # Everyone non-admin gets the customer storefront.
        n_cart = db.cart_count(user["id"])
        cart_title = f"Cart ({n_cart})" if n_cart else "Cart"
        cmp_n = len(shared.compare_ids())
        _home = st.Page(_home_page, title="Home", icon=":material/home:",
                        url_path="home", default=True)
        st.session_state["_home_page"] = _home  # so hidden pages can route back home
        pages = [
            _home,
            st.Page("views/1_Catalogue.py", title="Catalogue",
                    icon=":material/storefront:", url_path="catalogue"),
            st.Page("views/_compare.py", title=f"Compare ({cmp_n})" if cmp_n else "Compare",
                    icon=":material/balance:", url_path="compare"),
            st.Page("views/2_Wishlist.py", title="Wishlist",
                    icon=":material/favorite:", url_path="wishlist"),
            st.Page("views/_cart.py", title=cart_title,
                    icon=":material/shopping_bag:", url_path="cart"),
            # Hidden pages — reached via buttons / switch_page; nav links hidden in CSS.
            st.Page("views/_product.py", title="Product", url_path="product"),
            st.Page("views/_checkout.py", title="Checkout", url_path="checkout"),
            st.Page("views/_success.py", title="Order confirmed", url_path="success"),
            st.Page("views/_orders.py", title="Payment history", url_path="orders"),
        ]

    st.navigation(pages, position="sidebar").run()


main()
