"""
Data Transformation Module for RetailSense-AI ETL Pipeline.
Cleans, standardizes, filters, merges, and enriches retail transaction datasets.
"""

from typing import Tuple, Dict, Any
import pandas as pd
from etl.utils import setup_logger

logger = setup_logger("ETL_Transform")


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardizes column names into clean, uniform snake_case format.
    
    Args:
        df: Input DataFrame.
        
    Returns:
        pd.DataFrame: DataFrame with standardized column names.
    """
    column_mapping = {
        "InvoiceNo": "invoice_no",
        "Invoice": "invoice_no",
        "StockCode": "stock_code",
        "Description": "description",
        "Quantity": "quantity",
        "InvoiceDate": "invoice_date",
        "UnitPrice": "unit_price",
        "Price": "unit_price",
        "CustomerID": "customer_id",
        "Customer ID": "customer_id",
        "Country": "country"
    }
    
    df_renamed = df.rename(columns=column_mapping)
    return df_renamed


def transform_datasets(
    df_excel: pd.DataFrame,
    df_csv: pd.DataFrame
) -> Tuple[pd.DataFrame, Dict[str, Any], pd.DataFrame]:
    """
    Standardizes, merges, cleans, and enriches raw datasets.
    
    Transformation steps:
      1. Standardize column names for both datasets.
      2. Merge datasets (pd.concat).
      3. Capture baseline column metrics and missing values.
      4. Convert invoice_date to datetime.
      5. Remove cancelled orders (Invoice numbers starting with 'C').
      6. Remove duplicate records.
      7. Remove rows with missing CustomerID.
      8. Remove invalid/negative Quantity (Quantity <= 0).
      9. Remove invalid/negative UnitPrice (UnitPrice <= 0).
      10. Create TotalPrice = Quantity * UnitPrice.
      11. Sort by invoice_date.
      
    Args:
        df_excel: Excel DataFrame.
        df_csv: CSV DataFrame.
        
    Returns:
        Tuple[pd.DataFrame, Dict[str, Any], pd.DataFrame]: 
            (transformed_df, transform_stats, raw_merged_df)
    """
    logger.info("--- Starting Data Transformation ---")

    initial_excel_rows = len(df_excel)
    initial_csv_rows = len(df_csv)
    total_raw_rows = initial_excel_rows + initial_csv_rows

    logger.info(f"Raw rows loaded: Excel ({initial_excel_rows}), CSV ({initial_csv_rows}). Total: {total_raw_rows}")

    # 1. Standardize column names
    df_excel_std = standardize_columns(df_excel)
    df_csv_std = standardize_columns(df_csv)

    # 2. Merge raw datasets
    df_merged = pd.concat([df_excel_std, df_csv_std], ignore_index=True)
    logger.info(f"Merged raw dataset shape: {df_merged.shape[0]} rows, {df_merged.shape[1]} columns.")

    # Capture missing values per column in raw merged dataset
    missing_values_per_column = {col: int(df_merged[col].isna().sum()) for col in df_merged.columns}

    # 3. Convert InvoiceDate to datetime
    df_merged["invoice_date"] = pd.to_datetime(df_merged["invoice_date"], errors="coerce")

    # 4. Remove cancelled orders (invoice_no starts with 'C' or 'c')
    df_merged["invoice_no_str"] = df_merged["invoice_no"].astype(str).str.strip().str.upper()
    is_cancelled = df_merged["invoice_no_str"].str.startswith("C", na=False)
    cancelled_count = int(is_cancelled.sum())
    df_cleaned = df_merged[~is_cancelled].copy()
    df_cleaned.drop(columns=["invoice_no_str"], inplace=True)

    # 5. Remove duplicate records
    duplicate_count_before = len(df_cleaned)
    df_cleaned = df_cleaned.drop_duplicates()
    duplicates_removed = duplicate_count_before - len(df_cleaned)

    # 6. Remove rows with missing CustomerID
    missing_customer_id_count = int(df_cleaned["customer_id"].isna().sum())
    df_cleaned = df_cleaned.dropna(subset=["customer_id"]).copy()

    # Format customer_id as integer string for consistency
    df_cleaned["customer_id"] = df_cleaned["customer_id"].astype(int).astype(str)

    # 7. Remove Quantity <= 0
    qty_numeric = pd.to_numeric(df_cleaned["quantity"], errors="coerce")
    invalid_qty_count = int((qty_numeric.isna() | (qty_numeric <= 0)).sum())
    df_cleaned = df_cleaned[qty_numeric > 0].copy()

    # 8. Remove UnitPrice <= 0
    price_numeric = pd.to_numeric(df_cleaned["unit_price"], errors="coerce")
    invalid_price_count = int((price_numeric.isna() | (price_numeric <= 0)).sum())
    df_cleaned = df_cleaned[price_numeric > 0].copy()

    # 9. Create TotalPrice = Quantity * UnitPrice
    df_cleaned["total_price"] = df_cleaned["quantity"] * df_cleaned["unit_price"]

    # 10. Sort by invoice_date
    df_cleaned = df_cleaned.sort_values(by="invoice_date", ascending=True).reset_index(drop=True)

    final_rows = len(df_cleaned)
    rows_removed = total_raw_rows - final_rows

    transform_stats = {
        "total_raw_rows": total_raw_rows,
        "final_rows": final_rows,
        "rows_removed": rows_removed,
        "cancelled_orders_removed": cancelled_count,
        "duplicates_removed": duplicates_removed,
        "missing_customer_ids_handled": missing_customer_id_count,
        "invalid_quantities_removed": invalid_qty_count,
        "invalid_prices_removed": invalid_price_count,
        "missing_values_per_column": missing_values_per_column,
    }

    logger.info(f"Transformation complete:")
    logger.info(f"  - Final Clean Rows: {final_rows}")
    logger.info(f"  - Total Rows Removed: {rows_removed}")
    logger.info(f"  - Cancelled Orders Removed: {cancelled_count}")
    logger.info(f"  - Duplicates Removed: {duplicates_removed}")
    logger.info(f"  - Invalid Quantities Removed: {invalid_qty_count}")
    logger.info(f"  - Invalid Prices Removed: {invalid_price_count}")

    return df_cleaned, transform_stats, df_merged
