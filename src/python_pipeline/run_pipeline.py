"""
Run the Python ETL pipeline (Phase 2 cleaning + Phase 3 feature engineering).

This is a thin wrapper around the existing modules in `src/` to match the
`src/python_pipeline/` project structure used in the diabetes reference repo.
"""

import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.python_pipeline.data_cleaning import run_cleaning_pipeline, DEFAULT_PREPROCESSED_PATH  # noqa: E402
from src.python_pipeline.feature_engineering import (  # noqa: E402
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
    print("Python pipeline complete.")

