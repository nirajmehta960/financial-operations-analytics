"""Tests for data_cleaning module."""
from pathlib import Path
import sys
import pandas as pd
import pytest

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.python_pipeline.data_cleaning import (
    drop_unused_columns,
    parse_dates,
    drop_duplicates,
    validate_ranges,
)


@pytest.fixture
def sample_df():
    """Minimal DataFrame matching Superstore structure."""
    return pd.DataFrame({
        "Row ID": [1, 2, 3],
        "Order ID": ["A", "A", "B"],
        "Order Date": ["1/1/2016", "1/1/2016", "2/1/2016"],
        "Ship Date": ["1/5/2016", "1/5/2016", "2/5/2016"],
        "Country": ["United States"] * 3,
        "Sales": [100.0, 50.0, 75.0],
        "Quantity": [1, 1, 2],
        "Discount": [0, 0.1, 0],
        "Profit": [20.0, -5.0, 15.0],
    })


def test_drop_unused_columns(sample_df):
    out = drop_unused_columns(sample_df)
    assert "Row ID" not in out.columns
    assert "Country" not in out.columns
    assert "Order ID" in out.columns


def test_parse_dates(sample_df):
    out = parse_dates(sample_df)
    assert pd.api.types.is_datetime64_any_dtype(out["Order Date"])
    assert pd.api.types.is_datetime64_any_dtype(out["Ship Date"])


def test_drop_duplicates(sample_df):
    # Add one exact duplicate and verify it is removed.
    dup = sample_df.iloc[0:1]
    df2 = pd.concat([sample_df, dup], ignore_index=True)
    out = drop_duplicates(df2)
    assert len(out) == len(sample_df)


def test_validate_ranges(sample_df):
    out = validate_ranges(sample_df)
    assert (out["Sales"] >= 0).all()
    assert (out["Quantity"] > 0).all()
    assert (out["Discount"] >= 0).all() and (out["Discount"] <= 1).all()
