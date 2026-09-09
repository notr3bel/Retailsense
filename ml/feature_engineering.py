"""
Customer Feature Engineering Module for RetailSense-AI.
Generates comprehensive customer-level ML features from transaction records.
Includes profile, monetary, order, recency, product, temporal, and business segmentation features.
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, Tuple, Optional, Union
import pandas as pd
import numpy as np

from etl.utils import setup_logger, ensure_directory
from etl.gold import classify_category

logger = setup_logger("ML_FeatureEngineering")


def compute_average_days_between_orders(df: pd.DataFrame, inv_col: str = "invoice_no") -> pd.Series:
    """
    Computes average interval in days between consecutive orders per customer using vector operations.
    Single-order customers receive 0.0.
    """
    if inv_col not in df.columns or inv_col == "invoice_date":
        order_dates = df[["customer_id", "invoice_date"]].drop_duplicates().sort_values(["customer_id", "invoice_date"]).copy()
    else:
        order_dates = df.groupby(["customer_id", inv_col])["invoice_date"].min().reset_index()
        order_dates = order_dates.sort_values(["customer_id", "invoice_date"])

    # Calculate interval in days to previous order
    order_dates["prev_order_date"] = order_dates.groupby("customer_id")["invoice_date"].shift(1)
    order_dates["days_between"] = (order_dates["invoice_date"] - order_dates["prev_order_date"]).dt.days

    # Compute mean interval per customer
    avg_days = order_dates.groupby("customer_id")["days_between"].mean().fillna(0.0).round(2)
    return avg_days


def generate_customer_features(
    input_data: Union[str, pd.DataFrame] = "data/processed/final_dataset.csv",
    output_csv_path: str = "data/ml/customer_features.csv",
    output_report_path: str = "reports/feature_engineering_report.json"
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Generates customer-level feature dataset for Machine Learning.
    
    Args:
        input_data: Path to final_dataset.csv or a Pandas DataFrame.
        output_csv_path: Path where customer_features.csv will be saved.
        output_report_path: Path where feature_engineering_report.json will be saved.
        
    Returns:
        Tuple[pd.DataFrame, Dict[str, Any]]: (features_df, summary_report)
    """
    logger.info("Starting Customer Feature Engineering...")

    # 1. Load Data
    if isinstance(input_data, str):
        if not os.path.exists(input_data):
            logger.error(f"Input processed dataset not found at: {input_data}")
            raise FileNotFoundError(f"Processed dataset not found at {input_data}")
        logger.info(f"Loading processed dataset from: {input_data}")
        df = pd.read_csv(input_data)
    elif isinstance(input_data, pd.DataFrame):
        df = input_data.copy()
    else:
        raise ValueError("input_data must be a filepath string or Pandas DataFrame.")

    if df.empty:
        logger.warning("Input dataset is empty. Returning empty features DataFrame.")
        empty_cols = [
            "customer_id", "country", "first_purchase", "last_purchase", "customer_lifetime_days",
            "total_spent", "average_order_value", "max_order_value", "min_order_value",
            "total_quantity", "average_quantity", "total_orders", "purchase_frequency",
            "purchase_velocity", "average_days_between_orders", "recency_days",
            "unique_products", "favorite_product", "favorite_category", "category_diversity",
            "preferred_month", "preferred_weekday", "preferred_hour", "weekend_purchase_ratio",
            "revenue_per_day", "items_per_order", "customer_value_segment", "basket_size"
        ]
        empty_df = pd.DataFrame(columns=empty_cols)
        report = {
            "total_customers": 0,
            "number_of_features": len(empty_cols) - 1,
            "missing_values": {},
            "feature_names": empty_cols,
            "generation_timestamp": datetime.now().astimezone().isoformat()
        }
        return empty_df, report

    # 2. Data Preparation & Normalization
    df["invoice_date"] = pd.to_datetime(df["invoice_date"], errors="coerce")
    df = df.dropna(subset=["customer_id", "invoice_date"]).copy()
    df["customer_id"] = df["customer_id"].astype(int, errors="ignore")

    inv_col = "invoice_no" if "invoice_no" in df.columns else ("invoice" if "invoice" in df.columns else "invoice_date")
    
    # Classify categories using gold.py category logic
    if "description" in df.columns:
        df["category"] = df["description"].apply(classify_category)
    else:
        df["category"] = "General & Gifts"

    # Derive temporal fields if missing
    df["month"] = df["invoice_date"].dt.month
    df["weekday"] = df["invoice_date"].dt.strftime("%A")
    df["hour"] = df["invoice_date"].dt.hour
    df["is_weekend"] = df["invoice_date"].dt.weekday.isin([5, 6]).astype(int)

    # Calculate invoice totals for min/max order value
    invoice_totals = df.groupby(["customer_id", inv_col])["total_price"].sum().reset_index()

    # Max Reference Date for Recency
    max_dataset_date = df["invoice_date"].max()

    # Mode helper
    def get_mode(series):
        mode_vals = series.mode()
        return mode_vals.iloc[0] if not mode_vals.empty else np.nan

    logger.info("Computing customer-level aggregated feature metrics...")

    # 3. Base Grouped Aggregations
    grouped = df.groupby("customer_id").agg(
        country=("country", get_mode),
        first_purchase_dt=("invoice_date", "min"),
        last_purchase_dt=("invoice_date", "max"),
        total_spent=("total_price", "sum"),
        total_quantity=("quantity", "sum"),
        total_orders=(inv_col, "nunique"),
        unique_products=("stock_code", "nunique"),
        favorite_product=("stock_code", get_mode),
        favorite_category=("category", get_mode),
        category_diversity=("category", "nunique"),
        preferred_month=("month", get_mode),
        preferred_weekday=("weekday", get_mode),
        preferred_hour=("hour", get_mode),
        total_transactions=("invoice_date", "count"),
        weekend_transactions=("is_weekend", "sum")
    ).reset_index()

    # Min / Max Order Values per Customer
    inv_agg = invoice_totals.groupby("customer_id")["total_price"].agg(
        max_order_value="max",
        min_order_value="min"
    ).reset_index()

    features_df = pd.merge(grouped, inv_agg, on="customer_id", how="left")

    # 4. Feature Transformations & Derived Engineering

    # Profile & Lifetime
    features_df["first_purchase"] = features_df["first_purchase_dt"].dt.strftime("%Y-%m-%d")
    features_df["last_purchase"] = features_df["last_purchase_dt"].dt.strftime("%Y-%m-%d")
    
    # Lifetime in days (at least 1 day to prevent division by zero)
    features_df["customer_lifetime_days"] = (
        (features_df["last_purchase_dt"] - features_df["first_purchase_dt"]).dt.days + 1
    ).clip(lower=1)

    # Monetary Features
    features_df["total_spent"] = round(features_df["total_spent"], 2)
    features_df["average_order_value"] = round(features_df["total_spent"] / features_df["total_orders"], 2)
    features_df["max_order_value"] = round(features_df["max_order_value"], 2)
    features_df["min_order_value"] = round(features_df["min_order_value"], 2)
    features_df["average_quantity"] = round(features_df["total_quantity"] / features_df["total_orders"], 2)

    # Order Features
    features_df["purchase_frequency"] = round(features_df["total_orders"] / features_df["customer_lifetime_days"], 4)
    features_df["purchase_velocity"] = round(features_df["total_orders"] / features_df["customer_lifetime_days"], 4)

    # Average Days Between Orders
    logger.info("Computing average days between orders per customer...")
    avg_days_series = compute_average_days_between_orders(df[["customer_id", inv_col, "invoice_date"]], inv_col=inv_col)
    features_df["average_days_between_orders"] = features_df["customer_id"].map(avg_days_series).fillna(0.0)

    # Recency Features
    features_df["recency_days"] = (max_dataset_date - features_df["last_purchase_dt"]).dt.days

    # Temporal Features
    features_df["weekend_purchase_ratio"] = round(features_df["weekend_transactions"] / features_df["total_transactions"], 4)

    # Advanced Business Features
    features_df["revenue_per_day"] = round(features_df["total_spent"] / features_df["customer_lifetime_days"], 2)
    features_df["items_per_order"] = round(features_df["total_quantity"] / features_df["total_orders"], 2)
    features_df["basket_size"] = round(features_df["total_quantity"] / features_df["total_orders"], 2)

    # Customer Value Segment (Quartiles based on total_spent)
    try:
        features_df["customer_value_segment"] = pd.qcut(
            features_df["total_spent"],
            q=4,
            labels=["Low", "Medium", "High", "VIP"],
            duplicates="drop"
        )
    except Exception:
        features_df["customer_value_segment"] = "Medium"

    # 5. Final Column Formatting & Ordering
    ordered_columns = [
        "customer_id",
        "country",
        "first_purchase",
        "last_purchase",
        "customer_lifetime_days",
        "total_spent",
        "average_order_value",
        "max_order_value",
        "min_order_value",
        "total_quantity",
        "average_quantity",
        "total_orders",
        "purchase_frequency",
        "purchase_velocity",
        "average_days_between_orders",
        "recency_days",
        "unique_products",
        "favorite_product",
        "favorite_category",
        "category_diversity",
        "preferred_month",
        "preferred_weekday",
        "preferred_hour",
        "weekend_purchase_ratio",
        "revenue_per_day",
        "items_per_order",
        "customer_value_segment",
        "basket_size"
    ]

    features_df = features_df[ordered_columns].sort_values("customer_id").reset_index(drop=True)

    # 6. Quality Audit & Report Generation
    total_cust = len(features_df)
    missing_dict = {col: int(features_df[col].isna().sum()) for col in features_df.columns}
    num_features = len(features_df.columns) - 1 if "customer_id" in features_df.columns else len(features_df.columns)
    total_columns = len(features_df.columns)

    report = {
        "total_customers": total_cust,
        "total_columns": total_columns,
        "number_of_features": num_features,
        "missing_values": missing_dict,
        "feature_names": list(features_df.columns),
        "generation_timestamp": datetime.now().astimezone().isoformat()
    }

    # 7. Save Outputs
    ensure_directory(output_csv_path)
    ensure_directory(output_report_path)

    features_df.to_csv(output_csv_path, index=False)
    logger.info(f"Saved customer features dataset ({total_cust:,} customers, {len(ordered_columns)} columns) to: {output_csv_path}")

    with open(output_report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4)
    logger.info(f"Saved feature engineering report to: {output_report_path}")

    return features_df, report


if __name__ == "__main__":
    generate_customer_features()
