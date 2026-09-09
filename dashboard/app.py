"""
RetailSense-AI Streamlit Dashboard Main Entry Point.
Production-Quality Multi-Page BI & MLOps Intelligence System.
"""

import streamlit as st
from dashboard.utils import load_all_datasets, load_pipeline_reports, get_filtered_metrics
from dashboard.components.styles import apply_custom_styles
from dashboard.components.sidebar import render_sidebar
from dashboard.components.cards import render_executive_kpis

st.set_page_config(
    page_title="RetailSense-AI | Enterprise BI Dashboard",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply Dark BI Aesthetic Styling
apply_custom_styles()

# Load Datasets & Metadata
datasets = load_all_datasets()
metadata, quality = load_pipeline_reports()

# Render Global Sidebar Navigation & Filters
filters = render_sidebar(datasets, metadata)

# Main Title & Subtitle
st.markdown('<div class="page-title">🛍️ RetailSense-AI Enterprise Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="page-subtitle">End-to-End MLOps Retail Intelligence Platform — Sales, Customer, Product & Data Operations</div>', unsafe_allow_html=True)
st.markdown('<div class="accent-line"></div>', unsafe_allow_html=True)

# Render Global KPI Summary Cards
metrics = get_filtered_metrics(datasets, filters)
render_executive_kpis(metrics)

st.markdown("<br>", unsafe_allow_html=True)

# Navigation Feature Cards Grid
st.markdown("### 🧭 Dashboard Sections")

nav_col1, nav_col2, nav_col3 = st.columns(3)

with nav_col1:
    st.markdown(
        """
        <div class="kpi-card">
            <h3>📊 1. Home Overview</h3>
            <p style="color: #94a3b8; font-size: 0.9rem;">High-level executive financial metrics, top-performing product leaderboards, global revenue distribution, and pipeline health alerts.</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown(
        """
        <div class="kpi-card" style="margin-top: 16px;">
            <h3>👥 4. Customer Analytics</h3>
            <p style="color: #94a3b8; font-size: 0.9rem;">Customer lifetime value (CLV) distributions, RFM segmentation scatter plots, repeat vs one-time buyers ratio, and average basket sizes.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

with nav_col2:
    st.markdown(
        """
        <div class="kpi-card">
            <h3>📈 2. Sales Analytics</h3>
            <p style="color: #94a3b8; font-size: 0.9rem;">Temporal sales velocity, order volumes, Month-over-Month revenue growth percentages, weekday/hourly peak traffic, and 3-month moving averages.</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown(
        """
        <div class="kpi-card" style="margin-top: 16px;">
            <h3>🌍 5. Country Intelligence</h3>
            <p style="color: #94a3b8; font-size: 0.9rem;">Global revenue heatmap choropleth, order volumes by country, international customer density, and market breakdown table.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

with nav_col3:
    st.markdown(
        """
        <div class="kpi-card">
            <h3>🛍️ 3. Product Intelligence</h3>
            <p style="color: #94a3b8; font-size: 0.9rem;">Product revenue leaderboards, category share donut charts, quantity sold metrics, and Pareto 80/20 cumulative revenue analysis.</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown(
        """
        <div class="kpi-card" style="margin-top: 16px;">
            <h3>⚙️ 6. MLOps Pipeline & DQ</h3>
            <p style="color: #94a3b8; font-size: 0.9rem;">Airflow DAG execution status, data validation reports, row cleanliness gauges, schema audit tables, and task timeline Gantt charts.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

st.markdown("<br>", unsafe_allow_html=True)
st.info("👈 Use the left sidebar to navigate between pages and apply global filters across Country, Year, and Month.")
