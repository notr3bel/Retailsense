# ⏱️ Apache Airflow Guide - RetailSense-AI

This document provides instructions for configuring and executing the **Apache Airflow Orchestration DAG** for RetailSense-AI.

---

## Airflow DAG Overview

- **DAG Name**: `retail_pipeline_dag`
- **Schedule**: `@daily` (Daily execution)
- **Retries**: 2 retries per task with a 5-minute retry delay
- **Location**: [`airflow/dags/retail_pipeline_dag.py`](file:///d:/Projects/Retailsense/airflow/dags/retail_pipeline_dag.py)

---

## Task Execution Graph

```text
[extract_data] ➔ [validate_data] ➔ [transform_data] ➔ [load_postgres] ➔ [generate_gold_layer] ➔ [generate_reports] ➔ [pipeline_metadata] ➔ [success_notification]
```

### Task Descriptions

1. `extract_data`: Reads raw Excel (`Online Retail.xlsx`) and CSV (`online_retail_II.csv`) files from `data/raw/`.
2. `validate_data`: Performs validation check for nulls, duplicates, cancelled orders, and negative values.
3. `transform_data`: Normalizes column names, converts dates, computes derived features, and outputs `cleaned_data.csv` and `final_dataset.csv`.
4. `load_postgres`: Populates dimension and fact tables in the PostgreSQL Star Schema Data Warehouse.
5. `generate_gold_layer`: Computes business aggregate datasets (`customers`, `products`, `monthly_sales`, `country_summary`, `sales_summary`).
6. `generate_reports`: Generates JSON and CSV Data Quality reports in `reports/`.
7. `pipeline_metadata`: Writes pipeline metadata including run ID, duration, version, and row processing metrics to `reports/pipeline_metadata.json`.
8. `success_notification`: Logs pipeline run success completion message.

---

## Airflow Setup Instructions

```bash
# Set Airflow Home
export AIRFLOW_HOME=$(pwd)/airflow

# Initialize Airflow Database
airflow db init

# Create Admin User
airflow users create \
    --username admin \
    --firstname Retail \
    --lastname Admin \
    --role Admin \
    --email admin@retailsense.ai \
    --password admin

# Start Scheduler & Webserver
airflow scheduler &
airflow webserver --port 8080
```

Access the Airflow Web UI at `http://localhost:8080`.
