"""
Customer Page - RetailSense-AI BI Dashboard
Customer Lifetime Value, RFM Segmentation, Repeat vs. One-Time Buyers & Basket Metrics.
"""

import streamlit as st
from dashboard.utils import load_all_datasets, load_pipeline_reports, apply_global_filters, render_download_button
from dashboard.components.styles import apply_custom_styles
from dashboard.components.sidebar import render_sidebar
from dashboard.components.charts import (
    plot_top_customers,
    plot_clv_distribution,
    plot_repeat_vs_new,
    plot_avg_basket_size,
    plot_rfm_summary
)

st.set_page_config(page_title="Customer Analytics | RetailSense-AI", page_icon="👥", layout="wide")
apply_custom_styles()

datasets = load_all_datasets()
metadata, quality = load_pipeline_reports()
filters = render_sidebar(datasets, metadata)

# Header Section
st.markdown('<div class="page-title">👥 Customer Analytics & Behavior</div>', unsafe_allow_html=True)
st.markdown('<div class="page-subtitle">Customer lifetime value (CLV), repeat purchase ratios, RFM segmentation, and basket dynamics.</div>', unsafe_allow_html=True)
st.markdown('<div class="accent-line"></div>', unsafe_allow_html=True)

df_cust = datasets.get("customers")
df_proc = datasets.get("processed")
df_filtered = apply_global_filters(df_proc, filters) if df_proc is not None else None

# Top Bar Export
top_col1, top_col2 = st.columns([3, 1])
with top_col1:
    st.write(f"Customer metrics synthesized from Gold profiles & transactional logs.")
with top_col2:
    render_download_button(df_cust if df_cust is not None else df_filtered, "customer_analytics.csv", "📥 Download Customers CSV")

st.markdown("<br>", unsafe_allow_html=True)

# Row 1: Top Customers & Repeat vs New
col1, col2 = st.columns(2)
with col1:
    fig_top_c = plot_top_customers(df_cust if df_cust is not None else df_filtered, top_n=10)
    st.plotly_chart(fig_top_c, use_container_width=True)

with col2:
    fig_repeat = plot_repeat_vs_new(df_cust if df_cust is not None else df_filtered)
    st.plotly_chart(fig_repeat, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# Row 2: Customer Lifetime Value (CLV) & Average Basket Size
col3, col4 = st.columns(2)
with col3:
    fig_clv = plot_clv_distribution(df_cust if df_cust is not None else df_filtered)
    st.plotly_chart(fig_clv, use_container_width=True)

with col4:
    fig_basket = plot_avg_basket_size(df_cust if df_cust is not None else df_filtered)
    st.plotly_chart(fig_basket, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# Row 3: RFM Segmentation Scatter Summary
st.markdown("### 🎯 RFM Segmentation (Frequency vs Monetary Value)")
st.caption("Maps customers based on order frequency and lifetime spend to identify VIP vs At-Risk segments.")
fig_rfm = plot_rfm_summary(df_cust if df_cust is not None else df_filtered)
st.plotly_chart(fig_rfm, use_container_width=True)
