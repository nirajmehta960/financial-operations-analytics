"""
Revenue forecasting: linear trend + optional moving average.
Per BRD: 3–6 month forward projection with R².
"""

import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression


def prepare_monthly_series(orders: pd.DataFrame) -> pd.DataFrame:
    """Aggregate orders to monthly Sales and Profit. Index = period (e.g. month number or datetime)."""
    orders = orders.copy()
    if "order_date" in orders.columns:
        orders["order_date"] = pd.to_datetime(orders["order_date"])
        orders["month"] = orders["order_date"].dt.to_period("M")
    else:
        return pd.DataFrame()
    monthly = orders.groupby("month").agg(
        Sales=("order_total_sales", "sum"),
        Profit=("order_total_profit", "sum"),
        OrderCount=("Order ID", "nunique"),
    ).reset_index()
    monthly["month_ordinal"] = np.arange(len(monthly))
    return monthly


def fit_trend(monthly: pd.DataFrame, value_col: str = "Sales") -> tuple:
    """
    Linear regression of value_col on month_ordinal.
    Returns (model, r2, predictions on training range).
    """
    X = monthly[["month_ordinal"]].values
    y = monthly[value_col].values
    model = LinearRegression().fit(X, y)
    pred = model.predict(X)
    r2 = np.corrcoef(y, pred)[0, 1] ** 2
    return model, r2, pred


def forecast_months(model: LinearRegression, last_ordinal: int, n_months: int = 6) -> np.ndarray:
    """Forecast next n_months using fitted linear model (month_ordinal)."""
    future = np.arange(last_ordinal + 1, last_ordinal + n_months + 1).reshape(-1, 1)
    return model.predict(future)


def add_moving_average(monthly: pd.DataFrame, value_col: str = "Sales", window: int = 3) -> pd.DataFrame:
    """Add moving average column."""
    monthly = monthly.copy()
    monthly[f"{value_col}_MA{window}"] = monthly[value_col].rolling(window=window, min_periods=1).mean()
    return monthly
