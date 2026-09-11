"""
Model Evaluation and Plot Generation Module for RetailSense-AI.
Calculates Accuracy, Precision, Recall, F1, ROC AUC, and generates evaluation plots.
"""

import os
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report,
    roc_curve,
    precision_recall_curve
)
from etl.utils import setup_logger, ensure_directory

logger = setup_logger("ML_Evaluate")

# Set Matplotlib dark aesthetics
plt.style.use("dark_background")


def evaluate_model(
    model: Any,
    X_test: np.ndarray,
    y_test: pd.Series,
    model_name: str
) -> Dict[str, Any]:
    """
    Evaluates a trained classifier on test data and returns comprehensive metrics.
    
    Args:
        model: Trained model instance.
        X_test: Test features.
        y_test: True test labels.
        model_name: Model display name.
        
    Returns:
        Dict[str, Any]: Evaluation metrics dictionary.
    """
    y_pred = model.predict(X_test)
    
    if hasattr(model, "predict_proba"):
        y_prob = model.predict_proba(X_test)[:, 1]
    elif hasattr(model, "decision_function"):
        y_prob = model.decision_function(X_test)
    else:
        y_prob = y_pred

    acc = round(float(accuracy_score(y_test, y_pred)), 4)
    prec = round(float(precision_score(y_test, y_pred, zero_division=0)), 4)
    rec = round(float(recall_score(y_test, y_pred, zero_division=0)), 4)
    f1 = round(float(f1_score(y_test, y_pred, zero_division=0)), 4)
    roc_auc = round(float(roc_auc_score(y_test, y_prob)), 4)

    cm = confusion_matrix(y_test, y_pred).tolist()
    clf_report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)

    metrics = {
        "model_name": model_name,
        "accuracy": acc,
        "precision": prec,
        "recall": rec,
        "f1_score": f1,
        "roc_auc": roc_auc,
        "confusion_matrix": cm,
        "classification_report": clf_report,
        "y_prob": y_prob
    }

    logger.info(f"Evaluated [{model_name}] -> ROC_AUC: {roc_auc}, Accuracy: {acc}, Precision: {prec}, Recall: {rec}, F1: {f1}")
    return metrics


def extract_feature_importance(
    model: Any,
    feature_names: List[str]
) -> Dict[str, float]:
    """
    Extracts and maps feature importance scores to feature names for tree-based or linear models.
    
    Returns:
        Dict[str, float]: Dictionary mapping feature names to importance values sorted descending.
    """
    importances = None
    if hasattr(model, "feature_importances_"):
        importances = model.feature_importances_
    elif hasattr(model, "coef_"):
        importances = np.abs(model.coef_[0])

    if importances is not None and len(importances) == len(feature_names):
        fi_df = pd.DataFrame({
            "feature": feature_names,
            "importance": importances
        }).sort_values("importance", ascending=False)
        
        # Convert to dictionary with rounded scores
        return {row["feature"]: round(float(row["importance"]), 6) for _, row in fi_df.iterrows()}
    return {}


def generate_plots(
    eval_results: Dict[str, Dict[str, Any]],
    best_model_name: str,
    best_model: Any,
    X_test: np.ndarray,
    y_test: pd.Series,
    feature_names: List[str],
    output_dir: str = "reports/plots"
) -> Tuple[Dict[str, str], Dict[str, float]]:
    """
    Generates and saves ROC Curve, Confusion Matrix, Precision-Recall Curve, and Feature Importance PNGs.
    
    Returns:
        Tuple[Dict[str, str], Dict[str, float]]: (map of plot paths, feature importance dict)
    """
    ensure_directory(os.path.join(output_dir, "placeholder.png"))
    plot_paths = {}

    # 1. ROC Curves Overlay Plot
    plt.figure(figsize=(8, 6))
    for name, res in eval_results.items():
        y_prob = res["y_prob"]
        fpr, tpr, _ = roc_curve(y_test, y_prob)
        plt.plot(fpr, tpr, label=f"{name} (AUC = {res['roc_auc']:.4f})", linewidth=2)

    plt.plot([0, 1], [0, 1], 'k--', alpha=0.6, label="Random Guess")
    plt.xlabel("False Positive Rate", color="#cbd5e1")
    plt.ylabel("True Positive Rate", color="#cbd5e1")
    plt.title("Model Comparison - ROC Curves (No Target Leakage)", fontsize=13, pad=12, color="#ffffff")
    plt.legend(loc="lower right", facecolor="#1e293b", edgecolor="none")
    plt.grid(True, alpha=0.15)
    plt.tight_layout()
    
    roc_path = os.path.join(output_dir, "roc_curve.png")
    plt.savefig(roc_path, dpi=150, bbox_inches="tight")
    plt.close()
    plot_paths["roc_curve"] = roc_path

    # 2. Confusion Matrix Heatmap (Best Model)
    best_metrics = eval_results[best_model_name]
    cm = np.array(best_metrics["confusion_matrix"])
    
    plt.figure(figsize=(6, 5))
    plt.imshow(cm, interpolation="nearest", cmap="Purples")
    plt.title(f"Confusion Matrix - {best_model_name}", fontsize=13, pad=12, color="#ffffff")
    plt.colorbar()

    tick_marks = np.arange(2)
    plt.xticks(tick_marks, ["Active (0)", "Churned (1)"], color="#cbd5e1")
    plt.yticks(tick_marks, ["Active (0)", "Churned (1)"], color="#cbd5e1")

    thresh = cm.max() / 2.
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            plt.text(j, i, f"{cm[i, j]:,}",
                     horizontalalignment="center",
                     color="white" if cm[i, j] > thresh else "#cbd5e1",
                     fontsize=14, fontweight="bold")

    plt.ylabel("True Label", color="#cbd5e1")
    plt.xlabel("Predicted Label", color="#cbd5e1")
    plt.tight_layout()
    
    cm_path = os.path.join(output_dir, "confusion_matrix.png")
    plt.savefig(cm_path, dpi=150, bbox_inches="tight")
    plt.close()
    plot_paths["confusion_matrix"] = cm_path

    # 3. Precision-Recall Curve (Best Model)
    y_prob_best = best_metrics["y_prob"]
    precision, recall, _ = precision_recall_curve(y_test, y_prob_best)
    
    plt.figure(figsize=(8, 6))
    plt.plot(recall, precision, color="#10b981", linewidth=2, label=f"{best_model_name}")
    plt.xlabel("Recall", color="#cbd5e1")
    plt.ylabel("Precision", color="#cbd5e1")
    plt.title(f"Precision-Recall Curve - {best_model_name}", fontsize=13, pad=12, color="#ffffff")
    plt.legend(loc="lower left", facecolor="#1e293b", edgecolor="none")
    plt.grid(True, alpha=0.15)
    plt.tight_layout()
    
    pr_path = os.path.join(output_dir, "precision_recall_curve.png")
    plt.savefig(pr_path, dpi=150, bbox_inches="tight")
    plt.close()
    plot_paths["precision_recall_curve"] = pr_path

    # 4. Feature Importance Plot (Best Model)
    feat_imp_dict = extract_feature_importance(best_model, feature_names)

    if feat_imp_dict:
        top_fi = list(feat_imp_dict.items())[:15]
        top_names = [item[0] for item in top_fi][::-1]
        top_scores = [item[1] for item in top_fi][::-1]

        plt.figure(figsize=(10, 6))
        plt.barh(top_names, top_scores, color="#6366f1")
        plt.xlabel("Feature Importance Score", color="#cbd5e1")
        plt.ylabel("Engineered Feature", color="#cbd5e1")
        plt.title(f"Top 15 Feature Importances - {best_model_name}", fontsize=13, pad=12, color="#ffffff")
        plt.grid(True, alpha=0.15, axis="x")
        plt.tight_layout()
        
        fi_path = os.path.join(output_dir, "feature_importance.png")
        plt.savefig(fi_path, dpi=150, bbox_inches="tight")
        plt.close()
        plot_paths["feature_importance"] = fi_path

    logger.info(f"Saved evaluation plots to directory: {output_dir}")
    return plot_paths, feat_imp_dict
