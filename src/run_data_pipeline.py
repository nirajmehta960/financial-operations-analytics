"""
Run full data pipeline: cleaning (Phase 2) and feature engineering (Phase 3).
"""

import sys
import os

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from src.data_cleaning import run_cleaning_pipeline, DEFAULT_PREPROCESSED_PATH
from src.feature_engineering import (
    run_feature_engineering_pipeline,
    DEFAULT_ORDERS_PATH,
    DEFAULT_CUSTOMERS_PATH,
    DEFAULT_MODEL_READY_PATH,
)


def run_pipeline(
    raw_path: str = None,
    preprocessed_path: str = None,
    orders_path: str = None,
    customers_path: str = None,
    model_ready_path: str = None,
):
    """Execute cleaning then feature engineering. All path args optional."""
    run_cleaning_pipeline(data_path=raw_path, save_path=preprocessed_path)
    print(f"Phase 2 done: preprocessed -> {preprocessed_path or DEFAULT_PREPROCESSED_PATH}")

    run_feature_engineering_pipeline(
        input_path=preprocessed_path,
        orders_path=orders_path,
        customers_path=customers_path,
        model_ready_path=model_ready_path,
    )
    print(f"Phase 3 done: orders -> {orders_path or DEFAULT_ORDERS_PATH}")
    print(f"Phase 3 done: customers -> {customers_path or DEFAULT_CUSTOMERS_PATH}")
    print(f"Phase 3 done: model_ready -> {model_ready_path or DEFAULT_MODEL_READY_PATH}")


if __name__ == "__main__":
    run_pipeline()
    print("Data pipeline complete.")
