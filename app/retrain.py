"""ALS retraining triggered from the admin page.

Combines a recent slice of H&M transactions with currently-active platform
interactions (saves + likes + purchases) and refits ALS. The bundle saved to
`models/cf_als_model.pkl` keeps the same shape as the notebook 03 output, so
the live app picks it up after `shared.load_cf.clear()`.

H&M and platform users share the same matrix but use disjoint key spaces:
H&M customer IDs are the original hashes; platform users are prefixed
`"app:<id>"`. Platform interactions are weighted higher than H&M transactions
(3.0 vs 1.0) because they are explicit user feedback on this platform.
"""

from __future__ import annotations

import pickle
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix

from app import db
from src import data as dataio

REPO_ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = REPO_ROOT / "models"
PLATFORM_WEIGHT = 3.0


def _existing_factors(default: int = 64) -> int:
    """Read the current bundle's factor count so the retrained model keeps the
    same dimensionality (so anything that cached factor shapes still works)."""
    path = MODEL_DIR / "cf_als_model.pkl"
    if not path.exists():
        return default
    try:
        with open(path, "rb") as f:
            bundle = pickle.load(f)
        return int(bundle["model"].factors)
    except Exception:
        return default


def retrain_als(
    hm_last_months: int = 1,
    hm_sample_size: int | None = 300_000,
    iterations: int = 15,
    regularization: float = 0.01,
    progress_cb=None,
) -> dict:
    """Refit ALS and overwrite `models/cf_als_model.pkl`.

    Returns a stats dict for the admin UI.
    """
    from implicit.als import AlternatingLeastSquares

    def step(msg):
        if progress_cb:
            progress_cb(msg)

    started = time.time()

    step("Loading catalogue…")
    articles = dataio.load_articles()
    item_index = pd.Index(articles["article_id"].values, name="article_id")
    item_to_row = {a: i for i, a in enumerate(item_index)}

    step("Loading recent H&M transactions…")
    hm = dataio.load_transactions(last_months=hm_last_months)
    if hm_sample_size and len(hm) > hm_sample_size:
        hm = hm.sample(n=hm_sample_size, random_state=42).reset_index(drop=True)

    step("Loading platform interactions…")
    platform_pairs = db.positive_platform_interactions()  # [(user_id, article_id)]

    step("Building user-item matrix…")
    # Build combined user index: H&M customer IDs + prefixed platform users
    hm_users = hm["customer_id"].unique() if len(hm) else np.array([], dtype=object)
    platform_user_ids = sorted({uid for uid, _ in platform_pairs})
    platform_keys = [f"app:{uid}" for uid in platform_user_ids]
    user_index = pd.Index(list(hm_users) + platform_keys, name="customer_id")
    user_to_row = {u: i for i, u in enumerate(user_index)}

    rows_list: list[int] = []
    cols_list: list[int] = []
    vals_list: list[float] = []

    # H&M side — vectorised
    if len(hm):
        hm = hm.copy()
        hm["_u"] = hm["customer_id"].map(user_to_row)
        hm["_i"] = hm["article_id"].map(item_to_row)
        hm = hm.dropna(subset=["_u", "_i"])
        rows_list.extend(hm["_u"].astype(int).tolist())
        cols_list.extend(hm["_i"].astype(int).tolist())
        vals_list.extend([1.0] * len(hm))

    # Platform side — small loop is fine
    for uid, aid in platform_pairs:
        u = user_to_row.get(f"app:{uid}")
        c = item_to_row.get(aid)
        if u is not None and c is not None:
            rows_list.append(int(u))
            cols_list.append(int(c))
            vals_list.append(PLATFORM_WEIGHT)

    if not rows_list:
        raise RuntimeError(
            "Nothing to train on — no H&M transactions loaded and no platform interactions."
        )

    matrix = csr_matrix(
        (vals_list, (rows_list, cols_list)),
        shape=(len(user_index), len(item_index)),
        dtype=np.float32,
    )

    step("Fitting ALS (this can take ~20–60s)…")
    model = AlternatingLeastSquares(
        factors=_existing_factors(),
        iterations=iterations,
        regularization=regularization,
        use_gpu=False,
        calculate_training_loss=False,
    )
    model.fit(matrix, show_progress=False)

    step("Saving model bundle…")
    bundle = {
        "model": model,
        "user_index": user_index,
        "item_index": item_index,
    }
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    with open(MODEL_DIR / "cf_als_model.pkl", "wb") as f:
        pickle.dump(bundle, f)

    elapsed = time.time() - started
    return {
        "n_users": len(user_index),
        "n_hm_users": int(len(hm_users)),
        "n_platform_users": len(platform_user_ids),
        "n_items": len(item_index),
        "n_interactions": len(rows_list),
        "factors": int(model.factors),
        "iterations": int(iterations),
        "elapsed_seconds": round(elapsed, 1),
    }
