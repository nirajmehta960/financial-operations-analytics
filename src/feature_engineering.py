"""
Feature engineering for U.S. Superstore: order-level and customer-level features, churn target.
Phase 3: build order aggregates, customer-level table, model-ready dataset for churn prediction.
"""

import os
import pandas as pd
import numpy as np

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_PREPROCESSED_PATH = os.path.join(_PROJECT_ROOT, "data", "preprocessed", "superstore_preprocessed.csv")
DEFAULT_ORDERS_PATH = os.path.join(_PROJECT_ROOT, "data", "featured", "superstore_orders.csv")
DEFAULT_CUSTOMERS_PATH = os.path.join(_PROJECT_ROOT, "data", "featured", "superstore_customers.csv")
DEFAULT_MODEL_READY_PATH = os.path.join(_PROJECT_ROOT, "data", "featured", "model_ready.csv")

# Churn = no purchase in last 365 days (per BRD)
CHURN_RECENCY_DAYS = 365

# Discount bands per PRD Section 4
DISCOUNT_BAND_BINS = [-0.001, 0, 0.10, 0.20, 0.30, 1.0]
DISCOUNT_BAND_LABELS = [
    "No Discount",
    "Light (1-10%)",
    "Moderate (11-20%)",
    "Heavy (21-30%)",
    "Extreme (31%+)",
]


def add_discount_bands(df: pd.DataFrame, col: str = "Discount") -> pd.DataFrame:
    """Create discount bands per PRD Section 4 (Discount Analysis Framework)."""
    df = df.copy()
    if col not in df.columns:
        return df
    df["discount_band"] = pd.cut(
        df[col], bins=DISCOUNT_BAND_BINS, labels=DISCOUNT_BAND_LABELS, include_lowest=True
    )
    return df


def discount_band_metrics(df: pd.DataFrame, discount_col: str = "Discount") -> pd.DataFrame:
    """
    Per-band metrics: tx count, total_sales, total_profit, avg_profit, loss_pct, margin_pct.
    Input: transaction-level DataFrame with Discount and Profit (and Sales for margin).
    """
    df = add_discount_bands(df, col=discount_col)
    agg_dict = {
        "tx_count": ("Profit", "count"),
        "total_profit": ("Profit", "sum"),
        "avg_profit": ("Profit", "mean"),
        "loss_pct": ("Profit", lambda x: 100.0 * (x < 0).sum() / len(x)),
    }
    if "Sales" in df.columns:
        agg_dict["total_sales"] = ("Sales", "sum")
    agg = df.groupby("discount_band", observed=False).agg(**agg_dict).reset_index()
    if "total_sales" in agg.columns:
        agg["margin_pct"] = np.where(
            agg["total_sales"] > 0,
            100.0 * agg["total_profit"] / agg["total_sales"],
            np.nan,
        )
    return agg


def add_transaction_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add profit_margin and is_profitable at transaction level."""
    if "Sales" in df.columns and "Profit" in df.columns:
        df = df.copy()
        df["profit_margin"] = np.where(df["Sales"] > 0, df["Profit"] / df["Sales"] * 100, np.nan)
        df["is_profitable"] = (df["Profit"] > 0).astype(int)
    return df


def add_shipping_days(df: pd.DataFrame) -> pd.DataFrame:
    """Shipping days = Ship Date - Order Date (days)."""
    if "Ship Date" in df.columns and "Order Date" in df.columns:
        df = df.copy()
        df["shipping_days"] = (df["Ship Date"] - df["Order Date"]).dt.days
    return df


def build_order_level(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate to order level: order_total_sales, order_total_profit, order_items_count,
    order_avg_discount, shipping_days (avg), order_month, order_quarter, order_year.
    """
    df = add_transaction_features(df)
    df = add_shipping_days(df)

    agg = {
        "Sales": "sum",
        "Profit": "sum",
        "Discount": "mean",
        "shipping_days": "mean",
    }
    # Count rows per order
    order_agg = df.groupby("Order ID").agg(agg).rename(columns={
        "Sales": "order_total_sales",
        "Profit": "order_total_profit",
        "Discount": "order_avg_discount",
        "shipping_days": "avg_shipping_days",
    })
    order_agg["order_items_count"] = df.groupby("Order ID").size()

    # Order date from first row per order
    order_dates = df.groupby("Order ID")["Order Date"].first()
    order_agg["order_date"] = order_dates
    order_agg["order_month"] = order_dates.dt.to_period("M").astype(str)
    order_agg["order_quarter"] = order_dates.dt.to_period("Q").astype(str)
    order_agg["order_year"] = order_dates.dt.year

    order_agg = order_agg.reset_index()
    # Profit margin at order level
    order_agg["order_profit_margin"] = np.where(
        order_agg["order_total_sales"] > 0,
        order_agg["order_total_profit"] / order_agg["order_total_sales"] * 100,
        np.nan,
    )
    return order_agg


def attach_customer_and_region_to_orders(df: pd.DataFrame, orders: pd.DataFrame) -> pd.DataFrame:
    """Attach Customer ID, Segment, Region, State, Ship Mode (from first row per Order ID) to order-level table."""
    first = df.groupby("Order ID").first().reset_index()
    cols = ["Order ID", "Customer ID", "Segment", "Region", "State", "Ship Mode"]
    cols = [c for c in cols if c in first.columns]
    merge_df = first[cols]
    orders = orders.merge(merge_df, on="Order ID", how="left")
    return orders


def build_customer_level(orders: pd.DataFrame, reference_date: pd.Timestamp = None) -> pd.DataFrame:
    """
    Customer-level features for churn: first_order_date, last_order_date, order_count,
    total_spent, total_profit, avg_order_value, avg_profit_margin, avg_discount,
    unique_categories, unique_subcategories, preferred_segment, preferred_ship_mode,
    tenure_days, recency_days, avg_shipping_days, is_churned.
    """
    if reference_date is None:
        reference_date = orders["order_date"].max()

    customers = orders.groupby("Customer ID").agg(
        first_order_date=("order_date", "min"),
        last_order_date=("order_date", "max"),
        order_count=("Order ID", "nunique"),
        total_spent=("order_total_sales", "sum"),
        total_profit=("order_total_profit", "sum"),
        avg_discount=("order_avg_discount", "mean"),
        avg_shipping_days=("avg_shipping_days", "mean"),
    ).reset_index()

    customers["avg_order_value"] = customers["total_spent"] / customers["order_count"]
    customers["avg_profit_margin"] = np.where(
        customers["total_spent"] > 0,
        customers["total_profit"] / customers["total_spent"] * 100,
        np.nan,
    )
    customers["tenure_days"] = (customers["last_order_date"] - customers["first_order_date"]).dt.days
    customers["recency_days"] = (reference_date - customers["last_order_date"]).dt.days
    customers["is_churned"] = (customers["recency_days"] > CHURN_RECENCY_DAYS).astype(int)

    # Segment: take mode per customer from orders
    seg = orders.groupby("Customer ID")["Segment"].agg(lambda x: x.mode().iloc[0] if len(x) else None).reset_index()
    seg.columns = ["Customer ID", "Segment"]
    customers = customers.merge(seg, on="Customer ID", how="left")

    # Preferred ship mode: mode per customer (PRD 2.4)
    if "Ship Mode" in orders.columns:
        ship = orders.groupby("Customer ID")["Ship Mode"].agg(
            lambda x: x.mode().iloc[0] if len(x) else None
        ).reset_index()
        ship.columns = ["Customer ID", "preferred_ship_mode"]
        customers = customers.merge(ship, on="Customer ID", how="left")

    return customers


def add_customer_category_breadth(df_raw: pd.DataFrame, customers: pd.DataFrame) -> pd.DataFrame:
    """Add unique_categories and unique_subcategories per customer from raw transaction data."""
    n_cats = df_raw.groupby("Customer ID")["Category"].nunique().reset_index()
    n_cats.columns = ["Customer ID", "unique_categories"]
    n_subs = df_raw.groupby("Customer ID")["Sub-Category"].nunique().reset_index()
    n_subs.columns = ["Customer ID", "unique_subcategories"]
    customers = customers.merge(n_cats, on="Customer ID", how="left")
    customers = customers.merge(n_subs, on="Customer ID", how="left")
    return customers


def build_model_ready(customers: pd.DataFrame, target_col: str = "is_churned") -> pd.DataFrame:
    """
    Prepare model-ready dataset: numeric features only, one-hot encode Segment.
    Drops date columns, Customer ID, and recency_days (target is derived from it — would leak).
    """
    df = customers.copy()
    # Drop identifiers, dates, and recency_days (directly defines is_churned — data leakage)
    drop_cols = ["Customer ID", "first_order_date", "last_order_date", "recency_days"]
    df = df.drop(columns=[c for c in drop_cols if c in df.columns])

    # One-hot encode Segment (and preferred_ship_mode if present)
    for cat_col in ["Segment", "preferred_ship_mode"]:
        if cat_col in df.columns:
            df = pd.get_dummies(df, columns=[cat_col], drop_first=True)

    # Fill NaN in numeric columns (e.g. avg_profit_margin from zero-sales customers)
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if target_col in df.columns:
        numeric_cols = numeric_cols.drop(target_col, errors="ignore")
    df[numeric_cols] = df[numeric_cols].fillna(0)

    # Ensure target is last
    if target_col in df.columns:
        y = df[target_col]
        df = df.drop(columns=[target_col])
        df[target_col] = y
    return df


def run_feature_engineering_pipeline(
    input_path: str = None,
    orders_path: str = None,
    customers_path: str = None,
    model_ready_path: str = None,
) -> tuple:
    """
    Load preprocessed data, build order-level and customer-level tables, save model_ready.
    Returns (orders_df, customers_df, model_ready_df).
    """
    input_path = input_path or DEFAULT_PREPROCESSED_PATH
    orders_path = orders_path or DEFAULT_ORDERS_PATH
    customers_path = customers_path or DEFAULT_CUSTOMERS_PATH
    model_ready_path = model_ready_path or DEFAULT_MODEL_READY_PATH

    df = pd.read_csv(input_path)
    df["Order Date"] = pd.to_datetime(df["Order Date"], errors="coerce")
    df["Ship Date"] = pd.to_datetime(df["Ship Date"], errors="coerce")

    orders = build_order_level(df)
    orders = attach_customer_and_region_to_orders(df, orders)

    reference_date = orders["order_date"].max()
    customers = build_customer_level(orders, reference_date=reference_date)
    customers = add_customer_category_breadth(df, customers)

    os.makedirs(os.path.dirname(orders_path), exist_ok=True)
    orders.to_csv(orders_path, index=False)
    customers.to_csv(customers_path, index=False)

    model_ready = build_model_ready(customers)
    model_ready.to_csv(model_ready_path, index=False)

    print(f"Orders: {len(orders):,} | Customers: {len(customers):,} | Churn rate: {customers['is_churned'].mean():.2%}")
    return orders, customers, model_ready


if __name__ == "__main__":
    run_feature_engineering_pipeline()
    print(f"Featured data saved to {DEFAULT_ORDERS_PATH}, {DEFAULT_CUSTOMERS_PATH}, {DEFAULT_MODEL_READY_PATH}")
