"""
Churn prediction: Logistic Regression, Random Forest, Gradient Boosting.
Train/test split, scaling for LR, AUC-ROC evaluation, save best model and scaler.
"""

import os
import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.utils.class_weight import compute_sample_weight
from sklearn.metrics import (
    roc_auc_score,
    classification_report,
    confusion_matrix,
    RocCurveDisplay,
    recall_score,
    precision_score,
    f1_score,
)

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_MODEL_READY_PATH = os.path.join(_PROJECT_ROOT, "data", "featured", "model_ready.csv")
DEFAULT_MODEL_DIR = os.path.join(_PROJECT_ROOT, "model")
TARGET_COL = "is_churned"


def prepare_train_test(
    df: pd.DataFrame,
    target_col: str = TARGET_COL,
    test_size: float = 0.2,
    random_state: int = 42,
):
    """Split into X, y and train/test with stratification."""
    X = df.drop(columns=[target_col])
    y = df[target_col]
    return train_test_split(X, y, test_size=test_size, random_state=random_state, stratify=y)


def get_numeric_columns(X: pd.DataFrame) -> list:
    """Numeric columns for scaling (exclude any remaining non-numeric)."""
    return X.select_dtypes(include=[np.number]).columns.tolist()


def scale_numeric(X_train: pd.DataFrame, X_test: pd.DataFrame, numeric_cols: list = None):
    """StandardScaler fit on train, transform train and test."""
    numeric_cols = numeric_cols or get_numeric_columns(X_train)
    scaler = StandardScaler()
    X_train_scaled = X_train.copy()
    X_test_scaled = X_test.copy()
    if numeric_cols:
        X_train_scaled[numeric_cols] = scaler.fit_transform(X_train[numeric_cols])
        X_test_scaled[numeric_cols] = scaler.transform(X_test[numeric_cols])
    return X_train_scaled, X_test_scaled, scaler


def get_default_models():
    """Return dict of name -> sklearn model instance."""
    return {
        "Logistic Regression": LogisticRegression(
            max_iter=1000, class_weight="balanced", random_state=42
        ),
        "Random Forest": RandomForestClassifier(
            n_estimators=200, max_depth=10, class_weight="balanced",
            random_state=42, n_jobs=-1
        ),
        "Gradient Boosting": GradientBoostingClassifier(
            n_estimators=200, max_depth=5, learning_rate=0.1,
            random_state=42
        ),
    }


def train_and_evaluate(models, X_train, X_test, y_train, y_test,
                      X_train_scaled=None, X_test_scaled=None):
    """Train each model; use scaled features for LR. Return results dict with y_pred, y_proba."""
    results = {}
    for name, model in models.items():
        if name == "Logistic Regression" and X_train_scaled is not None:
            model.fit(X_train_scaled, y_train)
            y_pred = model.predict(X_test_scaled)
            y_proba = model.predict_proba(X_test_scaled)[:, 1]
        else:
            if name == "Gradient Boosting":
                sample_weights = compute_sample_weight(class_weight="balanced", y=y_train)
                model.fit(X_train, y_train, sample_weight=sample_weights)
            else:
                model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            y_proba = model.predict_proba(X_test)[:, 1]
        auc = roc_auc_score(y_test, y_proba)
        recall = recall_score(y_test, y_pred, zero_division=0)
        precision = precision_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        results[name] = {
            "AUC-ROC": auc, "Recall": recall, "Precision": precision, "F1": f1,
            "y_pred": y_pred, "y_proba": y_proba,
        }
    return results


def get_best_model_name(results: dict, metric: str = "AUC-ROC"):
    """Return the model name with highest value for the given metric."""
    return max(results, key=lambda k: results[k][metric])


def get_feature_importances(model, feature_names) -> pd.Series:
    """Feature importances for tree-based models."""
    return pd.Series(model.feature_importances_, index=feature_names).sort_values(ascending=False)


def run_training_pipeline(
    data_path: str = None,
    model_dir: str = None,
    save_all_models: bool = False,
):
    """Load model_ready.csv, train all models, save best model and scaler to model/."""
    data_path = data_path or DEFAULT_MODEL_READY_PATH
    model_dir = model_dir or DEFAULT_MODEL_DIR
    os.makedirs(model_dir, exist_ok=True)

    df = pd.read_csv(data_path)
    X_train, X_test, y_train, y_test = prepare_train_test(df)
    X_train_scaled, X_test_scaled, scaler = scale_numeric(X_train, X_test)

    models = get_default_models()
    results = train_and_evaluate(
        models, X_train, X_test, y_train, y_test,
        X_train_scaled=X_train_scaled, X_test_scaled=X_test_scaled,
    )
    best_name = get_best_model_name(results)
    best_model = models[best_name]

    best_path = os.path.join(model_dir, "best_model.pkl")
    scaler_path = os.path.join(model_dir, "scaler.pkl")
    joblib.dump(best_model, best_path)
    joblib.dump(scaler, scaler_path)
    print(f"Best model ({best_name}) saved to {best_path}")
    print(f"Scaler saved to {scaler_path}")

    if save_all_models:
        for name, model in models.items():
            safe_name = name.lower().replace(" ", "_") + ".pkl"
            path = os.path.join(model_dir, safe_name)
            joblib.dump(model, path)
            print(f"Saved {name} to {path}")

    return results, best_model, scaler


if __name__ == "__main__":
    import sys
    if _PROJECT_ROOT not in sys.path:
        sys.path.insert(0, _PROJECT_ROOT)
    results, best_model, scaler = run_training_pipeline(save_all_models=True)
    print("Training complete. Artifacts in model/")

    # Save model evaluation charts to images/eda_charts
    images_dir = os.path.join(_PROJECT_ROOT, "images", "eda_charts")
    os.makedirs(images_dir, exist_ok=True)
    df = pd.read_csv(DEFAULT_MODEL_READY_PATH)
    X_train, X_test, y_train, y_test = prepare_train_test(df)
    try:
        from src.visualizations import plot_roc_curves, plot_confusion_matrices, plot_feature_importance
        plot_roc_curves(results, y_test, save_path=os.path.join(images_dir, "roc_comparison.png"))
        plot_confusion_matrices(results, y_test, save_path=os.path.join(images_dir, "confusion_matrices.png"))
        if hasattr(best_model, "feature_importances_"):
            imp = get_feature_importances(best_model, X_train.columns)
            plot_feature_importance(imp, save_path=os.path.join(images_dir, "feature_importance.png"))
        print(f"Model charts saved to {images_dir}")
    except Exception as e:
        print(f"Could not save model charts: {e}")
