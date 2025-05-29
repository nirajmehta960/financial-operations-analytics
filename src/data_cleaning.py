"""
Phase 2 data cleaning for U.S. Superstore.

Pipeline goals:
- Parse date columns to datetime
- Drop unused columns
- Remove exact duplicate rows
- Enforce basic numeric validity checks
"""

from pathlib import Path
import pandas as pd

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_RAW_PATH = _PROJECT_ROOT / "data" / "raw" / "superstore.csv"
DEFAULT_PREPROCESSED_PATH = _PROJECT_ROOT / "data" / "preprocessed" / "superstore_preprocessed.csv"


def load_raw(data_path: str = None, encoding: str = None) -> pd.DataFrame:
    """Load raw CSV into a DataFrame.

    Defaults:
    - data_path: data/raw/superstore.csv
    - encoding: latin-1 (handles special byte characters such as 0xa0)
    """
    path = Path(data_path) if data_path else DEFAULT_RAW_PATH
    enc = encoding or "latin-1"
    return pd.read_csv(path, encoding=enc)


def drop_unused_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Drop columns not needed for downstream analysis.

    Drops (if present):
    - Row ID
    - Country
    """
    drop_cols = ["Row ID", "Country"]
    return df.drop(columns=[c for c in drop_cols if c in df.columns])


def parse_dates(df: pd.DataFrame) -> pd.DataFrame:
    """Parse Order Date and Ship Date to datetime values.

    Invalid date values are coerced to NaT.
    """
    for col in ["Order Date", "Ship Date"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], format="mixed", errors="coerce")
    return df


def drop_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove exact duplicate rows only.

    Why not dedupe by primary/composite keys here:
    - This transactional dataset does not expose a guaranteed row-level primary key.
    - Order ID repeats across line items, and Product ID behaves like a coded grouping field,
      so key-based dedupe can remove valid records.
    - Full-row dedupe is safer at this stage because it removes only true accidental copies
      where every column value is identical.
    """
    n_before = len(df)
    # No subset: compare all columns and drop only exact row copies.
    df = df.drop_duplicates()
    n_after = len(df)
    if n_before > n_after:
        print(f"Dropped {n_before - n_after} exact duplicate rows")
    return df


def validate_ranges(df: pd.DataFrame) -> pd.DataFrame:
    """Apply basic range validation filters.

    Rules:
    - Sales >= 0
    - Quantity > 0
    - Discount in [0, 1]

    Note: Negative Profit is allowed (real business losses).
    """
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
    Run the full Phase 2 cleaning pipeline and save cleaned data.

    Uses default paths when arguments are None.

    Output file:
    - data/preprocessed/superstore_preprocessed.csv

    Returns:
    - Cleaned DataFrame (same columns as input minus dropped columns, with parsed dates)
    """
    data_path = Path(data_path) if data_path else DEFAULT_RAW_PATH
    save_path = Path(save_path) if save_path else DEFAULT_PREPROCESSED_PATH

    df = load_raw(data_path)
    print(f"Started with: {len(df):,} rows")

    df = drop_unused_columns(df)
    df = parse_dates(df)
    df = drop_duplicates(df)
    df = validate_ranges(df)

    print(f"Final preprocessed rows: {len(df):,}")

    save_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(save_path, index=False)
    return df


if __name__ == "__main__":
    run_cleaning_pipeline()
    print(f"Preprocessed data saved to {DEFAULT_PREPROCESSED_PATH}")
