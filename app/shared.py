"""Shared loaders, recommenders, and UI helpers for every page.

The Streamlit page scripts (`app/main.py` and `app/pages/*.py`) all import
from here. Cached resources are keyed by function identity, so a single
`load_articles()` call is shared across the whole app.
"""

from __future__ import annotations

import pickle
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
from scipy.sparse import csr_matrix, load_npz
from sklearn.preprocessing import normalize

from app import auth, db

REPO_ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = REPO_ROOT / "models"
IMAGE_DIR = REPO_ROOT / "data" / "images"
IMAGE_CACHE_DIR = REPO_ROOT / "data" / "image_cache"
ASSETS_DIR = REPO_ROOT / "app" / "assets"


@st.cache_data(show_spinner=False)
def curated_ids() -> list[str]:
    """Ordered list of the 50 curated demo article IDs (app/assets/curated_products.csv).

    Empty list ⇒ no curation (app falls back to the full catalogue). The visible
    catalogue, home rails, and recommendation candidate pools are gated to these
    IDs; the full articles df is still loaded for TF-IDF row alignment.
    """
    if cosmetics_mode():
        return []  # cosmetics is the whole catalogue — no fashion-curated gating
    p = ASSETS_DIR / "curated_products.csv"
    if not p.exists():
        return []
    return pd.read_csv(p, dtype={"article_id": str})["article_id"].tolist()


def curated_set() -> set:
    return set(curated_ids())


# ---------- product comparison (Asaxiy-style, session-scoped) ----------
COMPARE_MAX = 4
_COMPARE_COOKIE = "bk_compare"


def compare_ids() -> list:
    """Article IDs in the compare tray. Persisted in a cookie so it survives the
    full-page reloads triggered by clicking a card link (#3)."""
    if "compare_ids" not in st.session_state:
        try:
            raw = st.context.cookies.get(_COMPARE_COOKIE) or ""
        except Exception:
            raw = ""
        st.session_state["compare_ids"] = [a for a in raw.split(",") if a][:COMPARE_MAX]
    return st.session_state["compare_ids"]


def _persist_compare(lst: list) -> None:
    try:
        _cookie_controller().set(_COMPARE_COOKIE, ",".join(lst),
                                 max_age=86400, same_site="lax", path="/")
    except Exception:
        pass


def in_compare(article_id: str) -> bool:
    return str(article_id) in compare_ids()


def toggle_compare(article_id: str) -> None:
    aid = str(article_id)
    lst = list(compare_ids())
    if aid in lst:
        lst.remove(aid)
    elif len(lst) < COMPARE_MAX:
        lst.append(aid)
    else:
        st.toast(f"Compare holds up to {COMPARE_MAX} items — remove one first.", icon=":material/balance:")
        return
    st.session_state["compare_ids"] = lst
    _persist_compare(lst)


def clear_compare() -> None:
    st.session_state["compare_ids"] = []
    _persist_compare([])


def render_brand() -> None:
    """Project logo in the sidebar's top-left (above the nav) via st.logo.

    Full wordmark when the sidebar is expanded; mark-only when collapsed.
    Swap app/assets/logo.svg to rebrand — change the <text> to rename it.
    """
    st.logo(
        str(ASSETS_DIR / "logo.svg"),
        size="large",
        icon_image=str(ASSETS_DIR / "logo_icon.svg"),
    )


@st.cache_data(show_spinner=False)
def _login_art_data_uri() -> str:
    """Base64 the login art so CSS can use it without static file serving.

    Prefers a raster photo (app/assets/login_hero.jpg) if present; otherwise uses
    the minimalist vector illustration (login_art.svg). Drop a JPG/PNG in to swap.
    """
    import base64
    jpg = ASSETS_DIR / "login_hero.jpg"
    if jpg.exists():
        return "data:image/jpeg;base64," + base64.b64encode(jpg.read_bytes()).decode()
    svg = ASSETS_DIR / "login_art.svg"
    if svg.exists():
        return "data:image/svg+xml;base64," + base64.b64encode(svg.read_bytes()).decode()
    return ""


def render_carousel(catalogue: "pd.DataFrame | None" = None) -> None:
    """3-slide cross-fading promo banner — each themed slide shows real product
    images: on-sale, popular/bestsellers, and giftable picks (#1)."""
    df = catalogue if catalogue is not None else load_articles()
    by_id = df.set_index(df["article_id"].astype(str))

    def shots(ids: list) -> str:
        imgs = []
        for aid in ids[:3]:
            item = by_id.loc[aid].to_dict() if aid in by_id.index else None
            src = _resolve_image_src(str(aid), item, width=300, height=380)
            # each banner product links to its detail page (#1)
            imgs.append(f'<a class="caro-shot" href="product?aid={aid}" target="_self">'
                        f'<img src="{src}" alt="" /></a>')
        return "".join(imgs)

    all_ids = df["article_id"].astype(str).tolist()
    sale_ids = (df[df["sale_price"].notna()]["article_id"].astype(str).tolist()
                if "sale_price" in df.columns else [])
    if "quality" in df.columns:
        lux = df[df["quality"] == "Luxury"]["article_id"].astype(str).tolist()
        prem = df[df["quality"].isin(["Premium", "Luxury"])]["article_id"].astype(str).tolist()
    else:
        lux, prem = [], []
    # de-dupe across slides so they don't show the same three items
    sale_ids = (sale_ids or all_ids)[:3]
    pop_ids = ([a for a in prem if a not in sale_ids] or all_ids)[:3]
    used = set(sale_ids) | set(pop_ids)
    gift_ids = ([a for a in lux if a not in used] or [a for a in all_ids if a not in used] or all_ids)[:3]

    slides = [
        ("This week · on sale", "Beauty, on sale",
         "Limited-time prices on serums, scents &amp; more — while they last.",
         "linear-gradient(120deg,#b8893a 0%,#6f5418 100%)", sale_ids),
        ("Bestsellers", "Loved by everyone",
         "The most popular picks across skincare, makeup &amp; fragrance.",
         "linear-gradient(120deg,#caa24a 0%,#8a6d22 100%)", pop_ids),
        ("Gifting", "Gifts for your closest",
         "Luxe sets &amp; signature scents — beautifully giftable.",
         "linear-gradient(120deg,#c19a3e 0%,#9a7a2c 100%)", gift_ids),
    ]
    inner = "".join(
        f'<div class="slide" style="background:{grad};">'
        f'<div class="copy"><span class="tag">{tag}</span><h2>{title}</h2><p>{sub}</p></div>'
        f'<div class="shots">{shots(ids)}</div></div>'
        for tag, title, sub, grad, ids in slides
    )
    st.markdown(f'<div class="carousel">{inner}<div class="dots"><i></i><i></i><i></i></div></div>',
                unsafe_allow_html=True)


def render_auth_panel() -> None:
    """Split-screen auth: editorial form hard-left, minimalist art panel hard-right.
    Only injected while logged out, so this CSS is scoped to the auth page.
    Swap the visual by dropping app/assets/login_hero.jpg (takes priority) or
    editing app/assets/login_art.svg.
    """
    uri = _login_art_data_uri()
    bg = (f"url('{uri}')" if uri
          else "radial-gradient(135% 120% at 75% 12%, #e6c878 0%, #c19a3e 48%, #a07e2c 100%)")
    st.markdown(
        f"""
<style>
  /* Auth screen: no sidebar or its collapsed-reopen control (#15). Scoped here
     because this CSS only renders while logged out. */
  [data-testid="stSidebar"],
  [data-testid="stExpandSidebarButton"],
  [data-testid="stSidebarCollapsedControl"] {{ display: none !important; }}
  /* Pin the form/hero to a left column. stMain is a flex COLUMN with
     align-items:center, so margins alone keep it centered — align-self:flex-start
     is what actually left-aligns it. Higher specificity ([stMain] prefix) beats
     the global .block-container rule deterministically. */
  [data-testid="stMain"] [data-testid="stMainBlockContainer"],
  [data-testid="stMain"] .block-container {{
    max-width: 540px !important;
    align-self: flex-start !important;
    margin-left: clamp(24px, 3vw, 64px) !important;
    margin-right: 0 !important;
    padding-right: 1rem !important;
  }}
  h1.hero-headline {{ font-size: clamp(38px, 3.4vw, 52px) !important; }}
  /* minimalist art panel hard against the right edge */
  .auth-photo {{
    position: fixed; top: 0; right: 0; height: 100vh; width: 44vw; z-index: 0;
    background-image: {bg};
    background-size: cover; background-position: center center;
    box-shadow: -40px 0 110px -60px rgba(26,23,20,0.45);
  }}
  .auth-photo .ap-brand {{
    position: absolute; left: 44px; bottom: 40px;
    color: var(--ink);
    font-family: var(--display); font-size: 30px; font-weight: 600;
  }}
  .auth-photo .ap-brand .dot {{ color: var(--accent); }}
  @media (max-width: 1100px) {{
    .auth-photo {{ display: none; }}
    [data-testid="stMain"] [data-testid="stMainBlockContainer"],
    [data-testid="stMain"] .block-container {{
      max-width: 560px !important; align-self: center !important; margin: 0 auto !important;
    }}
  }}
</style>
<div class="auth-photo"><div class="ap-brand">Barakaly<span class="dot">.</span></div></div>
""",
        unsafe_allow_html=True,
    )


# ---------- persistent login (server-side sessions + browser cookie) ----------
# Streamlit has no native cookie-write, so we use streamlit-cookies-controller
# for set/delete. Crucially we READ the token on boot from st.context.cookies
# (populated synchronously from the request headers) so a refresh restores the
# user with NO iframe round-trip and therefore no flash of the login screen.

def mount_cookie_controller():
    """Instantiate the cookie component for THIS run and stash it.

    streamlit-cookies-controller renders an (invisible) component every time its
    constructor runs; it must be constructed exactly once per script run to stay
    mounted. Call this once at the top of the entrypoint (main.py) — set/remove
    issued later in the same run then operate on a mounted component.
    """
    from streamlit_cookies_controller import CookieController
    ctrl = CookieController()
    st.session_state["_cookie_ctrl"] = ctrl
    return ctrl


def _cookie_controller():
    ctrl = st.session_state.get("_cookie_ctrl")
    return ctrl if ctrl is not None else mount_cookie_controller()


def restore_session() -> dict | None:
    """If a valid session cookie exists, hydrate st.session_state['user'].

    Reads from st.context.cookies (request headers — instant, no flash). Safe
    to call on every run; it's a no-op once the user is in session_state.
    """
    user = st.session_state.get("user")
    if user is not None:
        return user
    try:
        token = st.context.cookies.get(auth.SESSION_COOKIE_NAME)
    except Exception:
        token = None
    if not token:
        return None
    user = db.get_session_user(token)
    if user is not None:
        st.session_state["user"] = user
    return user


def establish_session(user: dict) -> None:
    """Persist a login: create a server-side session and set the browser cookie."""
    token = auth.new_session_token()
    db.create_session(token, user["id"], ttl_days=auth.SESSION_TTL_DAYS)
    try:
        _cookie_controller().set(
            auth.SESSION_COOKIE_NAME, token,
            max_age=auth.SESSION_TTL_DAYS * 24 * 3600, same_site="lax", path="/",
        )
    except Exception:
        # Cookie write failed (e.g. component not yet mounted) — login still
        # works for this session; persistence resumes on the next successful set.
        pass


def clear_session() -> None:
    """Log out: revoke the server-side session and remove the browser cookie."""
    st.session_state.pop("auth_view", None)  # so logout returns to public browsing, not the auth screen
    try:
        token = st.context.cookies.get(auth.SESSION_COOKIE_NAME)
    except Exception:
        token = None
    if token:
        db.delete_session(token)
    try:
        _cookie_controller().remove(auth.SESSION_COOKIE_NAME)
    except Exception:
        pass


def go_signin() -> None:
    """Send a guest to the (sidebar-less) sign-in screen."""
    st.session_state["auth_view"] = True
    st.rerun()


def leave_signin() -> None:
    """Return from the sign-in screen to public browsing."""
    st.session_state.pop("auth_view", None)
    st.rerun()


def _picsum_fallback_url(article_id: str, width: int, height: int) -> str:
    return f"https://picsum.photos/seed/hm{article_id}/{width}/{height}"


def _cache_path(article_id: str) -> Path:
    return IMAGE_CACHE_DIR / f"{article_id}.jpg"


def _fetch_one_image(args: tuple) -> tuple:
    """Worker for parallel prefetch. Returns (article_id, success_bool)."""
    article_id, url = args
    cache = _cache_path(article_id)
    if cache.exists() and cache.stat().st_size > 1024:
        return article_id, True
    try:
        import requests
        r = requests.get(url, timeout=10, headers={"User-Agent": "btec-recsys/1.0"})
        ctype = r.headers.get("content-type", "")
        if r.status_code == 200 and ctype.startswith("image/") and len(r.content) > 1024:
            IMAGE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
            cache.write_bytes(r.content)
            return article_id, True
    except Exception:
        pass
    return article_id, False


def prefetch_images_sync(items: list, max_workers: int = 6, timeout: float = 12.0) -> None:
    """Pre-fetch Pollinations images for a list of item dicts in parallel.

    Called once at the top of pages that render cards, so the disk cache is
    populated before `_resolve_image_src` runs. Idempotent — skips items
    already cached. Bounded by `timeout` total (not per-image) to keep page
    renders responsive when Pollinations is slow or down.
    """
    if not items:
        return
    from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
    import time

    seen: set[str] = set()
    tasks: list[tuple[str, str]] = []
    for item in items:
        aid = str(item["article_id"])
        # Skip items with a committed local photo (cosmetics / curated) — those are
        # served by _resolve_image_src Tier 0 and need no remote fetch.
        if (ASSETS_DIR / "cosmetics" / f"{aid}.jpg").exists() or \
           (ASSETS_DIR / "products" / f"{aid}.jpg").exists():
            continue
        if aid in seen or _cache_path(aid).exists():
            continue
        seen.add(aid)
        tasks.append((aid, article_image_url(aid, item=item)))
    if not tasks:
        return

    started = time.time()
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = [pool.submit(_fetch_one_image, t) for t in tasks]
        # Drain futures with a global timeout so a slow Pollinations response
        # doesn't block the whole page render.
        remaining = futures
        while remaining and (time.time() - started) < timeout:
            done, remaining_set = wait(remaining, timeout=1, return_when=FIRST_COMPLETED)
            remaining = list(remaining_set)
        # Anything still pending will get cancelled / abandoned — those items
        # render with the picsum fallback URL until the next prefetch warms them.


def _resolve_image_src(article_id: str, item: dict | None,
                       width: int = 400, height: int = 500) -> str:
    """Return the actual img src to embed in HTML.

    Priority: disk-cached image (as base64 data URI) → picsum URL fallback.
    The Pollinations URL is *not* used directly in img src because the browser
    fetch can return 500 and Streamlit's markdown sanitiser strips `onerror`
    handlers — leaving broken-image icons when remote fetches fail. Server-side
    fetch (in `prefetch_images_sync`) sidesteps both issues.
    """
    aid = str(article_id)
    import base64
    # Tier 0: seller-provided image URL (marketplace listings have no committed photo).
    if item:
        u = item.get("image_url")
        if isinstance(u, str) and u.strip().startswith(("http://", "https://", "data:")):
            return u.strip()
    # Tier 0a: committed cosmetics product photo (Chiroyli catalogue).
    cos = ASSETS_DIR / "cosmetics" / f"{aid}.jpg"
    if cos.exists():
        return f"data:image/jpeg;base64,{base64.b64encode(cos.read_bytes()).decode()}"
    # Tier 0b: committed curated fashion photo (legacy demo catalogue).
    curated = ASSETS_DIR / "products" / f"{aid}.jpg"
    if curated.exists():
        return f"data:image/jpeg;base64,{base64.b64encode(curated.read_bytes()).decode()}"
    # Tier 1: locally-downloaded H&M product photos (if user has the 16 GB bundle)
    if len(aid) >= 3:
        local = IMAGE_DIR / aid[:3] / f"{aid}.jpg"
        if local.exists():
            import base64
            return f"data:image/jpeg;base64,{base64.b64encode(local.read_bytes()).decode()}"
    # Tier 2: cached Pollinations image (the prefetch path's output)
    cache = _cache_path(aid)
    if cache.exists() and cache.stat().st_size > 1024:
        import base64
        return f"data:image/jpeg;base64,{base64.b64encode(cache.read_bytes()).decode()}"
    # Tier 3: picsum fallback — random but reliably loads without JS
    return _picsum_fallback_url(aid, width, height)


def cosmetics_gallery(article_id: str, item: dict | None = None) -> list[str]:
    """Image sources for a product's gallery (#8): the primary photo plus any
    committed extras at app/assets/cosmetics/{aid}_2.jpg, _3.jpg, _4.jpg."""
    import base64
    aid = str(article_id)
    srcs = [_resolve_image_src(aid, item, width=640, height=640)]
    for n in (2, 3, 4):
        p = ASSETS_DIR / "cosmetics" / f"{aid}_{n}.jpg"
        if p.exists() and p.stat().st_size > 1024:
            srcs.append("data:image/jpeg;base64," + base64.b64encode(p.read_bytes()).decode())
    return srcs


# Product-type → Loremflickr keyword. H&M product_type_name values are
# fine-grained ("Vest top", "Sweatshirt", "Espadrilles") and Flickr's tag
# vocabulary is broader, so we map to ~15 well-tagged generic categories.
_FLICKR_KW = {
    "tshirt":  ("t-shirt", "tee", "top", "vest", "tank", "blouse", "shirt", "polo"),
    "dress":   ("dress", "gown"),
    "skirt":   ("skirt",),
    "pants":   ("trouser", "jeans", "pant", "legging", "short", "chino"),
    "sweater": ("sweater", "jumper", "cardigan", "pullover", "hoodie", "sweatshirt"),
    "jacket":  ("jacket", "coat", "blazer", "anorak", "parka", "outerwear"),
    "shoes":   ("shoe", "sneaker", "trainer", "sandal", "boot", "heel", "loafer", "espadrille"),
    "bag":     ("bag", "tote", "backpack", "purse"),
    "lingerie":("bra", "panties", "knicker", "underwear", "thong", "brief"),
    "hat":     ("hat", "cap", "beanie"),
    "scarf":   ("scarf",),
    "socks":   ("sock", "tight"),
    "swim":    ("swim", "bikini"),
    "jewelry": ("jewellery", "jewelry", "earring", "necklace", "ring", "bracelet"),
    "sunglasses": ("sunglass", "glasses"),
}


def _flickr_keyword_for(item: dict) -> str:
    pt = (item.get("product_type_name") or "").lower()
    pg = (item.get("product_group_name") or "").lower()
    haystack = pt + " " + pg
    for category, needles in _FLICKR_KW.items():
        if any(n in haystack for n in needles):
            return category
    return "fashion"


# Pexels API — free, real curated product photography. Register at
# https://www.pexels.com/api/ (takes 30 seconds), then before launching:
#   export PEXELS_API_KEY=<your-key>
# Free tier: 200 requests/hour, 20,000/month. Cached for 1 hour per query
# so 30 unique (category, colour) combos cost 30 API calls total per hour.
def _pexels_api_key() -> str:
    """Read the Pexels API key from env var (highest priority) or `.streamlit/secrets.toml`."""
    import os
    key = os.environ.get("PEXELS_API_KEY", "").strip()
    if key:
        return key
    try:
        return str(st.secrets.get("PEXELS_API_KEY", "")).strip()
    except Exception:
        return ""


@st.cache_data(show_spinner=False, ttl=3600)
def _pexels_files_for(query: str) -> list[str]:
    """Return Pexels image URLs for a query, or [] if no API key is set."""
    api_key = _pexels_api_key()
    if not api_key:
        return []
    import urllib.parse, requests
    q = urllib.parse.quote(query)
    url = f"https://api.pexels.com/v1/search?query={q}&per_page=30&orientation=square"
    try:
        r = requests.get(url, timeout=6, headers={"Authorization": api_key})
        if r.status_code != 200:
            return []
        data = r.json()
        return [p["src"]["medium"] for p in data.get("photos", [])]
    except Exception:
        return []


def _pexels_image_for(category: str, colour: str | None, aid: str,
                      width: int, height: int) -> str | None:
    """Deterministic per-article Pexels URL. Returns None if no API key /
    no results — caller falls back to the next tier."""
    query = f"{category} {colour} product" if colour else f"{category} product"
    urls = _pexels_files_for(query)
    if not urls:
        return None
    return urls[abs(hash(aid)) % len(urls)]


def article_image_url(article_id: str, item: dict | None = None,
                       width: int = 400, height: int = 400) -> str:
    """URL that — when fetched server-side — yields a real category-matched
    product photo. Resolution order (highest priority first):

    1. Local H&M product photo if the 16 GB Kaggle images bundle was downloaded
       (canonical, but blocked by disk on most demo machines).
    2. **Wikimedia Commons** real photo search by `{category} {colour} product`.
       Free-licensed photography, no API key, pool is hundreds of photos per
       category. Deterministic mapping via `hash(article_id) % len(results)`
       so each article *consistently* shows the same image AND the same article
       always shows that image (matters for trust + cache-friendliness).
    3. Loremflickr fallback (~10 photos per category, smaller pool).
    4. Picsum random fallback if everything else fails.
    """
    aid = str(article_id)

    # Tier 1 — local H&M images
    if len(aid) >= 3:
        local = IMAGE_DIR / aid[:3] / f"{aid}.jpg"
        if local.exists():
            return f"data/images/{aid[:3]}/{aid}.jpg"

    if item is not None:
        kw = _flickr_keyword_for(item)
        colour = (item.get("perceived_colour_master_name") or "").strip().lower()
        if colour in ("", "undefined", "unknown"):
            colour = None

        # Tier 2 — Pexels API if a key is configured. Pexels has actual curated
        # product photography (registration is free at pexels.com/api, 200 req/h).
        # Pass the key via env var PEXELS_API_KEY before launching streamlit.
        pexels = _pexels_image_for(kw, colour, aid, width, height)
        if pexels:
            return pexels

        # Tier 3 — Loremflickr fallback (no auth, ~3-5 unique photos per
        # (category, colour) combo; not great but reliable).
        tags = [kw, "product"]
        if colour:
            tags.append(colour)
        lock = abs(hash(aid)) % 1_000_000
        return f"https://loremflickr.com/{width}/{height}/{','.join(tags)}?lock={lock}"

    # Tier 4 — picsum
    return _picsum_fallback_url(aid, width, height)


CUSTOM_CSS = """
<style>
  /* ===== Design system — editorial fashion (2026) ===== */
  /* Warm paper background + vermilion accent + Fraunces display serif headlines
     over Inter body. Bolder depth on cards, oversized hero type. Fonts are
     loaded by the theme in config.toml; families referenced here by name. */
  :root {
    --ink:       #1a1714;       /* warm near-black */
    --ink-2:     #4a443d;
    --muted:     #8a8178;       /* warm grey */
    --border:    #ece7e0;       /* warm hairline */
    --border-2:  #d8d1c7;
    --bg:        #ffffff;
    --bg-soft:   #f7f4ef;       /* warm paper */
    --accent:      #c19a3e;     /* Chiroyli gold */
    --accent-2:    #a07e2c;     /* darker gold — hover */
    --accent-soft: rgba(193,154,62,0.14);
    --shadow-1:  0 1px 2px rgba(26,23,20,0.05);
    --shadow-2:  0 18px 44px -16px rgba(26,23,20,0.22);
    --display:   "Fraunces", "Times New Roman", Georgia, serif;
    --sans:      "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
  }

  html, body, [class*="css"]  {
    font-family: var(--sans);
    color: var(--ink);
    -webkit-font-smoothing: antialiased;
    background: var(--bg-soft);
  }
  /* Faint tiling gold sparkle motif on the warm cream — subtle beauty-brand
     texture (behind all content; only visible in whitespace). */
  [data-testid="stAppViewContainer"]::before {
    content: "";
    position: fixed; inset: 0; z-index: 0; pointer-events: none;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='140' height='140' viewBox='0 0 140 140'%3E%3Cpath d='M70 50 C72 62 78 68 90 70 C78 72 72 78 70 90 C68 78 62 72 50 70 C62 68 68 62 70 50 Z' fill='%23c19a3e' fill-opacity='0.07'/%3E%3C/svg%3E");
    background-size: 140px 140px;
  }
  /* Hide the menu/deploy chrome but NOT the whole toolbar — the sidebar reopen
     control (stExpandSidebarButton) is nested inside stToolbar, so hiding the
     toolbar wholesale removed the only way to reopen a collapsed sidebar (#14). */
  #MainMenu, footer,
  [data-testid="stMainMenu"], [data-testid="stMainMenuButton"],
  [data-testid="stToolbarActions"], [data-testid="stAppDeployButton"],
  [data-testid="stHeaderActionElements"] { display: none !important; }
  header[data-testid="stHeader"] { background: transparent !important; box-shadow: none !important; }
  [data-testid="stExpandSidebarButton"] { display: flex !important; z-index: 1003 !important; }
  .block-container,
  [data-testid="stMainBlockContainer"] {
    max-width: 1600px;
    margin-left: auto !important;     /* centre on wide monitors — no big right gap */
    margin-right: auto !important;
    padding-top: 2.5rem;
    padding-bottom: 7rem;             /* breathing room so cards don't hug the footer (#9) */
    padding-left: 3rem; padding-right: 3rem;
    min-height: 920px;
    position: relative; z-index: 1;   /* sit above the fixed grain overlay */
  }
  [data-testid="stSidebar"] { position: relative; z-index: 1; }

  /* Sidebar nav (st.navigation auto-menu) */
  [data-testid="stSidebar"] [data-testid="stSidebarNav"] a {
    font-size: 14px;
    font-weight: 500;
    border-radius: 9px;
  }
  /* Highlight the active page in accent */
  [data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-current="page"] {
    background: var(--accent-soft) !important;
    color: var(--accent-2) !important;
    font-weight: 600;
  }
  /* Reached via buttons, not the menu — hide these nav entries. */
  [data-testid="stSidebar"] [data-testid="stSidebarNav"] a[href$="/product"],
  [data-testid="stSidebar"] [data-testid="stSidebarNav"] a[href$="/checkout"],
  [data-testid="stSidebar"] [data-testid="stSidebarNav"] a[href$="/success"],
  [data-testid="stSidebar"] [data-testid="stSidebarNav"] a[href$="/orders"] {
    display: none !important;
  }

  /* Headings — editorial display serif, oversized */
  h1, h2 { position: relative; z-index: 1; }
  h1 {
    font-family: var(--display);
    font-weight: 600; font-size: 52px;
    letter-spacing: -0.02em;
    line-height: 1.02;
    margin-bottom: 0.35rem !important;
    color: var(--ink);
  }
  h1.hero-headline {
    font-size: clamp(46px, 6.5vw, 92px);
    font-weight: 600;
    letter-spacing: -0.035em;
    line-height: 0.98;
  }
  h2 {
    font-family: var(--display);
    font-weight: 600; font-size: 27px;
    letter-spacing: -0.01em;
    margin-top: 2.5rem !important;
    color: var(--ink);
  }
  h3 {
    font-weight: 600; font-size: 15px;
    color: var(--ink); margin: 0 !important;
  }
  .subtitle {
    color: var(--ink-2); font-size: 18px;
    line-height: 1.55;
    margin-bottom: 2.5rem; max-width: 620px;
    position: relative; z-index: 1;
  }

  /* Pill — accent-tinted editorial label */
  .pill {
    display: inline-block; padding: 5px 14px; border-radius: 100px;
    background: var(--accent-soft);
    border: 1px solid transparent;
    color: var(--accent-2); font-size: 12px; font-weight: 600;
    letter-spacing: 0.01em;
    margin-bottom: 1.25rem;
    position: relative; z-index: 1;
  }

  /* ===== Product cards — square, minimal, breathable ===== */
  .card {
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 0;
    margin: 6px 0;
    overflow: hidden;
    transition: transform 0.22s cubic-bezier(.2,.7,.2,1), box-shadow 0.22s ease, border-color 0.22s ease;
    box-shadow: var(--shadow-1);
  }
  .card:hover {
    transform: translateY(-6px);
    box-shadow: var(--shadow-2);
    border-color: var(--border-2);
  }
  .card-image-wrapper {
    position: relative;
    width: 100%;
    aspect-ratio: 1 / 1;        /* square — minimal, Apple/Instagram convention */
    background: linear-gradient(135deg, #f4f4f6 0%, #ebebef 100%);
    overflow: hidden;
  }
  .card-image {
    width: 100%; height: 100%;
    object-fit: cover;
    display: block;
    transition: transform 0.35s ease;
  }
  .card:hover .card-image { transform: scale(1.03); }
  .card-match {
    position: absolute;
    top: 10px; right: 10px;
    padding: 4px 9px;
    border-radius: 100px;
    font-size: 11px; font-weight: 600;
    letter-spacing: -0.01em;
    box-shadow: 0 2px 8px rgba(0,0,0,0.10);
  }
  .card-match.high  { background: var(--accent); color: var(--ink); }
  .card-match.mid   { background: rgba(255,255,255,0.96); color: var(--ink); }
  .card-rank-badge {
    position: absolute;
    top: 10px; left: 10px;
    min-width: 24px; height: 24px; line-height: 24px; text-align: center;
    padding: 0 7px;
    background: rgba(29,29,31,0.92);
    color: #fff;
    font-size: 11px; font-weight: 700;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.15);
  }
  .card-body { padding: 11px 14px 4px; }
  .card-title {
    font-size: 14px; font-weight: 600; color: var(--ink);
    margin: 0; line-height: 1.3;
    overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  }
  .card-meta {
    font-size: 12px; color: var(--muted);
    margin: 3px 0 0; line-height: 1.35;
    overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  }
  .card-meta .dot { color: var(--border-2); margin: 0 5px; }
  .card-reason {
    font-size: 11px; color: var(--muted);
    margin: 8px 0 2px;
    padding-top: 8px;
    border-top: 1px solid var(--border);
    line-height: 1.35;
    display: -webkit-box;
    -webkit-line-clamp: 2; -webkit-box-orient: vertical;
    overflow: hidden;
  }
  .card-reason .why-icon { font-size: 12px; margin-right: 3px; }
  .card-id {
    color: #c7c7cc; font-size: 10px;
    font-family: ui-monospace, SFMono-Regular, monospace;
    margin: 6px 0 0;
  }
  .card-price { font-size: 14px; font-weight: 700; color: var(--ink); margin: 5px 0 0; }
  .card-price s { color: var(--muted); font-weight: 400; font-size: 12px; margin-right: 6px; }
  .card-price .sale { color: var(--accent-2); }

  /* ===== Home carousel banner (3 cross-fading slides, CSS-only) ===== */
  .carousel {
    position: relative; height: 240px; border-radius: 22px; overflow: hidden;
    margin: 4px 0 28px; box-shadow: var(--shadow-2);
  }
  .carousel .slide {
    position: absolute; inset: 0; opacity: 0; animation: carofade 18s infinite;
    display: flex; flex-direction: column; justify-content: center;
    padding: 0 56px; color: #fff;
  }
  .carousel .slide:nth-child(1) { animation-delay: 0s; }
  .carousel .slide:nth-child(2) { animation-delay: 6s; }
  .carousel .slide:nth-child(3) { animation-delay: 12s; }
  .carousel .slide h2 { font-family: var(--display); font-size: 34px; margin: 0 !important; color: #fff; }
  .carousel .slide p  { font-size: 16px; margin: 8px 0 0; color: rgba(255,255,255,0.92); max-width: 460px; }
  .carousel .slide .tag {
    display: inline-block; width: fit-content; font-size: 12px; font-weight: 600;
    letter-spacing: 0.04em; text-transform: uppercase; margin-bottom: 12px;
    background: rgba(255,255,255,0.22); padding: 4px 12px; border-radius: 100px;
  }
  @keyframes carofade {
    0% { opacity: 0; } 4% { opacity: 1; } 30% { opacity: 1; } 36% { opacity: 0; } 100% { opacity: 0; }
  }
  .carousel .dots { position: absolute; bottom: 14px; right: 22px; display: flex; gap: 7px; }
  .carousel .dots i { width: 7px; height: 7px; border-radius: 50%; background: rgba(255,255,255,0.55); display: block; }

  /* History row (saved-items panel) */
  .history-row {
    display: flex; align-items: center; padding: 10px 12px; border-radius: 10px;
    background: var(--bg);
    border: 1px solid var(--border);
    margin-bottom: 5px;
  }
  .history-name { font-size: 13px; font-weight: 500; }
  .history-meta { color: var(--muted); font-size: 11px; margin-top: 2px; }
  .divider { border-top: 1px solid var(--border); margin: 2.5rem 0 1.5rem; }
  .muted { color: var(--muted); font-size: 13px; }

  /* ===== Buttons — Apple pill style (border-radius: 980px convention) ===== */
  .stButton > button {
    background: var(--bg) !important;
    border: 1px solid var(--border-2) !important;
    border-radius: 980px !important;    /* Apple's full-pill convention */
    color: var(--ink) !important;
    font-weight: 400 !important;
    font-size: 14px !important;
    padding: 7px 18px !important;
    transition: all 0.18s ease !important;
    box-shadow: none !important;
  }
  .stButton > button:hover {
    background: var(--bg-soft) !important;
    border-color: var(--ink) !important;
    color: var(--ink) !important;
  }
  .stButton > button:active {
    transform: scale(0.97);
  }
  .stButton > button[kind="primary"] {
    background: var(--accent) !important;
    color: var(--ink) !important;          /* ink on gold — legible + luxe */
    border-color: var(--accent) !important;
    font-weight: 600 !important;
    box-shadow: none !important;
  }
  .stButton > button[kind="primary"]:hover {
    background: var(--accent-2) !important;
    border-color: var(--accent-2) !important;
    transform: translateY(-1px);
  }
  /* Compact action buttons inside cards — keep pill but smaller */
  .card + div .stButton > button,
  [data-testid="column"] .stButton > button {
    padding: 5px 12px !important;
    font-size: 13px !important;
  }
  .stDownloadButton > button {
    background: var(--bg) !important;
    border: 1px solid var(--border-2) !important;
    border-radius: 980px !important;
    font-size: 13px !important;
    padding: 7px 16px !important;
  }

  /* iOS-style segmented control (algorithm radio) */
  div[role="radiogroup"] {
    display: flex !important; flex-direction: row !important; flex-wrap: nowrap !important;
    gap: 4px !important;
    background: #ececef;
    padding: 3px;
    border-radius: 10px;
    width: fit-content;
  }
  div[role="radiogroup"] > label {
    padding: 5px 12px !important;
    border-radius: 7px !important;
    font-size: 13px !important; font-weight: 500 !important;
    white-space: nowrap !important;
    cursor: pointer; color: var(--ink-2);
    transition: all 0.12s ease;
  }
  div[role="radiogroup"] > label:hover { color: var(--ink); }
  div[role="radiogroup"] > label[data-baseweb="radio"]:has(input:checked) {
    background: var(--bg) !important; color: var(--ink) !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.08);
  }
  div[role="radiogroup"] > label > div:first-child { display: none !important; }

  /* Auth-screen mode selector: underline tabs (override the segmented pill) */
  .st-key-auth_mode div[role="radiogroup"] {
    flex-direction: row !important;
    gap: 26px !important;
    background: transparent !important;
    padding: 0 !important;
    border-radius: 0 !important;
    width: 100% !important;
    border-bottom: 1px solid var(--border);
  }
  .st-key-auth_mode div[role="radiogroup"] > label {
    background: transparent !important;
    padding: 6px 2px 12px !important;
    border-radius: 0 !important;
    font-size: 17px !important;
    color: var(--muted) !important;
    box-shadow: none !important;
    border-bottom: 2px solid transparent;
    margin-bottom: -1px;
  }
  .st-key-auth_mode div[role="radiogroup"] > label:hover { color: var(--ink) !important; }
  .st-key-auth_mode div[role="radiogroup"] > label:has(input:checked) {
    background: transparent !important;
    color: var(--accent) !important;
    border-bottom: 2px solid var(--accent) !important;
    box-shadow: none !important;
  }

  /* Form labels */
  .field-label {
    font-size: 11px; font-weight: 500; color: var(--muted);
    text-transform: uppercase; letter-spacing: 0.05em;
    margin-bottom: 5px;
  }

  /* Metrics card spacing */
  [data-testid="stMetricValue"] { font-size: 28px !important; font-weight: 600 !important; }
  [data-testid="stMetricLabel"] { font-size: 12px !important; color: var(--muted) !important; }

  /* ===== Top-right account menu (circular initials avatar + dropdown) ===== */
  .st-key-account_menu {
    position: fixed;
    top: 14px; right: 22px;
    z-index: 1000;
    width: auto !important;
  }
  .st-key-account_menu button {
    width: 42px !important; height: 42px !important;
    min-height: 42px !important; padding: 0 !important;
    border-radius: 50% !important;
    background: var(--accent) !important;
    border: 2px solid #fff !important;
    color: var(--ink) !important;
    font-weight: 700 !important; font-size: 15px !important;
    letter-spacing: 0;
    box-shadow: var(--shadow-2) !important;
    transition: transform .15s ease, background .15s ease !important;
    /* keep the initials on one centered line — no wrapping */
    display: flex !important; align-items: center !important; justify-content: center !important;
    line-height: 1 !important; white-space: nowrap !important; overflow: hidden !important;
  }
  .st-key-account_menu button > * { margin: 0 !important; line-height: 1 !important; white-space: nowrap !important; }
  .st-key-account_menu button p { margin: 0 !important; line-height: 1 !important; }
  .st-key-account_menu button:hover {
    transform: translateY(-1px) scale(1.04);
    background: var(--accent-2) !important; color: var(--ink) !important;
  }
  /* drop the popover's default caret — the avatar IS the affordance.
     The caret lives in an aria-hidden wrapper that reserves width even when the
     glyph is hidden, so hide the whole wrapper (it otherwise reads as "Z˅"). */
  .st-key-account_menu button div[aria-hidden="true"] { display: none !important; }
  .st-key-account_menu button svg,
  .st-key-account_menu button [data-testid="stIconMaterial"] { display: none !important; }

  .acct-pop { text-align: center; padding: 8px 6px 2px; min-width: 210px; }
  .acct-avatar-lg {
    width: 58px; height: 58px; margin: 0 auto 12px;
    border-radius: 50%;
    background: var(--accent); color: var(--ink);
    display: flex; align-items: center; justify-content: center;
    font-weight: 700; font-size: 21px;
  }
  .acct-name { font-family: var(--display); font-size: 20px; font-weight: 600; color: var(--ink); line-height: 1.15; }
  .acct-email { font-size: 13px; color: var(--muted); margin-top: 3px; word-break: break-all; }
  .acct-role {
    display: inline-block; margin-top: 10px;
    padding: 2px 11px; border-radius: 100px;
    background: var(--accent-soft); color: var(--accent-2);
    font-size: 11px; font-weight: 600;
  }

  /* Guest Sign-in button — pinned top-right where the account avatar sits */
  .st-key-guest_signin { position: fixed; top: 14px; right: 22px; z-index: 1000; width: auto !important; }
  .st-key-guest_signin button { box-shadow: var(--shadow-2) !important; }

  /* ===== Whole-card click — a transparent button overlays the card (#3) ===== */
  div[class*="st-key-cw_"] { position: relative !important; }
  div[class*="st-key-cw_"] > div[data-testid="stVerticalBlock"] { gap: 0 !important; }
  div[class*="st-key-cl_"] {
    position: absolute !important; inset: 0 !important; z-index: 4 !important;
    margin: 0 !important; padding: 0 !important; height: 100% !important;
  }
  div[class*="st-key-cl_"] .stButton,
  div[class*="st-key-cl_"] .stButton > button {
    height: 100% !important; width: 100% !important;
  }
  div[class*="st-key-cl_"] button {
    opacity: 0 !important; min-height: 100% !important; border: none !important;
    background: transparent !important; cursor: pointer !important; box-shadow: none !important;
  }
  /* hover-lift driven by the wrapper so it still works under the overlay */
  div[class*="st-key-cw_"]:hover .card {
    transform: translateY(-6px); box-shadow: var(--shadow-2); border-color: var(--border-2);
  }

  /* ===== Product gallery thumbnails (#8) ===== */
  .pthumbs { display: flex; gap: 10px; margin-top: 12px; flex-wrap: wrap; }
  .pthumb {
    display: block; width: 76px; height: 76px; border-radius: 12px; overflow: hidden;
    border: 2px solid var(--border); transition: border-color .15s ease;
  }
  .pthumb.active { border-color: var(--accent); }
  .pthumb:hover { border-color: var(--accent-2); }
  .pthumb img { width: 100%; height: 100%; object-fit: cover; display: block; }

  /* ===== Product one-line description + rating (#7) ===== */
  .desc-rating {
    font-size: 14px; color: var(--ink-2); line-height: 1.5; margin: 0 0 14px;
    display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
  }

  /* ===== Inputs: keep placeholder inside the field, clear of trailing icons (#16) ===== */
  [data-baseweb="input"], [data-baseweb="base-input"] { overflow: hidden !important; }
  [data-testid="stTextInputRootElement"] { overflow: hidden !important; }
  [data-testid="stTextInput"] input,
  [data-testid="stNumberInput"] input,
  [data-testid="stTextArea"] textarea {
    text-overflow: ellipsis;
  }
  [data-testid="stTextInput"] input::placeholder,
  [data-testid="stTextArea"] textarea::placeholder {
    color: var(--muted); opacity: 0.85;
  }

  /* ===== Home category shortcuts (#6) ===== */
  .shortcut-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 6px 0 4px; }
  @media (max-width: 760px) { .shortcut-grid { grid-template-columns: repeat(2, 1fr); } }

  /* ===== Carousel product-image strip (#1) ===== */
  .carousel .slide { flex-direction: row !important; align-items: center; gap: 28px; }
  .carousel .slide .copy { flex: 0 0 40%; }
  .carousel .slide .shots { display: flex; gap: 12px; flex: 1; justify-content: flex-end; }
  .carousel .slide .shots a.caro-shot { line-height: 0; transition: transform .2s ease; cursor: pointer; }
  .carousel .slide .shots a.caro-shot:hover { transform: translateY(-4px); }
  .carousel .slide .shots img {
    width: 150px; height: 188px; object-fit: cover; border-radius: 14px;
    box-shadow: 0 10px 28px -10px rgba(0,0,0,0.45); border: 2px solid rgba(255,255,255,0.5);
  }
  @media (max-width: 900px) { .carousel .slide .shots img:nth-child(n+3) { display: none; } }
</style>
"""


def apply_css() -> None:
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def scroll_to_top_if_flagged() -> None:
    """Scroll the main panel to the top once, if a prior action set
    st.session_state['_scroll_top'] (e.g. after login or a home shortcut), so the
    user doesn't land scrolled into the middle of a list (#17)."""
    if st.session_state.pop("_scroll_top", False):
        import streamlit.components.v1 as components
        components.html(
            "<script>setTimeout(function(){var d=window.parent.document;"
            "var m=d.querySelector('section.main')||d.querySelector('[data-testid=\"stMain\"]');"
            "if(m){m.scrollTo(0,0);} window.parent.scrollTo(0,0);},40);</script>",
            height=0,
        )


# ---------- cached loaders (shared across pages) ----------
# `show_spinner=<msg>` on @st.cache_resource fires the spinner only when the
# underlying function actually executes (cache miss). On cache hits the loader
# returns instantly with no spinner — which is what we want after the first
# session warm-up, so navigation feels snappy.

@st.cache_resource(show_spinner="Loading product catalogue…")
def load_hm_articles() -> pd.DataFrame:
    """The original H&M fashion catalogue — used by the analyst research pages
    (Evaluation/Compare) and the trained models."""
    from src import data as dataio
    return dataio.load_articles()


COSMETICS_CSV = ASSETS_DIR / "cosmetics_products.csv"


def cosmetics_mode() -> bool:
    """True when the generated cosmetics catalogue is present (Chiroyli's products)."""
    return COSMETICS_CSV.exists()


@st.cache_resource(show_spinner="Loading catalogue…")
def load_cosmetics() -> pd.DataFrame:
    base = pd.read_csv(COSMETICS_CSV, dtype={"article_id": str})
    sellers = db.active_seller_products()
    if not sellers:
        return base
    # Map seller rows onto the full catalogue schema (derive the columns the
    # CSV carries but sellers don't set, so filters / TF-IDF keep working).
    rows = []
    for s in sellers:
        rows.append({
            "article_id": str(s["article_id"]), "prod_name": s["prod_name"],
            "brand": s["brand"], "category": s["category"],
            "product_type_name": s["product_type_name"],
            "product_group_name": s["category"], "section_name": s["category"],
            "department_name": s["category"], "garment_group_name": s["product_type_name"],
            "index_group_name": s["index_group_name"],
            "colour_group_name": s["colour_group_name"],
            "perceived_colour_master_name": s["colour_group_name"],
            "quality": s["quality"], "size": s["size"], "made_in": s["made_in"],
            "price": s["price"], "sale_price": s["sale_price"],
            "detail_desc": s["detail_desc"], "image_query": s["prod_name"],
            "image_url": s["image_url"],
        })
    seller_df = pd.DataFrame(rows).reindex(columns=list(base.columns) + ["image_url"])
    if "image_url" not in base.columns:
        base = base.assign(image_url=None)
    return pd.concat([base, seller_df], ignore_index=True)


def refresh_catalogue() -> None:
    """Flush cached catalogue + derived TF-IDF after a seller mutates products."""
    load_cosmetics.clear()
    _cosmetics_tfidf.clear()


def load_articles() -> pd.DataFrame:
    """Consumer catalogue: cosmetics when present, else the H&M fashion data."""
    return load_cosmetics() if cosmetics_mode() else load_hm_articles()


@st.cache_resource(show_spinner="Loading content-based model…")
def load_content_based():
    with open(MODEL_DIR / "content_based_vectorizer.pkl", "rb") as f:
        vec = pickle.load(f)
    tfidf = load_npz(MODEL_DIR / "content_based_item_tfidf.npz")
    return vec, tfidf


@st.cache_resource(show_spinner="Loading collaborative-filtering model…")
def load_cf():
    with open(MODEL_DIR / "cf_als_model.pkl", "rb") as f:
        bundle = pickle.load(f)
    return bundle["model"], bundle["user_index"], bundle["item_index"]


@st.cache_resource(show_spinner="Loading neural CF model…")
def load_ncf():
    """Load NCF item embeddings for item-item similarity recommendations.

    The NeuMF model has two item-embedding towers (GMF 16-dim, MLP 32-dim) which
    we concatenate to a 48-dim space and L2-normalise. For platform users not
    in NCF's `user_id_to_idx` (which holds the H&M training customer IDs), the
    user vector is approximated as the centroid of the embeddings of their
    saved items — a standard item-item cold-start fallback.

    Returns (item_emb, item_id_to_idx, idx_to_item_id), or (None, None, None)
    if the bundle isn't present (NCF is optional).
    """
    pt_path = MODEL_DIR / "ncf_neumf.pt"
    map_path = MODEL_DIR / "ncf_id_maps.pkl"
    if not pt_path.exists() or not map_path.exists():
        return None, None, None
    import torch
    sd = torch.load(pt_path, map_location="cpu", weights_only=False)
    item_gmf = sd["item_gmf.weight"].cpu().numpy()
    item_mlp = sd["item_mlp.weight"].cpu().numpy()
    item_emb = np.concatenate([item_gmf, item_mlp], axis=1)
    item_emb = normalize(item_emb, norm="l2", axis=1)
    with open(map_path, "rb") as f:
        maps = pickle.load(f)
    return item_emb, maps["item_id_to_idx"], maps["idx_to_item_id"]


def recommend_ncf(positives: set, excluded: set | None, k: int = 6,
                  include: set | None = None
                  ) -> list[tuple[str, float]] | None:
    """Recommend via item-item cosine similarity in NCF embedding space.

    For platform users not in NCF's training set, the "user vector" is the
    centroid of their saved-item embeddings. Items not present in NCF's
    `item_id_to_idx` (about 60% of the H&M catalogue) are simply unscoreable
    and don't appear in the output.

    Returns None when the user has no positives with NCF embeddings, or when
    the NCF bundle isn't loadable.
    """
    item_emb, item_to_idx, idx_to_item = load_ncf()
    if item_emb is None:
        return None
    rows = [item_to_idx[a] for a in positives if a in item_to_idx]
    if not rows:
        return None
    user_emb = item_emb[rows].mean(axis=0)
    norm = float(np.linalg.norm(user_emb))
    if norm < 1e-12:
        return None
    user_emb = user_emb / norm
    scores = item_emb @ user_emb  # cosine since both L2-normalised
    if include is not None:
        keep = np.zeros(len(scores), dtype=bool)
        for a in include:
            idx = item_to_idx.get(a)
            if idx is not None:
                keep[idx] = True
        scores[~keep] = -np.inf
    if excluded:
        for aid in excluded:
            idx = item_to_idx.get(aid)
            if idx is not None:
                scores[idx] = -np.inf
    for aid in positives:  # don't re-recommend folded-in items
        idx = item_to_idx.get(aid)
        if idx is not None:
            scores[idx] = -np.inf
    # Rank, then keep only finite candidates (masked/excluded items are -inf and
    # must not reach the rescale → NaN).
    order = np.argsort(-scores)
    order = order[np.isfinite(scores[order])][:k]
    if len(order) == 0:
        return []
    top_scores = scores[order]
    if top_scores.max() - top_scores.min() < 1e-12:
        rescaled = np.ones_like(top_scores) * 0.9
    else:
        rescaled = 0.65 + 0.34 * (top_scores - top_scores.min()) / (top_scores.max() - top_scores.min())
    return [(idx_to_item[int(i)], float(s)) for i, s in zip(order, rescaled)]


@st.cache_resource(show_spinner=False)
def load_hybrid_config():
    path = MODEL_DIR / "hybrid_config.pkl"
    if not path.exists():
        return None
    with open(path, "rb") as f:
        return pickle.load(f)


@st.cache_resource(show_spinner=False)
def build_item_id_to_row(_articles: pd.DataFrame) -> dict:
    return {a: i for i, a in enumerate(_articles["article_id"].values)}


@st.cache_resource(show_spinner=False)
def als_lookups(_als_item_index):
    item_to_row = {a: i for i, a in enumerate(_als_item_index)}
    return item_to_row, list(_als_item_index)


# ---------- per-user CB profile + recommenders ----------

def build_user_profile(saved_articles, preferences, articles, tfidf, item_id_to_row):
    rows: list[int] = []
    for aid in saved_articles:
        if aid in item_id_to_row:
            rows.append(item_id_to_row[aid])
    if not rows and preferences:
        cat_articles = articles[articles["product_type_name"].isin(preferences)]
        seed_aids = cat_articles["article_id"].head(80).tolist()
        rows = [item_id_to_row[a] for a in seed_aids if a in item_id_to_row]
    if not rows:
        return None
    profile = np.asarray(tfidf[rows].mean(axis=0))
    return normalize(csr_matrix(profile), norm="l2", axis=1)


def recommend_cb(profile, tfidf, item_id_to_row, excluded, k, include=None):
    """CB rec → list of (article_id, normalised_score). Score is cosine
    similarity (0–1, since both profile and tfidf rows are L2-normalised).
    `include` restricts candidates (ranks within the curated catalogue)."""
    if profile is None or profile.nnz == 0:
        return None
    scores = (profile @ tfidf.T).toarray().ravel()
    if include is not None:
        keep = np.zeros(len(scores), dtype=bool)
        keep[[item_id_to_row[a] for a in include if a in item_id_to_row]] = True
        scores[~keep] = -np.inf
    if excluded:
        excl_rows = [item_id_to_row[a] for a in excluded if a in item_id_to_row]
        scores[excl_rows] = -np.inf
    if len(scores) <= k:
        order = np.argsort(-scores)
    else:
        order = np.argpartition(-scores, k)[:k]
        order = order[np.argsort(-scores[order])]
    row_to_item = {v: kk for kk, v in item_id_to_row.items()}
    # Drop masked (-inf) candidates so we never surface (or rescale) junk when
    # the include/excluded filters leave fewer than k valid items.
    return [(row_to_item[i], float(scores[i])) for i in order[:k] if np.isfinite(scores[i])]


def recommend_als(model, item_index, item_to_row, positives, excluded, k, include=None):
    """ALS rec → list of (article_id, normalised_score). Raw ALS scores aren't
    bounded to 0–1, so we minmax-rescale the top-k slice for display. `include`
    restricts to a candidate set (then we rank all items so curated ones surface)."""
    cols = [item_to_row[a] for a in positives if a in item_to_row]
    if not cols:
        return None
    user_items = csr_matrix(
        (np.ones(len(cols), dtype=np.float32), ([0] * len(cols), cols)),
        shape=(1, len(item_index)),
    )
    if include is not None:
        request_n = len(item_index)   # rank everything, then keep the curated slice
    else:
        extra = sum(1 for a in (excluded or ()) if a in item_to_row and a not in positives)
        request_n = min(k + extra, len(item_index))
    item_rows, raw_scores = model.recommend(
        0, user_items, N=request_n,
        filter_already_liked_items=True, recalculate_user=True,
    )
    pairs = [(item_index[i], float(s)) for i, s in zip(item_rows, raw_scores)]
    if excluded:
        pairs = [(a, s) for a, s in pairs if a not in excluded]
    if include is not None:
        pairs = [(a, s) for a, s in pairs if a in include]
    pairs = pairs[:k]
    if not pairs:
        return []
    # Rescale to 0–1 across the returned slice for display only.
    scores_arr = np.array([s for _, s in pairs], dtype=np.float32)
    lo, hi = float(scores_arr.min()), float(scores_arr.max())
    if hi - lo < 1e-12:
        scores_norm = np.ones_like(scores_arr) * 0.9
    else:
        scores_norm = 0.6 + 0.39 * (scores_arr - lo) / (hi - lo)  # 0.6 → 0.99
    return [(a, float(s)) for (a, _), s in zip(pairs, scores_norm)]


def recommend_hybrid(profile, tfidf, item_id_to_row, als_model, als_item_index,
                     als_item_to_row, candidate_items, positives, excluded, alpha, k,
                     include=None):
    """Hybrid rec → list of (article_id, combined_score). The combined score is
    α·minmax(CB) + (1-α)·minmax(CF), already in 0–1."""
    cb_score = np.zeros(len(candidate_items), dtype=np.float32)
    if profile is not None and profile.nnz > 0:
        rows = np.array([item_id_to_row.get(i, -1) for i in candidate_items])
        mask = rows >= 0
        if mask.any():
            sims = (profile @ tfidf[rows[mask]].T).toarray().ravel()
            cb_score[mask] = sims

    cf_score = np.zeros(len(candidate_items), dtype=np.float32)
    cols = [als_item_to_row[a] for a in positives if a in als_item_to_row]
    if cols:
        user_items = csr_matrix(
            (np.ones(len(cols), dtype=np.float32), ([0] * len(cols), cols)),
            shape=(1, len(als_item_index)),
        )
        item_rows, scores = als_model.recommend(
            0, user_items, N=len(als_item_index),
            filter_already_liked_items=False, recalculate_user=True,
        )
        cf_score[np.asarray(item_rows, dtype=np.int64)] = np.asarray(scores, dtype=np.float32)

    def minmax(x):
        lo, hi = float(x.min()), float(x.max())
        return np.zeros_like(x) if hi - lo < 1e-12 else (x - lo) / (hi - lo)

    combined = alpha * minmax(cb_score) + (1 - alpha) * minmax(cf_score)
    if excluded:
        excl_mask = np.array([c in excluded for c in candidate_items])
        combined = np.where(excl_mask, -np.inf, combined)
    if include is not None:
        inc_mask = np.array([c in include for c in candidate_items])
        combined = np.where(inc_mask, combined, -np.inf)

    # Rank, then keep only finite candidates — masked items (excluded / outside
    # `include`) are -inf and must not reach the rescale (would produce NaN).
    order = np.argsort(-combined)
    order = order[np.isfinite(combined[order])][:k]
    if len(order) == 0:
        return []
    arr = np.array(candidate_items)
    top_scores = combined[order]
    # Display rescale: pull the top-k slice into a snug 0.65–0.99 band so even
    # the worst-of-rail still reads as a healthy match%. Better UX than showing
    # raw normalised scores like 0.04.
    if top_scores.max() - top_scores.min() < 1e-12:
        norm = np.ones_like(top_scores) * 0.9
    else:
        norm = 0.65 + 0.34 * (top_scores - top_scores.min()) / (top_scores.max() - top_scores.min())
    return [(str(a), float(s)) for a, s in zip(arr[order], norm)]


@st.cache_resource(show_spinner="Computing article prices (one-time)…")
def load_article_prices() -> pd.Series:
    """Mean price per article from H&M transactions, in normalised H&M units.

    First call streams `transactions_train.csv` (~30–60s on the project droplet)
    and persists the result to `models/article_prices.pkl`. Subsequent calls
    return the cached series.

    Returns a Series indexed by `article_id` with mean price (H&M-normalised).
    For UI display, multiply by 1000 → approximate $.
    """
    path = MODEL_DIR / "article_prices.pkl"
    if path.exists():
        with open(path, "rb") as f:
            return pickle.load(f)
    import pandas as _pd
    sums: dict[str, float] = {}
    counts: dict[str, int] = {}
    for chunk in _pd.read_csv(
        REPO_ROOT / "data" / "transactions_train.csv",
        usecols=["article_id", "price"],
        dtype={"article_id": str},
        chunksize=500_000,
    ):
        agg = chunk.groupby("article_id")["price"].agg(["sum", "count"])
        for aid, row in agg.iterrows():
            sums[aid] = sums.get(aid, 0.0) + float(row["sum"])
            counts[aid] = counts.get(aid, 0) + int(row["count"])
    means = {aid: sums[aid] / counts[aid] for aid in sums if counts[aid] > 0}
    series = pd.Series(means, name="price")
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        pickle.dump(series, f)
    return series


PRICE_DISPLAY_SCALE = 1000.0  # H&M-normalised price → approximate $ for display


@st.cache_resource(show_spinner=False)
def _cosmetics_price_map() -> dict:
    """{article_id: (regular_price, sale_price_or_None)} from the cosmetics CSV."""
    df = load_cosmetics()
    out = {}
    for r in df.itertuples():
        sale = getattr(r, "sale_price", None)
        sale = float(sale) if (sale is not None and str(sale).strip() not in ("", "nan")
                               and not pd.isna(sale)) else None
        out[str(r.article_id)] = (round(float(r.price), 2), (round(sale, 2) if sale else None))
    return out


def catalogue_price(article_id: str) -> tuple[float, float | None]:
    """(regular_price, sale_price_or_None) in $ for a catalogue item."""
    if cosmetics_mode():
        return _cosmetics_price_map().get(str(article_id), (0.0, None))
    return (display_price(article_id), None)


def effective_price(article_id: str) -> float:
    """Price actually charged — the sale price when on sale, else regular."""
    reg, sale = catalogue_price(article_id)
    return sale if sale is not None else reg


def display_price(article_id: str, prices: "pd.Series | None" = None) -> float:
    """Display price ($). Cosmetics → effective (sale-aware) price; else H&M mean × scale."""
    if cosmetics_mode():
        return effective_price(article_id)
    prices = prices if prices is not None else load_article_prices()
    try:
        raw = prices.get(str(article_id))
        raw = float(raw) if raw is not None and not pd.isna(raw) else 0.0
    except Exception:
        raw = 0.0
    return round(raw * PRICE_DISPLAY_SCALE, 2)


# ---------- cosmetics content recommender (trained H&M models don't apply) ----------

@st.cache_resource(show_spinner=False)
def _cosmetics_tfidf():
    """TF-IDF over cosmetics text (brand + category + type + shade + audience + desc)."""
    from sklearn.feature_extraction.text import TfidfVectorizer
    df = load_cosmetics()
    text = (df["brand"].fillna("") + " " + df["category"].fillna("") + " "
            + df["product_type_name"].fillna("") + " " + df["colour_group_name"].fillna("") + " "
            + df["index_group_name"].fillna("") + " " + df["detail_desc"].fillna(""))
    vec = TfidfVectorizer(max_features=2000, stop_words="english")
    mat = normalize(vec.fit_transform(text.values))
    ids = df["article_id"].astype(str).tolist()
    return mat, ids, {a: i for i, a in enumerate(ids)}


def recommend_cosmetics(seed_ids=None, prefs=None, k: int = 12, exclude=None):
    """Content-based cosmetics recs → [(article_id, score)]. Profile = mean TF-IDF of
    the user's saved/seed items (or preference categories); cold-start falls back to a
    featured order (on-sale + premium first)."""
    mat, ids, id_to_row = _cosmetics_tfidf()
    df = load_cosmetics()
    exclude = set(exclude or set())
    rows = [id_to_row[a] for a in (seed_ids or []) if a in id_to_row]
    if not rows and prefs:
        mask = (df["category"].isin(prefs) | df["product_type_name"].isin(prefs)
                | df["index_group_name"].isin(prefs))
        rows = [id_to_row[a] for a in df[mask]["article_id"].astype(str) if a in id_to_row]

    if rows:
        profile = normalize(csr_matrix(np.asarray(mat[rows].mean(axis=0))))
        scores = (profile @ mat.T).toarray().ravel()
        for r in rows:
            scores[r] = -np.inf  # don't recommend the seed items themselves
        order = np.argsort(-scores)
        scored = [(ids[i], float(scores[i])) for i in order if np.isfinite(scores[i])]
    else:
        # cold-start: featured — on-sale first, then by price desc
        pm = _cosmetics_price_map()
        feat = sorted(ids, key=lambda a: (pm.get(a, (0, None))[1] is None, -pm.get(a, (0, None))[0]))
        scored = [(a, None) for a in feat]

    out = [(a, s) for a, s in scored if a not in exclude][:k]
    return out


# ---------------------------------------------------------------- assistant (#10)
# Concern keyword -> substrings looked for in product name / type / description.
_ASSIST_CONCERNS = {
    "dry": ["hydrat", "moistur", "nourish", "hyaluronic"],
    "hydrat": ["hydrat", "moistur", "hyaluronic"],
    "moistur": ["hydrat", "moistur", "cream"],
    "oily": ["oil-free", "matte", "clarify", "balanc"],
    "acne": ["blemish", "clarify", "salicylic", "purify"],
    "anti-aging": ["firm", "retinol", "wrinkle", "renew", "lift"],
    "aging": ["firm", "retinol", "wrinkle", "renew", "lift"],
    "wrinkle": ["firm", "retinol", "renew"],
    "bright": ["bright", "glow", "radian", "vitamin c", "luminous"],
    "glow": ["glow", "radian", "luminous", "dewy"],
    "dull": ["bright", "glow", "radian"],
    "sensitive": ["gentle", "soothing", "calm", "fragrance-free"],
    "soothing": ["gentle", "soothing", "calm"],
    "redness": ["calm", "soothing", "gentle"],
    "volume": ["volume", "thicken", "plump"],
    "frizz": ["smooth", "frizz", "anti-frizz"],
}
_ASSIST_QUICK = ["Gift for her", "Something on sale", "Hydrating skincare", "A nice perfume"]


def cosmetics_assistant_reply(query: str, catalogue=None):
    """Rule-based shopping assistant (#10) — no external LLM.

    Parses free text for category / product type / brand / shade / made-in /
    audience / quality / price-cap / on-sale / gift / skin-concern intents,
    scores every product by how many signals it matches, and returns
    ``(reply_text, [article_ids])`` (up to 4 ids). Falls back to the cold-start
    featured order when nothing matches.
    """
    import re

    df = (catalogue if catalogue is not None else load_articles()).copy()
    q = (query or "").lower().strip()
    if not q:
        return ("Tell me what you're after — a category, a concern, a budget, "
                "or a gift idea. Try the chips above to get started.", [])

    tokens = set(re.findall(r"[a-z']+", q))
    if tokens & {"hi", "hello", "hey", "salom", "help"} and len(tokens) <= 2:
        return ("Hi! I can help you find products. Tell me a category (skincare, "
                "makeup, fragrance, hair & body), a concern (dry skin, anti-aging, "
                "oily), a budget (\"under $30\"), or who it's for (\"a gift for her\").", [])

    def vals(col):
        return {str(v) for v in df[col].dropna()} if col in df.columns else set()

    cats = {c.lower(): c for c in vals("category")}
    types = {t.lower(): t for t in vals("product_type_name")}
    brands = {b.lower(): b for b in vals("brand")}
    shades = {s.lower(): s for s in vals("colour_group_name")}
    made = {m.lower(): m for m in vals("made_in")}

    want_cat = [v for k, v in cats.items() if k in q]
    want_type = [v for k, v in types.items() if k in q]
    want_brand = [v for k, v in brands.items() if k in q]
    want_shade = [v for k, v in shades.items() if k in q]
    want_made = [v for k, v in made.items() if k in q]
    # "perfume"/"scent"/"cologne" -> Fragrance category
    if any(w in q for w in ("perfume", "scent", "cologne", "fragrance")) and "Fragrance" not in want_cat:
        if "Fragrance" in cats.values():
            want_cat.append("Fragrance")

    audience = None
    if tokens & {"women", "woman", "her", "she", "female", "ladies", "mom", "mum", "girlfriend", "wife"}:
        audience = "Women"
    elif tokens & {"men", "man", "him", "he", "male", "dad", "boyfriend", "husband"}:
        audience = "Men"
    elif tokens & {"kids", "kid", "children", "child", "baby", "toddler"}:
        audience = "Kids"

    want_luxury = any(w in q for w in ("luxury", "luxe", "premium", "high end", "high-end", "splurge", "best"))
    want_budget = any(w in q for w in ("cheap", "budget", "affordable", "inexpensive", "low cost"))
    want_sale = any(w in q for w in ("sale", "discount", "deal", "offer", "bargain"))
    want_gift = any(w in q for w in ("gift", "present", "for her", "for him"))

    cap = None
    m = (re.search(r"(?:under|below|less than|max|up ?to|<)\s*\$?\s*(\d+)", q)
         or re.search(r"\$\s*(\d+)", q))
    if m:
        cap = float(m.group(1))

    concern_terms = []
    for kw, terms in _ASSIST_CONCERNS.items():
        if kw in q:
            concern_terms += terms

    eff = {a: effective_price(a) for a in df["article_id"].astype(str)}

    scored = []
    for _, r in df.iterrows():
        aid = str(r["article_id"])
        score = 0
        if want_cat and r.get("category") in want_cat:
            score += 3
        if want_type and r.get("product_type_name") in want_type:
            score += 4
        if want_brand and r.get("brand") in want_brand:
            score += 3
        if want_shade and r.get("colour_group_name") in want_shade:
            score += 2
        if want_made and r.get("made_in") in want_made:
            score += 2
        if audience:
            ig = r.get("index_group_name")
            if ig == audience:
                score += 3
            elif ig == "Unisex":
                score += 1
            elif audience in ("Men", "Kids"):
                score -= 4  # gendered/age request — exclude the wrong aisle
        if want_luxury and r.get("quality") in ("Luxury", "Premium"):
            score += 2
        if want_budget and r.get("quality") == "Standard":
            score += 1
        if want_sale and pd.notna(r.get("sale_price")):
            score += 3
        if want_gift and r.get("quality") in ("Luxury", "Premium"):
            score += 1
        if concern_terms:
            text = " ".join(str(r.get(c, "")) for c in
                            ("prod_name", "product_type_name", "category", "detail_desc")).lower()
            score += 2 * sum(1 for t in concern_terms if t in text)
        if cap is not None:
            score += 2 if eff.get(aid, 0.0) <= cap else -6
        scored.append((aid, score))

    hits = sorted([(a, s) for a, s in scored if s > 0], key=lambda x: -x[1])
    ids = [a for a, _ in hits[:4]]

    # ---- build a natural-language summary of what was understood ----
    bits = []
    if audience:
        bits.append({"Women": "for women", "Men": "for men", "Kids": "for kids"}[audience])
    if want_cat:
        bits.append(" / ".join(want_cat).lower())
    if want_type:
        bits.append(" / ".join(want_type).lower())
    if want_brand:
        bits.append("by " + " / ".join(want_brand))
    if want_shade:
        bits.append("in " + " / ".join(want_shade).lower())
    if want_made:
        bits.append("made in " + " / ".join(want_made))
    if concern_terms:
        bits.append("for that concern")
    if want_luxury:
        bits.append("on the luxury end")
    if want_budget:
        bits.append("budget-friendly")
    if cap is not None:
        bits.append(f"under ${cap:.0f}")
    if want_sale:
        bits.append("on sale")
    if want_gift and not (want_cat or want_type):
        bits.append("gift-worthy")

    if not ids:
        # nothing matched — fall back to featured (or on-sale if they asked)
        ex = set()
        fb = recommend_cosmetics(prefs=None, k=4, exclude=ex)
        if want_sale:
            sale = [a for a in df[df["sale_price"].notna()]["article_id"].astype(str)][:4]
            fb = [(a, None) for a in sale] or fb
        ids = [a for a, _ in fb][:4]
        return ("I couldn't pin that down exactly, so here are some popular picks to "
                "browse. Try naming a category, a concern, or a budget.", ids)

    desc = " ".join(bits) if bits else "matching your request"
    return (f"Here {'is' if len(ids) == 1 else 'are'} {len(ids)} pick"
            f"{'' if len(ids) == 1 else 's'} {desc}:", ids)


@st.cache_resource(show_spinner="Computing trending items (one-time)…")
def load_trending(top_n: int = 400) -> pd.Series:
    """Article popularity from the last month of H&M transactions.

    First call computes from `transactions_train.csv` (~10–30s) and persists to
    `models/trending.pkl`. Subsequent calls return the cached series instantly.
    Returns a pandas Series indexed by article_id with frequency counts.
    """
    path = MODEL_DIR / "trending.pkl"
    if path.exists():
        with open(path, "rb") as f:
            return pickle.load(f)
    # Cold compute — stream the article_id column only (much faster than full load).
    counts = pd.Series(dtype=int)
    import pandas as _pd
    for chunk in _pd.read_csv(
        REPO_ROOT / "data" / "transactions_train.csv",
        usecols=["article_id", "t_dat"],
        dtype={"article_id": str},
        chunksize=500_000,
    ):
        # Keep only the most-recent slice — use chunks at end of file as a cheap recency proxy
        counts = counts.add(chunk["article_id"].value_counts(), fill_value=0)
    counts = counts.sort_values(ascending=False).head(top_n).astype(int)
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        pickle.dump(counts, f)
    return counts


def recommend_trending(excluded: set | None, k: int = 6,
                       include: set | None = None) -> list[tuple[str, float]]:
    """Top-k most-purchased articles, filtered against `excluded`. Score is the
    item's frequency rescaled to 0.65–0.99 for display. `include` restricts the
    pool (used to rank within the curated catalogue)."""
    counts = load_trending()
    if include is not None:
        counts = counts[counts.index.isin(include)]
    if excluded:
        counts = counts[~counts.index.isin(excluded)]
    top = counts.head(k)
    if top.empty:
        return []
    arr = top.values.astype(np.float32)
    lo, hi = float(arr.min()), float(arr.max())
    if hi - lo < 1e-12:
        norm = np.ones_like(arr) * 0.9
    else:
        norm = 0.65 + 0.34 * (arr - lo) / (hi - lo)
    return [(str(a), float(s)) for a, s in zip(top.index, norm)]


def recommend_customers_like_you(als_model, als_item_index, als_item_to_row,
                                  positives: set, excluded: set, k: int = 6,
                                  include: set | None = None
                                  ) -> list[tuple[str, float]]:
    """Pure-ALS rec, framed as 'customers like you also liked'. Same fold-in
    mechanic as recommend_als — distinct rail title gives users intuition for
    what the CF tower contributes vs the content-based one.

    Returns [] (not None) so the rail renders an empty-state card when the user
    has no positives yet."""
    out = recommend_als(als_model, als_item_index, als_item_to_row, positives, excluded, k,
                        include=include)
    return out or []


def recommend_new_arrivals(articles: pd.DataFrame, preferences: list[str] | None,
                            excluded: set | None, k: int = 6
                            ) -> list[tuple[str, float]]:
    """Newest articles matching the user's preferred product types.

    The H&M articles dataset has no date column, so we use `article_id` (a
    10-digit zero-padded string that sorts chronologically) as the newness
    proxy — higher = newer. Filters to the user's signup-preference categories
    when those exist; otherwise returns the catalogue-wide newest items.
    """
    df = articles
    if preferences:
        scope = df[df["product_type_name"].isin(preferences)]
        if not scope.empty:
            df = scope
    if excluded:
        df = df[~df["article_id"].isin(excluded)]
    if df.empty:
        return []
    newest = df.sort_values("article_id", ascending=False).head(k)
    n = len(newest)
    # Linear score 0.99 → 0.7 (newest at top) so the chip varies by rank.
    if n == 1:
        scores = [0.95]
    else:
        scores = [0.99 - 0.29 * i / (n - 1) for i in range(n)]
    return [(str(a), float(s)) for a, s in zip(newest["article_id"].tolist(), scores)]


# ---------- diversity re-ranking ----------

def intra_list_diversity(rec_ids, tfidf, item_id_to_row) -> float:
    """Mean pairwise dissimilarity (1 - cosine) across the recommendation list,
    measured in TF-IDF space. 0.0 = all items identical, 1.0 = all orthogonal.

    Standard Intra-List Diversity (Smyth & McClave 2001). Used as the on-screen
    diversity score per rail.
    """
    if isinstance(rec_ids, list) and rec_ids and isinstance(rec_ids[0], tuple):
        rec_ids = [a for a, _ in rec_ids]
    rows = [item_id_to_row[a] for a in rec_ids if a in item_id_to_row]
    if len(rows) < 2:
        return 0.0
    sub = tfidf[rows]
    sims = (sub @ sub.T).toarray()
    n = len(rows)
    iu_i, iu_j = np.triu_indices(n, k=1)
    return float((1.0 - sims[iu_i, iu_j]).mean())


def mmr_rerank(candidates, tfidf, item_id_to_row, k: int,
               lambda_param: float = 0.7) -> list[tuple[str, float]]:
    """Maximal Marginal Relevance re-ranking (Carbonell & Goldstein 1998).

    Greedy selection: at each step pick the candidate that maximises
        λ · relevance(c) − (1−λ) · max_sim(c, already_selected)

    where relevance is the recommender's original score and similarity is
    TF-IDF cosine. λ=1.0 reproduces the input ranking (pure relevance);
    λ=0.0 ignores relevance entirely (pure diversity). 0.7 is a standard
    default that visibly diversifies without sacrificing top-of-list quality.

    `candidates` is the recommender's output: [(article_id, score), ...].
    Returns the top-k after re-ranking, with original scores preserved.
    """
    if not candidates:
        return []
    pool: list[tuple[str, float]] = list(candidates)
    selected: list[tuple[str, float]] = []
    selected_rows: list[int] = []

    # Normalise relevance scores to [0, 1] so λ-mixing is comparable
    rels = np.array([s for _, s in pool], dtype=np.float32)
    lo, hi = float(rels.min()), float(rels.max())
    if hi - lo < 1e-12:
        rels_norm = np.ones_like(rels) * 0.5
    else:
        rels_norm = (rels - lo) / (hi - lo)

    # Pick the most-relevant item first
    first_idx = int(np.argmax(rels_norm))
    first_aid, first_score = pool.pop(first_idx)
    rels_norm = np.delete(rels_norm, first_idx)
    selected.append((first_aid, first_score))
    if first_aid in item_id_to_row:
        selected_rows.append(item_id_to_row[first_aid])

    while len(selected) < k and pool:
        # Vectorised max-similarity to any already-selected item
        if selected_rows:
            cand_rows = []
            row_to_pool_idx = []
            for i, (aid, _) in enumerate(pool):
                r = item_id_to_row.get(aid)
                if r is not None:
                    cand_rows.append(r)
                    row_to_pool_idx.append(i)
            if cand_rows:
                sims = (tfidf[cand_rows] @ tfidf[selected_rows].T).toarray()
                max_sims = sims.max(axis=1)
                penalties = np.zeros(len(pool), dtype=np.float32)
                for i, mp in zip(row_to_pool_idx, max_sims):
                    penalties[i] = mp
            else:
                penalties = np.zeros(len(pool), dtype=np.float32)
        else:
            penalties = np.zeros(len(pool), dtype=np.float32)

        mmr_scores = lambda_param * rels_norm - (1.0 - lambda_param) * penalties
        best = int(np.argmax(mmr_scores))
        chosen_aid, chosen_score = pool.pop(best)
        rels_norm = np.delete(rels_norm, best)
        selected.append((chosen_aid, chosen_score))
        if chosen_aid in item_id_to_row:
            selected_rows.append(item_id_to_row[chosen_aid])

    return selected


def recommend_similar(article_id: str, tfidf, item_id_to_row, k=8, exclude=None,
                      include=None):
    """'More like this' → list of (article_id, cosine_similarity). `include`
    restricts candidates (ranks within the curated catalogue)."""
    if article_id not in item_id_to_row:
        return []
    row = item_id_to_row[article_id]
    scores = (tfidf[row] @ tfidf.T).toarray().ravel()
    if include is not None:
        keep = np.zeros(len(scores), dtype=bool)
        inc_rows = [item_id_to_row[a] for a in include if a in item_id_to_row]
        keep[inc_rows] = True
        scores[~keep] = -np.inf
    scores[row] = -np.inf
    if exclude:
        for aid in exclude:
            if aid in item_id_to_row:
                scores[item_id_to_row[aid]] = -np.inf
    if len(scores) <= k:
        order = np.argsort(-scores)
    else:
        order = np.argpartition(-scores, k)[:k]
        order = order[np.argsort(-scores[order])]
    row_to_item = {v: kk for kk, v in item_id_to_row.items()}
    # Drop masked (-inf) candidates so we never surface (or rescale) junk when
    # the include/excluded filters leave fewer than k valid items.
    return [(row_to_item[i], float(scores[i])) for i in order[:k] if np.isfinite(scores[i])]


# ---------- explainability ----------

def explain_cb_for_items(profile, rec_ids, tfidf, item_id_to_row, vectorizer, top_n=3):
    """Per-item explanation for CB-driven recs: top shared TF-IDF terms.

    Returns a dict {article_id: 'shares: term1, term2, term3'} or None for items
    with no overlap. Cheap because the profile vector is sparse — only nonzero
    profile terms can contribute.
    """
    if profile is None or profile.nnz == 0 or not rec_ids:
        return {}
    try:
        feature_names = vectorizer.get_feature_names_out()
    except AttributeError:
        return {}
    profile_dense = profile.toarray().ravel()
    out: dict[str, str] = {}
    for aid in rec_ids:
        row = item_id_to_row.get(aid)
        if row is None:
            continue
        item_dense = tfidf[row].toarray().ravel()
        contribution = profile_dense * item_dense
        nonzero = np.where(contribution > 0)[0]
        if len(nonzero) == 0:
            continue
        ordered = nonzero[np.argsort(-contribution[nonzero])][:top_n]
        terms = [str(feature_names[i]) for i in ordered]
        out[aid] = "shares: " + ", ".join(terms)
    return out


def explain_cf_for_items(rec_ids: list[str]) -> dict[str, str]:
    """CF-style explanations: how many platform users currently have each item saved.

    Per supervisor feedback §3.5 — CF cards should tell the user "47 customers
    with similar purchase histories also bought this" rather than reusing the
    content-based "shares X, Y" copy. We use the platform's own interaction
    log rather than H&M training data because the latter is anonymous and
    doesn't represent meaningful peer overlap.
    """
    if not rec_ids:
        return {}
    counts = db.article_save_counts(rec_ids)
    out: dict[str, str] = {}
    for aid in rec_ids:
        n = counts.get(aid, 0)
        if n >= 2:
            out[aid] = f"{n} other customers also saved this"
        elif n == 1:
            out[aid] = "1 other customer also saved this"
        else:
            out[aid] = "matched by collaborative filtering on your wishlist"
    return out


def explain_hybrid_for_items(profile, rec_ids: list[str], tfidf, item_id_to_row,
                              vectorizer, alpha: float) -> dict[str, str]:
    """Hybrid-style explanations: "Both models agree — matches your taste for X · α=0.50".

    Combines the CB shared-terms signal with the ensemble framing the supervisor
    asked for in §3.5. When the CB profile has no overlap (rare), falls back to
    a generic "both models contributed" line that still names the algorithm.
    """
    cb_terms = explain_cb_for_items(profile, rec_ids, tfidf, item_id_to_row, vectorizer)
    out: dict[str, str] = {}
    for aid in rec_ids:
        terms = cb_terms.get(aid, "")
        if terms:
            # Strip the "shares: " prefix so the hybrid prefix reads cleanly
            terms_clean = terms.replace("shares: ", "")
            out[aid] = f"both models agree — matches your taste for {terms_clean} · α={alpha:.2f}"
        else:
            out[aid] = f"content + collaborative ensemble · α={alpha:.2f}"
    return out


def explain_trending(rec_ids: list[str], trending_series) -> dict[str, str]:
    """Trending-rail explanations: "1,234 purchases in last month"."""
    out: dict[str, str] = {}
    for aid in rec_ids:
        if aid in trending_series.index:
            n = int(trending_series.loc[aid])
            out[aid] = f"{n:,} purchases · trending across the catalogue"
        else:
            out[aid] = "popular this period"
    return out


def explain_new_arrivals(rec_ids: list[str], preferences: list[str] | None) -> dict[str, str]:
    """New-arrivals-rail explanations: "New in your style · matches: Dress, T-shirt"."""
    if preferences:
        prefs_str = ", ".join(preferences[:3])
        line = f"new arrival in your preferred categories: {prefs_str}"
    else:
        line = "newly added to the catalogue"
    return {aid: line for aid in rec_ids}


def explain_similar_to(seed_article_id, rec_ids, articles):
    """Per-item explanation for 'similar to X' rails: list shared categorical
    attributes (type, colour, section) with the seed item."""
    seed_row = articles[articles["article_id"] == seed_article_id]
    if seed_row.empty:
        return {}
    seed = seed_row.iloc[0]
    rec_df = articles[articles["article_id"].isin(rec_ids)].set_index("article_id")
    out: dict[str, str] = {}
    fields = [
        ("product_type_name", "type"),
        ("colour_group_name", "colour"),
        ("section_name", "section"),
        ("department_name", "department"),
    ]
    for aid in rec_ids:
        if aid not in rec_df.index:
            continue
        item = rec_df.loc[aid]
        shared = [
            label for col, label in fields
            if pd.notna(seed.get(col)) and pd.notna(item.get(col)) and seed[col] == item[col]
        ]
        if shared:
            out[aid] = "same " + ", same ".join(shared)
    return out


# ---------- UI helpers shared across pages ----------

@st.cache_data(show_spinner=False)
def _load_docs_pdf() -> bytes | None:
    path = REPO_ROOT / "docs" / "project_explained.pdf"
    return path.read_bytes() if path.exists() else None


SESSION_TIMEOUT_SECONDS = 30 * 60  # 30 minutes — matches banking-tier convention


def check_session_timeout() -> None:
    """Auto-logout when the session has been idle past `SESSION_TIMEOUT_SECONDS`.

    Streamlit doesn't run timers between user interactions — this is checked
    each time the user does anything (which triggers a rerun). So a user who
    closed the tab and came back hours later gets bounced to the login screen
    on their next click rather than at exactly the 30-minute mark, which is
    the standard behaviour for session cookies anyway.
    """
    import time
    if st.session_state.get("user") is None:
        return
    last = st.session_state.get("_last_activity")
    now = time.time()
    if last is not None and (now - last) > SESSION_TIMEOUT_SECONDS:
        # Idle too long — revoke the persistent cookie too, else restore_session()
        # would immediately log them back in on the next run.
        clear_session()
        for k in list(st.session_state.keys()):
            if k not in ("mmr_enabled", "show_tech_details"):
                st.session_state.pop(k, None)
        st.warning(
            f"Session timed out after {SESSION_TIMEOUT_SECONDS // 60} minutes of inactivity. "
            f"Please log in again."
        )
        st.rerun()
    st.session_state["_last_activity"] = now


def _initials(name: str) -> str:
    parts = [p for p in name.replace(".", " ").replace("_", " ").split() if p]
    if len(parts) >= 2:                       # "Demo Customer" -> "DC"
        return (parts[0][0] + parts[1][0]).upper()
    if parts:                                  # "Zahid" -> "Z" (single initial, conventional)
        return parts[0][0].upper()
    return "?"


def render_account_menu(user: dict) -> None:
    """Top-right account avatar that opens a dropdown (name, email, role, logout).

    The conventional web pattern: a circular initials avatar in the corner that
    reveals the full identity + a destructive logout on click. Rendered in the
    main area and pinned top-right via the `.st-key-account_menu` scope in CSS.
    """
    import html
    name = user.get("display_name") or user.get("email", "")
    email = user.get("email", "")
    role = user.get("role", "customer")
    initials = _initials(name)
    unread = db.unread_notifications(user["id"])
    if unread:  # red badge on the avatar when there are unread notifications
        st.markdown(
            "<style>.st-key-account_menu button{position:relative;}"
            ".st-key-account_menu button::after{content:'';position:absolute;top:1px;right:1px;"
            "width:12px;height:12px;border-radius:50%;background:#e8462a;border:2px solid #fff;}</style>",
            unsafe_allow_html=True,
        )
    with st.popover(initials, use_container_width=False, key="account_menu"):
        role_chip = (f'<span class="acct-role">{html.escape(role.capitalize())}</span>'
                     if role in ("admin", "analyst") else "")
        st.markdown(
            '<div class="acct-pop">'
            f'<div class="acct-avatar-lg">{html.escape(initials)}</div>'
            f'<div class="acct-name">{html.escape(name)}</div>'
            f'<div class="acct-email">{html.escape(email)}</div>'
            f'{role_chip}'
            '</div>',
            unsafe_allow_html=True,
        )

        # ---------- notifications ----------
        notes = db.get_notifications(user["id"], limit=8)
        if notes:
            hdr = f"Notifications · {unread} new" if unread else "Notifications"
            st.markdown(f'<p style="font-weight:600;margin:6px 0 4px;">{html.escape(hdr)}</p>',
                        unsafe_allow_html=True)
            for nt in notes:
                bg = "var(--accent-soft)" if not nt["read"] else "transparent"
                st.markdown(
                    f'<div style="background:{bg};border:1px solid var(--border);border-radius:10px;'
                    f'padding:8px 10px;margin-bottom:6px;font-size:12.5px;line-height:1.45;">'
                    f'{html.escape(nt["message"])}'
                    f'<div class="muted" style="font-size:11px;margin-top:3px;">{(nt["created_at"] or "")[:16]}</div>'
                    f'</div>', unsafe_allow_html=True)
            if unread and st.button("Mark all read", use_container_width=True, key="acct_mark_read"):
                db.mark_notifications_read(user["id"])
                st.rerun()
            st.markdown('<div class="divider" style="margin:6px 0 !important;"></div>', unsafe_allow_html=True)

        # Payment history (only roles with a storefront / orders page registered).
        if role in ("customer", "analyst"):
            if st.button("Payment history", use_container_width=True, key="acct_orders",
                         icon=":material/receipt_long:"):
                st.switch_page("pages/_orders.py")

        if st.button("Log out", use_container_width=True, key="acct_logout"):
            clear_session()  # revoke server-side session + clear the browser cookie
            for k in list(st.session_state.keys()):
                if k not in ("mmr_enabled", "show_tech_details"):  # preserve display prefs
                    st.session_state.pop(k, None)
            st.rerun()


def render_sidebar(user: dict) -> None:
    """Top-right account menu + sidebar extras (docs, display options).

    Page links (Home/Catalogue/Analytics/Admin/…) are owned by st.navigation;
    identity + logout live in the top-right account menu (render_account_menu).
    """
    if user is None:
        # Guest: a persistent Sign-in button pinned top-right (no account menu/docs).
        if st.button("Sign in", key="guest_signin", type="primary",
                     icon=":material/login:"):
            go_signin()
        return

    render_account_menu(user)  # rendered in main area, pinned top-right via CSS

    # Docs + recommender display options are a research-role affordance (analyst).
    # Customers get a clean shopping sidebar; admins are back-office only.
    if user.get("role") != "analyst":
        return

    with st.sidebar:
        # ---------- documentation ----------
        pdf_bytes = _load_docs_pdf()
        if pdf_bytes:
            st.download_button(
                "📄 Project documentation",
                pdf_bytes,
                file_name="project_explained.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="sidebar_docs",
                help="Full project report — methodology, literature review, "
                     "evaluation, critical reflection.",
            )

        # ---------- display options ----------
        st.divider()
        st.markdown("**Display options**")
        st.checkbox(
            "Diversify (MMR)",
            value=True, key="mmr_enabled",
            help="Maximal Marginal Relevance re-ranking — reduces redundancy in "
                 "recommendation rails. Turn off to see the un-diversified output.",
        )
        st.checkbox(
            "Show technical details",
            value=False, key="show_tech_details",
            help="Display article IDs and other internal identifiers on product "
                 "cards. Off by default (end-user view).",
        )


def _save_toggle(article_id: str, user_id: int, is_saved: bool, key: str) -> None:
    """Heart toggle. Icon-only (Material) keeps the card minimal."""
    help_msg = "Remove from wishlist" if is_saved else "Add to wishlist"
    if st.button("", key=key, use_container_width=True, help=help_msg,
                 icon=(":material/favorite:" if is_saved else ":material/favorite_border:"),
                 type=("primary" if is_saved else "secondary")):
        db.log_interaction(user_id, article_id, "unsave" if is_saved else "save")
        st.rerun()


def _feedback_buttons(article_id: str, user_id: int, liked: bool, disliked: bool,
                      key_prefix: str) -> None:
    """Mutually-exclusive thumbs row. Icon-only — text is in the tooltip."""
    c1, c2 = st.columns(2)
    with c1:
        help_msg = "Unlike" if liked else "Like — feeds the recommender"
        if st.button("", icon=":material/thumb_up:",
                     type=("primary" if liked else "secondary"),
                     key=f"{key_prefix}_like_{article_id}",
                     use_container_width=True,
                     help=help_msg):
            if liked:
                db.log_interaction(user_id, article_id, "unlike")
            else:
                if disliked:
                    db.log_interaction(user_id, article_id, "undislike")
                db.log_interaction(user_id, article_id, "like")
            st.rerun()
    with c2:
        help_msg = "Un-hide" if disliked else "Not for me — hides from future rails"
        if st.button("", icon=":material/thumb_down:",
                     type=("primary" if disliked else "secondary"),
                     key=f"{key_prefix}_dislike_{article_id}",
                     use_container_width=True,
                     help=help_msg):
            if disliked:
                db.log_interaction(user_id, article_id, "undislike")
            else:
                if liked:
                    db.log_interaction(user_id, article_id, "unlike")
                db.log_interaction(user_id, article_id, "dislike")
            st.rerun()


def _render_actions(article_id: str, key_prefix: str,
                    user_id: int | None = None,
                    saved_set: set | None = None,
                    liked_set: set | None = None,
                    disliked_set: set | None = None,
                    reason: str | None = None,
                    cart_set: set | None = None) -> None:
    """Render the action row(s) below a card.

    - View+Save row whenever user_id + saved_set are passed.
    - Like+Dislike row whenever liked_set + disliked_set are passed (rec cards).
    - 'Why this?' caption when reason is passed.
    """
    def _compare_btn(col):
        with col:
            on = in_compare(article_id)
            if st.button("", key=f"{key_prefix}_cmp_{article_id}",
                         icon=(":material/balance:"),
                         type="primary" if on else "secondary", use_container_width=True,
                         help="Remove from compare" if on else "Add to compare"):
                toggle_compare(article_id)
                st.rerun()

    # The whole card is a link to the detail page (#3); the action row below it
    # leads with Add-to-cart (#4), then wishlist + compare.
    if user_id is not None and saved_set is not None:
        b1, b2, b3 = st.columns([2, 1, 1])  # Add to cart, heart, compare
        with b1:
            in_cart = bool(cart_set) and article_id in cart_set
            if st.button("In cart" if in_cart else "Add to cart",
                         key=f"{key_prefix}_cart_{article_id}",
                         icon=(":material/check:" if in_cart else ":material/shopping_cart:"),
                         type="primary",
                         use_container_width=True,
                         help="In your cart — add another" if in_cart else "Add to cart"):
                db.add_to_cart(user_id, article_id, 1)
                st.toast("Added to cart", icon=":material/shopping_cart:")
                st.rerun()
        with b2:
            _save_toggle(article_id, user_id, article_id in saved_set, key=f"{key_prefix}_save_{article_id}")
        _compare_btn(b3)
    else:
        b1, b2 = st.columns([3, 1])  # Add to cart (→ sign in), compare (guest)
        with b1:
            if st.button("Add to cart", key=f"{key_prefix}_cart_{article_id}",
                         icon=":material/shopping_cart:",
                         type="primary", use_container_width=True, help="Sign in to add to cart"):
                go_signin()
        _compare_btn(b2)

    if user_id is not None and liked_set is not None and disliked_set is not None:
        _feedback_buttons(
            article_id, user_id,
            liked=article_id in liked_set,
            disliked=article_id in disliked_set,
            key_prefix=key_prefix,
        )

    if reason:
        st.caption(f"Why: {reason}")


def _card_match_chip(score: float | None) -> str:
    """Render the match% chip as inline HTML, or '' if no/invalid score."""
    import math
    if score is None or not math.isfinite(score):
        return ""
    pct = max(0, min(99, int(round(score * 100))))
    klass = "high" if pct >= 80 else "mid"
    return f'<span class="card-match {klass}">{pct}% match</span>'


def product_href(article_id: str) -> str:
    """Relative URL to the product detail page (resolves to /product from any
    single-segment page path). Used to make whole cards clickable links (#3)."""
    return f"product?aid={article_id}"


def _card_html(item: dict, rank: int | None = None,
               score: float | None = None, reason: str | None = None,
               href: str | None = None) -> str:
    """Render the full image-led card body (image, match chip, title, meta, reason).

    When `href` is given the whole card is wrapped in a link to the product page.
    """
    aid = str(item["article_id"])
    img_src = _resolve_image_src(aid, item)
    rank_html = f'<span class="card-rank-badge">{rank}</span>' if rank else ""
    match_html = _card_match_chip(score)
    name = item.get("prod_name") or "—"
    meta_parts = [
        item.get("product_type_name") or "",
        item.get("colour_group_name") or "",
    ]
    meta_parts = [m for m in meta_parts if m]
    meta = '<span class="dot">·</span>'.join(meta_parts) if meta_parts else "—"
    section = item.get("section_name") or ""
    # Price line (cosmetics): regular, or struck-through original + gold sale price.
    price_html = ""
    if cosmetics_mode():
        reg, sale = catalogue_price(aid)
        if sale is not None:
            price_html = (f'<p class="card-price"><s>${reg:,.2f}</s>'
                          f'<span class="sale">${sale:,.2f}</span></p>')
        elif reg:
            price_html = f'<p class="card-price">${reg:,.2f}</p>'
    reason_html = (
        f'<p class="card-reason"><span class="why-icon">'
        f'<svg width="11" height="11" viewBox="0 0 24 24" fill="#C19A3E" '
        f'style="vertical-align:-1px;margin-right:3px;">'
        f'<path d="M12 2l2.2 5.8L20 10l-5.8 2.2L12 18l-2.2-5.8L4 10l5.8-2.2z"/></svg>'
        f'</span>{reason}</p>'
        if reason else ""
    )
    # Article ID is internal data — only show if user has explicitly toggled it on
    # in the sidebar's Display options.
    show_id = st.session_state.get("show_tech_details", False)
    id_html = f'<p class="card-id">{aid}</p>' if show_id else ""
    body = (
        '<div class="card">'
        '  <div class="card-image-wrapper">'
        f'    <img class="card-image" src="{img_src}" loading="lazy" alt="{name}" />'
        f'    {rank_html}'
        f'    {match_html}'
        '  </div>'
        '  <div class="card-body">'
        f'    <p class="card-title">{name}</p>'
        f'    <p class="card-meta">{meta}{" · " + section if section else ""}</p>'
        f'    {price_html}'
        f'    {reason_html}'
        f'    {id_html}'
        '  </div>'
        '</div>'
    )
    if href:
        return f'<a class="card-link" href="{href}" target="_self">{body}</a>'
    return body


def _coerce_recs(recs) -> tuple[list[str], dict]:
    """Accept either `[aid, ...]` or `[(aid, score), ...]` and return both forms."""
    if not recs:
        return [], {}
    if isinstance(recs[0], tuple):
        ids = [a for a, _ in recs]
        scores = {a: s for a, s in recs}
    else:
        ids = list(recs)
        scores = {}
    return ids, scores


def render_rec_cards(rec_ids, articles: pd.DataFrame, key_prefix: str = "rec",
                     user_id: int | None = None, saved_set: set | None = None,
                     liked_set: set | None = None, disliked_set: set | None = None,
                     reasons: dict | None = None, scores: dict | None = None,
                     cart_set: set | None = None) -> None:
    """Two-column grid of ranked recommendation cards (with rank badge)."""
    ids, inferred_scores = _coerce_recs(rec_ids)
    scores = scores if scores is not None else inferred_scores
    rec_df = articles[articles["article_id"].isin(ids)].copy()
    rank_map = {a: i + 1 for i, a in enumerate(ids)}
    rec_df["rank"] = rec_df["article_id"].map(rank_map)
    rec_df = rec_df.sort_values("rank")
    for i in range(0, len(rec_df), 2):
        row_cols = st.columns(2, gap="small")
        for col, (_, item) in zip(row_cols, rec_df.iloc[i: i + 2].iterrows()):
            with col:
                d = item.to_dict()
                aid = str(d["article_id"])
                with st.container(key=f"cw_{key_prefix}_{aid}"):
                    st.markdown(
                        _card_html(
                            d,
                            rank=int(d["rank"]),
                            score=scores.get(d["article_id"]),
                            reason=(reasons or {}).get(d["article_id"]),
                        ),
                        unsafe_allow_html=True,
                    )
                    if st.button("View product", key=f"cl_{key_prefix}_{aid}"):  # transparent overlay (#3)
                        st.session_state["viewing_article_id"] = aid
                        st.switch_page("pages/_product.py")
                _render_actions(
                    d["article_id"], key_prefix,
                    user_id=user_id, saved_set=saved_set,
                    liked_set=liked_set, disliked_set=disliked_set,
                    cart_set=cart_set,
                )


def render_catalogue_card(item: dict, key_prefix: str,
                          user_id: int | None = None, saved_set: set | None = None,
                          liked_set: set | None = None, disliked_set: set | None = None,
                          reason: str | None = None, score: float | None = None,
                          cart_set: set | None = None) -> None:
    """Unranked card (used in browse/wishlist grids and rails)."""
    aid = str(item["article_id"])
    with st.container(key=f"cw_{key_prefix}_{aid}"):
        st.markdown(_card_html(item, rank=None, score=score, reason=reason), unsafe_allow_html=True)
        if st.button("View product", key=f"cl_{key_prefix}_{aid}"):  # transparent overlay (#3)
            st.session_state["viewing_article_id"] = aid
            st.switch_page("pages/_product.py")
    _render_actions(
        aid, key_prefix,
        user_id=user_id, saved_set=saved_set,
        liked_set=liked_set, disliked_set=disliked_set,
        cart_set=cart_set,
    )


def render_rail(title: str, caption: str, recs, articles: pd.DataFrame,
                key_prefix: str, user_id: int | None = None,
                saved_set: set | None = None, liked_set: set | None = None,
                disliked_set: set | None = None, reasons: dict | None = None,
                cols: int = 3, cart_set: set | None = None) -> None:
    """Product-rail layout: heading + caption + n-col grid of unranked cards.

    `recs` accepts either a list of article_ids or a list of (article_id, score)
    tuples — match% chips are rendered automatically when scores are present.
    """
    st.markdown(f"<h2>{title}</h2>", unsafe_allow_html=True)
    st.markdown(f'<p class="muted">{caption}</p>', unsafe_allow_html=True)
    ids, scores = _coerce_recs(recs)
    if not ids:
        st.markdown(
            '<div class="card" style="padding:32px; text-align:center;">'
            '<p class="muted">Not enough signal yet — save a few items to fill this rail.</p>'
            '</div>',
            unsafe_allow_html=True,
        )
        return
    rec_df = articles[articles["article_id"].isin(ids)].copy()
    order = {aid: i for i, aid in enumerate(ids)}
    rec_df["_order"] = rec_df["article_id"].map(order)
    rec_df = rec_df.sort_values("_order")
    rows = (len(rec_df) + cols - 1) // cols
    for r in range(rows):
        col_widgets = st.columns(cols, gap="small")
        for ci, col in enumerate(col_widgets):
            idx = r * cols + ci
            if idx >= len(rec_df):
                break
            item = rec_df.iloc[idx].to_dict()
            with col:
                render_catalogue_card(
                    item, key_prefix=f"{key_prefix}_r{r}_c{ci}",
                    user_id=user_id, saved_set=saved_set,
                    liked_set=liked_set, disliked_set=disliked_set,
                    reason=(reasons or {}).get(item["article_id"]),
                    score=scores.get(item["article_id"]),
                    cart_set=cart_set,
                )
