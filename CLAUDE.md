# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

BTEC L6 Unit 2 Independent Project (PDP University, due 2026-06-01): hybrid product recommendation system on the H&M Personalized Fashion Recommendations dataset. The four algorithms (TF-IDF content-based, ALS collaborative filtering via `implicit`, weighted hybrid, NeuMF) are implemented across notebooks 02–05 and exposed via an **auth-gated multi-page Streamlit platform**. Supervisor scoped this as a "real product" submission, not just an academic demo — the platform layer is graded, not optional.

**The platform was pivoted (2026-06) into "Chiroyli" — a gold-themed cosmetics marketplace.** This is the current user-facing product. Because the H&M-trained models only score H&M article IDs, the cosmetics catalogue uses a **separate content-based recommender** (`shared.recommend_cosmetics`, TF-IDF over generated cosmetics attributes); the four trained models + their quantitative evaluation remain the academic core and still back the analyst-only Evaluation/Algorithms pages. The marketplace adds: a 3-slide carousel, public browse with an auth gate at order time, on-sale + recommended rails, pagination, category/brand/quality/size/made-in/shade filters + men/women/kids tags, reviews & ratings, Asaxiy-style product comparison, a rule-based "Ask Chiroyli" assistant (no external LLM), an offline "Order now" flow + in-app notifications, online cart/checkout, and a seller panel. **`CLAUDE.md` describes both layers; `docs/` (findings_*.md, final_report.md, project_explained.md) still describe the pre-pivot H&M fashion platform and are stale.**

**Cosmetics mode is auto-detected:** `shared.cosmetics_mode()` is true when `app/assets/cosmetics_products.csv` exists, which flips `load_articles()` to the cosmetics catalogue and the home/catalogue/product pages to their cosmetics branches. Delete that CSV to fall back to the H&M fashion catalogue.

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

# Seed demo accounts (customer/admin/analyst/seller + a cold-start user) — used by sync.sh, runnable locally
python -m app.auth seed-demos
```

Demo accounts (committed credentials, all `@example.com`): `demo_customer`/`Demo2026!`, `demo_admin`/`Admin2026!`, `demo_analyst`/`Analyst2026!`, `demo_seller`/`Seller2026!`, `cold_user`/`Cold2026!`.

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
- **`app/db.py`** — SQLite (at `data/app.db`, gitignored). Tables: `users`, `preferences`, `interactions`, `login_attempts`, `sessions` (persistent-login tokens), `experiment_bucket` (A/B/n algorithm assignment — legacy H&M feature), `cart`, `orders` + `order_items` (status `paid`/`offline`), `reviews` (one per user per article), `notifications`, and `seller_products` (marketplace listings). `interactions` is append-only with event types `view/save/unsave/like/unlike/dislike/undislike/purchase/rate_1..5`. State (wishlist, likes, dislikes) is derived by replaying the event log per user — see `_toggle_set`. **`ORDER BY created_at, id`** everywhere because `datetime('now')` has 1-second resolution; ties without a deterministic tiebreaker break the toggle semantics. **Migration gotcha:** relaxing a CHECK constraint (e.g. adding a role) needs a table rebuild; the `ALTER TABLE users RENAME` cascades into *every* child table's FK unless both `legacy_alter_table=ON` **and** `foreign_keys=OFF` are set, and those pragmas are no-ops inside a transaction. Do all `users`/role rebuilds via `db._migrate_user_role()` — it uses a dedicated autocommit connection and self-repairs any table left pointing at `users_old`. Never add another rename-based migration inside the `init_db()` transaction.
- **`app/auth.py`** — pure functions (no Streamlit imports): `register`, `authenticate`, `set_preferences`, `get_preferences`. Bcrypt-hashed passwords. `MIN_PASSWORD_LEN = 8`; email regex requires TLD ≥ 2 chars; roles whitelisted to `customer`/`admin`/`analyst`/`seller` (`ALLOWED_ROLES`). `analyst` sees Analytics (not Admin); `seller` is back-office only (Seller panel); `admin` is back-office only (Analytics + Admin). Keep pure so CLI scripts can call them. Demo-account seeding lives here (`seed_demo_accounts()`, exposed as `python -m app.auth seed-demos`) and seeds `DEMO_SELLER_PRODUCTS` for the demo seller.
- **`app/shared.py`** — all UI helpers, cached loaders (`@st.cache_resource`), recommenders, explainability, the `CUSTOM_CSS` design system (gold "Chiroyli" theme; tokens in `.streamlit/config.toml`), and the **persistent-session helpers** (`mount_cookie_controller`/`establish_session`/`restore_session`/`clear_session` — writes via `streamlit-cookies-controller`, reads via `st.context.cookies`). `render_brand()` puts the logo (`app/assets/logo.svg` — gold bloom + "Chiroyli" wordmark; `logo_icon.svg` collapsed) top-left via `st.logo`.
  - **Cosmetics layer:** `load_cosmetics()` reads `app/assets/cosmetics_products.csv` (51 products, `C`-prefixed ids) **and unions in active `seller_products`** (`S`-prefixed ids), mapping seller rows onto the full catalogue schema. `recommend_cosmetics(seed_ids, prefs, k, exclude)` is the cosmetics content recommender (`_cosmetics_tfidf`, cached). `catalogue_price`/`effective_price`/`display_price` are sale-aware. **After any seller mutation call `shared.refresh_catalogue()`** (clears `load_cosmetics` + `_cosmetics_tfidf`). `cosmetics_assistant_reply(query, catalogue)` is the rule-based "Ask Chiroyli" assistant (parses category/type/brand/shade/made-in/audience/quality/price-cap/on-sale/gift/skin-concern → scored picks). `compare_ids`/`in_compare`/`toggle_compare` back the product-compare tray (`COMPARE_MAX=4`).
  - **Image resolution** (`_resolve_image_src`): **Tier 0** = seller `image_url` (http/data URI), **Tier 0a** = committed `app/assets/cosmetics/{aid}.jpg`, **Tier 0b** = `app/assets/products/{aid}.jpg` (legacy fashion), then local H&M / cached / picsum fallback. **Prices in markdown must use `&#36;` not `$`** — two bare `$` on a line trigger Streamlit's LaTeX math mode.
  - **H&M legacy recommenders** (`recommend_cb/als/hybrid/ncf/similar/trending`) take **`positives` (profile signal) + `excluded` (output filter)** as separate sets and an `include` filter so they **rank within** a subset rather than top-k-then-filter. `load_articles()` returns the FULL df (the TF-IDF matrix is positionally aligned — never shrink it). **ALS uses `recalculate_user=True`** to fold platform users in. These back the analyst Evaluation/Algorithms pages only.
- **`app/main.py`** — entry point and **`st.navigation` router** (Streamlit ≥1.50). Each run: `mount_cookie_controller()` → `restore_session()` → `check_session_timeout()` → `render_brand()`. Four role branches build the page list (visibility = page registration, not per-page buttons): **guest** (Home/Catalogue/Compare/Sign-in; stashes the sign-in `st.Page` in `_signin_page` so action buttons can `switch_page` to it), **admin** (Analytics + Admin only), **seller** (Seller panel only), **customer/analyst** (Home/Catalogue/Compare/Wishlist/Cart, + Evaluation/Algorithms/Analytics for analyst, + hidden product/checkout/success). `_render_cosmetics_home(user)` renders the carousel + on-sale rail + recommended rail + the "Ask Chiroyli" assistant (`_render_assistant`); guests are supported throughout (`user=None`).
- **`app/pages/`** — registered by `main.py`'s `st.navigation` (filename prefix is cosmetic). Consumer: `1_Catalogue.py` (cosmetics filter UI + tags + pagination, public), `2_Wishlist.py`, `_compare.py` (Asaxiy-style product comparison, public), `_product.py` (detail view + reviews + similar items + add-to-cart + offline order-now + compare toggle; guests see "Sign in to buy"), `_cart.py`/`_checkout.py` (inline red-border validation)/`_success.py` (balloons). Seller: `_seller.py` (metrics + My products with show/hide/edit/delete + Add-product form + Orders table; `seller` role only). Analyst/research: `3_Evaluation.py`, `4_Compare.py` (four algorithms side-by-side, live α — registered as "Algorithms", `url_path="algo-compare"`), `_analytics.py` (also admin). `_product.py`/`_checkout.py`/`_success.py` are hidden from the menu via CSS (`a[href$="/product"]` etc.), since `st.navigation` has no per-page hide. Pages call `shared.render_sidebar(user)` (top-right account menu via `render_account_menu` — avatar popover with notifications + logout; sidebar docs/display-options for analyst only).
- **`app/retrain.py`** — `retrain_als()` rebuilds the ALS user-item matrix from a recent H&M slice + currently-active platform saves/likes/purchases, fits ALS at the same `factors` as the previous bundle, and overwrites `models/cf_als_model.pkl`. Platform users are keyed `"app:<id>"` to share the matrix with H&M customers without ID collision. Platform interactions are weighted 3× vs H&M's 1× because explicit feedback is stronger signal. The admin page calls `shared.load_cf.clear()` afterwards to flush the cached model.

## Constraints & conventions

- **Data and models are gitignored.** `data/` requires manual Kaggle download of `articles.csv`, `customers.csv`, `transactions_train.csv` (~3.5 GB). `data/app.db` is the platform's SQLite store, also gitignored and auto-created by `db.init_db()`. `models/` must be regenerated by re-running notebooks 02–05 in order (04 depends on 02 and 03's artefacts; 06 evaluates all four).
- **`article_id` is a string.** All loaders pin `dtype={"article_id": str}` — preserve this when adding new IO. Leading zeros in IDs break joins if cast to int. Cosmetics ids are `C`-prefixed (CSV) / `S`-prefixed (seller-added); H&M ids are numeric.
- **Cosmetics assets ARE committed** (unlike H&M data/models): `app/assets/cosmetics_products.csv` + `app/assets/cosmetics/{aid}.jpg` (51 products), `app/assets/products/*.jpg` + `curated_products.csv` (legacy fashion), and the Chiroyli logos/login art. Regenerate the cosmetics set with `scripts/generate_cosmetics.py` (needs a Pexels API key in `.streamlit/secrets.toml`, which is gitignored — never commit it).
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
