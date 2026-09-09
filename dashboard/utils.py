"""
Data Loading & Helper Utilities for RetailSense-AI Streamlit Dashboard.
Provides cached dataset loading, database/CSV fallback mechanisms, dynamic filtering, and CSV exports.
"""

import os
import json
from typing import Dict, Any, Tuple, Optional
import pandas as pd
import streamlit as st


@st.cache_data(ttl=3600)
def load_all_datasets() -> Dict[str, pd.DataFrame]:
    """
    Loads Gold Data Layer datasets with automatic fallback to processed dataset.
    
    Returns:
        Dict[str, pd.DataFrame]: Dictionary containing analytical datasets.
    """
    gold_dir = "data/gold"
    processed_path = "data/processed/final_dataset.csv"

    datasets = {}

    # Try reading Gold Layer CSVs
    try:
        if os.path.exists(os.path.join(gold_dir, "sales_summary.csv")):
            datasets["sales_summary"] = pd.read_csv(os.path.join(gold_dir, "sales_summary.csv"))
        if os.path.exists(os.path.join(gold_dir, "monthly_sales.csv")):
            datasets["monthly_sales"] = pd.read_csv(os.path.join(gold_dir, "monthly_sales.csv"))
        if os.path.exists(os.path.join(gold_dir, "products.csv")):
            datasets["products"] = pd.read_csv(os.path.join(gold_dir, "products.csv"))
        if os.path.exists(os.path.join(gold_dir, "customers.csv")):
            datasets["customers"] = pd.read_csv(os.path.join(gold_dir, "customers.csv"))
        if os.path.exists(os.path.join(gold_dir, "country_summary.csv")):
            datasets["country_summary"] = pd.read_csv(os.path.join(gold_dir, "country_summary.csv"))
    except Exception:
        pass

    # Load Main Processed Dataset for Granular Time, Customer & Product Analysis
    if os.path.exists(processed_path):
        df_proc = pd.read_csv(processed_path)
        df_proc["invoice_date"] = pd.to_datetime(df_proc["invoice_date"], errors="coerce")
        df_proc["year"] = df_proc["invoice_date"].dt.year
        df_proc["month"] = df_proc["invoice_date"].dt.month
        df_proc["month_name"] = df_proc["invoice_date"].dt.strftime("%B")
        df_proc["year_month"] = df_proc["invoice_date"].dt.strftime("%Y-%m")
        df_proc["weekday"] = df_proc["invoice_date"].dt.strftime("%A")
        df_proc["hour"] = df_proc["invoice_date"].dt.hour
        datasets["processed"] = df_proc

    return datasets


@st.cache_data(ttl=300)
def load_pipeline_reports() -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Loads pipeline_metadata.json and data_quality_report.json.
    
    Returns:
        Tuple[Dict[str, Any], Dict[str, Any]]: (metadata_dict, quality_dict)
    """
    metadata_path = "reports/pipeline_metadata.json"
    quality_path = "reports/data_quality_report.json"

    metadata = {}
    quality = {}

    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
        except Exception:
            metadata = {}

    if os.path.exists(quality_path):
        try:
            with open(quality_path, "r", encoding="utf-8") as f:
                quality = json.load(f)
        except Exception:
            quality = {}

    return metadata, quality


def apply_global_filters(df: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
    """
    Applies global sidebar filters (Country, Years, Months) to a DataFrame.
    
    Args:
        df: Input DataFrame.
        filters: Filter dictionary from sidebar.
        
    Returns:
        pd.DataFrame: Filtered DataFrame.
    """
    if df is None or df.empty:
        return df

    filtered_df = df.copy()

    # Filter by Country
    if filters.get("country") and filters["country"] != "All Countries":
        if "country" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["country"] == filters["country"]]

    # Filter by Year
    if filters.get("years") and "year" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["year"].isin(filters["years"])]

    # Filter by Month
    if filters.get("months") and "month" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["month"].isin(filters["months"])]

    return filtered_df


def get_filtered_metrics(datasets: Dict[str, pd.DataFrame], filters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Computes aggregated KPI metrics dynamically based on active global filters.
    
    Returns:
        Dict[str, Any]: Key metrics (Total Revenue, Orders, Customers, Products, AOV, Countries).
    """
    df_proc = datasets.get("processed")
    if df_proc is not None and not df_proc.empty:
        df_filtered = apply_global_filters(df_proc, filters)
        if not df_filtered.empty:
            total_rev = df_filtered["total_price"].sum()
            inv_col = "invoice_no" if "invoice_no" in df_filtered.columns else ("invoice" if "invoice" in df_filtered.columns else None)
            total_orders = df_filtered[inv_col].nunique() if inv_col else 0
            total_customers = df_filtered["customer_id"].nunique() if "customer_id" in df_filtered.columns else 0
            total_products = df_filtered["stock_code"].nunique() if "stock_code" in df_filtered.columns else 0
            aov = total_rev / total_orders if total_orders > 0 else 0.0
            total_countries = df_filtered["country"].nunique()
            return {
                "total_revenue": total_rev,
                "total_orders": total_orders,
                "total_customers": total_customers,
                "total_products": total_products,
                "average_order_value": aov,
                "total_countries": total_countries,
                "df_filtered": df_filtered
            }

    # Fallback to pre-calculated gold sales_summary
    sales_sum = datasets.get("sales_summary")
    if sales_sum is not None and not sales_sum.empty:
        row = sales_sum.iloc[0]
        country_sum = datasets.get("country_summary")
        num_countries = country_sum["country"].nunique() if country_sum is not None else 0
        return {
            "total_revenue": row.get("total_revenue", 0.0),
            "total_orders": row.get("total_orders", 0),
            "total_customers": row.get("total_customers", 0),
            "total_products": row.get("total_products", 0),
            "average_order_value": row.get("average_order_value", 0.0),
            "total_countries": num_countries,
            "df_filtered": pd.DataFrame()
        }

    return {
        "total_revenue": 0.0,
        "total_orders": 0,
        "total_customers": 0,
        "total_products": 0,
        "average_order_value": 0.0,
        "total_countries": 0,
        "df_filtered": pd.DataFrame()
    }


def render_download_button(df: pd.DataFrame, filename: str, label: str = "📥 Download CSV") -> None:
    """
    Renders a styled CSV download button for any DataFrame.
    """
    if df is not None and not df.empty:
        csv_bytes = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label=label,
            data=csv_bytes,
            file_name=filename,
            mime="text/csv",
            use_container_width=False
        )
