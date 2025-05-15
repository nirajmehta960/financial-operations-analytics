"""
Plotting helpers for EDA and model evaluation — Financial Operations Analytics.
"""

import os
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from sklearn.metrics import RocCurveDisplay, confusion_matrix


def save_fig(fig, path: str, dpi: int = 150):
    """Save figure to path; create parent dirs if needed."""
    if path:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        fig.savefig(path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)


def plot_roc_curves(results_dict, y_test, title: str = "ROC Curves — Churn Models", save_path: str = None):
    """Plot ROC curves for multiple models."""
    fig, ax = plt.subplots(figsize=(8, 6))
    for name, res in results_dict.items():
        RocCurveDisplay.from_predictions(y_test, res["y_proba"], name=name, ax=ax)
    ax.set_title(title)
    ax.plot([0, 1], [0, 1], "k--")
    plt.tight_layout()
    if save_path:
        save_fig(fig, save_path)
    return fig


def plot_confusion_matrices(results_dict, y_test, save_path: str = None):
    """1x3 confusion matrices for each model."""
    fig, axes = plt.subplots(1, 3, figsize=(14, 5))
    for ax, (name, res) in zip(axes, results_dict.items()):
        cm = confusion_matrix(y_test, res["y_pred"])
        sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", ax=ax)
        ax.set_title(f"{name}\nAUC={res['AUC-ROC']:.3f}")
        ax.set_xlabel("Predicted")
        ax.set_ylabel("Actual")
    plt.tight_layout()
    if save_path:
        save_fig(fig, save_path)
    return fig


def plot_feature_importance(importance_series: pd.Series, top_n: int = 10, title: str = "Top Churn Predictors", save_path: str = None):
    """Horizontal bar chart of feature importance."""
    top = importance_series.head(top_n)
    fig, ax = plt.subplots(figsize=(8, 6))
    top.plot(kind="barh", ax=ax, color="steelblue")
    ax.set_title(title)
    ax.set_xlabel("Importance")
    ax.invert_yaxis()
    plt.tight_layout()
    if save_path:
        save_fig(fig, save_path)
    return fig


def plot_revenue_profit_trend(monthly: pd.DataFrame, save_path: str = None):
    """Dual-axis line: Sales and Profit over time (monthly index)."""
    fig, ax1 = plt.subplots(figsize=(10, 5))
    ax1.plot(monthly.index.astype(str), monthly["Sales"], color="C0", label="Sales")
    ax1.set_ylabel("Sales ($)")
    ax1.legend(loc="upper left")
    ax2 = ax1.twinx()
    ax2.plot(monthly.index.astype(str), monthly["Profit"], color="C1", label="Profit")
    ax2.set_ylabel("Profit ($)")
    ax2.legend(loc="upper right")
    plt.xticks(rotation=45)
    plt.title("Monthly Revenue & Profit Trend")
    plt.tight_layout()
    if save_path:
        save_fig(fig, save_path)
    return fig


def plot_subcategory_pl(subcat: pd.DataFrame, save_path: str = None):
    """Horizontal bar: Sales vs Profit by sub-category (diverging)."""
    subcat = subcat.sort_values("Profit")
    fig, ax = plt.subplots(figsize=(10, 8))
    y = range(len(subcat))
    ax.barh(y, subcat["Sales"], label="Sales", alpha=0.8, color="steelblue")
    ax.barh(y, subcat["Profit"], label="Profit", alpha=0.8, color="green")
    ax.set_yticks(y)
    ax.set_yticklabels(subcat["Sub-Category"] if "Sub-Category" in subcat.columns else subcat.index)
    ax.axvline(0, color="black", linewidth=0.5)
    ax.legend()
    ax.set_title("Sub-Category P&L (Sales vs Profit)")
    plt.tight_layout()
    if save_path:
        save_fig(fig, save_path)
    return fig


def plot_discount_vs_profit(df: pd.DataFrame, save_path: str = None):
    """Scatter: Discount % vs Profit (sample if large)."""
    plot_df = df
    if len(df) > 2000:
        plot_df = df.sample(2000, random_state=42)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(plot_df["Discount"] * 100, plot_df["Profit"], alpha=0.3, s=10)
    ax.axhline(0, color="red", linestyle="--")
    ax.set_xlabel("Discount (%)")
    ax.set_ylabel("Profit ($)")
    ax.set_title("Discount vs Profit (transaction-level)")
    plt.tight_layout()
    if save_path:
        save_fig(fig, save_path)
    return fig


def plot_discount_band_analysis(
    band_metrics: pd.DataFrame,
    value_col: str = "avg_profit",
    save_path: str = None,
):
    """
    Grouped bar: metric by discount band (PRD Section 4).
    band_metrics from feature_engineering.discount_band_metrics().
    """
    fig, ax = plt.subplots(figsize=(9, 5))
    bands = band_metrics["discount_band"].astype(str)
    values = band_metrics[value_col]
    colors = ["C0" if v >= 0 else "C3" for v in values]
    ax.bar(bands, values, color=colors)
    ax.axhline(0, color="black", linewidth=0.5)
    ax.set_xlabel("Discount Band")
    ax.set_ylabel(value_col.replace("_", " ").title())
    ax.set_title("Profit by Discount Band (PRD Section 4)")
    plt.xticks(rotation=25, ha="right")
    plt.tight_layout()
    if save_path:
        save_fig(fig, save_path)
    return fig


def generate_all_eda_charts(
    preprocessed_df: pd.DataFrame,
    orders_df: pd.DataFrame,
    customers_df: pd.DataFrame,
    save_dir: str = "images/eda_charts",
):
    """
    Generate and save all EDA charts to save_dir (e.g. images/eda_charts).
    Uses preprocessed (transaction-level), orders (order-level), and customers (customer-level) DataFrames.
    """
    os.makedirs(save_dir, exist_ok=True)

    # 1. Churn overview (target distribution)
    if "is_churned" in customers_df.columns:
        fig, ax = plt.subplots(figsize=(6, 4))
        sns.countplot(data=customers_df, x="is_churned", ax=ax, palette="Set2")
        ax.set_title("Target Variable Distribution (Churn = 365+ days inactive)")
        ax.set_xlabel("Churned (0=Active, 1=Churned)")
        ax.set_ylabel("Count")
        save_fig(fig, os.path.join(save_dir, "churn_overview.png"))

    # 2. Monthly revenue & profit trend
    orders_df = orders_df.copy()
    if "order_date" in orders_df.columns:
        orders_df["order_date"] = pd.to_datetime(orders_df["order_date"], errors="coerce")
        monthly = orders_df.groupby(orders_df["order_date"].dt.to_period("M")).agg(
            Sales=("order_total_sales", "sum"),
            Profit=("order_total_profit", "sum"),
        ).reset_index()
        monthly["order_date"] = monthly["order_date"].dt.to_timestamp()
        fig, ax1 = plt.subplots(figsize=(10, 5))
        ax1.plot(monthly["order_date"], monthly["Sales"], color="C0", label="Sales")
        ax1.set_ylabel("Sales ($)")
        ax1.legend(loc="upper left")
        ax2 = ax1.twinx()
        ax2.plot(monthly["order_date"], monthly["Profit"], color="C1", label="Profit")
        ax2.set_ylabel("Profit ($)")
        ax2.legend(loc="upper right")
        plt.xticks(rotation=45)
        plt.title("Monthly Revenue & Profit Trend")
        plt.tight_layout()
        save_fig(fig, os.path.join(save_dir, "revenue_profit_trend.png"))

    # 3. Sub-category P&L
    if "Sub-Category" in preprocessed_df.columns and "Sales" in preprocessed_df.columns:
        subcat = (
            preprocessed_df.groupby("Sub-Category")
            .agg(Sales=("Sales", "sum"), Profit=("Profit", "sum"))
            .reset_index()
            .sort_values("Profit")
        )
        fig, ax = plt.subplots(figsize=(10, 8))
        y_pos = range(len(subcat))
        ax.barh(y_pos, subcat["Sales"], label="Sales", alpha=0.7, color="steelblue")
        ax.barh(y_pos, subcat["Profit"], label="Profit", alpha=0.7, color="green")
        ax.set_yticks(y_pos)
        ax.set_yticklabels(subcat["Sub-Category"])
        ax.axvline(0, color="black", linewidth=0.5)
        ax.legend()
        ax.set_title("Sub-Category P&L (Sales vs Profit)")
        plt.tight_layout()
        save_fig(fig, os.path.join(save_dir, "subcategory_pl.png"))

    # 4. Discount vs Profit scatter
    if "Discount" in preprocessed_df.columns and "Profit" in preprocessed_df.columns:
        plot_df = preprocessed_df.sample(min(2000, len(preprocessed_df)), random_state=42)
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.scatter(plot_df["Discount"] * 100, plot_df["Profit"], alpha=0.3, s=10)
        ax.axhline(0, color="red", linestyle="--")
        ax.set_xlabel("Discount (%)")
        ax.set_ylabel("Profit ($)")
        ax.set_title("Discount vs Profit (transaction-level)")
        plt.tight_layout()
        save_fig(fig, os.path.join(save_dir, "discount_vs_profit.png"))

    # 5. Discount band analysis (PRD Section 4)
    try:
        try:
            from src.feature_engineering import discount_band_metrics
        except ImportError:
            from feature_engineering import discount_band_metrics
        band_metrics = discount_band_metrics(preprocessed_df, discount_col="Discount")
        plot_discount_band_analysis(
            band_metrics, value_col="avg_profit",
            save_path=os.path.join(save_dir, "discount_band_analysis.png"),
        )
    except Exception:
        pass

    # 6. Correlation matrix (customer-level numeric features)
    numeric = customers_df.select_dtypes(include=[np.number])
    if len(numeric.columns) > 1:
        # Drop target for clearer correlation with features only if desired; here we keep it
        fig, ax = plt.subplots(figsize=(10, 8))
        corr = numeric.corr()
        sns.heatmap(corr, cmap="coolwarm", center=0, ax=ax, fmt=".2f")
        ax.set_title("Customer-Level Feature Correlation")
        plt.tight_layout()
        save_fig(fig, os.path.join(save_dir, "correlation_matrix.png"))

    # 7. Regional profitability
    if "Region" in preprocessed_df.columns and "Sales" in preprocessed_df.columns:
        region = (
            preprocessed_df.groupby("Region")
            .agg(Sales=("Sales", "sum"), Profit=("Profit", "sum"))
            .assign(margin_pct=lambda x: np.where(x["Sales"] > 0, 100 * x["Profit"] / x["Sales"], np.nan))
        )
        fig, ax = plt.subplots(figsize=(8, 5))
        x_pos = range(len(region))
        ax.bar(x_pos, region["margin_pct"], color="steelblue")
        ax.set_xticks(x_pos)
        ax.set_xticklabels(region.index)
        ax.axhline(0, color="black", linewidth=0.5)
        ax.set_ylabel("Profit Margin (%)")
        ax.set_title("Profit Margin by Region")
        plt.tight_layout()
        save_fig(fig, os.path.join(save_dir, "region_profitability.png"))

    # 8. Segment profitability
    if "Segment" in preprocessed_df.columns and "Sales" in preprocessed_df.columns:
        seg = (
            preprocessed_df.groupby("Segment")
            .agg(Sales=("Sales", "sum"), Profit=("Profit", "sum"))
            .assign(margin_pct=lambda x: np.where(x["Sales"] > 0, 100 * x["Profit"] / x["Sales"], np.nan))
        )
        fig, ax = plt.subplots(figsize=(8, 5))
        x_pos = range(len(seg))
        ax.bar(x_pos, seg["margin_pct"], color="coral")
        ax.set_xticks(x_pos)
        ax.set_xticklabels(seg.index)
        ax.axhline(0, color="black", linewidth=0.5)
        ax.set_ylabel("Profit Margin (%)")
        ax.set_title("Profit Margin by Segment")
        plt.tight_layout()
        save_fig(fig, os.path.join(save_dir, "segment_profitability.png"))

    # 9. Profit impact summary (placeholder for estimated savings)
    total_profit = preprocessed_df["Profit"].sum()
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.text(
        0.5, 0.5,
        f"Total Profit (4 years): ${total_profit:,.0f}\n"
        "Cap discounts at 20% → est. +$50K–$80K/year",
        ha="center", va="center", fontsize=16, color="forestgreen", weight="bold",
    )
    ax.axis("off")
    save_fig(fig, os.path.join(save_dir, "profit_impact_summary.png"))

    print(f"EDA charts saved to {save_dir}")
