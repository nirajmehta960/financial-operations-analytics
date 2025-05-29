"""Tests for feature_engineering module."""
from pathlib import Path
import sys
import pandas as pd
import pytest

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.feature_engineering import (
    add_discount_bands,
    discount_band_metrics,
    add_transaction_features,
    add_shipping_days,
    build_order_level,
    build_model_ready,
    CHURN_RECENCY_DAYS,
)


# Discount band tests


def test_add_discount_bands():
    df = pd.DataFrame({"Discount": [0, 0.05, 0.15, 0.25, 0.50]})
    out = add_discount_bands(df)
    assert "discount_band" in out.columns
    assert list(out["discount_band"].astype(str)) == [
        "No Discount",
        "Light (1-10%)",
        "Moderate (11-20%)",
        "Heavy (21-30%)",
        "Extreme (31%+)",
    ]


def test_add_discount_bands_missing_column():
    df = pd.DataFrame({"Other": [1, 2]})
    out = add_discount_bands(df)
    assert "discount_band" not in out.columns


def test_discount_band_metrics_columns():
    df = pd.DataFrame({
        "Discount": [0, 0, 0.15, 0.15],
        "Sales": [100.0, 50.0, 80.0, 20.0],
        "Profit": [10.0, -5.0, 8.0, -2.0],
    })
    out = discount_band_metrics(df)
    assert "discount_band" in out.columns
    assert "tx_count" in out.columns
    assert "total_profit" in out.columns
    assert "avg_profit" in out.columns
    assert "loss_pct" in out.columns
    assert "total_sales" in out.columns
    assert "margin_pct" in out.columns


def test_discount_band_metrics_loss_pct():
    df = pd.DataFrame({
        "Discount": [0, 0, 0.5, 0.5],
        "Profit": [10.0, 20.0, -5.0, -5.0],
    })
    out = discount_band_metrics(df)
    # No discount should have 0% loss; extreme should have 100% loss.
    no_disc = out[out["discount_band"].astype(str) == "No Discount"].iloc[0]
    assert no_disc["loss_pct"] == 0.0
    extreme = out[out["discount_band"].astype(str) == "Extreme (31%+)"].iloc[0]
    assert extreme["loss_pct"] == 100.0


# Transaction-level feature tests


def test_add_transaction_features():
    df = pd.DataFrame({"Sales": [100.0, 50.0], "Profit": [20.0, -10.0]})
    out = add_transaction_features(df)
    assert "profit_margin" in out.columns
    assert "is_profitable" in out.columns
    assert out["profit_margin"].iloc[0] == 20.0
    assert out["profit_margin"].iloc[1] == -20.0
    assert list(out["is_profitable"]) == [1, 0]


def test_add_shipping_days():
    df = pd.DataFrame({
        "Order Date": pd.to_datetime(["2020-01-01", "2020-01-01"]),
        "Ship Date": pd.to_datetime(["2020-01-03", "2020-01-05"]),
    })
    out = add_shipping_days(df)
    assert "shipping_days" in out.columns
    assert list(out["shipping_days"]) == [2, 4]


# Order-level aggregation tests


@pytest.fixture
def sample_transactions():
    """Minimal transaction-level DataFrame for order aggregation."""
    return pd.DataFrame({
        "Order ID": ["O1", "O1", "O2"],
        "Order Date": pd.to_datetime(["2020-01-01", "2020-01-01", "2020-01-02"]),
        "Ship Date": pd.to_datetime(["2020-01-03", "2020-01-03", "2020-01-05"]),
        "Sales": [100.0, 50.0, 75.0],
        "Profit": [15.0, 5.0, 10.0],
        "Discount": [0, 0.1, 0],
    })


def test_build_order_level_shape(sample_transactions):
    out = build_order_level(sample_transactions)
    assert len(out) == 2  # Two unique orders.
    assert "order_total_sales" in out.columns
    assert "order_total_profit" in out.columns
    assert "order_items_count" in out.columns
    assert "order_avg_discount" in out.columns
    assert "order_date" in out.columns


def test_build_order_level_aggregation(sample_transactions):
    out = build_order_level(sample_transactions)
    o1 = out[out["Order ID"] == "O1"].iloc[0]
    assert o1["order_total_sales"] == 150.0
    assert o1["order_total_profit"] == 20.0
    assert o1["order_items_count"] == 2
    assert o1["order_avg_discount"] == 0.05


# Model-ready dataset tests (no target leakage)


@pytest.fixture
def sample_customers():
    """Minimal customer-level DataFrame for build_model_ready."""
    return pd.DataFrame({
        "Customer ID": ["C1", "C2"],
        "first_order_date": pd.to_datetime(["2020-01-01", "2020-02-01"]),
        "last_order_date": pd.to_datetime(["2020-06-01", "2020-08-01"]),
        "recency_days": [400, 100],  # should be dropped (leakage)
        "order_count": [5, 2],
        "total_spent": [1000.0, 200.0],
        "total_profit": [100.0, 20.0],
        "avg_order_value": [200.0, 100.0],
        "avg_profit_margin": [10.0, 10.0],
        "avg_discount": [0.1, 0.05],
        "avg_shipping_days": [3.0, 4.0],
        "tenure_days": [150, 180],
        "Segment": ["Consumer", "Corporate"],
        "unique_categories": [2, 1],
        "unique_subcategories": [4, 2],
        "is_churned": [1, 0],
    })


def test_build_model_ready_drops_recency_days(sample_customers):
    out = build_model_ready(sample_customers)
    assert "recency_days" not in out.columns
    assert "Customer ID" not in out.columns
    assert "first_order_date" not in out.columns
    assert "last_order_date" not in out.columns


def test_build_model_ready_target_last(sample_customers):
    out = build_model_ready(sample_customers)
    assert out.columns[-1] == "is_churned"
    assert "is_churned" in out.columns


def test_build_model_ready_no_target_in_features(sample_customers):
    out = build_model_ready(sample_customers)
    X_cols = [c for c in out.columns if c != "is_churned"]
    assert "is_churned" not in X_cols


def test_build_model_ready_segment_encoded(sample_customers):
    out = build_model_ready(sample_customers)
    # Segment should be one-hot encoded, so raw "Segment" must be absent.
    assert "Segment" not in out.columns
    # At least one Segment_* dummy column should exist.
    segment_dummies = [c for c in out.columns if c.startswith("Segment_")]
    assert len(segment_dummies) >= 1


def test_churn_constant():
    assert CHURN_RECENCY_DAYS == 365
