"""
Data Loading Script for RetailSense-AI PostgreSQL Data Warehouse.
Reads processed dataset, populates Star Schema dimension tables, resolves surrogate keys, 
and batch-inserts fact records into PostgreSQL.
"""

import time
import os
from typing import Optional, Dict
import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine
from database.db_connection import get_db_engine, test_connection
from database.create_tables import create_tables
from etl.utils import setup_logger

logger = setup_logger("DB_LoadPostgres")


def load_dimensions(df: pd.DataFrame, engine: Engine) -> Dict[str, Dict[str, int]]:
    """
    Populates Customer, Product, Date, and Country dimension tables and builds surrogate key mappings.
    
    Args:
        df: Processed sales pandas DataFrame.
        engine: SQLAlchemy Engine instance.
        
    Returns:
        Dict[str, Dict[str, int]]: Lookup dictionaries mapping business keys to surrogate integer keys.
    """
    logger.info("--- Populating Dimension Tables ---")

    # 1. Country Dimension
    unique_countries = df[["country"]].drop_duplicates().dropna()
    unique_countries.columns = ["country_name"]
    unique_countries.to_sql("country_dim", con=engine, if_exists="append", index=False, chunksize=1000)
    logger.info(f"Loaded {len(unique_countries)} records into country_dim.")

    # 2. Customer Dimension
    unique_customers = df[["customer_id"]].astype(str).drop_duplicates().dropna()
    unique_customers.columns = ["customer_id"]
    unique_customers.to_sql("customer_dim", con=engine, if_exists="append", index=False, chunksize=5000)
    logger.info(f"Loaded {len(unique_customers)} records into customer_dim.")

    # 3. Product Dimension
    unique_products = df[["stock_code", "description"]].drop_duplicates(subset=["stock_code"]).dropna(subset=["stock_code"])
    unique_products.to_sql("product_dim", con=engine, if_exists="append", index=False, chunksize=5000)
    logger.info(f"Loaded {len(unique_products)} records into product_dim.")

    # 4. Date Dimension
    dates_series = pd.to_datetime(df["invoice_date"]).dt.date.drop_duplicates()
    date_records = []
    for d in dates_series:
        date_key = int(d.strftime("%Y%m%d"))
        date_records.append({
            "date_key": date_key,
            "full_date": d,
            "year": d.year,
            "quarter": (d.month - 1) // 3 + 1,
            "month": d.month,
            "month_name": d.strftime("%B"),
            "day": d.day,
            "day_of_week": d.weekday(),
            "day_name": d.strftime("%A"),
            "is_weekend": d.weekday() >= 5
        })
    df_date_dim = pd.DataFrame(date_records).drop_duplicates(subset=["date_key"])
    df_date_dim.to_sql("date_dim", con=engine, if_exists="append", index=False, chunksize=5000)
    logger.info(f"Loaded {len(df_date_dim)} records into date_dim.")

    # Build Surrogate Key Lookup Dictionaries
    logger.info("Building surrogate key lookup maps from database...")
    country_map = pd.read_sql("SELECT country_name, country_key FROM country_dim", con=engine).set_index("country_name")["country_key"].to_dict()
    customer_map = pd.read_sql("SELECT customer_id, customer_key FROM customer_dim", con=engine).astype(str).set_index("customer_id")["customer_key"].to_dict()
    product_map = pd.read_sql("SELECT stock_code, product_key FROM product_dim", con=engine).set_index("stock_code")["product_key"].to_dict()

    return {
        "country_map": country_map,
        "customer_map": customer_map,
        "product_map": product_map,
    }


def load_sales_fact(
    df: pd.DataFrame,
    engine: Engine,
    lookup_maps: Dict[str, Dict[str, int]],
    batch_size: int = 3000
) -> int:
    """
    Resolves dimension surrogate keys and batch inserts sales fact records.
    
    Args:
        df: Processed sales pandas DataFrame.
        engine: SQLAlchemy Engine instance.
        lookup_maps: Dictionary containing surrogate key maps.
        batch_size: Batch insert size.
        
    Returns:
        int: Total fact records loaded.
    """
    logger.info("--- Mapping Foreign Keys & Loading Sales Fact Table ---")

    country_map = lookup_maps["country_map"]
    customer_map = lookup_maps["customer_map"]
    product_map = lookup_maps["product_map"]

    df_fact = pd.DataFrame()
    df_fact["invoice_no"] = df["invoice_no"].astype(str)
    
    # Map foreign surrogate keys
    df_fact["customer_key"] = df["customer_id"].astype(str).map(customer_map)
    df_fact["product_key"] = df["stock_code"].astype(str).map(product_map)
    
    dt_series = pd.to_datetime(df["invoice_date"])
    df_fact["date_key"] = dt_series.dt.strftime("%Y%m%d").astype(int)
    df_fact["country_key"] = df["country"].map(country_map)
    
    df_fact["quantity"] = df["quantity"].astype(int)
    df_fact["unit_price"] = df["unit_price"].astype(float)
    df_fact["total_price"] = df["total_price"].astype(float)
    df_fact["invoice_date"] = dt_series

    # Drop any unmapped FK rows
    df_fact = df_fact.dropna(subset=["customer_key", "product_key", "country_key", "date_key"])

    total_rows = len(df_fact)
    logger.info(f"Prepared {total_rows} fact records. Batch inserting with chunksize={batch_size}...")

    start_time = time.time()
    df_fact.to_sql(
        "sales_fact",
        con=engine,
        if_exists="append",
        index=False,
        chunksize=batch_size
    )

    elapsed = round(time.time() - start_time, 2)
    logger.info(f"Loaded {total_rows} sales fact records successfully in {elapsed} seconds.")

    return total_rows


def load_data_warehouse(
    processed_csv_path: str = "data/processed/final_dataset.csv",
    engine: Optional[Engine] = None
) -> None:
    """
    Orchestrates the data loading pipeline into the PostgreSQL Data Warehouse.
    
    Args:
        processed_csv_path: Path to processed final dataset CSV.
        engine: Optional SQLAlchemy Engine.
    """
    start_total = time.time()
    logger.info("==================================================")
    logger.info("Starting RetailSense-AI Data Warehouse Population")
    logger.info("==================================================")

    if engine is None:
        engine = get_db_engine()

    # Check connection; fallback to SQLite for local verification if PostgreSQL server unreachable
    if not test_connection(engine):
        logger.warning("PostgreSQL server unreachable on DB_HOST:DB_PORT. Using SQLite database file database/retailsense_dw.db...")
        sqlite_file = "database/retailsense_dw.db"
        if os.path.exists(sqlite_file):
            os.remove(sqlite_file)
        engine = get_db_engine(db_url=f"sqlite:///{sqlite_file}")

    # Create tables
    create_tables(engine)

    # Load Processed Dataset
    logger.info(f"Reading processed dataset from: {processed_csv_path}")
    if not os.path.exists(processed_csv_path):
        raise FileNotFoundError(f"Processed dataset missing at: {processed_csv_path}")

    df_processed = pd.read_csv(processed_csv_path)
    logger.info(f"Read {len(df_processed):,} records from {processed_csv_path}.")

    # Load Dimensions
    lookup_maps = load_dimensions(df_processed, engine)

    # Load Fact Table
    facts_loaded = load_sales_fact(df_processed, engine, lookup_maps)

    total_duration = round(time.time() - start_total, 2)
    logger.info(f"Data Warehouse population finished cleanly in {total_duration} seconds. Total Facts: {facts_loaded:,}.")


if __name__ == "__main__":
    load_data_warehouse()
