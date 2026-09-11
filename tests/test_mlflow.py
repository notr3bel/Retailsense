"""
Unit and Integration Tests for MLflow Experiment Tracking Module.
Uses isolated temporary tracking directory to avoid polluting project mlruns/.
"""

import os
import json
import joblib
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta

import mlflow
from ml.mlflow_tracking import (
    setup_mlflow,
    log_model_run,
    register_or_update_champion,
    extract_hyperparameters,
    DEFAULT_EXPERIMENT_NAME
)
from ml.train import run_training_pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


@pytest.fixture
def temp_mlflow_uri(tmp_path):
    """Sets up an isolated local MLflow tracking directory for testing."""
    mlruns_dir = tmp_path / "mlruns"
    uri = mlruns_dir.as_uri()
    setup_mlflow(tracking_uri=uri, experiment_name="Test-Experiment")
    return uri


@pytest.fixture
def sample_ml_dataset(tmp_path):
    """Generates synthetic customer features and churn dataset for training test."""
    n_samples = 60
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


def test_mlflow_setup(temp_mlflow_uri):
    """Verifies MLflow initialization and experiment creation."""
    success, exp_id = setup_mlflow(tracking_uri=temp_mlflow_uri, experiment_name="Test-Experiment")
    assert success is True
    assert exp_id is not None
    assert mlflow.get_experiment_by_name("Test-Experiment") is not None


def test_extract_hyperparameters():
    """Verifies hyperparameter extraction for candidate estimators."""
    lr = LogisticRegression(C=0.5, max_iter=500, random_state=42)
    lr_params = extract_hyperparameters(lr)
    assert lr_params.get("C") == 0.5
    assert lr_params.get("max_iter") == 500

    rf = RandomForestClassifier(n_estimators=50, max_depth=5, random_state=42)
    rf_params = extract_hyperparameters(rf)
    assert rf_params.get("n_estimators") == 50
    assert rf_params.get("max_depth") == 5


def test_log_model_run_and_champion(temp_mlflow_uri, tmp_path):
    """Verifies logging a run with params, metrics, pipeline artifact, and champion update."""
    setup_mlflow(tracking_uri=temp_mlflow_uri, experiment_name="Test-Experiment")

    pipeline = Pipeline([("scaler", StandardScaler()), ("clf", LogisticRegression())])
    pipeline.fit([[1.0], [2.0], [-1.0], [-2.0]], [1, 1, 0, 0])

    eval_metrics = {
        "accuracy": 0.90,
        "precision": 0.92,
        "recall": 0.88,
        "f1_score": 0.90,
        "roc_auc": 0.95
    }

    dataset_metadata = {
        "dataset_size": 100,
        "train_size": 80,
        "test_size": 20,
        "original_feature_count": 23,
        "encoded_feature_count": 30,
        "excluded_features": ["recency_days", "customer_id", "churn"]
    }

    run_id = log_model_run(
        model_name="TestLR",
        model=pipeline.named_steps["clf"],
        pipeline=pipeline,
        eval_metrics=eval_metrics,
        dataset_metadata=dataset_metadata,
        execution_duration=1.5
    )

    assert run_id is not None

    # Retrieve run from MLflow client
    client = mlflow.tracking.MlflowClient()
    run_data = client.get_run(run_id)

    assert run_data.data.metrics["roc_auc"] == 0.95
    assert run_data.data.metrics["accuracy"] == 0.90
    assert run_data.data.params["model_name"] == "TestLR"
    assert "recency_days" in run_data.data.tags["excluded_from_training"]

    # Test champion registration
    runs_summary = [{
        "model_name": "TestLR",
        "run_id": run_id,
        "roc_auc": 0.95,
        "pipeline": pipeline
    }]

    champion = register_or_update_champion(runs_summary, experiment_name="Test-Experiment")
    assert champion["model_name"] == "TestLR"
    assert champion["run_id"] == run_id


def test_standalone_pipeline_prediction(sample_ml_dataset, tmp_path):
    """Verifies models/best_model.pkl operates standalone for prediction without MLflow."""
    feat_path, churn_path = sample_ml_dataset
    models_dir = str(tmp_path / "models")
    reports_dir = str(tmp_path / "reports")

    summary = run_training_pipeline(
        features_path=feat_path,
        churn_path=churn_path,
        models_dir=models_dir,
        reports_dir=reports_dir
    )

    best_model_path = summary["best_model_path"]
    assert os.path.exists(best_model_path)

    # Load complete pipeline from disk
    standalone_pipeline = joblib.load(best_model_path)
    assert hasattr(standalone_pipeline, "predict")
    assert hasattr(standalone_pipeline, "predict_proba")

    # Perform prediction on sample features DataFrame
    df_feat = pd.read_csv(feat_path)
    preds = standalone_pipeline.predict(df_feat)
    probs = standalone_pipeline.predict_proba(df_feat)

    assert len(preds) == len(df_feat)
    assert probs.shape == (len(df_feat), 2)
    assert set(preds).issubset({0, 1})
