# MLflow Experiment Tracking Architecture — RetailSense-AI

This document provides technical documentation for the **MLflow Experiment Tracking** module in **RetailSense-AI**.

---

## 🏛️ MLOps Architecture & Role of MLflow

In the **RetailSense-AI** enterprise MLOps workflow, **MLflow** acts as the central experiment tracking and model registry store.

```text
data/ml/customer_features.csv
            │
            ▼
┌───────────────────────────────────────┐
│       ml.model_utils                  │  ◄── Excludes Target Leakage (recency_days)
│ (ColumnTransformer & Train/Test Split)│  ◄── Fits ONLY on Training Split (80/20)
└───────────────────┬───────────────────┘
                    │
                    ▼
┌───────────────────────────────────────┐
│        ml.train Pipeline              │
│ (Logistic Reg, Random Forest, XGBoost)│
└───────────┬───────────────┬───────────┘
            │               │
            ▼               ▼
┌───────────────────────┐ ┌──────────────────────────────────────┐
│ Local Disk Persistence│ │ MLflow Local Experiment Store        │
│  - models/best_model.  │ │  - Tracking URI: mlruns/             │
│    pkl (Pipeline)     │ │  - Experiment:                       │
│  - reports/           │ │    RetailSense-Churn-Prediction      │
│    model_metrics.csv  │ │  - Tracked Runs: LR, RF, XGBoost     │
│  - reports/           │ │  - Logged Metrics, Params, Plots     │
│    model_evaluation.  │ │  - Logged Sklearn Pipeline Model     │
│    json               │ │  - Model Registry:                   │
└───────────────────────┘ │    RetailSense-Churn-Model          │
                          └──────────────────────────────────────┘
```

---

## 🚀 Key Specifications

- **Experiment Name**: `RetailSense-Churn-Prediction`
- **Tracking URI**: `mlruns/` (Project-relative local file store)
- **Model Registry Name**: `RetailSense-Churn-Model`
- **Champion Selection Metric**: `ROC AUC` (Highest score selected)
- **Champion Model**: `XGBoost Classifier` (`ROC_AUC`: `0.9666`, `Accuracy`: `90.05%`)

---

## 📊 Tracked Metadata per Run

For every candidate model run (`Logistic Regression`, `Random Forest`, `XGBoost`), MLflow automatically tracks:

### 1. Parameters & Hyperparameters
- `model_name`: Candidate model string identifier.
- `random_state`: `42`
- `test_size`: `0.2` (80% train / 20% test split)
- `total_samples`: Total dataset rows (`5,878`)
- `training_samples`: Training split rows (`4,702`)
- `test_samples`: Test split rows (`1,176`)
- `feature_count_before_encoding`: `23` original behavioral features
- `feature_count_after_encoding`: `76` one-hot / scaled feature dimensions
- Model-specific hyperparameters:
  - **Logistic Regression**: `hp_C`, `hp_max_iter`, `hp_solver`, `hp_penalty`
  - **Random Forest**: `hp_n_estimators`, `hp_max_depth`, `hp_min_samples_split`, `hp_min_samples_leaf`
  - **XGBoost**: `hp_n_estimators`, `hp_max_depth`, `hp_learning_rate`, `hp_subsample`, `hp_colsample_bytree`

### 2. Tags
- `project`: `RetailSense-AI`
- `task`: `customer_churn_prediction`
- `target`: `churn`
- `selection_metric`: `roc_auc`
- `dataset_name`: `customer_features.csv`
- `excluded_from_training`: `recency_days, customer_id, churn, first_purchase, last_purchase, favorite_product`

### 3. Evaluation Metrics
- `accuracy`: Overall test correctness ratio
- `precision`: Positive predictive value
- `recall`: Sensitivity / True positive rate
- `f1_score`: Harmonic mean of precision and recall
- `roc_auc`: Area under receiver operating characteristic curve
- `training_time_seconds`: Model execution duration

### 4. Logged Artifacts
- `evaluation/confusion_matrix.png`: 2x2 confusion matrix plot.
- `evaluation/roc_curve.png`: ROC curve plot.
- `evaluation/precision_recall_curve.png`: PR curve plot.
- `evaluation/feature_importance.csv`: Feature names and importances.
- `model/`: Complete Scikit-Learn `Pipeline` artifact (ColumnTransformer + Classifier).

---

## 🛡️ Target Leakage Safeguard

`recency_days` is strictly excluded from model training feature matrix $X$ because customer churn was defined as `(recency_days >= 90)`. 
Including `recency_days` causes direct target leakage and artificially perfect scores (ROC AUC 1.0).

Excluding `recency_days` ensures models learn genuine customer behavioral patterns (spending velocity, order frequency, basket size, category diversity).

---

## 🖥️ Launching the MLflow User Interface

Developers can inspect experiment runs, compare metric curves, view logged artifacts, and audit parameters via the local MLflow UI:

```bash
# 1. Ensure virtual environment is active
# 2. Run model training pipeline to log runs to mlruns/
python -m ml.train

# 3. Launch local MLflow UI server
mlflow ui --port 5000
```

Open your browser to: **`http://localhost:5000`**

---

## ⚙️ Standalone Artifact Compatibility

The local serialized artifact [`models/best_model.pkl`](file:///d:/Projects/Retailsense/models/best_model.pkl) contains the complete Scikit-Learn `Pipeline`. It operates standalone and performs predictions (`pipeline.predict(X_sample)`) without requiring an active MLflow server process.
