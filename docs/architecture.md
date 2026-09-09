# 🏛️ Architecture Specification - RetailSense-AI

## Overview
RetailSense-AI uses an **Enterprise Data Warehouse Architecture** based on the Medallion Data Design pattern (Bronze $\rightarrow$ Silver $\rightarrow$ Gold) combined with a relational **Star Schema** Data Warehouse.

---

## Data Layer Architecture

```mermaid
flowchart LR
    subgraph Bronze Layer [Raw Data]
        B1[Online Retail.xlsx]
        B2[online_retail_II.csv]
    end

    subgraph Silver Layer [Processed & Cleaned]
        S1[cleaned_data.csv]
        S2[final_dataset.csv]
        S3[(PostgreSQL Star DW)]
    end

    subgraph Gold Layer [Business Aggregates]
        G1[customers.csv]
        G2[products.csv]
        G3[monthly_sales.csv]
        G4[country_summary.csv]
        G5[sales_summary.csv]
    end

    subgraph Presentation Layer [Streamlit BI]
        P1[1_Home.py]
        P2[2_Sales.py]
        P3[3_Products.py]
        P4[4_Customers.py]
        P5[5_Countries.py]
        P6[6_Pipeline.py]
    end

    Bronze Layer --> Silver Layer
    Silver Layer --> Gold Layer
    Gold Layer --> Presentation Layer
    Silver Layer --> Presentation Layer
```

---

## Star Schema Data Model

The PostgreSQL Data Warehouse organizes data into a central **Fact Table** surrounded by normalized **Dimension Tables**:

```text
                  +-------------------+
                  |   customer_dim    |
                  +-------------------+
                  | customer_id (PK)  |
                  | first_name        |
                  | country           |
                  +---------+---------+
                            |
                            | 1:N
                            v
+----------------+  +-------+---------+  +-------------------+
|   product_dim  |  |    sales_fact   |  |     date_dim      |
+----------------+  +-----------------+  +-------------------+
| product_id (PK)|  | sales_id (PK)   |  | date_id (PK)      |
| stock_code     |<-| product_id (FK) |->| full_date         |
| description    |  | customer_id (FK)|  | year              |
| category       |  | date_id (FK)    |  | month             |
+----------------+  | country_id (FK) |  | month_name        |
                    | quantity        |  | day               |
                    | unit_price      |  | weekday           |
                    | total_price     |  +-------------------+
                    +-------+---------+
                            |
                            | N:1
                            v
                  +---------+---------+
                  |   country_dim     |
                  +-------------------+
                  | country_id (PK)   |
                  | country_name      |
                  +-------------------+
```

---

## Technical Component Details

1. **Extraction**:
   - Accepts both `.xlsx` and `.csv` sources.
   - Normalizes raw field types and encoding quirks.
2. **Validation Engine**:
   - Enforces strict data quality contracts.
   - Filters duplicate transaction logs, null customer IDs, negative item quantities, and zero unit prices.
3. **Star Schema DW**:
   - Implements auto-incrementing integer surrogate keys for efficient indexing.
   - Employs batch insertion via SQLAlchemy to achieve sub-minute load times across 1.17M transaction facts.
4. **Gold Layer Engine**:
   - Computes pre-calculated business aggregations (RFM metrics, CLV spend, monthly totals, category distribution).
5. **Airflow Orchestrator**:
   - Manages daily scheduled runs with 8 modular DAG tasks, retry policies, and execution metadata JSON generation.
