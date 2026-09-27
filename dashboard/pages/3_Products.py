"""
Product Page - RetailSense-AI BI Dashboard
Product Performance, Revenue by Category, Pareto Analysis (80/20 Rule) & Category Distribution.
"""

import sys
import os

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import streamlit as st
from dashboard.utils import load_all_datasets, load_pipeline_reports, apply_global_filters, render_download_button
from dashboard.components.styles import apply_custom_styles
from dashboard.components.sidebar import render_sidebar
from dashboard.components.charts import (
    plot_top_products,
    plot_revenue_by_category,
    plot_quantity_sold,
    plot_pareto_chart,
    plot_category_distribution
)

st.set_page_config(page_title="Product Intelligence | RetailSense-AI", page_icon="🛍️", layout="wide")
apply_custom_styles()

datasets = load_all_datasets()
metadata, quality = load_pipeline_reports()
filters = render_sidebar(datasets, metadata)

# Header Section
st.markdown('<div class="page-title">🛍️ Product & Category Intelligence</div>', unsafe_allow_html=True)
st.markdown('<div class="page-subtitle">Product revenue leaderboard, category share, quantity dynamics, and Pareto 80/20 analysis.</div>', unsafe_allow_html=True)
st.markdown('<div class="accent-line"></div>', unsafe_allow_html=True)

df_prod = datasets.get("products")
df_proc = datasets.get("processed")
df_filtered = apply_global_filters(df_proc, filters) if df_proc is not None else None

# Add product category information to the filtered transaction data.
# Category is available in the Gold products dataset, not final_dataset.csv.
df_filtered_product = df_filtered

if df_filtered is not None and df_prod is not None:
    product_categories = (
        df_prod[["stock_code", "category"]]
        .drop_duplicates("stock_code")
    )

    df_filtered_product = df_filtered.merge(
        product_categories,
        on="stock_code",
        how="left"
    )

# Top Bar Export
top_col1, top_col2 = st.columns([3, 1])
with top_col1:
    st.write(f"Analyzing product catalog performance across active filters.")
with top_col2:
    render_download_button(df_prod if df_prod is not None else df_filtered, "product_intelligence.csv", "📥 Download Products CSV")

st.markdown("<br>", unsafe_allow_html=True)

# Row 1: Top Products & Quantity Sold
col1, col2 = st.columns(2)
with col1:
    fig_top = plot_top_products(df_filtered if df_filtered is not None else df_prod, top_n=10)
    st.plotly_chart(fig_top, use_container_width=True)

with col2:
    fig_qty = plot_quantity_sold(df_filtered if df_filtered is not None else df_prod, top_n=10)
    st.plotly_chart(fig_qty, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# Row 2: Revenue by Category & Category Distribution Donut
col3, col4 = st.columns(2)
with col3:
    fig_cat_rev = plot_revenue_by_category(
        df_filtered_product if df_filtered_product is not None else df_prod
    )
    st.plotly_chart(fig_cat_rev, use_container_width=True)

with col4:
    fig_cat_donut = plot_category_distribution(
        df_filtered_product if df_filtered_product is not None else df_prod
    )
    st.plotly_chart(fig_cat_donut, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# Row 3: Pareto Analysis Chart
st.markdown("### 📊 Pareto Product Analysis (80/20 Revenue Rule)")
st.caption("Identifies the top products driving 80% of cumulative retail revenue.")
fig_pareto = plot_pareto_chart(
    df_filtered_product if df_filtered_product is not None else df_prod
)
st.plotly_chart(fig_pareto, use_container_width=True)
