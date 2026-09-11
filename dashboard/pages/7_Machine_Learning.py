"""
Machine Learning Page - RetailSense-AI BI & AI Dashboard
Customer Churn Target Labeling, Model Benchmarking, MLflow Experiment Tracking, Champion Evaluation, and Feature Store.
"""

import sys
import os

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from dashboard.utils import (
    load_all_datasets,
    load_pipeline_reports,
    load_ml_datasets,
    load_model_evaluation_reports,
    render_download_button,
    apply_global_filters
)
from dashboard.components.styles import apply_custom_styles
from dashboard.components.sidebar import render_sidebar
from dashboard.components.cards import render_kpi_card, format_number
from dashboard.components.charts import DARK_LAYOUT, ACCENT_COLORS

st.set_page_config(page_title="Machine Learning | RetailSense-AI", page_icon="🤖", layout="wide")
apply_custom_styles()

# Load Datasets & Reports
datasets = load_all_datasets()
metadata, quality = load_pipeline_reports()
ml_data = load_ml_datasets()
metrics_df, eval_dict = load_model_evaluation_reports()
filters = render_sidebar(datasets, metadata)

# Header Section
st.markdown('<div class="page-title">🤖 Machine Learning & MLOps Tracking Engine</div>', unsafe_allow_html=True)
st.markdown('<div class="page-subtitle">MLflow experiment tracking, candidate benchmarking, champion model selection, diagnostic ROC/PR curves, and customer feature store.</div>', unsafe_allow_html=True)
st.markdown('<div class="accent-line"></div>', unsafe_allow_html=True)

# Datasets
churn_df = ml_data.get("churn_df")
churn_report = ml_data.get("churn_report", {})
features_df = ml_data.get("features_df")
feat_report = ml_data.get("feat_report", {})

# Apply Global Filters to Features if Country is selected
if features_df is not None and not features_df.empty:
    filtered_features = apply_global_filters(features_df, filters)
else:
    filtered_features = pd.DataFrame()

# Top Export Bar
top_col1, top_col2, top_col3, top_col4 = st.columns([2, 1, 1, 1])
with top_col1:
    num_f = feat_report.get("number_of_features", 27)
    num_c = len(filtered_features) if not filtered_features.empty else feat_report.get("total_customers", 0)
    st.write(f"Displaying **{num_c:,} customer profiles** with **{num_f} engineered ML features**.")
with top_col2:
    if features_df is not None and not features_df.empty:
        render_download_button(features_df, "customer_features.csv", "📥 Export Features")
with top_col3:
    if churn_df is not None and not churn_df.empty:
        render_download_button(churn_df, "customer_churn_dataset.csv", "📥 Export Churn CSV")
with top_col4:
    if metrics_df is not None and not metrics_df.empty:
        render_download_button(metrics_df, "model_metrics.csv", "📥 Export Metrics")

st.markdown("<br>", unsafe_allow_html=True)

# ============================================================================
# SECTION 1: BEST MODEL CARD & KPI BANNER
# ============================================================================

st.markdown("### 🏆 Champion Model Selection & Evaluation KPIs")

best_model_name = eval_dict.get("champion_model", eval_dict.get("best_model", "N/A"))
best_metrics = eval_dict.get("best_metrics", {})
champion_run_id = eval_dict.get("champion_run_id", "N/A")

# Extract metrics from eval_dict or fallback to top row in metrics_df
if not best_metrics and metrics_df is not None and not metrics_df.empty:
    top_row = metrics_df.sort_values(by="ROC_AUC", ascending=False).iloc[0]
    best_model_name = top_row["Model"]
    best_metrics = {
        "accuracy": top_row["Accuracy"],
        "precision": top_row["Precision"],
        "recall": top_row["Recall"],
        "f1_score": top_row["F1_Score"],
        "roc_auc": top_row["ROC_AUC"]
    }

def check_api_status() -> bool:
    try:
        import urllib.request
        req = urllib.request.Request("http://127.0.0.1:8000/health", headers={"User-Agent": "StreamlitDashboard"})
        with urllib.request.urlopen(req, timeout=1.0) as resp:
            return resp.status == 200
    except Exception:
        return False

api_online = check_api_status()
api_status_str = "🟢 FastAPI Server Online (http://127.0.0.1:8000)" if api_online else "⚪ FastAPI Server Offline (Launch: `uvicorn api.main:app --reload`)"

# Champion Highlight Banner & Target Leakage Notice
st.info(
    f"🥇 **Selected Champion Model:** `{best_model_name}` — Chosen based on highest test **ROC AUC**.\n\n"
    f"🧬 **MLflow Champion Run ID:** `{champion_run_id}` | **Experiment:** `RetailSense-Churn-Prediction`\n\n"
    f"⚡ **Model Serving API Status:** `{api_status_str}`\n\n"
    f"🛡️ **Target Leakage Safeguard:** `recency_days` was excluded from training inputs because churn was defined as `(recency_days >= 90)`."
)

col1, col2, col3, col4, col5 = st.columns(5)
acc = best_metrics.get("accuracy", 0.0)
prec = best_metrics.get("precision", 0.0)
rec = best_metrics.get("recall", 0.0)
f1 = best_metrics.get("f1_score", 0.0)
auc = best_metrics.get("roc_auc", 0.0)

render_kpi_card("Accuracy", f"{acc:.4f}", "Test Classification Accuracy", "🎯", col1)
render_kpi_card("Precision", f"{prec:.4f}", "Positive Predictive Value", "🔍", col2)
render_kpi_card("Recall", f"{rec:.4f}", "True Positive Rate (Sensitivity)", "⚡", col3)
render_kpi_card("F1 Score", f"{f1:.4f}", "Harmonic Mean (Prec & Rec)", "📊", col4)
render_kpi_card("ROC AUC", f"{auc:.4f}", "Area Under ROC Curve", "⭐", col5)

st.markdown("<br>", unsafe_allow_html=True)

# ============================================================================
# SECTION 2: MLFLOW EXPERIMENT TRACKING & BENCHMARK TABLE
# ============================================================================

comp_col1, comp_col2 = st.columns([3, 2])

with comp_col1:
    st.markdown("### 🧬 MLflow Experiment Benchmarking Runs")
    st.caption("Tracked runs in MLflow experiment `RetailSense-Churn-Prediction` (80/20 stratified split).")

    mlflow_runs = eval_dict.get("mlflow_runs", [])
    if mlflow_runs:
        runs_df = pd.DataFrame(mlflow_runs)
        st.dataframe(
            runs_df.style.highlight_max(subset=["roc_auc", "f1_score", "accuracy"], color="#065f46"),
            use_container_width=True,
            hide_index=True
        )
    elif metrics_df is not None and not metrics_df.empty:
        st.dataframe(
            metrics_df.style.highlight_max(subset=["ROC_AUC", "F1_Score", "Accuracy"], color="#065f46"),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.warning("No model metrics file found (`reports/model_metrics.csv`). Run `python -m ml.train` to generate benchmark.")

with comp_col2:
    st.markdown("### ⚙️ MLOps Artifacts & Local Tracking")
    st.caption("Local file store tracking URI & model deployment artifacts.")
    train_size = eval_dict.get("train_size", "N/A")
    test_size = eval_dict.get("test_size", "N/A")
    ds_size = eval_dict.get("dataset_size", "N/A")
    timestamp = eval_dict.get("training_timestamp", "N/A")
    excluded = eval_dict.get("excluded_features", ["customer_id", "recency_days", "churn", "first_purchase", "last_purchase"])

    st.write(f"- **MLflow Tracking URI**: `mlruns/` (Local File Store)")
    st.write(f"- **MLflow UI Launch**: `mlflow ui --port 5000`")
    st.write(f"- **Saved Model Pipeline**: `models/best_model.pkl` (joblib)")
    st.write(f"- **Saved Preprocessor**: `models/model_encoder.pkl` (joblib)")
    st.write(f"- **Train / Test Split**: `{train_size}` / `{test_size}` (80/20)")
    st.write(f"- **Excluded Features**: `{', '.join(excluded)}`")
    st.write(f"- **Training Timestamp**: `{timestamp}`")

st.markdown("<br>", unsafe_allow_html=True)

# ============================================================================
# SECTION 3: FEATURE IMPORTANCE & DIAGNOSTIC PLOTS
# ============================================================================

st.markdown("### 🔍 Model Interpretability & Diagnostic Plots")

plot_tab1, plot_tab2, plot_tab3, plot_tab4 = st.tabs([
    "⭐ Feature Importance", 
    "🎯 Confusion Matrix", 
    "📈 ROC Curve", 
    "📉 Precision-Recall Curve"
])

with plot_tab1:
    feat_imp_dict = eval_dict.get("feature_importance", {})
    if feat_imp_dict:
        fi_df = pd.DataFrame(list(feat_imp_dict.items()), columns=["Feature", "Importance"]).head(15)
        fi_df = fi_df.sort_values(by="Importance", ascending=True)

        fig_fi = px.bar(
            fi_df,
            x="Importance",
            y="Feature",
            orientation="h",
            title=f"Top 15 Feature Importances — {best_model_name}",
            color="Importance",
            color_continuous_scale="Viridis"
        )
        fig_fi.update_layout(
            xaxis_title="Importance Weight",
            yaxis_title="Feature Name",
            **DARK_LAYOUT
        )
        st.plotly_chart(fig_fi, use_container_width=True)
    elif os.path.exists("reports/plots/feature_importance.png"):
        st.image("reports/plots/feature_importance.png", caption="Feature Importance Chart", use_column_width=True)
    else:
        st.info("Feature importance data loading...")

with plot_tab2:
    if os.path.exists("reports/plots/confusion_matrix.png"):
        st.image("reports/plots/confusion_matrix.png", caption="Confusion Matrix — Champion Model", use_column_width=True)
    else:
        st.info("Confusion matrix image not found (`reports/plots/confusion_matrix.png`).")

with plot_tab3:
    if os.path.exists("reports/plots/roc_curve.png"):
        st.image("reports/plots/roc_curve.png", caption="Receiver Operating Characteristic (ROC) Curve", use_column_width=True)
    else:
        st.info("ROC curve image not found (`reports/plots/roc_curve.png`).")

with plot_tab4:
    if os.path.exists("reports/plots/precision_recall_curve.png"):
        st.image("reports/plots/precision_recall_curve.png", caption="Precision-Recall Curve", use_column_width=True)
    else:
        st.info("Precision-Recall curve image not found (`reports/plots/precision_recall_curve.png`).")

st.markdown("<br>", unsafe_allow_html=True)

# ============================================================================
# SECTION 4: CUSTOMER VALUE SEGMENTATION & CHURN DISTRIBUTION
# ============================================================================

st.markdown("### 📊 Customer Population & Segmentation Analytics")

df_plot = filtered_features if not filtered_features.empty else features_df

chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    if df_plot is not None and "customer_value_segment" in df_plot.columns:
        seg_counts = df_plot["customer_value_segment"].value_counts().reset_index()
        seg_counts.columns = ["segment", "count"]
        
        fig_seg = px.pie(
            seg_counts,
            values="count",
            names="segment",
            hole=0.45,
            title="🏷️ Customer Value Segments Distribution (Quartiles)",
            color="segment",
            color_discrete_sequence=["#a855f7", "#6366f1", "#3b82f6", "#94a3b8"]
        )
        fig_seg.update_traces(textinfo="percent+label", hovertemplate="<b>Segment:</b> %{label}<br><b>Customers:</b> %{value:,}<extra></extra>")
        fig_seg.update_layout(**DARK_LAYOUT)
        st.plotly_chart(fig_seg, use_container_width=True)
    else:
        st.info("Value segment feature not available.")

with chart_col2:
    if df_plot is not None and churn_df is not None and "customer_id" in df_plot.columns:
        merged_ml = pd.merge(df_plot, churn_df[["customer_id", "churn"]], on="customer_id", how="inner")
        merged_ml["churn_status"] = merged_ml["churn"].map({0: "Active", 1: "Churned"})
        
        fig_stack = px.histogram(
            merged_ml,
            x="customer_value_segment",
            color="churn_status",
            title="📊 Churn Rate by Customer Value Segment",
            color_discrete_map={"Active": "#10b981", "Churned": "#ef4444"},
            barmode="stack"
        )
        fig_stack.update_layout(
            xaxis_title="Value Segment",
            yaxis_title="Customer Count",
            **DARK_LAYOUT
        )
        st.plotly_chart(fig_stack, use_container_width=True)
    else:
        st.info("Churn vs segment correlation view loading...")

st.markdown("<br>", unsafe_allow_html=True)

# ============================================================================
# SECTION 5: FEATURE STORE DATA TABLE
# ============================================================================

st.markdown("### 📋 Machine Learning Feature Store Data Preview")
st.caption("Interactive feature table showing customer profiles, monetary velocity, product diversity, and temporal preferences.")

if df_plot is not None and not df_plot.empty:
    st.dataframe(
        df_plot.head(100),
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("Run python -m ml.train to generate the complete ML pipeline outputs.")
