"""
Data Extraction Module for RetailSense-AI ETL Pipeline.
Reads raw retail transaction datasets from Excel (.xlsx) and CSV files.
"""

import os
from typing import Tuple, Optional
import pandas as pd
from etl.utils import setup_logger

logger = setup_logger("ETL_Extract")


def extract_data(
    excel_path: Optional[str] = None,
    csv_path: Optional[str] = None
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Extracts raw datasets from specified Excel and CSV file paths or default data/raw paths.
    
    Args:
        excel_path: Path to the Excel dataset (.xlsx). Defaults to 'data/raw/Online Retail.xlsx'.
        csv_path: Path to the CSV dataset (.csv). Defaults to 'data/raw/online_retail_II.csv'.
        
    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]: (df_excel, df_csv)
    """
    raw_dir = "data/raw"
    
    if excel_path is None:
        excel_path = os.path.join(raw_dir, "Online Retail.xlsx")
        
    if csv_path is None:
        csv_path = os.path.join(raw_dir, "online_retail_II.csv")

    logger.info(f"Extracting Excel dataset from: {excel_path}")
    if not os.path.exists(excel_path):
        logger.error(f"Excel file not found at path: {excel_path}")
        raise FileNotFoundError(f"Raw Excel file not found: {excel_path}")
    
    df_excel = pd.read_excel(excel_path)
    logger.info(f"Excel dataset loaded successfully: {df_excel.shape[0]} rows, {df_excel.shape[1]} columns.")

    logger.info(f"Extracting CSV dataset from: {csv_path}")
    if not os.path.exists(csv_path):
        logger.error(f"CSV file not found at path: {csv_path}")
        raise FileNotFoundError(f"Raw CSV file not found: {csv_path}")
        
    df_csv = pd.read_csv(csv_path)
    logger.info(f"CSV dataset loaded successfully: {df_csv.shape[0]} rows, {df_csv.shape[1]} columns.")

    return df_excel, df_csv
