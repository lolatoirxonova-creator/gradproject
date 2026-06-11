"""Fetch 2 extra Pexels photos per cosmetics product for the product-page gallery (#8).

Saves app/assets/cosmetics/{aid}_2.jpg and _3.jpg (leaves the hand-verified
primary {aid}.jpg untouched). Idempotent: skips a product whose extras exist.

Usage:  python scripts/fetch_product_images.py
Needs a Pexels API key in .streamlit/secrets.toml (PEXELS_API_KEY) or env.
"""
from __future__ import annotations

import sys
import time
import urllib.parse
from pathlib import Path

import requests

REPO = Path(__file__).resolve().parents[1]
ASSETS = REPO / "app" / "assets" / "cosmetics"
CSV = REPO / "app" / "assets" / "cosmetics_products.csv"


def _api_key() -> str:
    import os
    if os.environ.get("PEXELS_API_KEY", "").strip():
        return os.environ["PEXELS_API_KEY"].strip()
    sec = REPO / ".streamlit" / "secrets.toml"
    if sec.exists():
        for line in sec.read_text().splitlines():
            if line.strip().startswith("PEXELS_API_KEY"):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def main():
    import pandas as pd

    key = _api_key()
    if not key:
        print("No PEXELS_API_KEY found — aborting.")
        sys.exit(1)

    df = pd.read_csv(CSV, dtype={"article_id": str})
    headers = {"Authorization": key}
    fetched = skipped = failed = 0

    for _, r in df.iterrows():
        aid = str(r["article_id"])
        if (ASSETS / f"{aid}_2.jpg").exists() and (ASSETS / f"{aid}_3.jpg").exists():
            skipped += 1
            continue
        query = str(r.get("image_query") or f"{r.get('category','')} {r.get('product_type_name','')}").strip()
        q = urllib.parse.quote(query)
        url = f"https://api.pexels.com/v1/search?query={q}&per_page=8&orientation=square"
        try:
            resp = requests.get(url, timeout=10, headers=headers)
            photos = resp.json().get("photos", []) if resp.status_code == 200 else []
        except Exception as e:
            print(f"  {aid}: request failed ({e})")
            failed += 1
            continue
        # take results 2 & 3 (index 1,2) so they differ from the primary photo
        picks = photos[1:3] if len(photos) >= 3 else photos[:2]
        if len(picks) < 2:
            print(f"  {aid}: only {len(picks)} extra photo(s) for '{query}'")
        for n, photo in enumerate(picks, start=2):
            src = photo["src"].get("large") or photo["src"].get("medium")
            try:
                img = requests.get(src, timeout=15)
                if img.status_code == 200 and len(img.content) > 1024:
                    (ASSETS / f"{aid}_{n}.jpg").write_bytes(img.content)
                    fetched += 1
            except Exception as e:
                print(f"  {aid}_{n}: download failed ({e})")
        time.sleep(0.4)  # be polite to the API

    print(f"Done. fetched={fetched} images, skipped={skipped} products, failed={failed}.")


if __name__ == "__main__":
    main()
