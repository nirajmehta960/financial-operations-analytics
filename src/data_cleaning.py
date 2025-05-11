"""
Cleaning pipeline for U.S. Superstore dataset.
Phase 2: parse dates, drop Row ID/Country, remove exact duplicates, validate ranges.
"""

import os
import pandas as pd
import numpy as np

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_RAW_PATH = os.path.join(_PROJECT_ROOT, "data", "raw", "superstore.csv")
DEFAULT_PREPROCESSED_PATH = os.path.join(_PROJECT_ROOT, "data", "preprocessed", "superstore_preprocessed.csv")


def load_raw(data_path: str = None, encoding: str = None) -> pd.DataFrame:
    """Load raw Superstore CSV. Uses latin-1 to handle non-breaking spaces (0xa0) in Product Name."""
    path = data_path or DEFAULT_RAW_PATH
    enc = encoding or "latin-1"
    return pd.read_csv(path, encoding=enc)


def drop_unused_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Drop Row ID and Country (constant). Keep Customer Name for optional lookup."""
    drop_cols = ["Row ID", "Country"]
    return df.drop(columns=[c for c in drop_cols if c in df.columns])


def parse_dates(df: pd.DataFrame) -> pd.DataFrame:
    """Parse Order Date and Ship Date to datetime."""
    for col in ["Order Date", "Ship Date"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], format="mixed", errors="coerce")
    return df


def drop_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Remove exact duplicate rows. Per BRD: ~17 duplicates expected."""
    n_before = len(df)
    df = df.drop_duplicates()
    n_after = len(df)
    if n_before > n_after:
        print(f"Dropped {n_before - n_after} exact duplicate rows")
    return df


def validate_ranges(df: pd.DataFrame) -> pd.DataFrame:
    """Basic validation: ensure Sales >= 0, Quantity > 0, Discount in [0, 1]. No row drop for negative Profit (real losses)."""
    if "Sales" in df.columns:
        df = df[df["Sales"] >= 0]
    if "Quantity" in df.columns:
        df = df[df["Quantity"] > 0]
    if "Discount" in df.columns:
        df = df[(df["Discount"] >= 0) & (df["Discount"] <= 1)]
    return df


def run_cleaning_pipeline(
    data_path: str = None,
    save_path: str = None,
) -> pd.DataFrame:
    """
    Run full Phase 2 cleaning pipeline.
    Uses default paths when arguments are None.
    """
    data_path = data_path or DEFAULT_RAW_PATH
    save_path = save_path or DEFAULT_PREPROCESSED_PATH

    df = load_raw(data_path)
    print(f"Started with: {len(df):,} rows")

    df = drop_unused_columns(df)
    df = parse_dates(df)
    df = drop_duplicates(df)
    df = validate_ranges(df)

    print(f"Final preprocessed rows: {len(df):,}")

    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    df.to_csv(save_path, index=False)
    return df


if __name__ == "__main__":
    run_cleaning_pipeline()
    print(f"Preprocessed data saved to {DEFAULT_PREPROCESSED_PATH}")
