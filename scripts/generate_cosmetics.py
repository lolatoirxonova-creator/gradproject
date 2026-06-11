"""Generate the Chiroyli cosmetics catalogue (data + Pexels images).

Produces app/assets/cosmetics_products.csv (~52 products across Skincare, Makeup,
Fragrance, Hair & body) with full attributes — brand, quality, size, made-in,
audience (women/men/kids/unisex), shade, price, sale_price, description — and
fetches a matching product photo per item to app/assets/cosmetics/<id>.jpg via
the Pexels key in .streamlit/secrets.toml.

Column names mirror what the app already reads (prod_name, product_type_name,
colour_group_name, index_group_name, detail_desc, …) plus the new cosmetics
attributes, so wiring is minimal.

Run:  python scripts/generate_cosmetics.py
"""
from __future__ import annotations
import io, random, re, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import pandas as pd
import requests
from PIL import Image, ImageDraw

random.seed(11)
OUT_DIR = ROOT / "app/assets/cosmetics"; OUT_DIR.mkdir(parents=True, exist_ok=True)
CSV = ROOT / "app/assets/cosmetics_products.csv"

BRANDS = ["Lumière", "Aurélia", "Velvet & Co", "Botané", "Maison Lux", "Pure Form",
          "Noir Atelier", "Gloss Lab", "Séraphine", "Hâloé", "Émerald", "Ivoire"]
COUNTRIES = ["France", "South Korea", "Italy", "Japan", "USA", "United Kingdom", "Uzbekistan", "Germany"]
QUALITY = ["Standard", "Premium", "Luxury"]

# category -> [(subtype, pexels_query, [sizes], default_audience, [shades])]
CATALOGUE = {
    "Skincare": [
        ("Serum", "face serum bottle cosmetic", ["30 ml", "50 ml"], "Women", ["Clear"]),
        ("Moisturiser", "moisturizer cream jar skincare", ["50 ml", "100 ml"], "Unisex", ["White"]),
        ("Cleanser", "facial cleanser bottle", ["150 ml", "200 ml"], "Unisex", ["Clear"]),
        ("Face Mask", "face mask skincare product", ["75 ml", "100 ml"], "Women", ["Clay"]),
        ("Eye Cream", "eye cream skincare jar", ["15 ml"], "Women", ["White"]),
        ("Sunscreen SPF50", "sunscreen bottle skincare", ["50 ml"], "Unisex", ["White"]),
        ("Toner", "facial toner bottle", ["200 ml"], "Women", ["Clear"]),
        ("Night Oil", "facial oil dropper bottle", ["30 ml"], "Women", ["Amber"]),
    ],
    "Makeup": [
        ("Lipstick", "lipstick makeup", ["3.5 g"], "Women", ["Rosewood", "Nude", "Crimson", "Mauve"]),
        ("Foundation", "liquid foundation makeup bottle", ["30 ml"], "Women", ["Ivory", "Beige", "Sand"]),
        ("Mascara", "mascara makeup", ["10 ml"], "Women", ["Black"]),
        ("Eyeshadow Palette", "eyeshadow palette makeup", ["12 g"], "Women", ["Sunset", "Nude", "Smoke"]),
        ("Blush", "blush makeup compact", ["6 g"], "Women", ["Peach", "Rose"]),
        ("Concealer", "concealer makeup", ["7 ml"], "Women", ["Ivory", "Beige"]),
        ("Lip Gloss", "lip gloss makeup", ["5 ml"], "Women", ["Clear", "Pink"]),
        ("Brow Gel", "eyebrow gel makeup", ["8 ml"], "Unisex", ["Brown", "Taupe"]),
    ],
    "Fragrance": [
        ("Eau de Parfum", "perfume bottle luxury", ["50 ml", "100 ml"], "Women", ["—"]),
        ("Eau de Toilette", "perfume bottle", ["50 ml", "100 ml"], "Men", ["—"]),
        ("Body Mist", "body mist spray bottle", ["150 ml"], "Women", ["—"]),
        ("Cologne", "cologne perfume bottle men", ["100 ml"], "Men", ["—"]),
    ],
    "Hair & body": [
        ("Shampoo", "shampoo bottle", ["250 ml", "400 ml"], "Unisex", ["—"]),
        ("Conditioner", "hair conditioner bottle", ["250 ml"], "Unisex", ["—"]),
        ("Body Wash", "body wash bottle", ["300 ml"], "Unisex", ["—"]),
        ("Body Lotion", "body lotion bottle", ["200 ml", "400 ml"], "Women", ["—"]),
        ("Hair Oil", "hair oil bottle", ["100 ml"], "Women", ["Amber"]),
        ("Hand Cream", "hand cream tube cosmetic", ["75 ml"], "Unisex", ["White"]),
        ("Kids Shampoo", "kids shampoo bottle", ["250 ml"], "Kids", ["—"]),
        ("Kids Body Lotion", "baby lotion bottle", ["200 ml"], "Kids", ["White"]),
    ],
}
DESCRIPTORS = ["Hydra-Glow", "Velvet", "Pure", "Radiance", "Silk", "Botanical", "Luxe",
               "Daily", "Intense", "Nourish", "Aura", "Bloom", "Satin", "Crystal"]

def price_for(category, quality):
    base = {"Skincare": 22, "Makeup": 18, "Fragrance": 55, "Hair & body": 12}[category]
    mult = {"Standard": 1.0, "Premium": 1.5, "Luxury": 2.4}[quality]
    return round(base * mult * random.uniform(0.85, 1.25), 2)

# variants per subtype to reach ~50 products: makeup → one per shade; others → 2 brands
VARIANTS = {"Skincare": 2, "Makeup": "shades", "Fragrance": 2, "Hair & body": 1}

rows = []
i = 0
for category, items in CATALOGUE.items():
    mode = VARIANTS[category]
    for (subtype, query, sizes, audience, shades) in items:
        n = len(shades) if mode == "shades" else mode
        brands_pool = random.sample(BRANDS, k=min(n, len(BRANDS)))
        for v in range(n):
            i += 1
            brand = brands_pool[v % len(brands_pool)]
            quality = random.choices(QUALITY, weights=[3, 3, 2])[0]
            size = random.choice(sizes)
            shade = shades[v % len(shades)] if mode == "shades" else random.choice(shades)
            made_in = random.choice(COUNTRIES)
            price = price_for(category, quality)
            on_sale = random.random() < 0.32
            sale_price = round(price * random.uniform(0.65, 0.85), 2) if on_sale else ""
            desc_word = random.choice(DESCRIPTORS)
            prod_name = f"{brand} {desc_word} {subtype}"
            desc = (f"{quality} {category.lower()} — {brand}'s {desc_word.lower()} {subtype.lower()}"
                    f"{(' in ' + shade) if shade not in ('—', 'Clear', 'White') else ''}. "
                    f"{size}. Made in {made_in}.")
            rows.append({
                "article_id": f"C{i:03d}",
                "prod_name": prod_name,
                "brand": brand,
                "category": category,
                "product_type_name": subtype,
                "product_group_name": category,
                "section_name": category,
                "department_name": audience,
                "garment_group_name": subtype,
                "index_group_name": audience,          # men/women/kids/unisex tag
                "colour_group_name": shade,
                "perceived_colour_master_name": shade,
                "quality": quality,
                "size": size,
                "made_in": made_in,
                "price": price,
                "sale_price": sale_price,
                "detail_desc": desc,
                "image_query": query,
            })

df = pd.DataFrame(rows)
df.to_csv(CSV, index=False)
print(f"wrote {CSV}  ({len(df)} products)")
print(df["category"].value_counts().to_string())
print("on sale:", (df["sale_price"] != "").sum(), "| audiences:", df["index_group_name"].value_counts().to_dict())

# ---- fetch Pexels images ----
KEY = ""
sec = ROOT / ".streamlit/secrets.toml"
if sec.exists():
    m = re.search(r'PEXELS_API_KEY\s*=\s*"([^"]+)"', sec.read_text())
    KEY = m.group(1) if m else ""
if not KEY:
    print("No Pexels key — skipping image fetch."); sys.exit(0)

H = {"Authorization": KEY}
def save_portrait(url, dst):
    rr = requests.get(url, timeout=25); im = Image.open(io.BytesIO(rr.content)).convert("RGB")
    tw, th = 600, 750; w, h = im.size; s = max(tw / w, th / h)
    im = im.resize((int(w * s), int(h * s)))
    x = (im.width - tw) // 2; y = (im.height - th) // 2
    im.crop((x, y, x + tw, y + th)).save(dst, "JPEG", quality=88)

ok = 0; fails = []
for query, grp in df.groupby("image_query"):
    r = requests.get("https://api.pexels.com/v1/search", headers=H,
                     params={"query": query, "per_page": 25, "orientation": "portrait"}, timeout=20)
    photos = r.json().get("photos", []) if r.status_code == 200 else []
    if not photos:
        fails += list(grp.article_id); continue
    for j, row in enumerate(grp.itertuples()):
        try:
            save_portrait(photos[j % len(photos)]["src"]["portrait"], OUT_DIR / f"{row.article_id}.jpg"); ok += 1
        except Exception:
            fails.append(row.article_id)
    time.sleep(0.25)
print(f"images: {ok}/{len(df)} | fails: {fails}")

# contact sheet
imgs = [(Image.open(OUT_DIR / f"{r.article_id}.jpg").convert("RGB"), r.product_type_name, r.brand)
        for r in df.itertuples() if (OUT_DIR / f"{r.article_id}.jpg").exists()]
cols = 6; tw, th, lab, pad = 150, 188, 18, 4
rws = (len(imgs) + cols - 1) // cols
sheet = Image.new("RGB", (cols * (tw + pad) + pad, rws * (th + lab + pad) + pad), (250, 246, 236))
d = ImageDraw.Draw(sheet)
for k, (im, sub, br) in enumerate(imgs):
    c = k % cols; rr = k // cols; x = pad + c * (tw + pad); y = pad + rr * (th + lab + pad)
    sheet.paste(im.resize((tw, th)), (x, y)); d.text((x + 3, y + th + 3), f"{sub[:16]}", fill=(20, 20, 20))
sheet.save("/tmp/cosmetics_montage.png"); print("montage:", sheet.size)
