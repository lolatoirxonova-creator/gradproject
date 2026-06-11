"""Seed four engineered test-persona accounts — one per core recommendation
algorithm — for evaluating each algorithm's pros/cons on the Compare page.

Each persona's saved-item profile is shaped to stress a different algorithm:
  - content : a tight single-style cluster (knit/jersey tops) → content-based shines
  - als     : co-bought / transaction-rich items (activewear) → collaborative shines
  - hybrid  : a content pair + a popular item → the weighted blend shines
  - neural  : items that all have NeuMF embeddings → neural CF can actually score

All saved IDs come from the curated-50 set (app/assets/curated_products.csv) so
the gated catalogue can display them. Idempotent: re-running won't duplicate.

Run:  python scripts/seed_test_personas.py
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd
from app import auth, db

PW = "Test2026!"
PERSONAS = [
    {"email": "test_content@example.com", "name": "CB Tester",     "algo": "Content-Based (TF-IDF)",
     "saves": ["0176209023", "0145872001", "0255396023"]},            # hoodie + sweater + cardigan
    {"email": "test_als@example.com",     "name": "ALS Tester",    "algo": "ALS Collaborative Filtering",
     "saves": ["0111586001", "0212042043", "0265071013"]},            # leggings + sneakers + tee (activewear)
    {"email": "test_hybrid@example.com",  "name": "Hybrid Tester", "algo": "Weighted Hybrid",
     "saves": ["0212629004", "0212629031", "0111586001"]},            # 2 dresses (content) + leggings (CF)
    {"email": "test_neural@example.com",  "name": "Neural CF Tester", "algo": "Neural CF (NeuMF)",
     "saves": ["0212629004", "0312878001", "0536663005", "0386678001"]},  # all have NCF embeddings
]


def main() -> None:
    db.init_db()
    cur = pd.read_csv(Path(__file__).resolve().parents[1] / "app/assets/curated_products.csv",
                      dtype={"article_id": str})
    ptype = dict(zip(cur["article_id"], cur["product_type_name"]))

    for p in PERSONAS:
        try:
            user = auth.register(p["email"], PW, p["name"])
            created = True
        except auth.AuthError:
            with db.get_conn() as c:
                row = c.execute("SELECT id FROM users WHERE email = ?", (p["email"],)).fetchone()
            user = {"id": row["id"]}
            created = False
        uid = user["id"]

        prefs = sorted({ptype[a] for a in p["saves"] if a in ptype})
        if prefs:
            auth.set_preferences(uid, prefs[:5])

        already = set(db.user_state(uid)["saved"])
        for aid in p["saves"]:
            if aid not in already:
                db.log_interaction(uid, aid, "save")

        print(f"{'created' if created else 'updated'}  {p['email']:28} ({p['algo']})  "
              f"saves={p['saves']}  prefs={prefs}")

    print("\nAll personas seeded. Password for all:", PW)


if __name__ == "__main__":
    main()
