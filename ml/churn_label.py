"""
Customer Churn Label Generation Module for RetailSense-AI.
Processes cleaned transaction facts to compute customer RFM features, recency days,
and assigns binary churn labels based on a 90-day inactivity threshold.
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, Tuple, Optional, Union
import pandas as pd
from etl.utils import setup_logger, ensure_directory

logger = setup_logger("ML_ChurnLabel")


def generate_churn_labels(
    input_data: Union[str, pd.DataFrame] = "data/processed/final_dataset.csv",
    output_csv_path: str = "data/ml/customer_churn_dataset.csv",
    output_report_path: str = "reports/churn_label_report.json",
    churn_threshold_days: int = 90
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Computes customer-level RFM metrics and generates binary churn labels.
    
    Business Rule:
        If a customer has made no purchases for >= churn_threshold_days (default 90 days)
        relative to the maximum transaction date in the dataset, label churn = 1, else churn = 0.
        
    Args:
        input_data: File path to processed CSV or Pandas DataFrame.
        output_csv_path: Path to save generated customer churn dataset.
        output_report_path: Path to save churn label JSON report.
        churn_threshold_days: Inactivity day threshold for churn definition.
        
    Returns:
        Tuple[pd.DataFrame, Dict[str, Any]]: (churn_df, churn_report)
    """
    logger.info("Starting Customer Churn Label Generation...")
    
    # 1. Load Data
    if isinstance(input_data, str):
        if not os.path.exists(input_data):
            logger.error(f"Input dataset not found at: {input_data}")
            raise FileNotFoundError(f"Processed dataset not found at {input_data}")
        logger.info(f"Reading processed dataset from: {input_data}")
        df = pd.read_csv(input_data)
    elif isinstance(input_data, pd.DataFrame):
        df = input_data.copy()
    else:
        raise ValueError("input_data must be a filepath string or Pandas DataFrame.")

    if df.empty:
        logger.warning("Input DataFrame is empty. Returning empty churn dataset.")
        empty_df = pd.DataFrame(columns=[
            "customer_id", "first_purchase", "last_purchase",
            "recency_days", "total_orders", "total_quantity", "total_spent", "churn"
        ])
        report = {
            "total_customers": 0,
            "active_customers": 0,
            "churned_customers": 0,
            "churn_rate": 0.0,
            "churn_rate_pct": "0.0%",
            "generation_timestamp": datetime.now().astimezone().isoformat()
        }
        return empty_df, report

    # 2. Schema Validation
    required_cols = {"customer_id", "invoice_date"}
    if not required_cols.issubset(df.columns):
        missing = required_cols - set(df.columns)
        raise KeyError(f"Missing required columns in dataset: {missing}")

    # Ensure correct data types
    df["invoice_date"] = pd.to_datetime(df["invoice_date"], errors="coerce")
    df = df.dropna(subset=["customer_id", "invoice_date"])

    # Determine order invoice column
    inv_col = "invoice_no" if "invoice_no" in df.columns else ("invoice" if "invoice" in df.columns else "invoice_date")
    qty_col = "quantity" if "quantity" in df.columns else None
    spent_col = "total_price" if "total_price" in df.columns else ("total_spent" if "total_spent" in df.columns else None)

    # 3. Maximum Reference Date
    max_dataset_date = df["invoice_date"].max()
    logger.info(f"Max transaction reference date in dataset: {max_dataset_date.strftime('%Y-%m-%d')}")

    # 4. Customer Aggregation
    agg_dict = {
        "invoice_date": ["min", "max"]
    }

    if inv_col in df.columns:
        agg_dict[inv_col] = "nunique"
    if qty_col and qty_col in df.columns:
        agg_dict[qty_col] = "sum"
    if spent_col and spent_col in df.columns:
        agg_dict[spent_col] = "sum"

    grouped = df.groupby("customer_id").agg(agg_dict)
    
    # Flatten multi-level columns
    grouped.columns = [
        "first_purchase_dt", "last_purchase_dt", "total_orders", "total_quantity", "total_spent"
    ][:len(grouped.columns)]

    churn_df = grouped.reset_index()

    # Normalize customer_id to integer or string representation
    churn_df["customer_id"] = churn_df["customer_id"].astype(int, errors="ignore")

    # Compute Recency & Dates
    churn_df["recency_days"] = (max_dataset_date - churn_df["last_purchase_dt"]).dt.days
    churn_df["first_purchase"] = churn_df["first_purchase_dt"].dt.strftime("%Y-%m-%d")
    churn_df["last_purchase"] = churn_df["last_purchase_dt"].dt.strftime("%Y-%m-%d")

    # Fill missing optional aggregations
    if "total_orders" not in churn_df.columns:
        churn_df["total_orders"] = 1
    if "total_quantity" not in churn_df.columns:
        churn_df["total_quantity"] = 0
    if "total_spent" not in churn_df.columns:
        churn_df["total_spent"] = 0.0

    churn_df["total_spent"] = churn_df["total_spent"].round(2)

    # 5. Apply Churn Business Rule (>= 90 Days)
    churn_df["churn"] = (churn_df["recency_days"] >= churn_threshold_days).astype(int)

    # Select and order final output columns
    final_columns = [
        "customer_id",
        "first_purchase",
        "last_purchase",
        "recency_days",
        "total_orders",
        "total_quantity",
        "total_spent",
        "churn"
    ]
    churn_df = churn_df[final_columns].sort_values("customer_id").reset_index(drop=True)

    # 6. Generate Summary Metrics & Report
    total_cust = int(len(churn_df))
    churned_cust = int((churn_df["churn"] == 1).sum())
    active_cust = int((churn_df["churn"] == 0).sum())
    churn_rate = round(churned_cust / total_cust, 4) if total_cust > 0 else 0.0
    churn_rate_pct = f"{round(churn_rate * 100, 2)}%"

    report = {
        "total_customers": total_cust,
        "active_customers": active_cust,
        "churned_customers": churned_cust,
        "churn_rate": churn_rate,
        "churn_rate_pct": churn_rate_pct,
        "churn_threshold_days": churn_threshold_days,
        "generation_timestamp": datetime.now().astimezone().isoformat()
    }

    # 7. Persist Output Files
    ensure_directory(output_csv_path)
    ensure_directory(output_report_path)

    churn_df.to_csv(output_csv_path, index=False)
    logger.info(f"Saved customer churn dataset ({total_cust:,} records) to: {output_csv_path}")

    with open(output_report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4)
    logger.info(f"Saved churn label report to: {output_report_path}")

    logger.info(f"Churn Label Summary -> Total: {total_cust:,} | Active: {active_cust:,} | Churned: {churned_cust:,} ({churn_rate_pct})")
    
    return churn_df, report


if __name__ == "__main__":
    generate_churn_labels()
