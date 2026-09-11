"""
RetailSense-AI Machine Learning Module.
"""

from ml.churn_label import generate_churn_labels
from ml.feature_engineering import generate_customer_features
from ml.train import run_training_pipeline
from ml.evaluate import evaluate_model
from ml.model_utils import load_and_merge_data, preprocess_and_split
from ml.mlflow_tracking import setup_mlflow, log_model_run, register_or_update_champion

__all__ = [
    "generate_churn_labels",
    "generate_customer_features",
    "run_training_pipeline",
    "evaluate_model",
    "load_and_merge_data",
    "preprocess_and_split",
    "setup_mlflow",
    "log_model_run",
    "register_or_update_champion"
]
