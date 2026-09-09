# RetailSense-AI Airflow Orchestration 🌬️

This directory contains the Apache Airflow DAGs and configurations for orchestrating the **RetailSense-AI** data pipelines.

---

## 🏗️ DAG Architecture (`retail_pipeline_dag`)

The `retail_pipeline_dag` automates the end-to-end MLOps pipeline on a **daily schedule** with automatic retries and execution logging.

```text
[1. extract_data]
        │
        ▼
[2. validate_data]
        │
        ▼
[3. transform_data]
        │
   ┌────┴────────────────────────┐
   ▼                             ▼
[4. load_postgres]    [5. generate_gold_layer]
   └────┬────────────────────────┘
        ▼
[6. generate_reports]
        │
        ▼
[7. pipeline_metadata]
        │
        ▼
[8. success_notification]
```

---

## 🛠️ Step-by-Step Airflow Setup Guide

### 1. Set Airflow Home Directory
```bash
# Set Airflow environment path
export AIRFLOW_HOME="$(pwd)/airflow"
# On Windows PowerShell:
$env:AIRFLOW_HOME="$PWD/airflow"
```

### 2. Initialize Airflow Database
Initialize or migrate the Airflow metadata database:
```bash
airflow db migrate
# (For Airflow 2.x):
# airflow db init
```

### 3. Create Admin User
Create an administrator account to access the web UI:
```bash
airflow users create \
    --username admin \
    --firstname Retail \
    --lastname Sense \
    --role Admin \
    --email admin@retailsense.ai \
    --password admin
```

### 4. Start Airflow Scheduler
Launch the background scheduler process:
```bash
airflow scheduler
```

### 5. Start Airflow Webserver
Launch the Airflow UI webserver on port `8080`:
```bash
airflow webserver -p 8080
```
Access the dashboard at `http://localhost:8080` (Credentials: `admin` / `admin`).

---

## 🚀 Running the DAG Manually

### Via CLI
Trigger immediate execution of `retail_pipeline_dag`:
```bash
airflow dags trigger retail_pipeline_dag
```

Check DAG execution state:
```bash
airflow dags list-runs -d retail_pipeline_dag
```

### Via Webserver UI
1. Navigate to `http://localhost:8080`.
2. Locate `retail_pipeline_dag` in the DAG list.
3. Toggle the DAG switch to **Active**.
4. Click the **Trigger DAG** (▶) button on the right action menu.

---

## 📸 Screenshots for Project Report

Include the following screenshots in project documentation and submissions:

1. **DAG Grid / Tree View**:
   - Shows status of historical runs and green success blocks across all 8 tasks.
2. **DAG Graph View**:
   - Visual dependency graph illustrating parallel branching (`load_postgres` & `generate_gold_layer`).
3. **Task Instance Details & Execution Logs**:
   - Detailed task log for `transform_data` showing rows loaded vs cleaned.
4. **Generated Pipeline Metadata**:
   - Content of [`reports/pipeline_metadata.json`](file:///d:/Projects/Retailsense/reports/pipeline_metadata.json).

---

## 📄 Pipeline Metadata Output Example (`reports/pipeline_metadata.json`)

```json
{
    "pipeline_run_id": "retail_run_1741549100",
    "execution_date": "2026-09-09T19:39:00+05:30",
    "start_time": "2026-09-09T19:39:00+05:30",
    "end_time": "2026-09-09T19:39:50+05:30",
    "duration_seconds": 50.25,
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
        "reports/data_quality_report.json",
        "reports/data_quality_report.csv"
    ],
    "rows_processed": 1609280,
    "rows_removed": 437163,
    "rows_loaded": 1172117
}
```
