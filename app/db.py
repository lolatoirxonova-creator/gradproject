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
"""


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

        # Migration: extend users.role CHECK to allow 'analyst' (added Day 4).
        # NOTE: SQLite updates FK references in OTHER tables when you rename a
        # table — i.e. `ALTER TABLE users RENAME TO users_old` retargets
        # preferences.user_id and interactions.user_id to point at users_old.
        # We work around this by setting `PRAGMA legacy_alter_table=ON` (which
        # disables the cascading FK rewrite), then by ALSO repairing any FKs
        # that got broken by past migrations that didn't set the pragma.
        sql_row = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='users'"
        ).fetchone()
        if sql_row and "'analyst'" not in (sql_row[0] or ""):
            conn.executescript("""
                PRAGMA legacy_alter_table=ON;
                ALTER TABLE users RENAME TO users_old;
                CREATE TABLE users (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    email           TEXT    UNIQUE NOT NULL,
                    password_hash   TEXT    NOT NULL,
                    display_name    TEXT    NOT NULL,
                    role            TEXT    NOT NULL DEFAULT 'customer'
                                    CHECK (role IN ('customer','admin','analyst')),
                    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
                );
                INSERT INTO users SELECT * FROM users_old;
                DROP TABLE users_old;
                PRAGMA legacy_alter_table=OFF;
            """)
            conn.commit()

        # Repair: if a previous migration left preferences.user_id or
        # interactions.user_id pointing at users_old (or any name other than
        # users), rebuild the table with the correct FK.
        for table, schema_sql in [
            ("preferences", """
                CREATE TABLE preferences (
                    user_id     INTEGER NOT NULL,
                    category    TEXT    NOT NULL,
                    PRIMARY KEY (user_id, category),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """),
        ]:
            fks = conn.execute(f"PRAGMA foreign_key_list({table})").fetchall()
            broken = any(r["table"] != "users" for r in fks)
            if broken:
                conn.executescript(f"""
                    ALTER TABLE {table} RENAME TO {table}_broken_fk;
                    {schema_sql};
                    INSERT INTO {table} SELECT * FROM {table}_broken_fk;
                    DROP TABLE {table}_broken_fk;
                """)
                conn.commit()


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


if __name__ == "__main__":
    init_db()
    print(f"Initialised {DB_PATH}")
