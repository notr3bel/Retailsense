"""
MLflow Experiment Tracking Module for RetailSense-AI.
Centralizes MLflow configuration, run logging, metrics tracking, artifact storage,
and champion model registration.
"""

import os
import tempfile
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd

import mlflow
import mlflow.sklearn
from etl.utils import setup_logger

logger = setup_logger("ML_MLflow")

DEFAULT_EXPERIMENT_NAME = "RetailSense-Churn-Prediction"


def get_default_tracking_uri() -> str:
    """
    Returns local project-relative tracking URI for MLflow.
    
    Returns:
        str: Absolute file URI pointing to project_root/mlruns
    """
    project_root = Path(__file__).resolve().parent.parent
    mlruns_dir = project_root / "mlruns"
    return mlruns_dir.as_uri()


def setup_mlflow(
    tracking_uri: Optional[str] = None,
    experiment_name: str = DEFAULT_EXPERIMENT_NAME
) -> Tuple[bool, Optional[str]]:
    """
    Configures MLflow tracking URI and sets active experiment.
    
    Args:
        tracking_uri: Custom tracking URI (defaults to project mlruns/).
        experiment_name: MLflow experiment name.
        
    Returns:
        Tuple[bool, Optional[str]]: (is_available, experiment_id)
    """
    try:
        os.environ["MLFLOW_ALLOW_FILE_STORE"] = "true"
        if tracking_uri is None:
            tracking_uri = get_default_tracking_uri()

        mlflow.set_tracking_uri(tracking_uri)
        experiment = mlflow.get_experiment_by_name(experiment_name)

        if experiment is None:
            exp_id = mlflow.create_experiment(
                name=experiment_name,
                tags={
                    "project": "RetailSense-AI",
                    "task": "customer_churn_prediction",
                    "target": "churn",
                    "selection_metric": "roc_auc"
                }
            )
        else:
            exp_id = experiment.experiment_id

        mlflow.set_experiment(experiment_name)
        logger.info(f"MLflow initialized successfully. Tracking URI: {tracking_uri} | Experiment: {experiment_name} (ID: {exp_id})")
        return True, exp_id

    except Exception as e:
        logger.warning(f"MLflow initialization warning (tracking will continue gracefully): {e}")
        return False, None


def extract_hyperparameters(model: Any) -> Dict[str, Any]:
    """
    Extracts relevant hyperparameter dictionary from a trained model instance.
    
    Args:
        model: Model estimator.
        
    Returns:
        Dict[str, Any]: Hyperparameter map.
    """
    params = {}
    model_class = model.__class__.__name__

    if hasattr(model, "get_params"):
        all_params = model.get_params()
        if model_class == "LogisticRegression":
            for k in ["C", "max_iter", "solver", "penalty", "random_state"]:
                if k in all_params:
                    params[k] = all_params[k]
        elif model_class == "RandomForestClassifier":
            for k in ["n_estimators", "max_depth", "min_samples_split", "min_samples_leaf", "random_state"]:
                if k in all_params:
                    params[k] = all_params[k]
        elif model_class in ["XGBClassifier", "XGBoost"]:
            for k in ["n_estimators", "max_depth", "learning_rate", "subsample", "colsample_bytree", "random_state", "eval_metric"]:
                if k in all_params and all_params[k] is not None:
                    params[k] = all_params[k]

    if not params and hasattr(model, "get_params"):
        # Fallback to general params if model not specifically mapped
        raw = model.get_params()
        params = {k: v for k, v in raw.items() if isinstance(v, (int, float, str, bool, type(None)))}

    return params


def log_model_run(
    model_name: str,
    model: Any,
    pipeline: Any,
    eval_metrics: Dict[str, Any],
    dataset_metadata: Dict[str, Any],
    plot_paths: Optional[Dict[str, str]] = None,
    feature_importance: Optional[Dict[str, float]] = None,
    execution_duration: float = 0.0
) -> Optional[str]:
    """
    Logs a single candidate model run to MLflow including parameters, tags, metrics, artifacts, and pipeline model.
    
    Returns:
        Optional[str]: MLflow run_id if successful, else None.
    """
    try:
        with mlflow.start_run(run_name=model_name) as run:
            run_id = run.info.run_id

            # 1. Log Tags
            mlflow.set_tags({
                "project": "RetailSense-AI",
                "task": "customer_churn_prediction",
                "target": "churn",
                "selection_metric": "roc_auc",
                "model_name": model_name,
                "dataset_name": "customer_features.csv",
                "excluded_from_training": ", ".join(dataset_metadata.get("excluded_features", []))
            })

            # 2. Log Dataset & Run Parameters
            params = {
                "model_name": model_name,
                "random_state": 42,
                "test_size": 0.2,
                "total_samples": dataset_metadata.get("dataset_size", 0),
                "training_samples": dataset_metadata.get("train_size", 0),
                "test_samples": dataset_metadata.get("test_size", 0),
                "feature_count_before_encoding": dataset_metadata.get("original_feature_count", 0),
                "feature_count_after_encoding": dataset_metadata.get("encoded_feature_count", 0)
            }
            # Merge model hyperparameters
            hyperparams = extract_hyperparameters(model)
            for hk, hv in hyperparams.items():
                params[f"hp_{hk}"] = hv

            mlflow.log_params(params)

            # 3. Log Performance Metrics
            mlflow.log_metrics({
                "accuracy": float(eval_metrics.get("accuracy", 0.0)),
                "precision": float(eval_metrics.get("precision", 0.0)),
                "recall": float(eval_metrics.get("recall", 0.0)),
                "f1_score": float(eval_metrics.get("f1_score", 0.0)),
                "roc_auc": float(eval_metrics.get("roc_auc", 0.0)),
                "training_time_seconds": float(execution_duration)
            })

            # 4. Log Evaluation Plot Artifacts
            if plot_paths:
                for plot_name, plot_path in plot_paths.items():
                    if os.path.exists(plot_path):
                        mlflow.log_artifact(plot_path, artifact_path="evaluation")

            # 5. Log Feature Importance CSV Artifact
            if feature_importance:
                fi_df = pd.DataFrame(list(feature_importance.items()), columns=["feature", "importance"])
                with tempfile.TemporaryDirectory() as tmp_dir:
                    fi_csv_path = os.path.join(tmp_dir, "feature_importance.csv")
                    fi_df.to_csv(fi_csv_path, index=False)
                    mlflow.log_artifact(fi_csv_path, artifact_path="evaluation")

            # 6. Log Complete Sklearn Pipeline Model Artifact
            if pipeline is not None:
                try:
                    mlflow.sklearn.log_model(pipeline, artifact_path="model", serialization_format="cloudpickle")
                except Exception:
                    try:
                        mlflow.sklearn.log_model(pipeline, artifact_path="model")
                    except Exception as e_mod:
                        logger.warning(f"Could not log model artifact for [{model_name}]: {e_mod}")

            logger.info(f"Logged MLflow run [{model_name}] -> Run ID: {run_id} | ROC_AUC: {eval_metrics.get('roc_auc')}")
            return run_id

    except Exception as e:
        logger.warning(f"Failed to log MLflow run for [{model_name}]: {e}")
        return None


def register_or_update_champion(
    all_runs_summary: List[Dict[str, Any]],
    experiment_name: str = DEFAULT_EXPERIMENT_NAME
) -> Optional[Dict[str, Any]]:
    """
    Identifies champion run by highest ROC AUC, tags run as champion, updates experiment tags,
    and registers champion model in local registry if supported.
    
    Args:
        all_runs_summary: List of run summary dicts containing model_name, run_id, roc_auc, pipeline.
        
    Returns:
        Optional[Dict[str, Any]]: Champion details.
    """
    if not all_runs_summary:
        return None

    try:
        # Sort by ROC_AUC descending
        sorted_runs = sorted(all_runs_summary, key=lambda x: x.get("roc_auc", 0.0), reverse=True)
        champion = sorted_runs[0]

        champion_model_name = champion["model_name"]
        champion_run_id = champion.get("run_id")
        champion_roc_auc = champion.get("roc_auc")

        logger.info(f"🏆 MLflow Champion Selected: [{champion_model_name}] (Run ID: {champion_run_id}) with ROC_AUC: {champion_roc_auc}")

        if champion_run_id:
            client = mlflow.tracking.MlflowClient()
            client.set_tag(champion_run_id, "champion", "true")
            client.set_tag(champion_run_id, "champion_model", champion_model_name)

            # Register model if supported
            try:
                model_uri = f"runs:/{champion_run_id}/model"
                reg_model = mlflow.register_model(model_uri, "RetailSense-Churn-Model")
                logger.info(f"Registered champion model in local MLflow registry: RetailSense-Churn-Model (Version: {reg_model.version})")
            except Exception as reg_err:
                logger.info(f"MLflow model registry note (tracking operational): {reg_err}")

        return champion

    except Exception as e:
        logger.warning(f"Failed to update MLflow champion: {e}")
        return None
