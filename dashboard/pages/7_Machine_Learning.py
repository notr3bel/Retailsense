"""
Machine Learning Page - RetailSense-AI BI & AI Dashboard
Customer Churn Labeling, 28 Engineered Features, Value Segmentation & Feature Store Metrics.
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
    render_download_button,
    apply_global_filters
)
from dashboard.components.styles import apply_custom_styles
from dashboard.components.sidebar import render_sidebar
from dashboard.components.cards import render_kpi_card, format_number
from dashboard.components.charts import DARK_LAYOUT, ACCENT_COLORS

st.set_page_config(page_title="Machine Learning | RetailSense-AI", page_icon="🤖", layout="wide")
apply_custom_styles()

# Load Datasets
datasets = load_all_datasets()
metadata, quality = load_pipeline_reports()
ml_data = load_ml_datasets()
filters = render_sidebar(datasets, metadata)

# Header Section
st.markdown('<div class="page-title">🤖 Machine Learning & Customer Feature Store</div>', unsafe_allow_html=True)
st.markdown('<div class="page-subtitle">Customer churn target labels, 28 engineered ML features, value segmentation, and feature distributions.</div>', unsafe_allow_html=True)
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
top_col1, top_col2, top_col3 = st.columns([2, 1, 1])
with top_col1:
    num_f = feat_report.get("number_of_features", 27)
    num_c = len(filtered_features) if not filtered_features.empty else feat_report.get("total_customers", 0)
    st.write(f"Displaying **{num_c:,} customer profiles** with **{num_f} engineered ML features**.")
with top_col2:
    if features_df is not None and not features_df.empty:
        render_download_button(features_df, "customer_features.csv", "📥 Export Features CSV")
with top_col3:
    if churn_df is not None and not churn_df.empty:
        render_download_button(churn_df, "customer_churn_dataset.csv", "📥 Export Churn CSV")

st.markdown("<br>", unsafe_allow_html=True)

# 1. KPI Cards Row
col1, col2, col3, col4, col5 = st.columns(5)

tot_cust = churn_report.get("total_customers", len(churn_df) if churn_df is not None else 0)
act_cust = churn_report.get("active_customers", int((churn_df["churn"] == 0).sum()) if churn_df is not None else 0)
chu_cust = churn_report.get("churned_customers", int((churn_df["churn"] == 1).sum()) if churn_df is not None else 0)
rate_str = churn_report.get("churn_rate_pct", f"{round(chu_cust / tot_cust * 100, 2)}%" if tot_cust > 0 else "0.0%")
num_feats = feat_report.get("number_of_features", 27)

render_kpi_card("Total Customers", format_number(tot_cust), "ML Dataset Population", "👥", col1)
render_kpi_card("Active Customers", format_number(act_cust), "Recent Buyers (<90d)", "🟢", col2)
render_kpi_card("Churned Customers", format_number(chu_cust), "Inactive Buyers (>=90d)", "🔴", col3)
render_kpi_card("Churn Rate", rate_str, "90-Day Inactivity Rule", "📉", col4)
render_kpi_card("Engineered Features", str(num_feats), "Profile, Order, Recency, RFM", "⚙️", col5)

st.markdown("<br>", unsafe_allow_html=True)

# 2. Charts Row 1: Value Segments & Churn Breakdown
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

# 3. Charts Row 2: Lifetime, Recency & Revenue Distributions
chart_col3, chart_col4 = st.columns(2)

with chart_col3:
    if df_plot is not None and "customer_lifetime_days" in df_plot.columns:
        fig_life = px.histogram(
            df_plot,
            x="customer_lifetime_days",
            nbins=40,
            title="⏱️ Customer Lifetime Distribution (Days)",
            color_discrete_sequence=["#6366f1"]
        )
        fig_life.update_layout(
            xaxis_title="Lifetime (Days)",
            yaxis_title="Customer Count",
            **DARK_LAYOUT
        )
        st.plotly_chart(fig_life, use_container_width=True)

with chart_col4:
    if df_plot is not None and "recency_days" in df_plot.columns:
        fig_rec = px.histogram(
            df_plot,
            x="recency_days",
            nbins=40,
            title="📅 Recency Days Distribution (Inactivity)",
            color_discrete_sequence=["#f59e0b"]
        )
        fig_rec.add_vline(x=90, line_dash="dash", line_color="#ef4444", annotation_text="90d Churn Boundary")
        fig_rec.update_layout(
            xaxis_title="Days Since Last Purchase",
            yaxis_title="Customer Count",
            **DARK_LAYOUT
        )
        st.plotly_chart(fig_rec, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# 4. Feature Table Data Preview
st.markdown("### 📋 Machine Learning Feature Store Data Table")
st.caption("Interactive feature table showing customer profiles, monetary velocity, product diversity, and temporal preferences.")

if df_plot is not None and not df_plot.empty:
    st.dataframe(
        df_plot.head(100),
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("Run python -m ml.feature_engineering to generate the feature store dataset.")

st.markdown("<br>", unsafe_allow_html=True)

# 5. Feature List & Report Metadata Accordion
with st.expander("ℹ️ View Feature Store Metadata & Report Details"):
    meta_col1, meta_col2 = st.columns(2)
    with meta_col1:
        st.markdown("#### Feature Store Audit Summary")
        st.write(f"- **Total Customers**: `{feat_report.get('total_customers', 0):,}`")
        st.write(f"- **Total Columns**: `{feat_report.get('total_columns', 28)}`")
        st.write(f"- **Engineered Features**: `{feat_report.get('number_of_features', 27)}`")
        st.write(f"- **Generation Timestamp**: `{feat_report.get('generation_timestamp', 'N/A')}`")
    
    with meta_col2:
        st.markdown("#### Engineered Feature List")
        f_list = feat_report.get("feature_names", list(df_plot.columns) if df_plot is not None else [])
        st.code(", ".join(f_list), language="markdown")
