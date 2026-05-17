"""H&M dataset loaders and splitters.

The full transactions_train.csv (~31M rows) is too large for interactive
notebook work on a 16 GB laptop, so all loaders accept a `nrows` /
`sample_frac` argument. Use `nrows=None` only when you have enough RAM
or are running on Colab/Kaggle.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def load_articles(nrows: int | None = None) -> pd.DataFrame:
    """Load the article (item) catalogue."""
    df = pd.read_csv(DATA_DIR / "articles.csv", nrows=nrows, dtype={"article_id": str})
    return df


def load_customers(nrows: int | None = None) -> pd.DataFrame:
    """Load the customer profile table."""
    df = pd.read_csv(DATA_DIR / "customers.csv", nrows=nrows)
    return df


def load_transactions(
    nrows: int | None = None,
    sample_frac: float | None = None,
    last_months: int | None = None,
    parse_dates: bool = True,
    seed: int = 42,
    chunksize: int = 500_000,
) -> pd.DataFrame:
    """Load the implicit-feedback transactions.

    Three loading modes (use exactly one):
      - `nrows=N`: reads the first N rows (chronological head — earliest period).
        Avoid for modelling — chronologically biased.
      - `sample_frac=F`: reads the file in chunks and randomly keeps a fraction
        F of rows across the whole 31.8M-row span. Use for **EDA** (unbiased
        distribution statistics). Avoid for modelling — produces sparse user
        profiles (~2 train interactions per user at frac=0.03).
      - `last_months=M`: keeps only the last M calendar months of data. Use for
        **modelling** — matches H&M competition protocol and gives realistic
        user-profile density.

    All modes are memory-bounded by `chunksize`.
    """
    path = DATA_DIR / "transactions_train.csv"
    if sample_frac is not None and 0 < sample_frac < 1:
        rng = np.random.default_rng(seed)
        sampled_chunks = []
        for chunk in pd.read_csv(path, chunksize=chunksize, dtype={"article_id": str}):
            mask = rng.random(len(chunk)) < sample_frac
            if mask.any():
                sampled_chunks.append(chunk.loc[mask])
        df = pd.concat(sampled_chunks, ignore_index=True)
    elif last_months is not None and last_months > 0:
        # Two-pass: cheap scan to find max date, then keep rows in window
        max_date = pd.to_datetime(
            pd.read_csv(path, usecols=["t_dat"], dtype=str)["t_dat"].max()
        )
        cutoff = max_date - pd.DateOffset(months=last_months)
        sampled_chunks = []
        for chunk in pd.read_csv(path, chunksize=chunksize, dtype={"article_id": str}):
            chunk_dates = pd.to_datetime(chunk["t_dat"])
            mask = chunk_dates > cutoff
            if mask.any():
                sampled_chunks.append(chunk.loc[mask])
        df = pd.concat(sampled_chunks, ignore_index=True) if sampled_chunks else pd.DataFrame()
    else:
        df = pd.read_csv(path, nrows=nrows, dtype={"article_id": str})
    if parse_dates and len(df):
        df["t_dat"] = pd.to_datetime(df["t_dat"])
    return df


def time_based_split(
    transactions: pd.DataFrame,
    cutoff_days: int = 7,
    date_col: str = "t_dat",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split transactions into train / test by holding out the last N days.

    Time-based splits are more realistic than random splits for purchase data
    because they avoid leakage from the future into the past.
    """
    max_date = transactions[date_col].max()
    cutoff = max_date - pd.Timedelta(days=cutoff_days)
    train = transactions[transactions[date_col] <= cutoff].copy()
    test = transactions[transactions[date_col] > cutoff].copy()
    return train, test


def cold_user_ids(train: pd.DataFrame, test: pd.DataFrame, user_col: str = "customer_id") -> set[str]:
    """Users present in test but not in train (user-side cold-start)."""
    return set(test[user_col].unique()) - set(train[user_col].unique())


def cold_item_ids(train: pd.DataFrame, test: pd.DataFrame, item_col: str = "article_id") -> set[str]:
    """Items present in test but not in train (item-side cold-start)."""
    return set(test[item_col].unique()) - set(train[item_col].unique())


def build_user_item_matrix(
    transactions: pd.DataFrame,
    user_col: str = "customer_id",
    item_col: str = "article_id",
    weight: str | None = None,
):
    """Build a sparse CSR user-item interaction matrix.

    `weight` can be `None` (binary) or a column name to sum (e.g. quantity).
    Returns (matrix, user_index, item_index).
    """
    from scipy.sparse import csr_matrix

    users = pd.Index(transactions[user_col].unique(), name=user_col)
    items = pd.Index(transactions[item_col].unique(), name=item_col)
    user_pos = users.get_indexer(transactions[user_col])
    item_pos = items.get_indexer(transactions[item_col])
    values = transactions[weight].values if weight else np.ones(len(transactions), dtype=np.float32)
    matrix = csr_matrix(
        (values, (user_pos, item_pos)),
        shape=(len(users), len(items)),
        dtype=np.float32,
    )
    return matrix, users, items
