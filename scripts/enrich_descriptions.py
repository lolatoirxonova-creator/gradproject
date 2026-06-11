"""Rewrite cosmetics_products.csv `detail_desc` with richer, descriptive copy (#6).

Composes 3–4 sentences per product from its attributes (brand, type, category,
shade, size, made-in, quality) using category- and type-aware phrasing. Idempotent.

Run:  python scripts/enrich_descriptions.py
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "app" / "assets" / "cosmetics_products.csv"

QUALITY_ADJ = {"Luxury": "a luxurious", "Premium": "a premium", "Standard": "an everyday"}

CATEGORY_BENEFIT = {
    "Skincare": ("Formulated to nourish and hydrate, it absorbs quickly without residue and, "
                 "with daily use, leaves skin softer, more balanced and visibly healthier."),
    "Makeup": ("It delivers rich, blendable colour and a smooth, comfortable finish that wears "
               "beautifully from morning to night without caking or fading."),
    "Fragrance": ("It opens bright and fresh, then settles into a warm, refined trail that lingers "
                  "softly through the day and into the evening."),
    "Hair & body": ("It cleanses and conditions gently, leaving hair and skin feeling soft, fresh "
                    "and lightly, elegantly scented."),
}
TYPE_TOUCH = {
    "Serum": "A few drops are all you need — lightweight yet concentrated.",
    "Moisturiser": "Lightweight but deeply moisturising, it makes an ideal everyday base.",
    "Cleanser": "It lifts away makeup and impurities without stripping or tightness.",
    "Eye Cream": "Gently formulated for the delicate eye area to look brighter and smoother.",
    "Face Mask": "A few minutes is all it takes for a visibly refreshed, glowing complexion.",
    "Toner": "It refines and rebalances after cleansing, prepping skin for what comes next.",
    "Lipstick": "Pigment-rich and comfortable, it glides on evenly in a single sweep.",
    "Lip Gloss": "A glossy, non-sticky shine that flatters on its own or over lipstick.",
    "Foundation": "Buildable coverage that evens tone while still looking like skin.",
    "Concealer": "Creamy and blendable, it covers without settling into fine lines.",
    "Blush": "A soft wash of colour for a healthy, lit-from-within flush.",
    "Mascara": "It lengthens and defines lashes cleanly, without clumping.",
    "Eau de Parfum": "A high concentration for a richer, longer-lasting wear.",
    "Eau de Toilette": "A lighter concentration, perfect for fresh, everyday wear.",
    "Cologne": "Crisp and understated, made for effortless daily wear.",
    "Body Lotion": "It sinks in fast for all-day softness with no greasy feel.",
    "Body Wash": "A gentle, richly lathering cleanse that leaves skin fresh.",
    "Shampoo": "It cleanses while caring for the scalp, leaving hair light and clean.",
    "Conditioner": "It smooths and detangles for soft, manageable, shinier hair.",
    "Body Mist": "A light, refreshing veil of scent you can layer all day.",
    "Brow Gel": "It shapes, sets and lightly tints brows for a groomed finish.",
}


def main():
    import pandas as pd
    df = pd.read_csv(CSV, dtype={"article_id": str})

    def describe(r) -> str:
        name = str(r.get("prod_name") or "This product")
        brand = str(r.get("brand") or "").strip()
        cat = str(r.get("category") or "").strip()
        ptype = str(r.get("product_type_name") or "product").strip()
        shade = str(r.get("colour_group_name") or "").strip()
        size = str(r.get("size") or "").strip()
        made = str(r.get("made_in") or "").strip()
        quality = str(r.get("quality") or "Standard").strip()

        adj = QUALITY_ADJ.get(quality, "a")
        lead = f"{name} is {adj} {ptype.lower()}"
        if brand:
            lead += f" from {brand}"
        if cat:
            lead += f", part of our {cat.lower()} edit"
        lead += "."

        s = [lead, CATEGORY_BENEFIT.get(cat, "")]
        if ptype in TYPE_TOUCH:
            s.append(TYPE_TOUCH[ptype])

        spec_bits = []
        if shade and shade.lower() not in ("clear", "nan"):
            spec_bits.append(f"shown in {shade.lower()}")
        if size and size.lower() != "nan":
            spec_bits.append(size)
        tail = ""
        if spec_bits:
            tail = "Available " + " · ".join(spec_bits)
        if made and made.lower() != "nan":
            tail = (tail + f", proudly made in {made}.") if tail else f"Proudly made in {made}."
        elif tail:
            tail += "."
        if tail:
            s.append(tail)
        return " ".join(x for x in s if x).strip()

    df["detail_desc"] = df.apply(describe, axis=1)
    df.to_csv(CSV, index=False)
    print(f"enriched {len(df)} descriptions")
    print("e.g.:", df.iloc[0]["detail_desc"])


if __name__ == "__main__":
    main()
