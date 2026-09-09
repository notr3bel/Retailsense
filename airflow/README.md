# RetailSense-AI Airflow Orchestration 🌬️

This directory contains the Apache Airflow DAGs and configurations for orchestrating the **RetailSense-AI** data pipelines.

---

## 🏗️ DAG Architecture (`retail_pipeline_dag`)

The `retail_pipeline_dag` automates the end-to-end MLOps pipeline on a **daily schedule** with automatic retries, execution logging, failure callbacks, and versioning.

```text
                  ┌──────────────────────┐
                  │ 1. extract_data      │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │ 2. validate_data     │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │ 3. transform_data    │
                  └──────────┬───────────┘
                             │
            ┌────────────────┴────────────────┐
            ▼                                 ▼
┌──────────────────────┐           ┌──────────────────────┐
│ 4. load_postgres     │           │ 5. generate_gold_layer│
└───────────┬──────────┘           └──────────┬───────────┘
            └────────────────┬────────────────┘
                             ▼
                  ┌──────────────────────┐
                  │ 6. generate_reports  │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │ 7. pipeline_metadata │  ──> (Version: 1.0.0)
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │ 8. success_notification│
                  └──────────────────────┘
```

---

## 🛡️ Production Error & Failure Notification Handling

In production environments, task execution resilience and alert monitoring follow a multi-tier fallback architecture:

```text
    Task Failure
         │
         ▼
  Automatic Retry (2 retries, 5-min delay)
         │
         ▼
  Retries Exhausted / Still Failed
         │
         ▼
  on_task_failure_callback Execution
         │
         ▼
  Generate Detailed Error Log Entry
         │
         ▼
  Email Notification Alert (alerts@retailsense.ai)
```

### Callback Code Snippet
```python
def on_task_failure_callback(context: Dict[str, Any]) -> None:
    task_instance = context.get("task_instance")
    exception = context.get("exception")
    execution_date = context.get("execution_date")
    error_msg = f"Task [{task_instance.task_id}] FAILED on {execution_date}. Exception: {exception}"
    
    logger.error(f"🚨 PRODUCTION FAILURE ALERT: {error_msg}")
```

---

## 🛠️ Step-by-Step Airflow Setup Guide

### 1. Set Airflow Home Directory
```bash
export AIRFLOW_HOME="$(pwd)/airflow"
# On Windows PowerShell:
$env:AIRFLOW_HOME="$PWD/airflow"
```

### 2. Initialize Airflow Database
```bash
airflow db migrate
# (For Airflow 2.x):
# airflow db init
```

### 3. Create Admin User
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
```bash
airflow scheduler
```

### 5. Start Airflow Webserver
```bash
airflow webserver -p 8080
```
Access dashboard at `http://localhost:8080` (Credentials: `admin` / `admin`).

---

## 🚀 Running the DAG Manually

### Via CLI
```bash
airflow dags trigger retail_pipeline_dag
```

### Via Web UI
1. Navigate to `http://localhost:8080`.
2. Locate `retail_pipeline_dag` in the DAG list.
3. Toggle the DAG switch to **Active**.
4. Click **Trigger DAG** (▶).

---

## 📸 DAG Visualization & Screenshot Recommendations

For project reports, presentations, and technical documentation, capture the following Airflow views:

1. **DAG Graph View**:
   - Displays task nodes (`extract_data`, `validate_data`, `transform_data`, `load_postgres`, `generate_gold_layer`, `generate_reports`, `pipeline_metadata`, `success_notification`) and dependency arrows.
2. **Grid / Tree View**:
   - Shows historic execution runs and green success status squares across all 8 tasks.
3. **Successful DAG Run Overview**:
   - Confirms run ID, execution date, and total duration.
4. **Task Instance Logs**:
   - Log details showing row counts, validation checks, and data warehouse updates.

---

## 📄 Pipeline Metadata Output Example (`reports/pipeline_metadata.json`)

```json
{
    "pipeline_version": "1.0.0",
    "pipeline_run_id": "retail_run_1788963242",
    "execution_date": "2026-09-09T19:44:02.939449+05:30",
    "start_time": "2026-09-09T19:44:02.939467+05:30",
    "end_time": "2026-09-09T19:44:31.976963+05:30",
    "duration_seconds": 29.04,
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
