"""SQLite layer for the recommendation platform.

The H&M article catalogue lives in `articles.csv` and is NOT mirrored here —
`article_id` is the cross-reference. We only persist platform-side state:
user accounts, signup preferences, and interaction events.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "app.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    email           TEXT    UNIQUE NOT NULL,
    password_hash   TEXT    NOT NULL,
    display_name    TEXT    NOT NULL,
    role            TEXT    NOT NULL DEFAULT 'customer'
                    CHECK (role IN ('customer','admin','analyst')),
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS preferences (
    user_id     INTEGER NOT NULL,
    category    TEXT    NOT NULL,
    PRIMARY KEY (user_id, category),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS interactions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    article_id  TEXT    NOT NULL,
    event_type  TEXT    NOT NULL
                CHECK (event_type IN (
                    'view','save','unsave','like','unlike','dislike','undislike','purchase',
                    'rate_1','rate_2','rate_3','rate_4','rate_5'
                )),
    created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_interactions_user
    ON interactions(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_interactions_article
    ON interactions(article_id);

-- Audit log of every authentication attempt (success or failure). Drives
-- the failed-login lockout (auth.MAX_FAILED_ATTEMPTS / LOCKOUT_WINDOW_MINUTES)
-- and the admin-page audit display.
CREATE TABLE IF NOT EXISTS login_attempts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    email       TEXT    NOT NULL,
    success     INTEGER NOT NULL CHECK (success IN (0, 1)),
    ip          TEXT,
    user_agent  TEXT,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_login_attempts_email
    ON login_attempts(email, created_at DESC);

-- Server-side sessions for persistent ("remember me") login. The browser
-- holds only an opaque random token in a cookie; the authoritative mapping
-- token -> user lives here so we can revoke and expire centrally. Token is a
-- 256-bit urlsafe secret (see auth.new_session_token).
CREATE TABLE IF NOT EXISTS sessions (
    token       TEXT    PRIMARY KEY,
    user_id     INTEGER NOT NULL,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    expires_at  TEXT    NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);

-- A/B/n experiment: each customer is round-robin assigned ONE recommendation
-- algorithm so engagement is attributable. Admins/analysts are not bucketed.
CREATE TABLE IF NOT EXISTS experiment_bucket (
    user_id     INTEGER PRIMARY KEY,
    algorithm   TEXT    NOT NULL,
    assigned_at TEXT    NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Shopping cart (one row per user+article; quantity mutable).
CREATE TABLE IF NOT EXISTS cart (
    user_id    INTEGER NOT NULL,
    article_id TEXT    NOT NULL,
    quantity   INTEGER NOT NULL DEFAULT 1,
    added_at   TEXT    NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (user_id, article_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Placed orders (mock checkout) + their line items.
CREATE TABLE IF NOT EXISTS orders (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL,
    total      REAL    NOT NULL,
    n_items    INTEGER NOT NULL,
    status     TEXT    NOT NULL DEFAULT 'paid',
    created_at TEXT    NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS order_items (
    order_id   INTEGER NOT NULL,
    article_id TEXT    NOT NULL,
    quantity   INTEGER NOT NULL,
    unit_price REAL    NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
);

-- Product reviews: one per user per article (rating + optional comment).
CREATE TABLE IF NOT EXISTS reviews (
    user_id    INTEGER NOT NULL,
    article_id TEXT    NOT NULL,
    rating     INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment    TEXT,
    created_at TEXT    NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (user_id, article_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_reviews_article ON reviews(article_id, created_at DESC);

-- In-app notifications (e.g. offline 'order now' confirmations).
CREATE TABLE IF NOT EXISTS notifications (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL,
    message    TEXT    NOT NULL,
    kind       TEXT    NOT NULL DEFAULT 'info',
    read       INTEGER NOT NULL DEFAULT 0,
    created_at TEXT    NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id, created_at DESC);

-- Seller-listed products (Chiroyli marketplace). The base cosmetics catalogue
-- ships as a static CSV; products added by sellers live here and are unioned
-- into the catalogue at load time. `active=0` hides a product without deleting.
CREATE TABLE IF NOT EXISTS seller_products (
    article_id        TEXT    PRIMARY KEY,
    seller_id         INTEGER NOT NULL,
    prod_name         TEXT    NOT NULL,
    brand             TEXT,
    category          TEXT,
    product_type_name TEXT,
    index_group_name  TEXT,
    colour_group_name TEXT,
    quality           TEXT,
    size              TEXT,
    made_in           TEXT,
    price             REAL    NOT NULL,
    sale_price        REAL,
    detail_desc       TEXT,
    image_url         TEXT,
    active            INTEGER NOT NULL DEFAULT 1,
    created_at        TEXT    NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (seller_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_seller_products_seller ON seller_products(seller_id, created_at DESC);
"""

# Round-robin order — also the canonical algorithm keys used across the app.
EXPERIMENT_ALGORITHMS = ("content", "als", "hybrid", "neural")
ALGORITHM_LABELS = {
    "content": "Content-Based",
    "als":     "ALS Collaborative",
    "hybrid":  "Weighted Hybrid",
    "neural":  "Neural CF (NeuMF)",
}


def get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript(SCHEMA)
        # One-shot migration: extend interactions.event_type CHECK to allow
        # unlike/undislike on databases created before step 6.
        sql_row = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='interactions'"
        ).fetchone()
        if sql_row and ("'unlike'" not in (sql_row[0] or "")
                        or "'rate_5'" not in (sql_row[0] or "")):
            conn.executescript("""
                ALTER TABLE interactions RENAME TO interactions_old;
                CREATE TABLE interactions (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id     INTEGER NOT NULL,
                    article_id  TEXT    NOT NULL,
                    event_type  TEXT    NOT NULL
                                CHECK (event_type IN (
                                    'view','save','unsave','like','unlike','dislike','undislike','purchase',
                                    'rate_1','rate_2','rate_3','rate_4','rate_5'
                                )),
                    created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );
                INSERT INTO interactions SELECT * FROM interactions_old;
                DROP TABLE interactions_old;
                CREATE INDEX IF NOT EXISTS idx_interactions_user
                    ON interactions(user_id, created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_interactions_article
                    ON interactions(article_id);
            """)
            conn.commit()

    # Relax users.role CHECK to cover all roles + repair any child FK a prior
    # RENAME-based migration retargeted to a temp users table. Runs on its own
    # autocommit connection (see _migrate_user_role for why).
    _migrate_user_role()

    purge_expired_sessions()
    backfill_buckets()


def _migrate_user_role() -> None:
    """Ensure users.role CHECK allows every ALLOWED_ROLE and repair broken FKs.

    Adding a value to a CHECK constraint in SQLite requires rebuilding the table
    (rename → create → copy → drop). That RENAME cascades into *other* tables'
    foreign-key definitions — retargeting them to the temp `users_old` table —
    UNLESS both `legacy_alter_table=ON` and `foreign_keys=OFF` are set. Those
    pragmas are ignored inside a transaction, so this uses a dedicated
    autocommit connection. It also fixes databases already broken by an earlier
    migration that lacked the `foreign_keys=OFF` guard, by rewriting any table
    whose schema still references `users_old` back to `users`.
    """
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.isolation_level = None  # autocommit — pragmas below take effect at once
    try:
        users_sql = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='users'"
        ).fetchone()
        users_ok = users_sql and "'seller'" in (users_sql["sql"] or "")
        broken = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' "
            "AND name != 'users' AND sql LIKE '%users_old%' LIMIT 1"
        ).fetchone()
        if users_ok and not broken:
            return

        conn.execute("PRAGMA foreign_keys=OFF")
        conn.execute("PRAGMA legacy_alter_table=ON")
        if not users_ok:
            conn.executescript("""
                ALTER TABLE users RENAME TO users_old;
                CREATE TABLE users (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    email           TEXT    UNIQUE NOT NULL,
                    password_hash   TEXT    NOT NULL,
                    display_name    TEXT    NOT NULL,
                    role            TEXT    NOT NULL DEFAULT 'customer'
                                    CHECK (role IN ('customer','admin','analyst','seller')),
                    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
                );
                INSERT INTO users SELECT * FROM users_old;
                DROP TABLE users_old;
            """)
        # Repair child tables whose FK still references a renamed users table.
        for row in conn.execute(
            "SELECT name, sql FROM sqlite_master WHERE type='table' "
            "AND name != 'users' AND sql LIKE '%users_old%'"
        ).fetchall():
            name, fixed = row["name"], row["sql"].replace("users_old", "users")
            conn.executescript(
                f"ALTER TABLE {name} RENAME TO _mig_{name};\n{fixed};\n"
                f"INSERT INTO {name} SELECT * FROM _mig_{name};\nDROP TABLE _mig_{name};"
            )
        conn.execute("PRAGMA legacy_alter_table=OFF")
        conn.execute("PRAGMA foreign_keys=ON")
    finally:
        conn.close()


def create_session(token: str, user_id: int, ttl_days: int = 30) -> None:
    """Persist a session token so the user stays logged in across refreshes."""
    with get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO sessions(token, user_id, expires_at) "
            "VALUES (?, ?, datetime('now', ?))",
            (token, user_id, f"+{int(ttl_days)} days"),
        )
        conn.commit()


def get_session_user(token: str) -> dict | None:
    """Return the user dict for a non-expired session token, else None.

    Lazily deletes the row if it has expired so stale tokens don't linger.
    """
    if not token:
        return None
    with get_conn() as conn:
        row = conn.execute(
            "SELECT u.id, u.email, u.display_name, u.role, s.expires_at "
            "FROM sessions s JOIN users u ON u.id = s.user_id "
            "WHERE s.token = ?",
            (token,),
        ).fetchone()
        if row is None:
            return None
        expired = conn.execute(
            "SELECT datetime('now') > ? AS expired", (row["expires_at"],)
        ).fetchone()["expired"]
        if expired:
            conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
            conn.commit()
            return None
    return {
        "id": row["id"],
        "email": row["email"],
        "display_name": row["display_name"],
        "role": row["role"],
    }


def delete_session(token: str) -> None:
    """Revoke a single session token (used on logout)."""
    if not token:
        return
    with get_conn() as conn:
        conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
        conn.commit()


def purge_expired_sessions() -> None:
    """Housekeeping — drop expired session rows. Cheap; called at init_db()."""
    with get_conn() as conn:
        conn.execute("DELETE FROM sessions WHERE datetime('now') > expires_at")
        conn.commit()


def get_algorithm(user_id: int) -> str | None:
    """The recommendation algorithm this user is bucketed into, or None."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT algorithm FROM experiment_bucket WHERE user_id = ?", (user_id,)
        ).fetchone()
    return row["algorithm"] if row else None


def backfill_buckets() -> None:
    """Round-robin assign any unbucketed *customers* (by signup order) to one of
    EXPERIMENT_ALGORITHMS, continuing the existing rotation. Idempotent — runs in
    init_db(), so new signups receive the next algorithm on their first load."""
    with get_conn() as conn:
        n = conn.execute("SELECT COUNT(*) AS c FROM experiment_bucket").fetchone()["c"]
        rows = conn.execute(
            "SELECT u.id FROM users u "
            "LEFT JOIN experiment_bucket b ON b.user_id = u.id "
            "WHERE b.user_id IS NULL AND u.role = 'customer' "
            "ORDER BY u.created_at, u.id"
        ).fetchall()
        for i, r in enumerate(rows):
            algo = EXPERIMENT_ALGORITHMS[(n + i) % len(EXPERIMENT_ALGORITHMS)]
            conn.execute(
                "INSERT OR IGNORE INTO experiment_bucket(user_id, algorithm) VALUES (?, ?)",
                (r["id"], algo),
            )
        if rows:
            conn.commit()


def algorithm_stats() -> list[dict]:
    """Per-algorithm experiment results: assigned users + engagement event counts.

    Engagement is attributed by the user's bucket (each bucketed customer only
    ever sees their one algorithm). Counts are raw events from the interactions
    log. Always returns a row for every algorithm (zero-filled)."""
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT b.algorithm,
                   COUNT(DISTINCT b.user_id) AS n_users,
                   COALESCE(SUM(i.event_type = 'view'),     0) AS n_views,
                   COALESCE(SUM(i.event_type = 'save'),     0) AS n_saves,
                   COALESCE(SUM(i.event_type = 'like'),     0) AS n_likes,
                   COALESCE(SUM(i.event_type = 'dislike'),  0) AS n_dislikes,
                   COALESCE(SUM(i.event_type = 'purchase'), 0) AS n_purchases
            FROM experiment_bucket b
            LEFT JOIN interactions i ON i.user_id = b.user_id
            GROUP BY b.algorithm
            """
        ).fetchall()
    by_algo = {r["algorithm"]: dict(r) for r in rows}
    out = []
    for algo in EXPERIMENT_ALGORITHMS:
        d = by_algo.get(algo, {"algorithm": algo, "n_users": 0, "n_views": 0,
                               "n_saves": 0, "n_likes": 0, "n_dislikes": 0, "n_purchases": 0})
        d["label"] = ALGORITHM_LABELS.get(algo, algo)
        out.append(d)
    return out


# ---------- shopping cart ----------

def add_to_cart(user_id: int, article_id: str, qty: int = 1) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO cart(user_id, article_id, quantity) VALUES (?, ?, ?) "
            "ON CONFLICT(user_id, article_id) DO UPDATE SET quantity = quantity + excluded.quantity",
            (user_id, str(article_id), max(1, int(qty))),
        )
        conn.commit()


def get_cart(user_id: int) -> list[dict]:
    """Cart lines [{article_id, quantity}] in add order."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT article_id, quantity FROM cart WHERE user_id = ? ORDER BY added_at, article_id",
            (user_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def set_cart_qty(user_id: int, article_id: str, qty: int) -> None:
    """Set a line's quantity; qty <= 0 removes the line."""
    if int(qty) <= 0:
        remove_from_cart(user_id, article_id)
        return
    with get_conn() as conn:
        conn.execute(
            "UPDATE cart SET quantity = ? WHERE user_id = ? AND article_id = ?",
            (int(qty), user_id, str(article_id)),
        )
        conn.commit()


def remove_from_cart(user_id: int, article_id: str) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM cart WHERE user_id = ? AND article_id = ?",
                     (user_id, str(article_id)))
        conn.commit()


def clear_cart(user_id: int) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
        conn.commit()


def cart_count(user_id: int) -> int:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT COALESCE(SUM(quantity), 0) AS n FROM cart WHERE user_id = ?", (user_id,)
        ).fetchone()
    return int(row["n"])


def create_order(user_id: int, items: list[tuple]) -> int:
    """Create a paid order from `items` = [(article_id, quantity, unit_price), ...].

    Records order + line items, logs a `purchase` interaction per article (feeds
    analytics + recommenders), clears the cart, and returns the new order id.
    """
    total = sum(q * p for _, q, p in items)
    n_items = sum(q for _, q, _ in items)
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO orders(user_id, total, n_items) VALUES (?, ?, ?)",
            (user_id, float(total), int(n_items)),
        )
        order_id = cur.lastrowid
        conn.executemany(
            "INSERT INTO order_items(order_id, article_id, quantity, unit_price) VALUES (?, ?, ?, ?)",
            [(order_id, str(a), int(q), float(p)) for a, q, p in items],
        )
        for a, _, _ in items:
            conn.execute(
                "INSERT INTO interactions(user_id, article_id, event_type) VALUES (?, ?, 'purchase')",
                (user_id, str(a)),
            )
        conn.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
        conn.commit()
    return int(order_id)


def get_order(order_id: int) -> dict | None:
    with get_conn() as conn:
        o = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
        if o is None:
            return None
        items = conn.execute(
            "SELECT article_id, quantity, unit_price FROM order_items WHERE order_id = ?",
            (order_id,),
        ).fetchall()
    d = dict(o)
    d["items"] = [dict(r) for r in items]
    return d


# ---------- product reviews ----------

def add_review(user_id: int, article_id: str, rating: int, comment: str = "") -> None:
    """Upsert a user's review (one per user per article)."""
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO reviews(user_id, article_id, rating, comment) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(user_id, article_id) DO UPDATE SET "
            "rating = excluded.rating, comment = excluded.comment, created_at = datetime('now')",
            (user_id, str(article_id), int(rating), (comment or "").strip()),
        )
        conn.commit()


def get_reviews(article_id: str, limit: int = 30) -> list[dict]:
    """Reviews for an article, newest first: [{display_name, rating, comment, created_at}]."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT u.display_name, r.rating, r.comment, r.created_at "
            "FROM reviews r JOIN users u ON u.id = r.user_id "
            "WHERE r.article_id = ? ORDER BY r.created_at DESC, u.display_name LIMIT ?",
            (str(article_id), limit),
        ).fetchall()
    return [dict(r) for r in rows]


def review_summary(article_id: str) -> dict:
    """{avg, count} for an article's reviews (avg=0.0, count=0 if none)."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS n, COALESCE(AVG(rating), 0) AS avg FROM reviews WHERE article_id = ?",
            (str(article_id),),
        ).fetchone()
    return {"count": int(row["n"]), "avg": round(float(row["avg"]), 1)}


# ---------- notifications ----------

def add_notification(user_id: int, message: str, kind: str = "info") -> None:
    with get_conn() as conn:
        conn.execute("INSERT INTO notifications(user_id, message, kind) VALUES (?, ?, ?)",
                     (user_id, message, kind))
        conn.commit()


def get_notifications(user_id: int, limit: int = 20) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, message, kind, read, created_at FROM notifications "
            "WHERE user_id = ? ORDER BY created_at DESC, id DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    return [dict(r) for r in rows]


def unread_notifications(user_id: int) -> int:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS n FROM notifications WHERE user_id = ? AND read = 0", (user_id,)
        ).fetchone()
    return int(row["n"])


def mark_notifications_read(user_id: int) -> None:
    with get_conn() as conn:
        conn.execute("UPDATE notifications SET read = 1 WHERE user_id = ? AND read = 0", (user_id,))
        conn.commit()


def order_now(user_id: int, article_id: str, quantity: int, unit_price: float,
              product_name: str = "") -> int:
    """Place an OFFLINE 'order now' for a single item — reserves it for in-store
    pickup (no online payment), logs a purchase, and posts a notification.
    Does not touch the cart. Returns the order id."""
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO orders(user_id, total, n_items, status) VALUES (?, ?, ?, 'offline')",
            (user_id, float(unit_price) * int(quantity), int(quantity)),
        )
        order_id = cur.lastrowid
        conn.execute(
            "INSERT INTO order_items(order_id, article_id, quantity, unit_price) VALUES (?, ?, ?, ?)",
            (order_id, str(article_id), int(quantity), float(unit_price)),
        )
        conn.execute(
            "INSERT INTO interactions(user_id, article_id, event_type) VALUES (?, ?, 'purchase')",
            (user_id, str(article_id)),
        )
        name = (product_name + " ") if product_name else ""
        conn.execute(
            "INSERT INTO notifications(user_id, message, kind) VALUES (?, ?, 'order')",
            (user_id,
             f"The {name}product you chose has been ordered! You can come to our market "
             f"and collect it, paying offline. Order #{order_id}."),
        )
        conn.commit()
    return int(order_id)


def user_review(user_id: int, article_id: str) -> dict | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT rating, comment FROM reviews WHERE user_id = ? AND article_id = ?",
            (user_id, str(article_id)),
        ).fetchone()
    return dict(row) if row else None


def record_login_attempt(email: str, success: bool,
                          ip: str | None = None,
                          user_agent: str | None = None) -> None:
    """Append a login attempt to the audit log."""
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO login_attempts(email, success, ip, user_agent) "
            "VALUES (?, ?, ?, ?)",
            (email.strip().lower(), 1 if success else 0, ip, user_agent),
        )
        conn.commit()


def failed_attempts_in_window(email: str, minutes: int = 15) -> int:
    """Count failed login attempts for this email in the last `minutes` minutes."""
    with get_conn() as conn:
        row = conn.execute(
            f"""
            SELECT COUNT(*) AS n FROM login_attempts
            WHERE email = ? AND success = 0
              AND created_at > datetime('now', '-{int(minutes)} minutes')
            """,
            (email.strip().lower(),),
        ).fetchone()
    return int(row["n"] or 0)


def recent_login_events(limit: int = 50) -> list[dict]:
    """Audit log — most recent N login attempts (successful + failed), newest first."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, email, success, ip, user_agent, created_at "
            "FROM login_attempts ORDER BY id DESC LIMIT ?",
            (int(limit),),
        ).fetchall()
    return [dict(r) for r in rows]


def log_interaction(user_id: int, article_id: str, event_type: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO interactions(user_id, article_id, event_type) VALUES (?, ?, ?)",
            (user_id, article_id, event_type),
        )
        conn.commit()


def user_saved_articles(user_id: int) -> list[str]:
    """Article IDs currently in the user's wishlist (saves minus later unsaves)."""
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT article_id, event_type
            FROM interactions
            WHERE user_id = ? AND event_type IN ('save','unsave','purchase')
            ORDER BY created_at, id
            """,
            (user_id,),
        ).fetchall()
    saved: dict[str, bool] = {}
    for r in rows:
        if r["event_type"] in ("save", "purchase"):
            saved[r["article_id"]] = True
        elif r["event_type"] == "unsave":
            saved.pop(r["article_id"], None)
    return list(saved)


def _toggle_set(user_id: int, on_event: str, off_event: str) -> set[str]:
    """Set of articles whose most recent on/off event is `on_event`."""
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT article_id, event_type
            FROM interactions
            WHERE user_id = ? AND event_type IN (?, ?)
            ORDER BY created_at, id
            """,
            (user_id, on_event, off_event),
        ).fetchall()
    state: dict[str, bool] = {}
    for r in rows:
        if r["event_type"] == on_event:
            state[r["article_id"]] = True
        elif r["event_type"] == off_event:
            state.pop(r["article_id"], None)
    return set(state)


def user_likes(user_id: int) -> set[str]:
    """Currently 'liked' articles (most recent feedback is a like)."""
    return _toggle_set(user_id, "like", "unlike")


def user_dislikes(user_id: int) -> set[str]:
    """Currently 'disliked' articles — filtered out of recommendation outputs."""
    return _toggle_set(user_id, "dislike", "undislike")


def log_rating(user_id: int, article_id: str, rating: int) -> None:
    """Log a 1-5 star rating. Appends a rate_N event; current rating is the
    most-recent rate_* event for the (user, article) pair."""
    if not 1 <= int(rating) <= 5:
        raise ValueError(f"rating must be 1-5, got {rating}")
    log_interaction(user_id, article_id, f"rate_{int(rating)}")


def user_rating(user_id: int, article_id: str) -> int | None:
    """Current rating (latest rate_N event), or None if not yet rated."""
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT event_type FROM interactions
            WHERE user_id = ? AND article_id = ? AND event_type LIKE 'rate_%'
            ORDER BY id DESC LIMIT 1
            """,
            (user_id, article_id),
        ).fetchone()
    if row is None:
        return None
    try:
        return int(row["event_type"].split("_", 1)[1])
    except (IndexError, ValueError):
        return None


def user_state(user_id: int) -> dict:
    """Single-query fetch of everything a page rerun needs from interactions.

    Returns:
        {
          'saved':    [article_id, ...]   # oldest first
          'liked':    {article_id, ...}
          'disliked': {article_id, ...}
          'signature': int                # max(id) — cheap fingerprint for caching
        }

    Replaces three separate DB connections (saved/likes/dislikes) with one,
    and gives caller a signature it can use to skip recomputation when nothing
    has changed since the last rerun.
    """
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT id, article_id, event_type
            FROM interactions
            WHERE user_id = ?
              AND event_type IN
                  ('save','unsave','purchase','like','unlike','dislike','undislike')
            ORDER BY created_at, id
            """,
            (user_id,),
        ).fetchall()

    saved: dict[str, bool] = {}
    liked: dict[str, bool] = {}
    disliked: dict[str, bool] = {}
    sig = 0
    for r in rows:
        sig = max(sig, r["id"])
        aid = r["article_id"]
        ev = r["event_type"]
        if ev in ("save", "purchase"):
            saved[aid] = True
        elif ev == "unsave":
            saved.pop(aid, None)
        elif ev == "like":
            liked[aid] = True
        elif ev == "unlike":
            liked.pop(aid, None)
        elif ev == "dislike":
            disliked[aid] = True
        elif ev == "undislike":
            disliked.pop(aid, None)

    return {
        "saved": list(saved),
        "liked": set(liked),
        "disliked": set(disliked),
        "signature": sig,
    }


# ---------- admin queries ----------

def admin_user_table() -> list[dict]:
    """All users with their interaction counts, newest-first."""
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT u.id, u.email, u.display_name, u.role, u.created_at,
                   COALESCE(i.n_interactions, 0) AS n_interactions
            FROM users u
            LEFT JOIN (
                SELECT user_id, COUNT(*) AS n_interactions
                FROM interactions
                GROUP BY user_id
            ) i ON i.user_id = u.id
            ORDER BY u.created_at DESC, u.id DESC
            """,
        ).fetchall()
    return [dict(r) for r in rows]


def interaction_stats() -> dict:
    """Aggregate counts: total interactions and breakdown by event_type."""
    with get_conn() as conn:
        total = conn.execute("SELECT COUNT(*) AS n FROM interactions").fetchone()["n"]
        by_type_rows = conn.execute(
            "SELECT event_type, COUNT(*) AS n FROM interactions GROUP BY event_type"
        ).fetchall()
        n_users = conn.execute("SELECT COUNT(*) AS n FROM users").fetchone()["n"]
        n_admins = conn.execute(
            "SELECT COUNT(*) AS n FROM users WHERE role = 'admin'"
        ).fetchone()["n"]
    return {
        "n_users": n_users,
        "n_admins": n_admins,
        "n_interactions": total,
        "by_event_type": {r["event_type"]: r["n"] for r in by_type_rows},
    }


# ---------- analytics queries (used by the analyst dashboard) ----------

def daily_signups(days: int = 30) -> list[dict]:
    """Daily signup counts for the last `days` days."""
    with get_conn() as conn:
        rows = conn.execute(
            f"""
            SELECT DATE(created_at) AS day, COUNT(*) AS n
            FROM users
            WHERE created_at > datetime('now', '-{int(days)} days')
            GROUP BY DATE(created_at)
            ORDER BY day
            """,
        ).fetchall()
    return [dict(r) for r in rows]


def daily_events(days: int = 30) -> list[dict]:
    """Daily event counts broken down by event_type."""
    with get_conn() as conn:
        rows = conn.execute(
            f"""
            SELECT DATE(created_at) AS day, event_type, COUNT(*) AS n
            FROM interactions
            WHERE created_at > datetime('now', '-{int(days)} days')
            GROUP BY DATE(created_at), event_type
            ORDER BY day
            """,
        ).fetchall()
    return [dict(r) for r in rows]


def active_users(days: int = 7) -> int:
    """Distinct users with at least one interaction in the last `days` days."""
    with get_conn() as conn:
        row = conn.execute(
            f"""
            SELECT COUNT(DISTINCT user_id) AS n
            FROM interactions
            WHERE created_at > datetime('now', '-{int(days)} days')
            """,
        ).fetchone()
    return int(row["n"] or 0)


def top_articles(event_type: str, limit: int = 10) -> list[dict]:
    """Top articles by count of a given event type (e.g. 'save', 'view')."""
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT article_id, COUNT(*) AS n
            FROM interactions
            WHERE event_type = ?
            GROUP BY article_id
            ORDER BY n DESC
            LIMIT ?
            """,
            (event_type, int(limit)),
        ).fetchall()
    return [dict(r) for r in rows]


def cold_start_distribution() -> list[dict]:
    """Number of users at each save-count bucket (the cold-start histogram).

    Useful for the analyst to see how warm the platform population is — most
    users at 0 saves = predominantly cold-start regime; long tail = warm users.
    Zero-save users (registered but never saved) are included via the LEFT JOIN.
    """
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT save_count, COUNT(*) AS n_users
            FROM (
                SELECT u.id AS user_id,
                       COUNT(CASE WHEN i.event_type = 'save' THEN 1 END)
                       - COUNT(CASE WHEN i.event_type = 'unsave' THEN 1 END) AS save_count
                FROM users u
                LEFT JOIN interactions i ON i.user_id = u.id
                GROUP BY u.id
            )
            GROUP BY save_count
            ORDER BY save_count
            """,
        ).fetchall()
    return [dict(r) for r in rows]


def engagement_rates() -> dict:
    """Aggregate engagement ratios: save-rate (saves/views) and like ratio."""
    with get_conn() as conn:
        views = conn.execute(
            "SELECT COUNT(*) AS n FROM interactions WHERE event_type='view'"
        ).fetchone()["n"]
        saves = conn.execute(
            "SELECT COUNT(*) AS n FROM interactions WHERE event_type='save'"
        ).fetchone()["n"]
        likes = conn.execute(
            "SELECT COUNT(*) AS n FROM interactions WHERE event_type='like'"
        ).fetchone()["n"]
        dislikes = conn.execute(
            "SELECT COUNT(*) AS n FROM interactions WHERE event_type='dislike'"
        ).fetchone()["n"]
    save_rate = (saves / views) if views else 0.0
    like_ratio = (likes / (likes + dislikes)) if (likes + dislikes) else 0.0
    return {
        "n_views": views,
        "n_saves": saves,
        "n_likes": likes,
        "n_dislikes": dislikes,
        "save_rate": save_rate,
        "like_ratio": like_ratio,
    }


def article_save_counts(article_ids: list[str]) -> dict[str, int]:
    """For each article_id in the list, return the number of platform users who
    *currently* have it saved (latest save/unsave/purchase event = save or purchase).

    Used by the CF-style "N other customers also saved this" explanation.
    """
    if not article_ids:
        return {}
    placeholders = ",".join("?" * len(article_ids))
    with get_conn() as conn:
        rows = conn.execute(
            f"""
            WITH latest AS (
                SELECT user_id, article_id, event_type,
                       ROW_NUMBER() OVER (
                           PARTITION BY user_id, article_id
                           ORDER BY created_at DESC, id DESC
                       ) AS rn
                FROM interactions
                WHERE article_id IN ({placeholders})
                  AND event_type IN ('save', 'unsave', 'purchase')
            )
            SELECT article_id, COUNT(*) AS n
            FROM latest
            WHERE rn = 1 AND event_type IN ('save', 'purchase')
            GROUP BY article_id
            """,
            article_ids,
        ).fetchall()
    return {r["article_id"]: int(r["n"]) for r in rows}


def positive_platform_interactions() -> list[tuple[int, str]]:
    """Currently-active (user_id, article_id) positive signals across all users.

    Saves/likes/purchases count as positive; subsequent unsave/unlike remove.
    Returned in stable iteration order — used by app.retrain to build the
    user-item matrix on top of H&M transactions.
    """
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT user_id, article_id, event_type
            FROM interactions
            WHERE event_type IN ('save','like','purchase','unsave','unlike')
            ORDER BY created_at, id
            """,
        ).fetchall()
    state: dict[tuple[int, str], bool] = {}
    for r in rows:
        key = (r["user_id"], r["article_id"])
        if r["event_type"] in ("save", "like", "purchase"):
            state[key] = True
        elif r["event_type"] in ("unsave", "unlike"):
            state.pop(key, None)
    return list(state.keys())


# ---------- seller products (marketplace) ----------

# Columns a seller controls (the rest of the catalogue schema is derived in
# shared.load_cosmetics). `article_id`, `seller_id`, timestamps are managed here.
SELLER_PRODUCT_FIELDS = (
    "prod_name", "brand", "category", "product_type_name", "index_group_name",
    "colour_group_name", "quality", "size", "made_in", "price", "sale_price",
    "detail_desc", "image_url",
)


def next_seller_article_id() -> str:
    """Mint the next seller article id (S0001, S0002, …) — distinct from the
    CSV catalogue's C-prefixed ids so the two never collide."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT article_id FROM seller_products WHERE article_id LIKE 'S%' "
            "ORDER BY CAST(SUBSTR(article_id, 2) AS INTEGER) DESC LIMIT 1"
        ).fetchone()
    n = (int(row["article_id"][1:]) + 1) if row else 1
    return f"S{n:04d}"


def add_seller_product(seller_id: int, data: dict) -> str:
    """Insert a new seller product; returns the minted article_id."""
    aid = next_seller_article_id()
    cols = ", ".join(SELLER_PRODUCT_FIELDS)
    ph = ", ".join("?" for _ in SELLER_PRODUCT_FIELDS)
    vals = [data.get(f) for f in SELLER_PRODUCT_FIELDS]
    with get_conn() as conn:
        conn.execute(
            f"INSERT INTO seller_products(article_id, seller_id, {cols}) VALUES (?, ?, {ph})",
            [aid, seller_id, *vals],
        )
        conn.commit()
    return aid


def update_seller_product(article_id: str, seller_id: int, data: dict) -> bool:
    """Update a product the seller owns. Returns False if it isn't theirs."""
    sets = ", ".join(f"{f} = ?" for f in SELLER_PRODUCT_FIELDS)
    vals = [data.get(f) for f in SELLER_PRODUCT_FIELDS]
    with get_conn() as conn:
        cur = conn.execute(
            f"UPDATE seller_products SET {sets} WHERE article_id = ? AND seller_id = ?",
            [*vals, str(article_id), seller_id],
        )
        conn.commit()
    return cur.rowcount > 0


def set_seller_product_active(article_id: str, seller_id: int, active: bool) -> bool:
    """Show/hide a seller's product without deleting it."""
    with get_conn() as conn:
        cur = conn.execute(
            "UPDATE seller_products SET active = ? WHERE article_id = ? AND seller_id = ?",
            (1 if active else 0, str(article_id), seller_id),
        )
        conn.commit()
    return cur.rowcount > 0


def delete_seller_product(article_id: str, seller_id: int) -> bool:
    with get_conn() as conn:
        cur = conn.execute(
            "DELETE FROM seller_products WHERE article_id = ? AND seller_id = ?",
            (str(article_id), seller_id),
        )
        conn.commit()
    return cur.rowcount > 0


def list_seller_products(seller_id: int) -> list[dict]:
    """All of a seller's products (active + hidden), newest first."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM seller_products WHERE seller_id = ? ORDER BY created_at DESC, article_id DESC",
            (seller_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def active_seller_products() -> list[dict]:
    """Every active seller product — unioned into the catalogue at load time."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM seller_products WHERE active = 1 ORDER BY created_at, article_id"
        ).fetchall()
    return [dict(r) for r in rows]


def seller_orders(seller_id: int) -> list[dict]:
    """Order line items for this seller's products, newest first.
    Each row: {order_id, status, created_at, buyer, article_id, prod_name, quantity, unit_price}."""
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT o.id AS order_id, o.status, o.created_at,
                   u.display_name AS buyer,
                   oi.article_id, sp.prod_name, oi.quantity, oi.unit_price
            FROM order_items oi
            JOIN seller_products sp ON sp.article_id = oi.article_id
            JOIN orders o ON o.id = oi.order_id
            JOIN users  u ON u.id = o.user_id
            WHERE sp.seller_id = ?
            ORDER BY o.created_at DESC, o.id DESC
            """,
            (seller_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def seller_stats(seller_id: int) -> dict:
    """{products, active, units_sold, revenue} for a seller's dashboard."""
    with get_conn() as conn:
        p = conn.execute(
            "SELECT COUNT(*) AS n, COALESCE(SUM(active),0) AS act "
            "FROM seller_products WHERE seller_id = ?", (seller_id,),
        ).fetchone()
        s = conn.execute(
            """
            SELECT COALESCE(SUM(oi.quantity),0) AS units,
                   COALESCE(SUM(oi.quantity * oi.unit_price),0) AS revenue
            FROM order_items oi
            JOIN seller_products sp ON sp.article_id = oi.article_id
            WHERE sp.seller_id = ?
            """,
            (seller_id,),
        ).fetchone()
    return {"products": int(p["n"]), "active": int(p["act"]),
            "units_sold": int(s["units"]), "revenue": round(float(s["revenue"]), 2)}


if __name__ == "__main__":
    init_db()
    print(f"Initialised {DB_PATH}")
