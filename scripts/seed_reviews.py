"""Seed realistic product reviews so each cosmetics product shows ratings/comments.

Creates a pool of reviewer persona accounts, then adds 4–8 reviews per product
with category-aware comments, positively-weighted ratings, and varied dates
(spread over the last few months). Idempotent — one review per user per product.

Run:  python scripts/seed_reviews.py
"""
from __future__ import annotations
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import pandas as pd
from app import auth, db

random.seed(7)

# Reviewer personas (realistic names for the target market).
REVIEWERS = [
    "Dilnoza R.", "Aziza K.", "Madina T.", "Sevara N.", "Kamola B.", "Nigora S.",
    "Malika A.", "Zarina U.", "Gulnora M.", "Feruza H.", "Shahnoza Y.", "Oydin K.",
    "Laylo R.", "Nodira T.", "Dildora S.", "Munisa A.", "Sabina V.", "Rayhona Q.",
]

GENERIC = [
    "Absolutely love this — works exactly as described.",
    "Great quality for the price, will definitely repurchase.",
    "A little pricey, but worth every penny.",
    "Holy-grail status now. Highly recommend.",
    "Beautiful packaging and it actually delivers.",
    "Subtle, elegant and long-lasting.",
    "Arrived quickly and exactly as pictured.",
    "Decent — nothing groundbreaking, but does the job well.",
    "", "",  # some are rating-only
]
BY_CATEGORY = {
    "Skincare": [
        "My skin feels so much softer after two weeks.",
        "Hydrating without feeling greasy — perfect for my dry skin.",
        "Cleared up my breakouts faster than I expected.",
        "Gentle enough for sensitive skin, no irritation at all.",
        "A little goes a long way; the bottle lasts ages.",
        "Brightened my complexion noticeably. Glowy without the shine.",
    ],
    "Makeup": [
        "The shade range is gorgeous and the pigment is rich.",
        "Stayed put all day through a long shift — no touch-ups.",
        "Blends like a dream, looks natural not cakey.",
        "Pigmented and buildable. A tiny bit goes far.",
        "Lovely satin finish, didn't settle into fine lines.",
    ],
    "Fragrance": [
        "Compliments every time I wear it — lasts all day.",
        "Warm and elegant, not overpowering. My signature now.",
        "The dry-down is beautiful, lingers softly into the evening.",
        "Bought it as a gift and they adored it.",
        "Long-lasting and the bottle is stunning on the vanity.",
    ],
    "Hair & body": [
        "Left my hair so soft and smooth, less frizz too.",
        "Smells incredible and lathers beautifully.",
        "Light, non-greasy and absorbs fast. Lovely scent.",
        "Tamed my frizz without weighing my hair down.",
    ],
}


def _ensure_reviewers() -> list[int]:
    ids = []
    for i, name in enumerate(REVIEWERS):
        email = f"reviewer{i + 1}@barakaly.example"
        try:
            u = auth.register(email, "Review2026!", name, role="customer")
            ids.append(u["id"])
        except auth.AuthError:
            existing = auth.authenticate(email, "Review2026!")
            ids.append(existing["id"])
    return ids


def main():
    db.init_db()
    reviewer_ids = _ensure_reviewers()

    csv = ROOT / "app/assets/cosmetics_products.csv"
    if not csv.exists():
        print("no cosmetics catalogue")
        return
    df = pd.read_csv(csv, dtype={"article_id": str})

    n = 0
    with db.get_conn() as c:
        for _, row in df.iterrows():
            aid = str(row["article_id"])
            category = str(row.get("category") or "")
            bank = BY_CATEGORY.get(category, []) + GENERIC
            k = random.randint(4, 8)
            for uid in random.sample(reviewer_ids, k=min(k, len(reviewer_ids))):
                rating = random.choices([2, 3, 4, 5], weights=[1, 2, 5, 9])[0]
                comment = random.choice(bank)
                days_ago = random.randint(1, 130)
                c.execute(
                    "INSERT INTO reviews(user_id, article_id, rating, comment, created_at) "
                    "VALUES (?, ?, ?, ?, datetime('now', ?)) "
                    "ON CONFLICT(user_id, article_id) DO UPDATE SET "
                    "rating = excluded.rating, comment = excluded.comment, created_at = excluded.created_at",
                    (uid, aid, rating, comment, f"-{days_ago} days"),
                )
                n += 1
        c.commit()
    print(f"seeded {n} reviews across {len(df)} products "
          f"(avg {n / max(1, len(df)):.1f}/product) from {len(reviewer_ids)} reviewers")


if __name__ == "__main__":
    main()
