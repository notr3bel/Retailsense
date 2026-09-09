"""
Analytical SQL Queries & Data Warehouse Insights Module for RetailSense-AI.
Provides modular SQL queries and execution functions for retail analytics.
"""

from typing import Dict, Optional
import pandas as pd
from sqlalchemy.engine import Engine
from database.db_connection import get_db_engine, test_connection
from etl.utils import setup_logger

logger = setup_logger("DB_Queries")

# ============================================================================
# SQL Query Constants
# ============================================================================

QUERY_MONTHLY_REVENUE = """
SELECT 
    d.year,
    d.month,
    d.month_name,
    COUNT(DISTINCT s.invoice_no) AS total_orders,
    ROUND(CAST(SUM(s.total_price) AS NUMERIC), 2) AS monthly_revenue
FROM sales_fact s
JOIN date_dim d ON s.date_key = d.date_key
GROUP BY d.year, d.month, d.month_name
ORDER BY d.year ASC, d.month ASC;
"""

QUERY_TOP_10_PRODUCTS = """
SELECT 
    p.stock_code,
    p.description,
    SUM(s.quantity) AS total_quantity_sold,
    ROUND(CAST(SUM(s.total_price) AS NUMERIC), 2) AS total_revenue
FROM sales_fact s
JOIN product_dim p ON s.product_key = p.product_key
GROUP BY p.stock_code, p.description
ORDER BY total_revenue DESC
LIMIT 10;
"""

QUERY_TOP_10_CUSTOMERS = """
SELECT 
    c.customer_id,
    COUNT(DISTINCT s.invoice_no) AS total_orders,
    SUM(s.quantity) AS total_items_purchased,
    ROUND(CAST(SUM(s.total_price) AS NUMERIC), 2) AS total_spend
FROM sales_fact s
JOIN customer_dim c ON s.customer_key = c.customer_key
GROUP BY c.customer_id
ORDER BY total_spend DESC
LIMIT 10;
"""

QUERY_COUNTRY_SALES = """
SELECT 
    co.country_name,
    COUNT(DISTINCT s.customer_key) AS total_customers,
    COUNT(DISTINCT s.invoice_no) AS total_orders,
    SUM(s.quantity) AS total_quantity,
    ROUND(CAST(SUM(s.total_price) AS NUMERIC), 2) AS total_revenue
FROM sales_fact s
JOIN country_dim co ON s.country_key = co.country_key
GROUP BY co.country_name
ORDER BY total_revenue DESC;
"""

QUERY_MONTHLY_ORDER_COUNT = """
SELECT 
    d.year,
    d.month,
    d.month_name,
    COUNT(DISTINCT s.invoice_no) AS monthly_order_count
FROM sales_fact s
JOIN date_dim d ON s.date_key = d.date_key
GROUP BY d.year, d.month, d.month_name
ORDER BY d.year ASC, d.month ASC;
"""

# Dictionary mapping analytical metric to SQL query
ANALYTICAL_QUERIES = {
    "1. Monthly Revenue": QUERY_MONTHLY_REVENUE,
    "2. Top 10 Products": QUERY_TOP_10_PRODUCTS,
    "3. Top 10 Customers": QUERY_TOP_10_CUSTOMERS,
    "4. Country-wise Sales": QUERY_COUNTRY_SALES,
    "5. Monthly Order Count": QUERY_MONTHLY_ORDER_COUNT,
}


def run_query(query_sql: str, engine: Optional[Engine] = None) -> pd.DataFrame:
    """
    Executes a SQL query string against the database engine and returns a pandas DataFrame.
    
    Args:
        query_sql: SQL query string.
        engine: Optional SQLAlchemy Engine instance.
        
    Returns:
        pd.DataFrame: Query result set as a pandas DataFrame.
    """
    if engine is None:
        engine = get_db_engine()

    return pd.read_sql(query_sql, con=engine)


def run_analytical_queries(engine: Optional[Engine] = None) -> Dict[str, pd.DataFrame]:
    """
    Executes all 5 required analytical queries and displays the results.
    
    Args:
        engine: Optional SQLAlchemy Engine.
        
    Returns:
        Dict[str, pd.DataFrame]: Map of query name to result DataFrame.
    """
    if engine is None:
        engine = get_db_engine()
        if not test_connection(engine):
            logger.warning("PostgreSQL server unreachable. Using SQLite database file database/retailsense_dw.db...")
            engine = get_db_engine(db_url="sqlite:///database/retailsense_dw.db")

    results = {}
    print("\n" + "=" * 60)
    print("RetailSense-AI Data Warehouse Analytical Insights")
    print("=" * 60 + "\n")

    for name, sql in ANALYTICAL_QUERIES.items():
        logger.info(f"Running analytical query: [{name}]...")
        df_result = run_query(sql, engine=engine)
        results[name] = df_result

        print(f"--- {name} ---")
        print(df_result.head(10).to_string(index=False))
        print("\n" + "-" * 60 + "\n")

    return results


if __name__ == "__main__":
    run_analytical_queries()
