"""
API Configuration Settings for RetailSense-AI.
Defines project-relative paths and application metadata without machine-specific absolute paths.
"""

from pathlib import Path

# Project Root Directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Model & Artifact File Paths
MODEL_PATH = PROJECT_ROOT / "models" / "best_model.pkl"
ENCODER_PATH = PROJECT_ROOT / "models" / "model_encoder.pkl"
METRICS_CSV_PATH = PROJECT_ROOT / "reports" / "model_metrics.csv"
EVAL_JSON_PATH = PROJECT_ROOT / "reports" / "model_evaluation.json"

# API Metadata & Constraints
APP_TITLE = "RetailSense-AI Churn Prediction API"
APP_DESCRIPTION = (
    "Production-grade REST API serving customer churn predictions powered by an end-to-end "
    "ETL data pipeline and champion XGBoost Machine Learning model."
)
APP_VERSION = "1.0.0"
MAX_BATCH_SIZE = 1000
