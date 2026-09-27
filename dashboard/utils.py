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


@st.cache_data(ttl=300)
def load_ml_datasets() -> Dict[str, Any]:
    """
    Loads customer churn dataset, churn report, customer feature dataset, and feature report.
    
    Returns:
        Dict[str, Any]: Dict containing churn_df, churn_report, features_df, and feat_report.
    """
    ml_data = {}
    churn_csv = "data/ml/customer_churn_dataset.csv"
    churn_json = "reports/churn_label_report.json"
    feat_csv = "data/ml/customer_features.csv"
    feat_json = "reports/feature_engineering_report.json"

    if os.path.exists(churn_csv):
        try:
            ml_data["churn_df"] = pd.read_csv(churn_csv)
        except Exception:
            pass

    if os.path.exists(churn_json):
        try:
            with open(churn_json, "r", encoding="utf-8") as f:
                ml_data["churn_report"] = json.load(f)
        except Exception:
            pass

    if os.path.exists(feat_csv):
        try:
            ml_data["features_df"] = pd.read_csv(feat_csv)
        except Exception:
            pass

    if os.path.exists(feat_json):
        try:
            with open(feat_json, "r", encoding="utf-8") as f:
                ml_data["feat_report"] = json.load(f)
        except Exception:
            pass

    return ml_data


@st.cache_data(ttl=300)
def load_model_evaluation_reports() -> Tuple[Optional[pd.DataFrame], Dict[str, Any]]:
    """
    Loads ML model evaluation metrics CSV and evaluation summary JSON.
    
    Returns:
        Tuple[Optional[pd.DataFrame], Dict[str, Any]]: (model_metrics_df, model_eval_dict)
    """
    metrics_path = "reports/model_metrics.csv"
    eval_path = "reports/model_evaluation.json"

    metrics_df = None
    eval_dict = {}

    if os.path.exists(metrics_path):
        try:
            metrics_df = pd.read_csv(metrics_path)
        except Exception:
            metrics_df = None

    if os.path.exists(eval_path):
        try:
            with open(eval_path, "r", encoding="utf-8") as f:
                eval_dict = json.load(f)
        except Exception:
            eval_dict = {}

    return metrics_df, eval_dict


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

@st.cache_data(ttl=3600)
def prepare_sales_aggregations(
    df: pd.DataFrame,
    country: str,
    years: tuple,
    months: tuple
) -> Dict[str, pd.DataFrame]:
    """
    Filters the processed dataset once and prepares compact datasets
    for Sales page visualizations.

    This avoids repeatedly grouping the full processed dataset
    independently for every chart.
    """
    if df is None or df.empty:
        return {
            "filtered": pd.DataFrame(),
            "monthly": pd.DataFrame(),
            "weekday": pd.DataFrame(),
            "hour": pd.DataFrame(),
        }

    # Apply filters once
    filtered = df

    if country and country != "All Countries" and "country" in filtered.columns:
        filtered = filtered[filtered["country"] == country]

    if years and "year" in filtered.columns:
        filtered = filtered[filtered["year"].isin(years)]

    if months and "month" in filtered.columns:
        filtered = filtered[filtered["month"].isin(months)]

    # Monthly revenue
    if "year_month" in filtered.columns and "total_price" in filtered.columns:
        monthly = (
            filtered.groupby("year_month")["total_price"]
            .sum()
            .reset_index()
            .sort_values("year_month")
        )
    else:
        monthly = pd.DataFrame()

    # Monthly orders
    if "year_month" in filtered.columns:
        inv_col = (
            "invoice_no"
            if "invoice_no" in filtered.columns
            else ("invoice" if "invoice" in filtered.columns else None)
        )

        if inv_col:
            monthly_orders = (
                filtered.groupby("year_month")[inv_col]
                .nunique()
                .reset_index(name="orders")
            )
        else:
            monthly_orders = pd.DataFrame()
    else:
        monthly_orders = pd.DataFrame()

    # Weekday revenue
    if "weekday" in filtered.columns and "total_price" in filtered.columns:
        days_order = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]

        weekday = (
            filtered.groupby("weekday")["total_price"]
            .sum()
            .reindex(days_order)
            .dropna()
            .reset_index()
        )
    else:
        weekday = pd.DataFrame()

    # Hourly revenue
    if "hour" in filtered.columns and "total_price" in filtered.columns:
        hour = (
            filtered.groupby("hour")["total_price"]
            .sum()
            .reset_index()
            .sort_values("hour")
        )
    else:
        hour = pd.DataFrame()

    return {
        "filtered": filtered,
        "monthly": monthly,
        "monthly_orders": monthly_orders,
        "weekday": weekday,
        "hour": hour,
    }

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
