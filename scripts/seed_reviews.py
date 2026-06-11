"""Seed demo product reviews so each cosmetics product shows real ratings/comments.

Adds 1–4 reviews per product from the existing demo/persona accounts, with varied
ratings (weighted positive) and canned beauty-appropriate comments. Idempotent —
one review per user per product (upsert).

Run:  python scripts/seed_reviews.py
"""
from __future__ import annotations
import random, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import pandas as pd
from app import db

random.seed(7)

COMMENTS = [
    "Absolutely love this — works exactly as described.",
    "Great quality for the price, will repurchase.",
    "A little pricey, but worth every penny.",
    "Gentle and effective. My new favourite.",
    "The texture and scent are lovely.",
    "Good product, takes a couple of weeks to see results.",
    "Holy-grail status. Highly recommend.",
    "Decent, nothing groundbreaking but does the job.",
    "Perfect for everyday use — skin feels amazing.",
    "Packaging is beautiful and it actually works.",
    "Didn't quite work for my skin, but quality is clear.",
    "Subtle, elegant, and long-lasting.",
    "", "",  # some reviews are rating-only
]


def main():
    db.init_db()
    with db.get_conn() as c:
        users = c.execute("SELECT id, display_name FROM users WHERE role != 'admin'").fetchall()
    user_ids = [u["id"] for u in users]
    if not user_ids:
        print("no users to review with"); return

    csv = ROOT / "app/assets/cosmetics_products.csv"
    if not csv.exists():
        print("no cosmetics catalogue"); return
    aids = pd.read_csv(csv, dtype={"article_id": str})["article_id"].tolist()

    n = 0
    for aid in aids:
        reviewers = random.sample(user_ids, k=min(len(user_ids), random.randint(1, 4)))
        for uid in reviewers:
            rating = random.choices([3, 4, 5], weights=[1, 3, 4])[0]
            db.add_review(uid, aid, rating, random.choice(COMMENTS))
            n += 1
    print(f"seeded {n} reviews across {len(aids)} products "
          f"(avg {n / max(1, len(aids)):.1f}/product)")


if __name__ == "__main__":
    main()
