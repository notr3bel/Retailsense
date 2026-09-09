# 🧹 ETL Pipeline & Data Cleaning Specification - RetailSense-AI

This document outlines the extraction, data quality validation, transformation rules, and Gold layer aggregations implemented in **RetailSense-AI**.

---

## 1. Extract (`etl/extract.py`)
- Reads raw multi-year transactional files from `data/raw/`:
  - `Online Retail.xlsx`
  - `online_retail_II.csv`
- Normalizes initial column headers across both input formats into standard names.

---

## 2. Validate (`etl/validate.py`)
Scanning 1,609,280 raw records, the validation module detects:
- Missing values per column (e.g. missing customer IDs)
- Exact duplicate transaction rows
- Negative quantities and negative unit prices
- Cancelled order invoices (starting with `C`)

Generates `reports/data_quality_report.json` and `reports/data_quality_report.csv`.

---

## 3. Transform (`etl/transform.py`)
Applies data cleaning contracts:
- Strips leading/trailing whitespace from text fields (`description`, `country`).
- Converts `invoice_date` to pandas datetime format.
- Removes duplicate rows (`39,179` rows dropped).
- Filters out cancelled orders (`28,782` rows dropped).
- Drops transactions with missing `customer_id` (`378,087` rows dropped).
- Filters invalid quantities ($\le 0$) and invalid unit prices ($\le 0$).
- Computes `total_price` ($quantity \times unit\_price$).
- Derives temporal features (`year`, `month`, `month_name`, `weekday`, `hour`).

Final clean output saved to `data/processed/final_dataset.csv` (`1,172,117` clean rows).

---

## 4. Load (`database/load_postgres.py` & `etl/load.py`)
- Saves `data/staging/cleaned_data.csv` and `data/processed/final_dataset.csv`.
- Populates PostgreSQL Star Schema DW (`sales_fact`, `customer_dim`, `product_dim`, `date_dim`, `country_dim`).

---

## 5. Gold Layer Generation (`etl/gold.py`)
Generates 5 specialized analytical datasets in `data/gold/`:
1. `customers.csv`: Customer RFM metrics, total spent, order count, AOV, first/last purchase dates.
2. `products.csv`: Stock code, description, derived category, quantity sold, total revenue.
3. `country_summary.csv`: Country customer count, total orders, total items sold, total revenue.
4. `monthly_sales.csv`: Monthly breakdown of orders, total revenue, and average order value.
5. `sales_summary.csv`: Macro enterprise KPIs (total revenue, total orders, active customers, total products).
