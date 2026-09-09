"""
Data Validation & Quality Reporting Module for RetailSense-AI ETL Pipeline.
Performs data quality checks and generates data quality reports in JSON and CSV formats.
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, List, Union
import pandas as pd
from etl.utils import setup_logger, ensure_directory

logger = setup_logger("ETL_Validate")


def validate_dataframe(df: pd.DataFrame, dataset_name: str = "Dataset") -> Dict[str, Any]:
    """
    Performs data quality checks on a DataFrame and returns a comprehensive validation report dict.
    
    Args:
        df: Pandas DataFrame to validate.
        dataset_name: Identifier name for the dataset.
        
    Returns:
        Dict[str, Any]: Validation report detailing quality metrics.
    """
    logger.info(f"--- Starting Validation for {dataset_name} ---")

    total_rows = len(df)
    total_columns = len(df.columns)
    
    # 1. Missing Values
    missing_values = {col: int(df[col].isna().sum()) for col in df.columns}
    total_missing_values = int(df.isna().sum().sum())

    # 2. Duplicate Rows
    duplicate_rows = int(df.duplicated().sum())

    # 3. Data Types Check
    data_types = {col: str(dtype) for col, dtype in df.dtypes.items()}

    # 4. Negative Quantities Check
    qty_col = next((col for col in df.columns if col.lower() in ["quantity", "qty"]), None)
    negative_quantities = 0
    if qty_col and qty_col in df.columns:
        negative_quantities = int((pd.to_numeric(df[qty_col], errors='coerce') < 0).sum())

    # 5. Negative Prices Check
    price_col = next((col for col in df.columns if col.lower() in ["unitprice", "price", "unit_price"]), None)
    negative_prices = 0
    if price_col and price_col in df.columns:
        negative_prices = int((pd.to_numeric(df[price_col], errors='coerce') < 0).sum())

    validation_report = {
        "dataset_name": dataset_name,
        "total_rows": total_rows,
        "total_columns": total_columns,
        "total_missing_values": total_missing_values,
        "missing_values_by_column": missing_values,
        "duplicate_rows": duplicate_rows,
        "negative_quantities": negative_quantities,
        "negative_prices": negative_prices,
        "data_types": data_types,
    }

    logger.info(f"Validation Report for [{dataset_name}]:")
    logger.info(f"  - Total Rows: {total_rows}")
    logger.info(f"  - Missing Values: {total_missing_values}")
    logger.info(f"  - Duplicate Rows: {duplicate_rows}")
    logger.info(f"  - Negative Quantities: {negative_quantities}")
    logger.info(f"  - Negative Prices: {negative_prices}")

    return validation_report


def validate_datasets(
    datasets: Union[pd.DataFrame, List[pd.DataFrame]],
    names: Union[str, List[str]] = "Dataset"
) -> List[Dict[str, Any]]:
    """
    Validates single or multiple datasets and generates validation reports.
    
    Args:
        datasets: Single DataFrame or list of DataFrames to validate.
        names: Name string or list of names matching the datasets.
        
    Returns:
        List[Dict[str, Any]]: List of validation reports.
    """
    if isinstance(datasets, pd.DataFrame):
        datasets = [datasets]
        names = [names] if isinstance(names, str) else names
    elif isinstance(names, str):
        names = [f"{names}_{i+1}" for i in range(len(datasets))]

    reports = []
    for df, name in zip(datasets, names):
        report = validate_dataframe(df, dataset_name=name)
        reports.append(report)

    return reports


def generate_data_quality_report(
    raw_df: pd.DataFrame,
    transform_stats: Dict[str, Any],
    execution_time: float,
    json_path: str = "reports/data_quality_report.json",
    csv_path: str = "reports/data_quality_report.csv"
) -> Tuple[str, str]:
    """
    Generates data_quality_report.json and data_quality_report.csv reports.
    
    Args:
        raw_df: Baseline raw merged DataFrame before cleaning.
        transform_stats: Transformation metrics dictionary.
        execution_time: Total pipeline execution time in seconds.
        json_path: Path to write the JSON data quality report.
        csv_path: Path to write the CSV data quality report.
        
    Returns:
        Tuple[str, str]: (json_path, csv_path)
    """
    logger.info("--- Generating Data Quality Reports ---")

    # Ensure reports directory exists
    ensure_directory(json_path)
    ensure_directory(csv_path)

    # 1. Generate JSON Data Quality Report
    timestamp = datetime.now().astimezone().isoformat()

    json_report = {
        "total_rows_before_cleaning": transform_stats.get("total_raw_rows", len(raw_df)),
        "total_rows_after_cleaning": transform_stats.get("final_rows", 0),
        "duplicate_rows_removed": transform_stats.get("duplicates_removed", 0),
        "missing_values_per_column": transform_stats.get(
            "missing_values_per_column",
            {col: int(raw_df[col].isna().sum()) for col in raw_df.columns}
        ),
        "cancelled_orders_removed": transform_stats.get("cancelled_orders_removed", 0),
        "invalid_quantities_removed": transform_stats.get("invalid_quantities_removed", 0),
        "invalid_prices_removed": transform_stats.get("invalid_prices_removed", 0),
        "processing_timestamp": timestamp,
        "execution_time_seconds": round(execution_time, 2)
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_report, f, indent=4)
    logger.info(f"JSON Data Quality Report saved to: {json_path}")

    # 2. Generate CSV Data Quality Report (Column-wise missing values & data types)
    total_raw_rows = len(raw_df)
    csv_rows = []

    for col in raw_df.columns:
        dtype_str = str(raw_df[col].dtype)
        missing_count = int(raw_df[col].isna().sum())
        missing_pct = round((missing_count / total_raw_rows) * 100, 2) if total_raw_rows > 0 else 0.0

        csv_rows.append({
            "column_name": col,
            "data_type": dtype_str,
            "missing_count": missing_count,
            "missing_percentage": missing_pct
        })

    report_df = pd.DataFrame(csv_rows)
    report_df.to_csv(csv_path, index=False)
    logger.info(f"CSV Data Quality Report saved to: {csv_path}")

    return json_path, csv_path
