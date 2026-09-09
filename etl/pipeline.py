"""
Master ETL Pipeline Orchestrator for RetailSense-AI.
Executes the end-to-end data pipeline: Extract -> Validate -> Transform -> Load -> Report -> Gold Layer.
"""

import time
from typing import Dict, Any
from etl.utils import setup_logger
from etl.extract import extract_data
from etl.validate import validate_datasets, generate_data_quality_report
from etl.transform import transform_datasets
from etl.load import load_data
from etl.gold import generate_gold_layer
from ml.churn_label import generate_churn_labels

logger = setup_logger("ETL_Pipeline")


def run_pipeline() -> Dict[str, Any]:
    """
    Orchestrates the complete ETL pipeline execution, quality reports, and Gold Layer creation.
    
    Pipeline Steps:
        1. Extract: Reads raw datasets from data/raw/.
        2. Validate: Checks raw dataset quality & missingness.
        3. Transform: Standardizes, cleans, filters, merges, & enriches data.
        4. Load: Persists datasets to data/staging/ and data/processed/.
        5. Quality Report: Generates reports/data_quality_report.json & .csv.
        6. Gold Layer: Generates analytical datasets in data/gold/.
        
    Returns:
        Dict[str, Any]: Pipeline execution summary metrics.
    """
    start_time = time.time()
    logger.info("==================================================")
    logger.info("Starting RetailSense-AI End-to-End ETL Pipeline")
    logger.info("==================================================")

    # 1. EXTRACT
    df_excel, df_csv = extract_data()
    rows_loaded = len(df_excel) + len(df_csv)

    # 2. VALIDATE RAW DATASETS
    validate_datasets([df_excel, df_csv], names=["Raw_Excel", "Raw_CSV"])

    # 3. TRANSFORM
    df_cleaned, transform_stats, df_merged = transform_datasets(df_excel, df_csv)

    # 4. LOAD STAGING & PROCESSED
    staging_file, processed_file = load_data(df_cleaned)

    # 5. GENERATE GOLD DATA LAYER
    gold_files = generate_gold_layer(processed_df_or_path=df_cleaned)

    # 6. GENERATE CUSTOMER CHURN DATASET (PHASE 4.1 ML TARGET LABELS)
    churn_df, churn_report = generate_churn_labels(
        input_data=df_cleaned,
        output_csv_path="data/ml/customer_churn_dataset.csv",
        output_report_path="reports/churn_label_report.json"
    )

    execution_time = round(time.time() - start_time, 2)

    # 7. GENERATE DATA QUALITY REPORTS
    json_report_path, csv_report_path = generate_data_quality_report(
        raw_df=df_merged,
        transform_stats=transform_stats,
        execution_time=execution_time
    )

    rows_removed = transform_stats["rows_removed"]
    missing_handled = transform_stats["missing_customer_ids_handled"]
    final_rows = transform_stats["final_rows"]

    summary = {
        "rows_loaded": rows_loaded,
        "final_rows": final_rows,
        "rows_removed": rows_removed,
        "missing_values_handled": missing_handled,
        "execution_time_seconds": execution_time,
        "staging_file": staging_file,
        "processed_file": processed_file,
        "gold_files": gold_files,
        "churn_dataset": "data/ml/customer_churn_dataset.csv",
        "churn_report": "reports/churn_label_report.json",
        "json_report": json_report_path,
        "csv_report": csv_report_path,
    }

    # Print summary output
    print("\n==================================================")
    print("RetailSense-AI ETL Pipeline Execution Summary")
    print("==================================================")
    print(f"  * Rows loaded            : {rows_loaded:,}")
    print(f"  * Final rows processed   : {final_rows:,}")
    print(f"  * Rows removed           : {rows_removed:,}")
    print(f"  * Missing values handled : {missing_handled:,}")
    print(f"  * Gold Layer Datasets    : {len(gold_files)} generated in data/gold/")
    print(f"  * Churn Target Dataset   : {len(churn_df):,} customers (Churn Rate: {churn_report['churn_rate_pct']})")
    print(f"  * Execution time         : {execution_time} seconds")
    print(f"  * JSON Quality Report    : {json_report_path}")
    print(f"  * CSV Quality Report     : {csv_report_path}")
    print("==================================================\n")

    logger.info(f"ETL Pipeline finished successfully in {execution_time} seconds.")
    return summary


if __name__ == "__main__":
    run_pipeline()
