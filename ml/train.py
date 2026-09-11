"""
Machine Learning Training Pipeline Module for RetailSense-AI.
Trains candidate classifiers without target leakage, compares ROC_AUC,
tracks experiments with MLflow, saves complete inference pipeline,
outputs metrics CSV/JSON reports, and generates visual plots.
"""

import os
import json
import joblib
import time
from datetime import datetime
from typing import Dict, Any, Tuple, List
import pandas as pd

from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier

from etl.utils import setup_logger, ensure_directory
from ml.model_utils import (
    load_and_merge_data,
    preprocess_and_split,
    EXCLUDED_FEATURES,
    LEAKAGE_NOTES
)
from ml.evaluate import evaluate_model, generate_plots, extract_feature_importance
from ml.mlflow_tracking import (
    setup_mlflow,
    log_model_run,
    register_or_update_champion,
    DEFAULT_EXPERIMENT_NAME
)

logger = setup_logger("ML_Train")


def run_training_pipeline(
    features_path: str = "data/ml/customer_features.csv",
    churn_path: str = "data/ml/customer_churn_dataset.csv",
    models_dir: str = "models",
    reports_dir: str = "reports"
) -> Dict[str, Any]:
    """
    Executes end-to-end model training, evaluation, comparison, selection, MLflow experiment tracking,
    and local artifact persistence. Target-leaking features (recency_days) are strictly excluded.
    
    Args:
        features_path: Path to customer_features.csv.
        churn_path: Path to customer_churn_dataset.csv.
        models_dir: Directory where best_model.pkl & model_encoder.pkl will be saved.
        reports_dir: Directory where model_metrics.csv & model_evaluation.json will be saved.
        
    Returns:
        Dict[str, Any]: Training summary including best model metrics, MLflow run metadata, and file paths.
    """
    start_time = datetime.now()
    logger.info("==================================================")
    logger.info("Starting RetailSense-AI ML Model Training Pipeline")
    logger.info("==================================================")

    # 1. Initialize MLflow Experiment Tracking (Graceful fallback if service offline)
    mlflow_active, exp_id = setup_mlflow(experiment_name=DEFAULT_EXPERIMENT_NAME)

    # 2. Load Merged Features & Target Data
    df_merged = load_and_merge_data(features_path=features_path, churn_path=churn_path)
    dataset_size = len(df_merged)
    churn_counts = df_merged["churn"].value_counts().to_dict()
    target_distribution = {
        "active_0": int(churn_counts.get(0, 0)),
        "churned_1": int(churn_counts.get(1, 0)),
        "churn_rate_pct": round(float(churn_counts.get(1, 0) / dataset_size * 100), 2) if dataset_size > 0 else 0.0
    }

    # 3. Preprocess & Split (Excludes recency_days & target-leaking columns)
    (
        X_train, X_test, y_train, y_test,
        preprocessor, feature_names, original_model_features, excluded_features
    ) = preprocess_and_split(df_merged, test_size=0.2, random_state=42)

    train_size = len(X_train)
    test_size = len(X_test)
    num_encoded_features = len(feature_names)

    dataset_metadata = {
        "dataset_size": dataset_size,
        "train_size": train_size,
        "test_size": test_size,
        "original_feature_count": len(df_merged.columns),
        "encoded_feature_count": num_encoded_features,
        "excluded_features": excluded_features,
        "final_model_features": original_model_features,
        "target_distribution": target_distribution
    }

    # 4. Instantiate Candidate Classifiers
    candidate_models = {
        "Logistic Regression": LogisticRegression(max_iter=1000, random_state=42),
        "Random Forest": RandomForestClassifier(n_estimators=100, random_state=42),
        "XGBoost": XGBClassifier(n_estimators=100, random_state=42, eval_metric="logloss")
    }

    eval_results = {}
    metrics_list = []
    runs_summary = []

    # 5. Train, Evaluate, and Track Each Model with MLflow
    for name, model in candidate_models.items():
        logger.info(f"Training [{name}] model...")
        model_start = time.time()
        model.fit(X_train, y_train)
        duration = round(time.time() - model_start, 2)
        
        # Exact evaluation metrics computation
        res = evaluate_model(model, X_test, y_test, model_name=name)
        eval_results[name] = res

        # Build complete model pipeline for artifact logging
        candidate_pipeline = Pipeline(steps=[
            ("preprocessor", preprocessor),
            ("classifier", model)
        ])

        # Extract feature importance dict if model supports it
        fi_dict = extract_feature_importance(model, feature_names)

        # Temp plot paths for MLflow run artifact logging
        plots_dir = os.path.join(reports_dir, "plots")
        temp_plots, _ = generate_plots(
            eval_results={name: res},
            best_model_name=name,
            best_model=model,
            X_test=X_test,
            y_test=y_test,
            feature_names=feature_names,
            output_dir=plots_dir
        )

        # Log MLflow Run
        run_id = None
        if mlflow_active:
            run_id = log_model_run(
                model_name=name,
                model=model,
                pipeline=candidate_pipeline,
                eval_metrics=res,
                dataset_metadata=dataset_metadata,
                plot_paths=temp_plots,
                feature_importance=fi_dict,
                execution_duration=duration
            )

        metrics_list.append({
            "Model": name,
            "Accuracy": res["accuracy"],
            "Precision": res["precision"],
            "Recall": res["recall"],
            "F1_Score": res["f1_score"],
            "ROC_AUC": res["roc_auc"]
        })

        runs_summary.append({
            "model_name": name,
            "run_id": run_id,
            "roc_auc": res["roc_auc"],
            "accuracy": res["accuracy"],
            "precision": res["precision"],
            "recall": res["recall"],
            "f1_score": res["f1_score"],
            "pipeline": candidate_pipeline
        })

    # 6. Model Comparison & Champion Model Selection (Based strictly on ROC_AUC)
    df_metrics = pd.DataFrame(metrics_list).sort_values(by="ROC_AUC", ascending=False).reset_index(drop=True)
    best_model_name = df_metrics.iloc[0]["Model"]
    best_classifier = candidate_models[best_model_name]
    best_metrics = eval_results[best_model_name]
    best_run = next((r for r in runs_summary if r["model_name"] == best_model_name), {})
    best_run_id = best_run.get("run_id")

    logger.info(f"🏆 Champion Model Selected: [{best_model_name}] with ROC_AUC: {best_metrics['roc_auc']}")

    # Build full Sklearn Pipeline containing preprocessor + champion classifier
    best_full_pipeline = Pipeline(steps=[
        ("preprocessor", preprocessor),
        ("classifier", best_classifier)
    ])

    # Update MLflow Champion Metadata & Model Registration
    if mlflow_active:
        register_or_update_champion(runs_summary, experiment_name=DEFAULT_EXPERIMENT_NAME)

    # 7. Save Standalone Local Model Artifacts
    ensure_directory(os.path.join(models_dir, "placeholder.pkl"))
    best_model_path = os.path.join(models_dir, "best_model.pkl")
    encoder_path = os.path.join(models_dir, "model_encoder.pkl")

    joblib.dump(best_full_pipeline, best_model_path)
    joblib.dump({
        "preprocessor": preprocessor,
        "feature_names": feature_names,
        "original_features": original_model_features,
        "excluded_features": excluded_features,
        "best_model_name": best_model_name,
        "best_run_id": best_run_id
    }, encoder_path)

    logger.info(f"Saved complete Sklearn pipeline to: {best_model_path}")
    logger.info(f"Saved model preprocessor metadata to: {encoder_path}")

    # 8. Generate & Save Overall Visual Evaluation Plots
    plots_dir = os.path.join(reports_dir, "plots")
    plot_paths, feat_imp_dict = generate_plots(
        eval_results=eval_results,
        best_model_name=best_model_name,
        best_model=best_classifier,
        X_test=X_test,
        y_test=y_test,
        feature_names=feature_names,
        output_dir=plots_dir
    )

    # 9. Save Comparison CSV & Enhanced Evaluation JSON Reports
    ensure_directory(os.path.join(reports_dir, "placeholder.json"))
    csv_metrics_path = os.path.join(reports_dir, "model_metrics.csv")
    json_eval_path = os.path.join(reports_dir, "model_evaluation.json")

    df_metrics.to_csv(csv_metrics_path, index=False)
    logger.info(f"Saved model comparison table to: {csv_metrics_path}")

    eval_json = {
        "experiment_name": DEFAULT_EXPERIMENT_NAME,
        "champion_model": best_model_name,
        "champion_run_id": best_run_id or "N/A",
        "champion_roc_auc": best_metrics["roc_auc"],
        "best_model": best_model_name,
        "best_metrics": {
            "accuracy": best_metrics["accuracy"],
            "precision": best_metrics["precision"],
            "recall": best_metrics["recall"],
            "f1_score": best_metrics["f1_score"],
            "roc_auc": best_metrics["roc_auc"]
        },
        "model_metrics": metrics_list,
        "all_models_metrics": metrics_list,
        "mlflow_runs": [
            {
                "model": r["model_name"],
                "run_id": r["run_id"] or "N/A",
                "accuracy": r["accuracy"],
                "precision": r["precision"],
                "recall": r["recall"],
                "f1_score": r["f1_score"],
                "roc_auc": r["roc_auc"]
            }
            for r in runs_summary
        ],
        "training_timestamp": datetime.now().astimezone().isoformat(),
        "dataset_size": dataset_size,
        "train_size": train_size,
        "test_size": test_size,
        "original_feature_count": len(df_merged.columns),
        "excluded_features": excluded_features,
        "final_model_features": original_model_features,
        "encoded_feature_count": num_encoded_features,
        "encoded_feature_names": feature_names,
        "feature_importance": feat_imp_dict,
        "confusion_matrix": best_metrics["confusion_matrix"],
        "target_distribution": target_distribution,
        "preprocessing_summary": (
            "StandardScaler applied to numeric behavioral features; "
            "OneHotEncoder(handle_unknown='ignore') applied to categorical variables. "
            "Preprocessor fitted strictly on training data split (80/20)."
        ),
        "leakage_prevention_notes": LEAKAGE_NOTES,
        "execution_duration_seconds": round((datetime.now() - start_time).total_seconds(), 2)
    }

    with open(json_eval_path, "w", encoding="utf-8") as f:
        json.dump(eval_json, f, indent=4)

    logger.info(f"Saved model evaluation JSON report to: {json_eval_path}")

    summary = {
        "experiment_name": DEFAULT_EXPERIMENT_NAME,
        "best_model_name": best_model_name,
        "champion_run_id": best_run_id,
        "best_roc_auc": best_metrics["roc_auc"],
        "best_accuracy": best_metrics["accuracy"],
        "best_model_path": best_model_path,
        "encoder_path": encoder_path,
        "csv_metrics_path": csv_metrics_path,
        "json_eval_path": json_eval_path,
        "plot_paths": plot_paths,
        "excluded_features": excluded_features,
        "runs_summary": runs_summary
    }

    logger.info("==================================================")
    logger.info("ML Model Training Pipeline Completed Successfully!")
    logger.info("==================================================")
    return summary


if __name__ == "__main__":
    run_training_pipeline()
