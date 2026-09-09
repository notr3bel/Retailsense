"""
Sales Page - RetailSense-AI BI Dashboard
Sales Performance Analytics, Temporal Breakdown, MoM Growth & Moving Averages.
"""

import streamlit as st
from dashboard.utils import load_all_datasets, load_pipeline_reports, apply_global_filters, render_download_button
from dashboard.components.styles import apply_custom_styles
from dashboard.components.sidebar import render_sidebar
from dashboard.components.charts import (
    plot_monthly_revenue_trend,
    plot_monthly_orders,
    plot_revenue_growth,
    plot_revenue_by_weekday,
    plot_revenue_by_hour,
    plot_moving_average_revenue
)

st.set_page_config(page_title="Sales Analytics | RetailSense-AI", page_icon="📈", layout="wide")
apply_custom_styles()

datasets = load_all_datasets()
metadata, quality = load_pipeline_reports()
filters = render_sidebar(datasets, metadata)

# Header Section
st.markdown('<div class="page-title">📈 Sales Analytics Deep Dive</div>', unsafe_allow_html=True)
st.markdown('<div class="page-subtitle">Temporal revenue distribution, order velocity, growth percentages, and moving trends.</div>', unsafe_allow_html=True)
st.markdown('<div class="accent-line"></div>', unsafe_allow_html=True)

# Apply filters
df_proc = datasets.get("processed")
df_filtered = apply_global_filters(df_proc, filters) if df_proc is not None else None

# Top Bar Export
top_col1, top_col2 = st.columns([3, 1])
with top_col1:
    st.write(f"Showing sales data for **{len(df_filtered):,}** records." if df_filtered is not None else "Using aggregated sales data.")
with top_col2:
    render_download_button(df_filtered if df_filtered is not None else datasets.get("monthly_sales"), "sales_analytics.csv", "📥 Download Sales CSV")

st.markdown("<br>", unsafe_allow_html=True)

# Row 1: Monthly Revenue & Monthly Orders
col1, col2 = st.columns(2)
with col1:
    fig_rev = plot_monthly_revenue_trend(df_filtered if df_filtered is not None else datasets.get("monthly_sales"))
    st.plotly_chart(fig_rev, use_container_width=True)

with col2:
    fig_orders = plot_monthly_orders(df_filtered if df_filtered is not None else datasets.get("monthly_sales"))
    st.plotly_chart(fig_orders, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# Row 2: Revenue Growth % & Moving Average Trend
col3, col4 = st.columns(2)
with col3:
    fig_growth = plot_revenue_growth(df_filtered if df_filtered is not None else datasets.get("monthly_sales"))
    st.plotly_chart(fig_growth, use_container_width=True)

with col4:
    fig_ma = plot_moving_average_revenue(df_filtered if df_filtered is not None else datasets.get("monthly_sales"), window=3)
    st.plotly_chart(fig_ma, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# Row 3: Revenue by Weekday & Revenue by Hour
col5, col6 = st.columns(2)
with col5:
    if df_filtered is not None and "weekday" in df_filtered.columns:
        fig_weekday = plot_revenue_by_weekday(df_filtered)
        st.plotly_chart(fig_weekday, use_container_width=True)
    else:
        st.info("Hourly & Weekday temporal breakdown requires full processed dataset.")

with col6:
    if df_filtered is not None and "hour" in df_filtered.columns:
        fig_hour = plot_revenue_by_hour(df_filtered)
        st.plotly_chart(fig_hour, use_container_width=True)
    else:
        st.info("Hourly sales velocity analysis requires processed dataset.")
