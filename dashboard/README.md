# 🛍️ RetailSense-AI Streamlit Dashboard

Production-quality, multi-page interactive Business Intelligence (BI) and MLOps Operations Dashboard built with **Streamlit** and **Plotly**.

---

## 🏗️ Dashboard Architecture

```text
dashboard/
├── app.py                      # Main application entry point
├── components/
│   ├── cards.py                # Reusable glassmorphic KPI cards & status widgets
│   ├── charts.py               # Plotly dark theme chart builders
│   ├── sidebar.py              # Global sidebar navigation & filter controls
│   └── styles.py               # Custom CSS design system & dark BI theme
├── pages/
│   ├── 1_Home.py               # Executive Overview & Pipeline Status
│   ├── 2_Sales.py              # Sales Analytics & Temporal Trends
│   ├── 3_Products.py           # Product Performance & Pareto Analysis
│   ├── 4_Customers.py          # Customer Lifetime Value & RFM Segmentation
│   ├── 5_Countries.py          # Geographical Intelligence & Global Heatmap
│   └── 6_Pipeline.py           # Airflow DAG Operations & Data Quality
├── utils.py                    # Data loading, DB fallback, dynamic filtering & CSV exports
└── README.md                   # Documentation
```

---

## 🌟 Key Features

1. **Enterprise Dark BI Theme**:
   - Built with modern fonts (Inter), custom CSS glassmorphism cards, glowing status pill badges, subtle hover micro-animations, and styled download buttons.
2. **Dynamic Global Filtering**:
   - Interactive sidebar filters for **Country**, **Year**, and **Month** that dynamically re-aggregate metrics across all pages.
3. **Data Layer Fallback**:
   - Reads directly from PostgreSQL / Data Warehouse when online, with automatic seamless fallback to `data/gold/*.csv` and `data/processed/final_dataset.csv`.
4. **CSV Exporting**:
   - Instantaneous CSV download buttons on every page for export capability.
5. **Interactive Plotly Visualizations**:
   - Monthly Revenue & Order Volume Trends
   - Month-over-Month Revenue Growth % & 3-Month Moving Average
   - Peak Hourly & Weekday Sales Velocity
   - Product Revenue Leaderboards & Quantity Sold
   - Pareto Analysis (80/20 Cumulative Revenue Rule)
   - Product Category Donut Share
   - Top Customer Spend & Customer Lifetime Value (CLV) Histogram
   - RFM (Recency, Frequency, Monetary) Segmentation Scatter
   - Repeat vs. One-Time Customer Ratios
   - Global Revenue Choropleth Heatmap Map
   - Airflow MLOps Data Cleanliness & Load Efficiency Gauges
   - Airflow DAG Task Execution Timeline Gantt Chart

---

## 🚀 How to Run the Dashboard

Make sure your virtual environment is active:

```bash
# Windows PowerShell
.\venv\Scripts\Activate.ps1
```

Run the Streamlit application:

```bash
streamlit run dashboard/app.py
```

The dashboard will open automatically in your web browser at `http://localhost:8501`.

---

## 📖 Pages Guide

| Page | Description | Key Components |
|---|---|---|
| **1. Home** | Executive Financial Overview & Pipeline Status | 6 KPI Cards, Revenue Trend, Top Countries, Top Products, Pipeline Status Card |
| **2. Sales** | Sales Deep Dive & Temporal Analytics | Monthly Revenue/Orders, MoM Growth %, Weekday/Hourly Sales Velocity, Moving Average |
| **3. Products** | Product & Category Intelligence | Top Products, Category Share, Quantity Sold, Pareto 80/20 Chart |
| **4. Customers** | Customer Behavior & Segmentation | Top Customers, CLV Histogram, Repeat vs New Ratio, Basket Size, RFM Scatter |
| **5. Countries** | Geographical Intelligence | Global Choropleth Map, Country Bar Charts, International Market Table |
| **6. Pipeline** | MLOps & Data Quality Operations | Pipeline Health Status, Row Cleanliness Gauges, Data Quality Report Table, Task Timeline |
