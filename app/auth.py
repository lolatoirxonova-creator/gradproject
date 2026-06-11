"""Authentication primitives: pure functions, no Streamlit imports.

Session-state binding (st.session_state["user"]) is the UI layer's job and
lives in main.py. Keeping these helpers pure makes them testable in isolation
and reusable from CLI scripts (e.g. seeding an admin user).
"""

from __future__ import annotations

import re
import secrets
import sqlite3

import bcrypt

from app import db


EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")
MIN_PASSWORD_LEN = 8
ALLOWED_ROLES = ("customer", "admin", "analyst", "seller")
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_WINDOW_MINUTES = 15


SESSION_COOKIE_NAME = "hm_session"
SESSION_TTL_DAYS = 30


def new_session_token() -> str:
    """Opaque, unguessable session token stored in the browser cookie."""
    return secrets.token_urlsafe(32)


class AuthError(Exception):
    """User-facing auth failure (invalid input, duplicate email, bad password)."""


class LockedError(AuthError):
    """Account is temporarily locked due to excessive failed login attempts."""


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


def _row_to_user(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "email": row["email"],
        "display_name": row["display_name"],
        "role": row["role"],
    }


def register(email: str, password: str, display_name: str, role: str = "customer") -> dict:
    """Create a user. Raises AuthError on validation failure or duplicate email."""
    email = email.strip().lower()
    display_name = display_name.strip()
    if not EMAIL_RE.match(email):
        raise AuthError("Invalid email address.")
    if len(password) < MIN_PASSWORD_LEN:
        raise AuthError(f"Password must be at least {MIN_PASSWORD_LEN} characters.")
    if not display_name:
        raise AuthError("Display name is required.")
    if role not in ALLOWED_ROLES:
        raise AuthError("Invalid role.")
    try:
        with db.get_conn() as conn:
            cur = conn.execute(
                "INSERT INTO users(email, password_hash, display_name, role) "
                "VALUES (?, ?, ?, ?)",
                (email, _hash_password(password), display_name, role),
            )
            conn.commit()
            user_id = cur.lastrowid
    except sqlite3.IntegrityError:
        raise AuthError("That email is already registered.")
    return {"id": user_id, "email": email, "display_name": display_name, "role": role}


def authenticate(email: str, password: str, ip: str | None = None) -> dict:
    """Verify credentials. Records every attempt to the audit log and enforces
    a failed-attempt lockout (`MAX_FAILED_ATTEMPTS` failures in
    `LOCKOUT_WINDOW_MINUTES` → block).

    Returns the user dict or raises AuthError / LockedError.
    """
    email = email.strip().lower()

    # Check lockout before verifying — and crucially before revealing whether
    # the account exists, so probing doesn't bypass the limit.
    n_failed = db.failed_attempts_in_window(email, minutes=LOCKOUT_WINDOW_MINUTES)
    if n_failed >= MAX_FAILED_ATTEMPTS:
        db.record_login_attempt(email, success=False, ip=ip)
        raise LockedError(
            f"Too many failed attempts ({MAX_FAILED_ATTEMPTS} in the last "
            f"{LOCKOUT_WINDOW_MINUTES} minutes). Account is temporarily locked. "
            f"Try again in {LOCKOUT_WINDOW_MINUTES} minutes."
        )

    with db.get_conn() as conn:
        row = conn.execute(
            "SELECT id, email, password_hash, display_name, role "
            "FROM users WHERE email = ?",
            (email,),
        ).fetchone()

    if row is None or not _verify_password(password, row["password_hash"]):
        db.record_login_attempt(email, success=False, ip=ip)
        raise AuthError("Incorrect email or password.")

    db.record_login_attempt(email, success=True, ip=ip)
    return _row_to_user(row)


def get_user(user_id: int) -> dict | None:
    with db.get_conn() as conn:
        row = conn.execute(
            "SELECT id, email, display_name, role FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
    return _row_to_user(row) if row else None


def set_preferences(user_id: int, categories: list[str]) -> None:
    """Replace the user's preferred categories (used to seed cold-start recs)."""
    clean = [c.strip() for c in categories if c and c.strip()]
    with db.get_conn() as conn:
        conn.execute("DELETE FROM preferences WHERE user_id = ?", (user_id,))
        conn.executemany(
            "INSERT INTO preferences(user_id, category) VALUES (?, ?)",
            [(user_id, c) for c in clean],
        )
        conn.commit()


def get_preferences(user_id: int) -> list[str]:
    with db.get_conn() as conn:
        rows = conn.execute(
            "SELECT category FROM preferences WHERE user_id = ?",
            (user_id,),
        ).fetchall()
    return [r["category"] for r in rows]


# ---------- demo-account seeding ----------

# Accounts named per the supervisor's feedback table (§4.4). Passwords are the
# documented credentials the External Examiner will use during assessment —
# committed deliberately so the demo is reproducible from a fresh database.
DEMO_ACCOUNTS = [
    {
        "email": "demo_customer@example.com",
        "password": "Demo2026!",
        "display_name": "Demo Customer",
        "role": "customer",
        "preferences": ["Dress", "T-shirt", "Trousers"],
        "saves_n": 5,
        "scenario": "warm customer — saved items, preferences, full rail experience",
    },
    {
        "email": "demo_admin@example.com",
        "password": "Admin2026!",
        "display_name": "Demo Admin",
        "role": "admin",
        "preferences": ["Jumper", "Coat", "Sneakers"],
        "saves_n": 3,
        "scenario": "admin — sees Analytics + Admin panel + retrain button",
    },
    {
        "email": "demo_analyst@example.com",
        "password": "Analyst2026!",
        "display_name": "Demo Analyst",
        "role": "analyst",
        "preferences": ["Top", "Skirt"],
        "saves_n": 4,
        "scenario": "analyst — Analytics dashboard, no Admin panel",
    },
    {
        "email": "demo_seller@example.com",
        "password": "Seller2026!",
        "display_name": "Demo Seller",
        "role": "seller",
        "preferences": [],
        "saves_n": 0,
        "scenario": "seller — manages own product listings, sees orders for them",
    },
    {
        "email": "cold_user@example.com",
        "password": "Cold2026!",
        "display_name": "Cold User",
        "role": "customer",
        "preferences": [],
        "saves_n": 0,
        "scenario": "cold-start — no preferences, no saves, demonstrates fallback",
    },
]


# Sample listings so the seller panel isn't empty on a fresh demo database.
DEMO_SELLER_PRODUCTS = [
    {"prod_name": "Velora Rose Hand Cream", "brand": "Velora", "category": "Hair & body",
     "product_type_name": "Hand Cream", "index_group_name": "Women", "colour_group_name": "Pink",
     "quality": "Premium", "size": "75ml", "made_in": "Uzbekistan", "price": 18.0,
     "sale_price": 14.0, "detail_desc": "Nourishing rose-scented hand cream that hydrates dry skin.",
     "image_url": None},
    {"prod_name": "Velora Citrus Eau de Parfum", "brand": "Velora", "category": "Fragrance",
     "product_type_name": "Eau de Parfum", "index_group_name": "Unisex", "colour_group_name": "Amber",
     "quality": "Luxury", "size": "50ml", "made_in": "France", "price": 64.0, "sale_price": None,
     "detail_desc": "A bright, long-lasting citrus and amber fragrance for everyday wear.",
     "image_url": None},
]


def seed_demo_accounts(articles_df=None) -> list[dict]:
    """Create the demo accounts the supervisor's feedback (§4.4) listed for the
    External Examiner. Idempotent — pre-existing accounts are left untouched.

    Each account gets pre-populated state matching its scenario so the demo
    works without manual setup (warm vs cold, customer vs admin vs analyst).

    `articles_df` is optional — pass an already-loaded DataFrame to skip the
    CSV read when this is called from inside the running app.
    """
    if articles_df is None:
        import pandas as pd
        from pathlib import Path
        path = Path(__file__).resolve().parents[1] / "data" / "articles.csv"
        articles_df = pd.read_csv(path, dtype={"article_id": str})

    db.init_db()
    seeded = []
    for acc in DEMO_ACCOUNTS:
        try:
            user = register(acc["email"], acc["password"], acc["display_name"],
                            role=acc["role"])
        except AuthError as e:
            seeded.append({"email": acc["email"], "status": f"skipped ({e})"})
            continue

        if acc["preferences"]:
            set_preferences(user["id"], acc["preferences"])

        if acc["saves_n"] > 0:
            scope = articles_df
            if acc["preferences"]:
                pref_scope = articles_df[
                    articles_df["product_type_name"].isin(acc["preferences"])
                ]
                if len(pref_scope) >= acc["saves_n"]:
                    scope = pref_scope
            sample = scope.sample(
                n=acc["saves_n"], random_state=hash(acc["email"]) % (2**32),
            )
            for aid in sample["article_id"].tolist():
                db.log_interaction(user["id"], str(aid), "save")

        if acc["role"] == "seller" and not db.list_seller_products(user["id"]):
            for prod in DEMO_SELLER_PRODUCTS:
                db.add_seller_product(user["id"], prod)

        seeded.append({"email": acc["email"], "status": "created"})
    return seeded


if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 2 and sys.argv[1] == "seed-demos":
        results = seed_demo_accounts()
        print("Demo account seeding:")
        for r in results:
            print(f"  {r['email']:35} {r['status']}")
        print()
        print("Credentials (per supervisor feedback §4.4):")
        for a in DEMO_ACCOUNTS:
            print(f"  {a['email']:35} {a['password']:15} role={a['role']:10} — {a['scenario']}")
    else:
        print("Usage: python -m app.auth seed-demos")
