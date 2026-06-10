# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

BTEC L6 Unit 2 Independent Project (PDP University, due 2026-06-01): hybrid product recommendation system on the H&M Personalized Fashion Recommendations dataset. The four algorithms (TF-IDF content-based, ALS collaborative filtering via `implicit`, weighted hybrid, NeuMF) are implemented across notebooks 02–05 and exposed via an **auth-gated multi-page Streamlit platform** (signup/login, catalogue browse, wishlist, personalised home rails, explicit feedback capture, "Why recommended" explanations, admin panel with on-demand ALS retraining). Supervisor scoped this as a "real product" submission, not just an academic demo — the platform layer is graded, not optional.

## Common commands

```bash
# Activate the project venv (Python 3.12, lives in .venv/)
source .venv/bin/activate

# Run the demo app (from repo root — main.py adds REPO_ROOT to sys.path itself)
streamlit run app/main.py

# Run a single notebook end-to-end (e.g. to regenerate model artefacts)
jupyter nbconvert --to notebook --execute notebooks/02_content_based.ipynb --inplace

# Deploy to a fresh Ubuntu 24.04 droplet
bash deploy/install.sh   # see deploy/install.sh for required kaggle creds at /root/.kaggle/

# Update an EXISTING droplet with local code (run from laptop) — syncs app/, src/, outputs/,
# docs, precomputed pickles + image cache, refreshes deps, runs migrations, restarts streamlit
bash deploy/sync.sh      # override target: DROPLET=root@1.2.3.4 bash deploy/sync.sh

# Seed demo accounts (customer/admin/analyst + a cold-start user) — used by sync.sh, runnable locally
python -m app.auth seed-demos
```

No test suite, linter, or CI is configured — verify correctness via the notebooks' own assertions and by running the Streamlit app.

## Architecture

Two layers: a notebook-first pipeline that produces pickled model artefacts, and a Streamlit platform layer that consumes them.

```
notebooks/02–05  →  models/*.pkl, *.npz, *.pt  ─┐
                                                 ▼
                                            app/shared.py  ─► app/main.py + pages/
                                                 ▲                       │
                                            app/db.py  ◄─────── interactions ◄── users
                                                 ▲                       │
                                            app/retrain.py  (admin-triggered ALS refit, writes models/cf_als_model.pkl)

src/data.py, src/metrics.py  (shared loaders + eval, used by both notebooks and app/retrain.py)
```

**Notebook / model layer**
- **`src/data.py`** — the only sanctioned way to read the H&M CSVs. `load_transactions` has three mutually-exclusive memory-bounded modes — `nrows` (chronological head, biased — avoid for modelling), `sample_frac` (uniform random sample — use for EDA only), and `last_months` (recent window — use for modelling, matches the H&M competition protocol). `time_based_split` is the canonical train/test split; never use random splits on transaction data here.
- **`src/metrics.py`** — Top-N evaluation metrics (Precision/Recall/HitRate/MAP/NDCG @ k). `evaluate()` skips users absent from the recommendations dict (treats them as cold-start for that algorithm), so per-algorithm `users_evaluated` counts differ — compare metrics with that in mind.
- **Model artefacts** (all under `models/`, gitignored): `content_based_vectorizer.pkl` + `content_based_item_tfidf.npz` (notebook 02), `cf_als_model.pkl` (03, an `implicit` ALS bundle with `model`, `user_index`, `item_index` keys), `hybrid_config.pkl` (04, holds tuned `best_alpha`), `ncf_neumf.pt` + `ncf_id_maps.pkl` (05). Two **precomputed platform pickles** are not notebook-generated — `trending.pkl` and `article_prices.pkl` — and are synced to the droplet by `deploy/sync.sh` (step 3) rather than regenerated on the server. Admin retrain (see below) **overwrites** `cf_als_model.pkl` — coordinate with notebook 03 reruns.

**Platform layer (`app/`)** — every page imports from `app.shared`, which holds the cached loaders, recommenders, and card renderers.
- **`app/db.py`** — SQLite (at `data/app.db`, gitignored). Tables: `users`, `preferences`, `interactions`, `login_attempts`, and `sessions` (server-side persistent-login tokens — `token`/`user_id`/`expires_at`; helpers `create_session`/`get_session_user`/`delete_session`, expired rows purged in `init_db()`). `interactions` is append-only with event types `view/save/unsave/like/unlike/dislike/undislike/purchase`. State (wishlist, likes, dislikes) is derived by replaying the event log per user — see `_toggle_set`. Includes a one-shot migration in `init_db()` for older schemas missing `unlike`/`undislike`. **`ORDER BY created_at, id`** everywhere because `datetime('now')` has 1-second resolution; ties without a deterministic tiebreaker break the toggle semantics.
- **`app/auth.py`** — pure functions (no Streamlit imports): `register`, `authenticate`, `set_preferences`, `get_preferences`. Bcrypt-hashed passwords. `MIN_PASSWORD_LEN = 8`; email regex requires TLD ≥ 2 chars; roles whitelisted to `customer` / `admin` / `analyst` (`ALLOWED_ROLES`). `analyst` sees the Analytics dashboard but not the Admin panel. Keep pure so CLI scripts can call them. Demo-account seeding lives here too — `seed_demo_accounts()`, exposed as `python -m app.auth seed-demos`.
- **`app/shared.py`** — all UI helpers, cached loaders (`@st.cache_resource`), recommenders, explainability, the `CUSTOM_CSS` design system (editorial theme; theme **tokens** live in `.streamlit/config.toml`), and the **persistent-session helpers** (`mount_cookie_controller`/`establish_session`/`restore_session`/`clear_session`). Writes go through `streamlit-cookies-controller` (mounted once per run); reads use `st.context.cookies`. Logout and idle-timeout both call `clear_session()` so the cookie can't silently re-auth the user. `render_brand()` puts the project logo (`app/assets/logo.svg` — vermilion hanger mark + "Wardrobe." wordmark; `logo_icon.svg` for the collapsed sidebar) top-left above the nav via `st.logo`; edit the SVG `<text>` to rename.
- **Curated demo catalogue (50 products).** The consumer surfaces (catalogue, home rails, Compare) are gated to **50 curated real H&M article IDs** listed in `app/assets/curated_products.csv`, each with a hand-verified matching photo committed at `app/assets/products/{article_id}.jpg` (clean Pexels stock, sourced once). `shared.curated_ids()/curated_set()` expose the list; pages filter display to it and pass `include=curated_set()` to the recommenders (`recommend_cb/als/hybrid/ncf/similar/trending` all take an `include` filter so they **rank within** the 50 rather than top-k-then-filter). `_resolve_image_src` has a **Tier 0** that returns `app/assets/products/{aid}.jpg` when present, so curated photos always win. **Important:** `load_articles()` still returns the FULL df — the content-based TF-IDF matrix is positionally aligned to it, so it must not be shrunk; and `recommend_hybrid`'s `candidate_items` must stay the full ALS index (its CF-score array is indexed by ALS row position) — gating is done via `include`, never by shrinking those. Remove/empty the CSV to fall back to the full catalogue. Recommender signatures take **`positives` (fold-in/profile signal) and `excluded` (output filter) as separate sets** — saves go in both, dislikes go only in `excluded`. **ALS calls use `recalculate_user=True`** to fold the platform user in on the fly; the saved model was trained on H&M customer IDs that don't match platform users.
- **`app/main.py`** — entry point and **`st.navigation` router** (requires Streamlit ≥1.50). On every run it calls `shared.mount_cookie_controller()` → `shared.restore_session()` (rehydrates `st.session_state["user"]` from the session cookie, read instantly from `st.context.cookies` — no flash) → `check_session_timeout()`. If logged out it registers **only** the auth page with `position="hidden"` (no sidebar, no menu, no flash); if logged in it builds the page list (Home/Catalogue/Wishlist/Evaluation/Compare, plus Analytics for admin/analyst and Admin for admin — role gating is now **page registration**, not per-page buttons). The home page itself shows two product rails ("Picked for you" hybrid, "Because you saved X" content-based). The old "Compare algorithms" expander lives in the dedicated `4_Compare.py` page.
- **`app/pages/`** — page targets registered by `main.py`'s `st.navigation` (the filename-prefix convention is now cosmetic — `main.py` controls visibility, not Streamlit's native multipage). `1_Catalogue.py`, `2_Wishlist.py`, `3_Evaluation.py` (quantitative metrics dashboard surfacing notebook 06's outputs — all roles), `4_Compare.py` (all four algorithms side-by-side, live α slider, per-column ILD). `_admin.py` (admins) and `_analytics.py` (`admin`/`analyst`) are added to the menu only when the role qualifies. `_product.py` (detail view, reached via `st.switch_page` from card View buttons) is registered with `url_path="product"` but **hidden from the menu via one CSS rule** (`a[href$="/product"]`), since `st.navigation` has no per-page hide. The Evaluation/Compare/Analytics pages read precomputed CSVs/figures from `outputs/{evaluation,hybrid,neural_cf}/`. Pages still call `shared.render_sidebar(user)`, which renders the **top-right account menu** (`render_account_menu` — a circular initials avatar popover with name/email/role/logout, pinned via the `.st-key-account_menu` CSS scope) plus the sidebar's docs + display-options. Identity and logout live in that top-right menu, not the sidebar; page **links** come from `st.navigation`.
- **`app/retrain.py`** — `retrain_als()` rebuilds the ALS user-item matrix from a recent H&M slice + currently-active platform saves/likes/purchases, fits ALS at the same `factors` as the previous bundle, and overwrites `models/cf_als_model.pkl`. Platform users are keyed `"app:<id>"` to share the matrix with H&M customers without ID collision. Platform interactions are weighted 3× vs H&M's 1× because explicit feedback is stronger signal. The admin page calls `shared.load_cf.clear()` afterwards to flush the cached model.

## Constraints & conventions

- **Data and models are gitignored.** `data/` requires manual Kaggle download of `articles.csv`, `customers.csv`, `transactions_train.csv` (~3.5 GB). `data/app.db` is the platform's SQLite store, also gitignored and auto-created by `db.init_db()`. `models/` must be regenerated by re-running notebooks 02–05 in order (04 depends on 02 and 03's artefacts; 06 evaluates all four).
- **`article_id` is a string.** All loaders pin `dtype={"article_id": str}` — preserve this when adding new IO. Leading zeros in IDs break joins if cast to int.
- **`scikit-surprise` and `lightfm` are intentionally NOT in requirements** (numpy 2.x ABI conflict). Use `implicit` for ALS-style matrix factorisation; do not re-add the dropped packages.
- **`bcrypt` is required** for the platform's auth layer — listed in requirements.txt alongside Streamlit. **`plotly`** backs the Evaluation/Compare/Analytics dashboards, and **`streamlit-cookies-controller`** backs persistent login (added after v1; `deploy/sync.sh` step 4 reinstalls deps to pick them up on existing droplets). **Streamlit is pinned `>=1.50`** — `st.navigation` routing and the `config.toml` theme tokens (`baseRadius`, `borderColor`, `[[theme.fontFaces]]`/Google-Fonts shorthand, `[theme.sidebar]`) both require it.
- **The visual theme is split**: design *tokens* (palette, radii, fonts — Fraunces display + Inter body via Google-Fonts shorthand) live in `.streamlit/config.toml`; component CSS lives in `shared.CUSTOM_CSS`. Changing fonts/theme in `config.toml` **requires a server restart** (`deploy/sync.sh` step 6 restarts streamlit). `sync.sh` step 1 now rsyncs `.streamlit/` so theme changes deploy with the rest of the code.
- **Notebook 05 has two variants**: `05_neural_cf.ipynb` (local) and `05_neural_cf_colab.ipynb` (Colab/GPU). Keep them in sync when changing the NCF architecture.
- **Reports under `docs/`** (`findings_*.md`, `final_report.md`, etc.) are deliverables for the BTEC submission — when results change, update the relevant `findings_*.md` rather than overwriting `final_report.md` directly. `docs/project_explained.md` and its rendered PDF describe the pre-platform state — supersede them in the final report rather than editing them in place.
- **`logbook.md` is gitignored and personal** — do not read, edit, or reference it.
- **Seeding the admin user**: `python -c "from app import auth, db; db.init_db(); print(auth.register('admin@example.com','changeme123','Admin',role='admin'))"`. Or promote an existing user: `python -c "from app import db;\nimport sqlite3\nwith db.get_conn() as c: c.execute(\"UPDATE users SET role='admin' WHERE email=?\", ('user@x',)); c.commit()"`.

## Deployment

`deploy/install.sh` is a one-shot bootstrap for an Ubuntu 24.04 DigitalOcean droplet: installs system deps, clones the repo to `/opt/gradproject`, creates the venv, downloads the dataset via Kaggle CLI, writes a `streamlit.service` systemd unit, and configures nginx as a reverse proxy on port 80 **with gzip enabled for JS/CSS/JSON/wasm/SVG** (large GTmetrix win — Streamlit's bundled JS is ~2.5 MB uncompressed). Model `.pkl`/`.pt` files are **not** downloaded by the script — rsync them from a local machine after the script prints its rsync hint. For **existing** droplets, `deploy/sync.sh` (run from the laptop) is the canonical update path: it rsyncs `app/`/`src/`/`outputs/`/docs/precomputed-pickles/`image_cache`, rewrites the nginx site fragment (gzip + WS-friendly 86400s timeout), reinstalls deps, runs `db.init_db()` migrations, seeds demo accounts, and restarts the `streamlit` service. It does **not** sync the large model artefacts — push those separately.

**Perf reminder**: GTmetrix tests must hit port 80 (nginx-fronted) — port 8501 bypasses gzip and reports Grade E. After deploying nginx config changes: `sudo nginx -t && sudo systemctl reload nginx`. The `min-height: 920px` rule on `.block-container` in `app/shared.py` reserves vertical space to avoid the CLS shift that previously dragged Core Web Vitals down.
