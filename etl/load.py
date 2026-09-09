"""
Data Loading Module for RetailSense-AI ETL Pipeline.
Persists staging and processed datasets to disk in designated storage directories.
"""

import os
from typing import Dict, Any, Tuple
import pandas as pd
from etl.utils import setup_logger, ensure_directory

logger = setup_logger("ETL_Load")


def load_data(
    df: pd.DataFrame,
    staging_path: str = "data/staging/cleaned_data.csv",
    processed_path: str = "data/processed/final_dataset.csv"
) -> Tuple[str, str]:
    """
    Saves transformed DataFrame to staging and processed storage locations.
    
    Args:
        df: Transformed pandas DataFrame.
        staging_path: Path for saving cleaned staging dataset CSV.
        processed_path: Path for saving final processed dataset CSV.
        
    Returns:
        Tuple[str, str]: (staging_path, processed_path)
    """
    logger.info("--- Starting Data Load ---")

    # Ensure target directories exist
    ensure_directory(staging_path)
    ensure_directory(processed_path)

    # 1. Save to Staging
    logger.info(f"Saving staging dataset to: {staging_path}")
    df.to_csv(staging_path, index=False)
    logger.info(f"Staging dataset saved ({len(df)} rows).")

    # 2. Save to Processed
    logger.info(f"Saving final processed dataset to: {processed_path}")
    df.to_csv(processed_path, index=False)
    logger.info(f"Final processed dataset saved ({len(df)} rows).")

    return staging_path, processed_path
