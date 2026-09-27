# RetailSense-AI: Comprehensive Project Documentation & Architecture Guide

## 1. Executive Summary

**RetailSense-AI** is an enterprise-grade, end-to-end E-Commerce Data Engineering, Analytics, and Machine Learning platform. It ingests raw transaction logs from online retail operations, processes them through a **Medallion Data Lakehouse Architecture** (Raw → Bronze → Silver → Gold), stores analytical models in a **Star Schema Data Warehouse**, orchestrates automated workflows using **Apache Airflow**, tracks ML experiments via **MLflow**, serves real-time predictive APIs using **FastAPI**, and provides visual business intelligence through a **Streamlit Dashboard**.

---

## 2. System Architecture Overview

```
+-----------------------------------------------------------------------------------+
|                                  DATA SOURCES                                     |
|                       Raw Transaction CSV / Databases                             |
+-----------------------------------------------------------------------------------+
                                         │
                                         ▼
+-----------------------------------------------------------------------------------+
|                             ETL & MEDALLION PIPELINE                              |
|  [Raw Data] ──► [Bronze Layer] ──► [Silver Layer] ──► [Gold Layer (Aggregates)]   |
|                 (Validation &       (Deduplication,   (Star Schema Tables /   |
|                  Raw Storage)        Cleaning, RFM)    Analytics Data)        |
+-----------------------------------------------------------------------------------+
                                         │
                   ┌─────────────────────┴─────────────────────┐
                   ▼                                           ▼
+------------------------------------+       +------------------------------------+
|       DATA WAREHOUSE & DB          |       |         MACHINE LEARNING           |
|  SQLite / PostgreSQL (Star Schema) |       |  Feature Engineering & ML Pipeline |
|   - FactSales                      |       |   - Customer Segmentation (RFM)    |
|   - DimCustomer, DimProduct, etc.  |       |   - Churn Prediction (XGBoost/RF)  |
+------------------------------------+       |   - Sales Forecasting (Prophet)    |
                   │                         |   - Product Recommendations        |
                   │                         |  Tracked via MLflow Registry       |
                   │                         +------------------------------------+
                   │                                           │
                   ▼                                           ▼
+-----------------------------------------------------------------------------------+
|                                   SERVING LAYER                                   |
|  ┌─────────────────────────────────┐   ┌───────────────────────────────────────┐  |
|  │        FastAPI REST Service     │   │      Streamlit BI Dashboard           │  |
|  │ - Real-time ML Inference APIs   │   │ - Interactive KPIs & Visual Analytics │  |
|  │ - Health checks & Swagger Docs  │   │ - Cached Data Layer (load_all_datasets│  |
|  └─────────────────────────────────┘   └───────────────────────────────────────┘  |
+-----------------------------------------------------------------------------------+
                                         │
                                         ▼
+-----------------------------------------------------------------------------------+
|                           ORCHESTRATION & CONTAINERIZATION                        |
|  - Apache Airflow (Automated DAG schedules for ETL & ML re-training)              |
|  - Docker & Docker-Compose (Multi-container deployment for API, Dashboard, DB)    |
+-----------------------------------------------------------------------------------+
```

---

## 3. Data Pipeline & Medallion Architecture (`/etl`)

The ETL process follows the Medallion Architecture pattern:

### A. Raw & Ingestion Layer (`etl/extract.py`, `etl/ingest.py`)
- Reads initial raw transactions (`Online Retail II` dataset) containing invoice numbers, stock codes, descriptions, quantities, invoice dates, unit prices, customer IDs, and countries.

### B. Bronze Layer (`etl/validate.py`)
- Standardizes column names into snake_case (`invoice_no`, `stock_code`, `customer_id`, etc.).
- Applies data quality validation rules (ensuring non-null fields, correct data types, and valid date formats).
- Generates data validation and data quality reports saved under `reports/`.

### C. Silver Layer (`etl/transform.py`)
- **Data Cleaning**: Filters out invalid/negative unit prices and missing invoice records.
- **Returns & Cancellations**: Identifies cancelled transactions (invoices starting with `'C'`) and calculates net quantities and total line amounts (`total_amount = quantity * unit_price`).
- **Feature Computation**: Extracts datetime components (`year`, `month`, `year_month`, `weekday`, `hour`).

### D. Gold Layer (`etl/gold.py`)
Generates aggregated, analytical data models designed for fast querying:
- `sales_summary.csv`: Overall business performance, revenue, order count, unique customers.
- `monthly_sales.csv`: Monthly trends for revenue, quantity sold, and order counts.
- `products.csv`: Product-level revenue, total units sold, average price, and transaction counts.
- `customers.csv`: Customer-level aggregation including Recency, Frequency, Monetary (RFM) values.
- `country_summary.csv`: Geographic sales breakdown by country.

---

## 4. Data Warehouse & Schema (`/database`)

RetailSense includes a relational Data Warehouse setup in both SQLite (`retailsense_dw.db`) and PostgreSQL (`database/schema.sql`):

### Star Schema Structure
- **Fact Table**: `fact_sales` (transaction line items, quantities, total amounts, keys to dimension tables).
- **Dimension Tables**:
  - `dim_customer`: Customer metadata, location, segmentation tag.
  - `dim_product`: Stock code, description, category, unit price.
  - `dim_date`: Date hierarchy (day, month, quarter, year, day of week).
  - `dim_country`: Country details.

Database loading is handled by `database/load_postgres.py` and `database/create_tables.py`.

---

## 5. Machine Learning Pipeline (`/ml`)

The Machine Learning subsystem delivers predictive insights across four key business domains:

### 1. Customer Segmentation (RFM + K-Means)
- Calculates **Recency** (days since last purchase), **Frequency** (total orders), and **Monetary** (total spent).
- Uses K-Means clustering to classify customers into personas: *VIP/Champions*, *Loyal Customers*, *At-Risk*, and *Lost/Hibernating*.

### 2. Customer Churn Prediction
- Defines churn based on inactivity thresholds (e.g., no purchases in 90+ days).
- Trains classification models (Random Forest / XGBoost) to predict churn probability for each customer.
- Outputs feature importances to identify key drivers of customer attrition.

### 3. Sales & Demand Forecasting
- Uses time-series models (Prophet / Ridge Regression / ARIMA) on daily/weekly aggregated revenue data.
- Forecasts future sales revenue and order volume to assist in inventory planning.

### 4. Product Recommendation System
- Built using Market Basket Analysis (Apriori / FP-Growth) and Collaborative Filtering.
- Identifies items frequently bought together to power cross-sell and up-sell recommendations.

### MLflow Experiment Tracking (`ml/mlflow_tracking.py`)
- Logs model parameters, evaluation metrics (RMSE, MAE, R², Accuracy, F1-score, ROC-AUC), and model artifacts.
- Manages model versioning and registry for seamless deployment to the API service.

---

## 6. REST API Service (`/api`)

Built with **FastAPI**, the API service exposes machine learning predictions and analytics to external applications.

### Key Endpoints:
- `GET /health`: Health check and system status.
- `POST /predict/segment`: Accepts customer metrics and returns their predicted RFM segment.
- `POST /predict/churn`: Accepts customer history and returns churn probability + risk category.
- `POST /predict/forecast`: Returns sales forecasts for specified future horizons.
- `POST /predict/recommendations`: Returns top recommended products given a product ID or customer basket.
- `/docs`: Interactive OpenAPI / Swagger documentation.

---

## 7. Streamlit Interactive Dashboard (`/dashboard`)

The Streamlit dashboard provides visual analytics and self-service BI for business stakeholders.

### App Structure:
- **`app.py`**: Main application shell, sidebar navigation, theme config, and dataset initialization via cached function `load_all_datasets()`.
- **`utils.py`**: Data loading and helper utilities. `@st.cache_data(ttl=3600)` caches Gold and Processed datasets in memory to ensure fast page loads.
- **Pages**:
  - `1_Home.py`: Executive Overview (Revenue, Orders, Avg Order Value, High-level Trends).
  - `2_Sales.py`: Detailed Sales & Revenue Analytics (Time-of-day, Day-of-week, Monthly trends).
  - `3_Products.py`: Product Performance & Inventory Analytics (Top sellers, revenue drivers).
  - `4_Customers.py`: Customer Analytics & Lifetime Value breakdown.
  - `5_Countries.py`: International & Regional Geographic Distribution.
  - `6_Pipeline.py`: ETL Pipeline Monitoring, Data Quality Reports, and Execution Metadata.
  - `7_Machine_Learning.py`: Interactive ML Inference Playground (Run real-time Churn, Segmentation, and Recommendations directly from the UI).

---

## 8. Workflow Orchestration (`/airflow`)

Automated using **Apache Airflow**:
- **`retailsense_etl_dag.py`**: Scheduled daily pipeline that extracts raw data, runs bronze/silver/gold transformations, validates data quality, and updates the Data Warehouse.
- **`retailsense_ml_dag.py`**: Scheduled weekly pipeline that extracts fresh features, re-trains machine learning models, logs metrics to MLflow, and updates production model artifacts.

---

## 9. Deployment & Containerization (`/docker`)

Containerized using **Docker** and orchestrated via **Docker Compose**:
- **`Dockerfile.api`**: Python container running FastAPI with Uvicorn server.
- **`Dockerfile.dashboard`**: Container running the Streamlit dashboard on port 8501.
- **`docker-compose.yml`**: Spins up the complete ecosystem (FastAPI, Streamlit, PostgreSQL database, MLflow server, and Airflow scheduler/webserver).

---

## 10. Summary of Execution Commands

| Component | Command |
|---|---|
| **Run ETL Pipeline** | `python -m etl.pipeline` |
| **Train ML Models** | `python -m ml.train` |
| **Start FastAPI Server** | `uvicorn api.main:app --reload --port 8000` |
| **Launch Dashboard** | `streamlit run dashboard/app.py` |
| **Run Test Suite** | `pytest` |
| **Launch Docker Stack** | `docker-compose up --build` |
