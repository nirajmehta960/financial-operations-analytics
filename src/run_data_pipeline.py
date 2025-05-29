"""
Orchestrator for the end-to-end data pipeline.

Execution order:
1) Phase 2 cleaning
2) Phase 3 feature engineering
"""

import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

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
    """Run cleaning then feature engineering.

    All path arguments are optional. If omitted, each phase uses its module defaults.

    Output datasets:
    - preprocessed CSV (Phase 2)
    - orders CSV (Phase 3)
    - customers CSV (Phase 3)
    - model_ready CSV (Phase 3)
    """
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
