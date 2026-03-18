"""Tests for modeling module (churn prediction)."""
from pathlib import Path
import sys
import pandas as pd
import numpy as np
import pytest

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.python_pipeline.modeling import (
    prepare_train_test,
    scale_numeric,
    get_default_models,
    get_best_model_name,
    get_feature_importances,
    train_and_evaluate,
    TARGET_COL,
)


def _make_dummy_model_ready(n=200, target_col="is_churned"):
    """Minimal model-ready DataFrame for churn (no recency_days)."""
    rng = np.random.RandomState(42)
    df = pd.DataFrame({
        "order_count": rng.randint(1, 20, n),
        "total_spent": rng.uniform(100, 5000, n),
        "avg_order_value": rng.uniform(50, 500, n),
        "avg_profit_margin": rng.uniform(-5, 25, n),
        "avg_discount": rng.uniform(0, 0.3, n),
        "tenure_days": rng.randint(30, 1000, n),
        "unique_categories": rng.randint(1, 3, n),
        "unique_subcategories": rng.randint(1, 10, n),
        "avg_shipping_days": rng.uniform(2, 6, n),
        target_col: rng.choice([0, 1], n, p=[0.75, 0.25]),
    })
    return df


def test_prepare_train_test_shapes():
    df = _make_dummy_model_ready(200)
    X_train, X_test, y_train, y_test = prepare_train_test(df, target_col=TARGET_COL, test_size=0.2)
    assert len(X_train) == 160
    assert len(X_test) == 40
    assert len(y_train) == 160
    assert len(y_test) == 40
    assert TARGET_COL not in X_train.columns
    assert TARGET_COL not in X_test.columns


def test_prepare_train_test_stratification():
    df = _make_dummy_model_ready(500)
    _, _, y_train, y_test = prepare_train_test(df, target_col=TARGET_COL, test_size=0.2)
    train_rate = y_train.mean()
    test_rate = y_test.mean()
    assert abs(train_rate - test_rate) < 0.05


def test_scale_numeric():
    df = _make_dummy_model_ready(100)
    X_train, X_test, _, _ = prepare_train_test(df, target_col=TARGET_COL, test_size=0.2)
    cols = ["order_count", "total_spent"]
    X_train_s, X_test_s, scaler = scale_numeric(X_train, X_test, numeric_cols=cols)
    assert scaler is not None
    # Scaled train columns should have ~zero mean
    assert abs(X_train_s["order_count"].mean()) < 0.01
    assert abs(X_train_s["total_spent"].mean()) < 0.01


def test_get_default_models():
    models = get_default_models()
    assert "Logistic Regression" in models
    assert "Random Forest" in models
    assert "Gradient Boosting" in models
    assert len(models) == 3


def test_get_best_model_name():
    results = {
        "Model A": {"AUC-ROC": 0.70, "F1": 0.40},
        "Model B": {"AUC-ROC": 0.65, "F1": 0.50},
        "Model C": {"AUC-ROC": 0.72, "F1": 0.35},
    }
    assert get_best_model_name(results, metric="AUC-ROC") == "Model C"
    assert get_best_model_name(results, metric="F1") == "Model B"


def test_get_feature_importances():
    from sklearn.ensemble import RandomForestClassifier
    model = RandomForestClassifier(n_estimators=5, random_state=42)
    X = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6], "c": [7, 8, 9]})
    y = np.array([0, 1, 0])
    model.fit(X, y)
    imp = get_feature_importances(model, X.columns)
    assert isinstance(imp, pd.Series)
    assert set(imp.index) == {"a", "b", "c"}
    assert imp.sum() == pytest.approx(1.0)


def test_train_and_evaluate_returns_expected_keys():
    df = _make_dummy_model_ready(150)
    X_train, X_test, y_train, y_test = prepare_train_test(df, target_col=TARGET_COL, test_size=0.2)
    X_train_s, X_test_s, _ = scale_numeric(X_train, X_test)
    models = get_default_models()
    results = train_and_evaluate(
        models, X_train, X_test, y_train, y_test,
        X_train_scaled=X_train_s, X_test_scaled=X_test_s,
    )
    for name, res in results.items():
        assert "AUC-ROC" in res
        assert "Recall" in res
        assert "Precision" in res
        assert "F1" in res
        assert "y_pred" in res
        assert "y_proba" in res
        assert len(res["y_pred"]) == len(y_test)
        assert len(res["y_proba"]) == len(y_test)
