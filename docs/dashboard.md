# 📊 Streamlit Dashboard Guide - RetailSense-AI

## Overview
The **RetailSense-AI Streamlit Dashboard** is a multi-page interactive Business Intelligence (BI) engine with dark mode styling, custom CSS glassmorphism, responsive Plotly charts, global filters, and dynamic CSV downloads.

---

## Page Architecture

```text
dashboard/
├── app.py                      # Main entry point & layout routing
├── components/
│   ├── cards.py                # Reusable glassmorphic KPI cards & pipeline status badges
│   ├── charts.py               # Dark-themed Plotly chart builders for all pages
│   ├── sidebar.py              # RetailSense branding & global filter controls (Country, Year, Month)
│   └── styles.py               # Custom CSS design system, dark mode, animations & scrollbar
├── pages/
│   ├── 1_Home.py               # Executive Overview, KPIs, Top Charts & Pipeline Banner
│   ├── 2_Sales.py              # Sales Deep Dive, Temporal Velocity & Moving Averages
│   ├── 3_Products.py           # Product Leaderboard, Category Share & Pareto 80/20 Rule
│   ├── 4_Customers.py          # CLV Distribution, RFM Segmentation & Repeat Customer Ratio
│   ├── 5_Countries.py          # Geographical Heatmap & International Market Breakdown Table
│   └── 6_Pipeline.py           # Airflow DAG Health, Quality Gauges & Execution Timeline
├── utils.py                    # Dataset loading, DB fallback, dynamic filter & CSV exporter
└── README.md                   # Technical documentation
```

---

## Detailed Page Capabilities

| Page Name | Visualizations & Features | Data Sources |
|---|---|---|
| **1. Home** | 6 KPI Cards, Monthly Revenue Trend, Revenue by Country, Top 10 Products, Pipeline Status Card | Gold Layer & `processed` dataset |
| **2. Sales** | Monthly Revenue, Monthly Orders, MoM Growth %, Weekday Sales, Hourly Velocity, 3-Month Moving Average | `processed` & `monthly_sales.csv` |
| **3. Products** | Top Products by Revenue/Quantity, Category Share Donut, Category Revenue, Pareto 80/20 Line | `products.csv` & `processed` |
| **4. Customers** | Top Customers, CLV Histogram, Repeat vs. One-Time Ratio, Basket Size, RFM Scatter | `customers.csv` & `processed` |
| **5. Countries** | Global Revenue Map, Top Countries Bar Charts, Customer Density, Market Summary Table | `country_summary.csv` & `processed` |
| **6. Pipeline** | Airflow Status Banner, Cleanliness/Load Efficiency Gauges, Ingestion Audit Table, DAG Timeline | `pipeline_metadata.json` & `data_quality_report.json` |

---

## Running the Dashboard

```bash
streamlit run dashboard/app.py
```
Open browser at `http://localhost:8501`.
