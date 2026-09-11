"""
Unit and Integration Tests for Machine Learning Training, Evaluation, and Target Leakage Prevention.
"""

import os
import json
import joblib
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from ml.train import run_training_pipeline
from ml.model_utils import preprocess_and_split, prepare_preprocessor, load_and_merge_data, EXCLUDED_FEATURES
from ml.evaluate import evaluate_model
from sklearn.linear_model import LogisticRegression


@pytest.fixture
def sample_ml_dataset(tmp_path):
    """Generates synthetic customer features and churn dataset for training test."""
    n_samples = 100
    base_date = datetime(2026, 9, 1)

    features = []
    churn_labels = []

    for i in range(1, n_samples + 1):
        is_churn = 1 if i % 2 == 0 else 0
        recency = 100 if is_churn else 15

        feat = {
            "customer_id": i,
            "country": "United Kingdom" if i % 3 == 0 else "France",
            "first_purchase": (base_date - timedelta(days=200)).strftime("%Y-%m-%d"),
            "last_purchase": (base_date - timedelta(days=recency)).strftime("%Y-%m-%d"),
            "customer_lifetime_days": 200,
            "total_spent": float(i * 50.0),
            "average_order_value": float(i * 10.0),
            "max_order_value": float(i * 20.0),
            "min_order_value": 5.0,
            "total_quantity": i * 5,
            "average_quantity": 5.0,
            "total_orders": 5,
            "purchase_frequency": 0.025,
            "purchase_velocity": 0.025,
            "average_days_between_orders": 20.0,
            "recency_days": recency,
            "unique_products": i % 10 + 1,
            "favorite_product": "P100",
            "favorite_category": "Home & Decor",
            "category_diversity": 2,
            "preferred_month": 5,
            "preferred_weekday": "Monday",
            "preferred_hour": 12,
            "weekend_purchase_ratio": 0.1,
            "revenue_per_day": 1.2,
            "items_per_order": 5.0,
            "customer_value_segment": "Medium",
            "basket_size": 5.0
        }
        features.append(feat)

        churn_labels.append({
            "customer_id": i,
            "churn": is_churn
        })

    feat_df = pd.DataFrame(features)
    churn_df = pd.DataFrame(churn_labels)

    feat_path = str(tmp_path / "customer_features.csv")
    churn_path = str(tmp_path / "customer_churn_dataset.csv")

    feat_df.to_csv(feat_path, index=False)
    churn_df.to_csv(churn_path, index=False)

    return feat_path, churn_path


def test_target_leakage_exclusion(sample_ml_dataset):
    """Verifies that recency_days, customer_id, churn, and date columns are excluded from training inputs."""
    feat_path, churn_path = sample_ml_dataset
    df_merged = load_and_merge_data(feat_path, churn_path)
    
    X, y, num_cols, cat_cols, actual_excluded = prepare_preprocessor(df_merged)

    # 1. Assert leaky/identifier features are NOT present in feature matrix X
    assert "recency_days" not in X.columns, "recency_days MUST be excluded from feature matrix X"
    assert "customer_id" not in X.columns, "customer_id MUST be excluded from feature matrix X"
    assert "churn" not in X.columns, "churn MUST be excluded from feature matrix X"
    assert "first_purchase" not in X.columns, "first_purchase date string MUST be excluded"
    assert "last_purchase" not in X.columns, "last_purchase date string MUST be excluded"

    # 2. Assert excluded features list contains required items
    assert "recency_days" in actual_excluded
    assert "customer_id" in actual_excluded
    assert "churn" in actual_excluded


def test_training_pipeline_execution(sample_ml_dataset, tmp_path):
    """Tests complete training pipeline: model fitting, evaluation, saving artifacts, plots, & reports."""
    feat_path, churn_path = sample_ml_dataset
    models_dir = str(tmp_path / "models")
    reports_dir = str(tmp_path / "reports")

    summary = run_training_pipeline(
        features_path=feat_path,
        churn_path=churn_path,
        models_dir=models_dir,
        reports_dir=reports_dir
    )

    # 1. Model & Preprocessor Persistence
    best_model_path = summary["best_model_path"]
    encoder_path = summary["encoder_path"]
    
    assert os.path.exists(best_model_path)
    assert os.path.exists(encoder_path)

    # Load and verify saved pipeline artifact
    saved_pipeline = joblib.load(best_model_path)
    assert hasattr(saved_pipeline, "predict")

    saved_encoder = joblib.load(encoder_path)
    assert "preprocessor" in saved_encoder
    assert "feature_names" in saved_encoder
    assert "excluded_features" in saved_encoder

    # Verify recency_days is absent from saved encoder's original features
    assert "recency_days" not in saved_encoder["original_features"]

    # 2. Metrics & Report Persistence
    csv_metrics = summary["csv_metrics_path"]
    json_eval = summary["json_eval_path"]

    assert os.path.exists(csv_metrics)
    assert os.path.exists(json_eval)

    df_metrics = pd.read_csv(csv_metrics)
    assert len(df_metrics) == 3
    assert set(df_metrics["Model"]) == {"Logistic Regression", "Random Forest", "XGBoost"}
    assert "ROC_AUC" in df_metrics.columns

    with open(json_eval, "r", encoding="utf-8") as f:
        eval_data = json.load(f)

    # 3. Assert all required JSON report fields exist
    assert "best_model" in eval_data
    assert "best_metrics" in eval_data
    assert "excluded_features" in eval_data
    assert "final_model_features" in eval_data
    assert "leakage_prevention_notes" in eval_data
    assert "target_distribution" in eval_data
    assert "preprocessing_summary" in eval_data

    # Assert recency_days is in excluded_features
    assert "recency_days" in eval_data["excluded_features"]

    # 4. Plots Directory & PNG Files Validation
    plots = summary["plot_paths"]
    assert os.path.exists(plots["roc_curve"])
    assert os.path.exists(plots["confusion_matrix"])
    assert os.path.exists(plots["precision_recall_curve"])
    assert os.path.exists(plots["feature_importance"])


def test_evaluate_model_standalone():
    """Unit test for evaluate_model helper function."""
    X_train = np.array([[1.0, 2.0], [2.0, 3.0], [-1.0, -2.0], [-2.0, -3.0]])
    y_train = pd.Series([1, 1, 0, 0])
    
    model = LogisticRegression(random_state=42)
    model.fit(X_train, y_train)

    metrics = evaluate_model(model, X_train, y_train, model_name="TestLR")
    assert metrics["accuracy"] == 1.0
    assert metrics["roc_auc"] == 1.0
    assert metrics["model_name"] == "TestLR"
