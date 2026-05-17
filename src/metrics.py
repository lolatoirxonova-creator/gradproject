"""Top-N recommendation evaluation metrics.

All functions take ranked lists of predicted item IDs and a set of
ground-truth item IDs, evaluated at cutoff k.
"""

from __future__ import annotations

import numpy as np


def precision_at_k(predicted: list, actual: set, k: int) -> float:
    if k == 0:
        return 0.0
    top_k = predicted[:k]
    hits = sum(1 for p in top_k if p in actual)
    return hits / k


def recall_at_k(predicted: list, actual: set, k: int) -> float:
    if not actual:
        return 0.0
    top_k = predicted[:k]
    hits = sum(1 for p in top_k if p in actual)
    return hits / len(actual)


def hit_rate_at_k(predicted: list, actual: set, k: int) -> float:
    return 1.0 if any(p in actual for p in predicted[:k]) else 0.0


def average_precision_at_k(predicted: list, actual: set, k: int) -> float:
    if not actual:
        return 0.0
    score, hits = 0.0, 0
    for i, p in enumerate(predicted[:k]):
        if p in actual:
            hits += 1
            score += hits / (i + 1)
    return score / min(len(actual), k)


def ndcg_at_k(predicted: list, actual: set, k: int) -> float:
    if not actual:
        return 0.0
    dcg = 0.0
    for i, p in enumerate(predicted[:k]):
        if p in actual:
            dcg += 1.0 / np.log2(i + 2)
    ideal_hits = min(len(actual), k)
    idcg = sum(1.0 / np.log2(i + 2) for i in range(ideal_hits))
    return dcg / idcg if idcg > 0 else 0.0


def evaluate(recommendations: dict, ground_truth: dict, k: int = 10) -> dict:
    """Mean metrics across all evaluated users.

    `recommendations` and `ground_truth` are dicts: user_id -> list / set of item_ids.
    Users present in `ground_truth` but missing from `recommendations` are skipped
    (treat as cold-start for the algorithm being evaluated).
    """
    users = [u for u in ground_truth if u in recommendations]
    if not users:
        return {"users_evaluated": 0}
    p = np.mean([precision_at_k(recommendations[u], set(ground_truth[u]), k) for u in users])
    r = np.mean([recall_at_k(recommendations[u], set(ground_truth[u]), k) for u in users])
    h = np.mean([hit_rate_at_k(recommendations[u], set(ground_truth[u]), k) for u in users])
    m = np.mean([average_precision_at_k(recommendations[u], set(ground_truth[u]), k) for u in users])
    n = np.mean([ndcg_at_k(recommendations[u], set(ground_truth[u]), k) for u in users])
    return {
        f"Precision@{k}": float(p),
        f"Recall@{k}": float(r),
        f"HitRate@{k}": float(h),
        f"MAP@{k}": float(m),
        f"NDCG@{k}": float(n),
        "users_evaluated": len(users),
    }
