"""
Country Page - RetailSense-AI BI Dashboard
Geographical Revenue Intelligence, International Order Volumes & Country Market Rankings.
"""

import sys
import os

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import streamlit as st
import pandas as pd
from dashboard.utils import load_all_datasets, load_pipeline_reports, apply_global_filters, render_download_button
from dashboard.components.styles import apply_custom_styles
from dashboard.components.sidebar import render_sidebar
from dashboard.components.charts import (
    plot_country_map,
    plot_revenue_by_country,
    plot_orders_by_country,
    plot_customers_by_country
)

st.set_page_config(page_title="Country Analytics | RetailSense-AI", page_icon="🌍", layout="wide")
apply_custom_styles()

datasets = load_all_datasets()
metadata, quality = load_pipeline_reports()
filters = render_sidebar(datasets, metadata)

# Header Section
st.markdown('<div class="page-title">🌍 Geographical Market Intelligence</div>', unsafe_allow_html=True)
st.markdown('<div class="page-subtitle">Global revenue distribution map, country-wise order volumes, and international customer density.</div>', unsafe_allow_html=True)
st.markdown('<div class="accent-line"></div>', unsafe_allow_html=True)

df_country = datasets.get("country_summary")
df_proc = datasets.get("processed")
df_filtered = apply_global_filters(df_proc, filters) if df_proc is not None else None

# Build a country summary from the filtered transaction data.
# The Gold country_summary dataset is unfiltered, so we must
# recompute these metrics when dashboard filters are active.
if df_filtered is not None and not df_filtered.empty:
    df_country_filtered = (
        df_filtered.groupby("country")
        .agg(
            customers=("customer_id", "nunique"),
            total_orders=("invoice_no", "nunique"),
            total_quantity=("quantity", "sum"),
            total_revenue=("total_price", "sum")
        )
        .reset_index()
    )
else:
    df_country_filtered = df_country

# Top Bar Export
top_col1, top_col2 = st.columns([3, 1])
with top_col1:
    num_c = df_country_filtered["country"].nunique() if df_country_filtered is not None else 0
    st.write(f"Global retail footprint across **{num_c} international markets**.")
with top_col2:
    render_download_button(
    df_country_filtered if df_country_filtered is not None else df_filtered,
    "country_summary.csv",
    "📥 Download Country CSV"
)

st.markdown("<br>", unsafe_allow_html=True)

# Row 1: Global Revenue Map
st.markdown("### 🗺️ Global Revenue Heatmap")
fig_map = plot_country_map(df_filtered if df_filtered is not None else df_country)
st.plotly_chart(fig_map, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# Row 2: Revenue by Country & Orders by Country
col1, col2 = st.columns(2)
with col1:
    fig_rev_c = plot_revenue_by_country(df_filtered if df_filtered is not None else df_country, top_n=10)
    st.plotly_chart(fig_rev_c, use_container_width=True)

with col2:
    fig_ord_c = plot_orders_by_country(df_filtered if df_filtered is not None else df_country, top_n=10)
    st.plotly_chart(fig_ord_c, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# Row 3: Customers by Country & Country Summary Table
col3, col4 = st.columns([6, 6])
with col3:
    fig_cust_c = plot_customers_by_country(df_filtered if df_filtered is not None else df_country, top_n=10)
    st.plotly_chart(fig_cust_c, use_container_width=True)

with col4:
    st.markdown("### 📋 Top International Markets Breakdown")
    if df_country_filtered is not None and not df_country_filtered.empty:
        df_display = df_country_filtered.sort_values(
            "total_revenue",
            ascending=False
        ).head(10).copy()
        df_display["total_revenue"] = df_display["total_revenue"].apply(lambda x: f"${x:,.2f}")
        df_display["total_orders"] = df_display["total_orders"].apply(lambda x: f"{x:,}")
        df_display["total_quantity"] = df_display["total_quantity"].apply(lambda x: f"{x:,}")
        st.dataframe(
            df_display,
            column_config={
                "country": "Country",
                "customers": "Customers",
                "total_orders": "Total Orders",
                "total_quantity": "Units Sold",
                "total_revenue": "Revenue"
            },
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Country summary dataset not available.")
