"""
Home Page - RetailSense-AI BI Dashboard
Executive Overview, Key Financial KPIs, Top Trends & Pipeline Health Status.
"""

import sys
import os

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import streamlit as st
from dashboard.utils import load_all_datasets, load_pipeline_reports, get_filtered_metrics, render_download_button
from dashboard.components.styles import apply_custom_styles
from dashboard.components.sidebar import render_sidebar
from dashboard.components.cards import render_executive_kpis, render_pipeline_status_card
from dashboard.components.charts import plot_monthly_revenue_trend, plot_revenue_by_country, plot_top_products

st.set_page_config(page_title="Home | RetailSense-AI", page_icon="🛍️", layout="wide")
apply_custom_styles()

# Load Datasets & Pipeline Reports
datasets = load_all_datasets()
metadata, quality = load_pipeline_reports()

# Render Sidebar & Get Active Filters
filters = render_sidebar(datasets, metadata)

# Header Section
st.markdown('<div class="page-title">🛍️ Executive Overview</div>', unsafe_allow_html=True)
st.markdown('<div class="page-subtitle">Real-time retail performance intelligence, global metrics, and MLOps health monitoring.</div>', unsafe_allow_html=True)
st.markdown('<div class="accent-line"></div>', unsafe_allow_html=True)

# Top Bar: Download Button & Active Filters Indicator
top_col1, top_col2 = st.columns([3, 1])
with top_col1:
    if filters["country"] != "All Countries" or len(filters["years"]) < 3:
        st.info(f"Filtering active: **Country**: {filters['country']} | **Years**: {filters['years']}")
with top_col2:
    df_download = datasets.get("processed") if datasets.get("processed") is not None else datasets.get("sales_summary")
    render_download_button(df_download, "retailsense_overview_data.csv", "📥 Export Page Data CSV")

st.markdown("<br>", unsafe_allow_html=True)

# 1. KPI Cards Grid
metrics = get_filtered_metrics(datasets, filters)
render_executive_kpis(metrics)

st.markdown("<br>", unsafe_allow_html=True)

# 2. Main Executive Charts Layout
df_filtered = metrics.get("df_filtered")
if df_filtered is None or df_filtered.empty:
    df_filtered = datasets.get("processed")

row1_col1, row1_col2 = st.columns([7, 5])

with row1_col1:
    fig_rev = plot_monthly_revenue_trend(df_filtered if df_filtered is not None else datasets.get("monthly_sales"))
    st.plotly_chart(fig_rev, use_container_width=True)

with row1_col2:
    fig_country = plot_revenue_by_country(df_filtered if df_filtered is not None else datasets.get("country_summary"), top_n=10)
    st.plotly_chart(fig_country, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# 3. Top Products & Pipeline Status Row
row2_col1, row2_col2 = st.columns([7, 5])

with row2_col1:
    fig_top_prod = plot_top_products(df_filtered if df_filtered is not None else datasets.get("products"), top_n=10)
    st.plotly_chart(fig_top_prod, use_container_width=True)

with row2_col2:
    st.markdown("### ⚙️ Pipeline Execution Status")
    if metadata:
        render_pipeline_status_card(metadata)
        st.markdown(
            f"""
            <div class="kpi-card" style="margin-top: 10px;">
                <div style="font-weight: 600; color: #94a3b8; margin-bottom: 8px;">Pipeline Data Summary</div>
                <div style="font-size: 0.9rem; color: #cbd5e1; display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
                    <div><strong>Rows Processed:</strong> {metadata.get('rows_processed', 'N/A'):,}</div>
                    <div><strong>Rows Removed:</strong> {metadata.get('rows_removed', 'N/A'):,}</div>
                    <div><strong>Rows Loaded:</strong> {metadata.get('rows_loaded', 'N/A'):,}</div>
                    <div><strong>Run ID:</strong> {metadata.get('pipeline_run_id', 'N/A')[:12]}...</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.warning("Pipeline metadata report not found. Run pipeline.py to generate execution metrics.")
