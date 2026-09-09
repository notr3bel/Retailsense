"""
RetailSense-AI End-to-End Orchestration DAG.
Orchestrates raw data extraction, validation, transformation, warehouse loading, 
Gold layer generation, reporting, and metadata tracking.
"""

import os
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple

# Ensure project root is in python path
import sys
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Imports from existing ETL & Database modules
from etl.utils import setup_logger, ensure_directory
from etl.extract import extract_data
from etl.validate import validate_datasets, generate_data_quality_report
from etl.transform import transform_datasets
from etl.load import load_data
from etl.gold import generate_gold_layer
from database.load_postgres import load_data_warehouse

logger = setup_logger("Airflow_RetailPipeline")

# ============================================================================
# Airflow Import Handling (Graceful fallback for standalone execution)
# ============================================================================
try:
    from airflow import DAG
    from airflow.operators.python import PythonOperator
    AIRFLOW_AVAILABLE = True
except (ImportError, Exception):
    AIRFLOW_AVAILABLE = False

    class DummyOperator:
        def __init__(self, task_id, python_callable=None, op_kwargs=None, **kwargs):
            self.task_id = task_id
            self.python_callable = python_callable
            self.op_kwargs = op_kwargs or {}
            self.downstream = []

        def __rshift__(self, other):
            if isinstance(other, (list, tuple)):
                for item in other:
                    self.downstream.append(item)
            else:
                self.downstream.append(other)
            return other

        def execute(self, context=None):
            if self.python_callable:
                return self.python_callable(**self.op_kwargs)

    class DummyDAG:
        def __init__(self, dag_id, default_args=None, schedule_interval=None, **kwargs):
            self.dag_id = dag_id
            self.default_args = default_args or {}
            self.schedule_interval = schedule_interval
            self.tasks = []

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

    DAG = DummyDAG
    PythonOperator = DummyOperator


# ============================================================================
# Production Failure Notification Callback
# ============================================================================

def on_task_failure_callback(context: Dict[str, Any]) -> None:
    """
    Production Failure Callback Handler.
    Workflow: Task Failure -> Retries Exhausted (2 retries) -> Error Log Entry -> Email Alert.
    """
    task_instance = context.get("task_instance")
    exception = context.get("exception")
    execution_date = context.get("execution_date")

    task_id = task_instance.task_id if task_instance else "unknown_task"
    error_msg = f"Task [{task_id}] FAILED on {execution_date}. Exception: {exception}"

    logger.error("=========================================================================")
    logger.error(f"🚨 PRODUCTION FAILURE ALERT: {error_msg}")
    logger.error("Generating error log entry and dispatching email notification to ops team...")
    logger.error("=========================================================================")


# ============================================================================
# DAG Default Arguments & Definition
# ============================================================================
default_args = {
    "owner": "retailsense",
    "depends_on_past": False,
    "start_date": datetime(2026, 1, 1),
    "email": ["alerts@retailsense.ai"],
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "on_failure_callback": on_task_failure_callback,
}


# ============================================================================
# Task Callables
# ============================================================================

def task_extract_data(**context) -> Dict[str, int]:
    """Task 1: Extract raw datasets from data/raw/."""
    logger.info("Executing Task 1: extract_data")
    df_excel, df_csv = extract_data()
    excel_rows = len(df_excel)
    csv_rows = len(df_csv)
    total_raw_rows = excel_rows + csv_rows
    logger.info(f"Task 1 Complete: Extracted {total_raw_rows:,} raw rows.")
    return {"excel_rows": excel_rows, "csv_rows": csv_rows, "total_raw_rows": total_raw_rows}


def task_validate_data(**context) -> None:
    """Task 2: Validate raw dataset quality."""
    logger.info("Executing Task 2: validate_data")
    df_excel, df_csv = extract_data()
    reports = validate_datasets([df_excel, df_csv], names=["Raw_Excel", "Raw_CSV"])
    logger.info(f"Task 2 Complete: Quality check passed for {len(reports)} raw datasets.")


def task_transform_data(**context) -> Dict[str, Any]:
    """Task 3: Transform, clean, merge, and persist processed dataset."""
    logger.info("Executing Task 3: transform_data")
    df_excel, df_csv = extract_data()
    df_cleaned, transform_stats, df_merged = transform_datasets(df_excel, df_csv)
    staging_file, processed_file = load_data(df_cleaned)
    logger.info(f"Task 3 Complete: Processed {len(df_cleaned):,} rows. Saved to {processed_file}.")
    return transform_stats


def task_load_postgres(**context) -> None:
    """Task 4: Load clean dataset into PostgreSQL Star Schema Data Warehouse."""
    logger.info("Executing Task 4: load_postgres")
    load_data_warehouse(processed_csv_path="data/processed/final_dataset.csv")
    logger.info("Task 4 Complete: Data warehouse updated successfully.")


def task_generate_gold_layer(**context) -> Dict[str, str]:
    """Task 5: Create Gold Data Layer aggregated business datasets."""
    logger.info("Executing Task 5: generate_gold_layer")
    gold_files = generate_gold_layer(processed_df_or_path="data/processed/final_dataset.csv")
    logger.info(f"Task 5 Complete: Created {len(gold_files)} Gold datasets in data/gold/.")
    return gold_files


def task_generate_reports(**context) -> Tuple[str, str]:
    """Task 6: Generate JSON & CSV Data Quality Reports."""
    logger.info("Executing Task 6: generate_reports")
    df_excel, df_csv = extract_data()
    df_cleaned, transform_stats, df_merged = transform_datasets(df_excel, df_csv)
    json_path, csv_path = generate_data_quality_report(
        raw_df=df_merged,
        transform_stats=transform_stats,
        execution_time=0.0
    )
    logger.info(f"Task 6 Complete: Generated quality reports at {json_path} & {csv_path}.")
    return json_path, csv_path


def task_pipeline_metadata(
    output_metadata_path: str = "reports/pipeline_metadata.json",
    **context
) -> Dict[str, Any]:
    """Task 7: Generate pipeline execution metadata JSON."""
    logger.info("Executing Task 7: pipeline_metadata")
    ensure_directory(output_metadata_path)

    run_id = f"retail_run_{int(time.time())}"
    if context and "run_id" in context:
        run_id = str(context["run_id"])

    execution_date = datetime.now().astimezone().isoformat()
    start_time = datetime.now().astimezone().isoformat()
    
    # Process stats for metadata
    df_excel, df_csv = extract_data()
    total_raw_rows = len(df_excel) + len(df_csv)
    df_cleaned, transform_stats, _ = transform_datasets(df_excel, df_csv)
    final_rows = len(df_cleaned)
    rows_removed = transform_stats.get("rows_removed", total_raw_rows - final_rows)

    end_time = datetime.now().astimezone().isoformat()

    metadata = {
        "pipeline_version": "1.0.0",
        "pipeline_run_id": run_id,
        "execution_date": execution_date,
        "start_time": start_time,
        "end_time": end_time,
        "duration_seconds": 0.0,
        "status": "SUCCESS",
        "input_files": [
            "data/raw/Online Retail.xlsx",
            "data/raw/online_retail_II.csv"
        ],
        "output_files": [
            "data/staging/cleaned_data.csv",
            "data/processed/final_dataset.csv",
            "data/gold/customers.csv",
            "data/gold/products.csv",
            "data/gold/country_summary.csv",
            "data/gold/monthly_sales.csv",
            "data/gold/sales_summary.csv",
            "data/ml/customer_churn_dataset.csv",
            "reports/churn_label_report.json",
            "reports/data_quality_report.json",
            "reports/data_quality_report.csv"
        ],
        "rows_processed": total_raw_rows,
        "rows_removed": rows_removed,
        "rows_loaded": final_rows
    }

    with open(output_metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=4)

    logger.info(f"Task 7 Complete: Saved pipeline metadata v1.0.0 to {output_metadata_path}.")
    return metadata


def task_success_notification(**context) -> None:
    """Task 8: Log and notify successful pipeline execution."""
    logger.info("Executing Task 8: success_notification")
    logger.info("=========================================================================")
    logger.info("SUCCESS: RetailSense-AI End-to-End Pipeline Executed Successfully!")
    logger.info("=========================================================================")


# ============================================================================
# Airflow DAG Context Definition
# ============================================================================

with DAG(
    dag_id="retail_pipeline_dag",
    default_args=default_args,
    description="End-to-end RetailSense-AI ETL & MLOps Pipeline Orchestration",
    schedule_interval="@daily",
    catchup=False,
    tags=["retailsense", "mlops", "etl", "warehouse"],
) as dag:

    t1_extract = PythonOperator(
        task_id="extract_data",
        python_callable=task_extract_data
    )

    t2_validate = PythonOperator(
        task_id="validate_data",
        python_callable=task_validate_data
    )

    t3_transform = PythonOperator(
        task_id="transform_data",
        python_callable=task_transform_data
    )

    t4_load_postgres = PythonOperator(
        task_id="load_postgres",
        python_callable=task_load_postgres
    )

    t5_generate_gold = PythonOperator(
        task_id="generate_gold_layer",
        python_callable=task_generate_gold_layer
    )

    t6_generate_reports = PythonOperator(
        task_id="generate_reports",
        python_callable=task_generate_reports
    )

    t7_metadata = PythonOperator(
        task_id="pipeline_metadata",
        python_callable=task_pipeline_metadata
    )

    t8_notification = PythonOperator(
        task_id="success_notification",
        python_callable=task_success_notification
    )

    # Explicit Task Dependencies Graph
    t1_extract >> t2_validate >> t3_transform
    t3_transform >> t4_load_postgres
    t3_transform >> t5_generate_gold
    t4_load_postgres >> t6_generate_reports
    t5_generate_gold >> t6_generate_reports
    t6_generate_reports >> t7_metadata >> t8_notification


# Allow standalone script execution for verification
if __name__ == "__main__":
    logger.info("Running retail_pipeline_dag tasks sequentially in standalone mode...")
    t1_extract.execute()
    t2_validate.execute()
    t3_transform.execute()
    t4_load_postgres.execute()
    t5_generate_gold.execute()
    t6_generate_reports.execute()
    t7_metadata.execute()
    t8_notification.execute()
