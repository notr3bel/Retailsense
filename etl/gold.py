"""
Gold Layer Data Aggregation Module for RetailSense-AI.
Transforms cleaned processed transaction datasets into business-ready analytical Gold layer datasets.
"""

import os
from datetime import datetime
from typing import Dict, Tuple
import pandas as pd
from etl.utils import setup_logger, ensure_directory

logger = setup_logger("ETL_Gold")

# Category Keyword Classification Rules (Order-sensitive precedence)
CATEGORY_KEYWORDS = {
    "Stationery & Crafts": ["PAPER", "CRAFT", "PENCIL", "PEN", "NOTEBOOK", "CARD", "WRAP", "STICKER", "TAPE", "ALBUM", "BOX", "TIN"],
    "Kitchen & Dining": ["CAKESTAND", "MUG", "CUP", "BOWL", "PLATE", "TEAPOT", "JAR", "BOTTLE", "SPOON", "CUTLERY", "KITCHEN", "GLASS", "DISH"],
    "Bags & Accessories": ["BAG", "TOTE", "SHOPPER", "LUGGAGE", "CASE", "PURSE", "WALLET", "BACKPACK"],
    "Home & Decor": ["HEART", "HOLDER", "LIGHT", "CANDLE", "VINTAGE", "CLOCK", "MIRROR", "FRAME", "SIGN", "BIRD ORNAMENT", "FLOWER", "DECOR"],
    "Party & Celebrations": ["PARTY", "BUNTING", "BALLOON", "CHRISTMAS", "BIRTHDAY", "DECORATION", "GIFT", "FAVOUR", "STAR"],
    "Apparel & Textiles": ["APRON", "HAT", "GLOVES", "SCARF", "SOCKS", "CUSHION", "TOWEL", "CLOTH"],
    "Toys & Games": ["TOY", "GAME", "DOLL", "PUZZLE", "BALL", "BEAR", "PLUSH", "KIT"]
}


def classify_category(description: str) -> str:
    """
    Classifies a product description into a broad category based on keywords.
    
    Args:
        description: Product description string.
        
    Returns:
        str: Assigned category name.
    """
    if not isinstance(description, str) or not description.strip():
        return "Uncategorized"
    
    desc_upper = description.upper()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in desc_upper for keyword in keywords):
            return category

    return "General & Gifts"


def generate_customer_gold(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generates customer-level analytics dataset (customers.csv).
    
    Metrics:
        - customer_id, first_purchase_date, last_purchase_date
        - total_orders, total_quantity, total_spent
        - average_order_value, average_items_per_order, country
    """
    logger.info("Generating Gold layer: customers.csv...")

    # Group by customer_id
    grouped = df.groupby("customer_id").agg(
        first_purchase_date=("invoice_date", "min"),
        last_purchase_date=("invoice_date", "max"),
        total_orders=("invoice_no", "nunique"),
        total_quantity=("quantity", "sum"),
        total_spent=("total_price", "sum"),
        country=("country", lambda x: x.mode()[0] if not x.empty else "Unknown")
    ).reset_index()

    # Calculate derived averages
    grouped["total_spent"] = round(grouped["total_spent"], 2)
    grouped["average_order_value"] = round(grouped["total_spent"] / grouped["total_orders"], 2)
    grouped["average_items_per_order"] = round(grouped["total_quantity"] / grouped["total_orders"], 2)

    # Reorder columns
    cols = [
        "customer_id", "first_purchase_date", "last_purchase_date",
        "total_orders", "total_quantity", "total_spent",
        "average_order_value", "average_items_per_order", "country"
    ]
    df_customers = grouped[cols].sort_values(by="total_spent", ascending=False).reset_index(drop=True)
    return df_customers


def generate_product_gold(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generates product-level analytics dataset (products.csv).
    
    Metrics:
        - stock_code, description, category
        - total_quantity_sold, total_revenue
    """
    logger.info("Generating Gold layer: products.csv...")

    grouped = df.groupby("stock_code").agg(
        description=("description", lambda x: x.mode()[0] if not x.empty and pd.notna(x.mode()[0]) else "N/A"),
        total_quantity_sold=("quantity", "sum"),
        total_revenue=("total_price", "sum")
    ).reset_index()

    grouped["total_revenue"] = round(grouped["total_revenue"], 2)
    grouped["category"] = grouped["description"].apply(classify_category)

    cols = ["stock_code", "description", "category", "total_quantity_sold", "total_revenue"]
    df_products = grouped[cols].sort_values(by="total_revenue", ascending=False).reset_index(drop=True)
    return df_products


def generate_country_summary_gold(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generates country-level aggregated metrics (country_summary.csv).
    
    Metrics:
        - country, customers, total_orders, total_quantity, total_revenue
    """
    logger.info("Generating Gold layer: country_summary.csv...")

    grouped = df.groupby("country").agg(
        customers=("customer_id", "nunique"),
        total_orders=("invoice_no", "nunique"),
        total_quantity=("quantity", "sum"),
        total_revenue=("total_price", "sum")
    ).reset_index()

    grouped["total_revenue"] = round(grouped["total_revenue"], 2)
    df_country = grouped.sort_values(by="total_revenue", ascending=False).reset_index(drop=True)
    return df_country


def generate_monthly_sales_gold(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generates monthly aggregated sales dataset (monthly_sales.csv).
    
    Metrics:
        - year, month, total_orders, total_revenue, average_order_value
    """
    logger.info("Generating Gold layer: monthly_sales.csv...")

    df_temp = df.copy()
    df_temp["dt"] = pd.to_datetime(df_temp["invoice_date"])
    df_temp["year"] = df_temp["dt"].dt.year
    df_temp["month"] = df_temp["dt"].dt.month

    grouped = df_temp.groupby(["year", "month"]).agg(
        total_orders=("invoice_no", "nunique"),
        total_revenue=("total_price", "sum")
    ).reset_index()

    grouped["total_revenue"] = round(grouped["total_revenue"], 2)
    grouped["average_order_value"] = round(grouped["total_revenue"] / grouped["total_orders"], 2)

    df_monthly = grouped.sort_values(by=["year", "month"], ascending=[True, True]).reset_index(drop=True)
    return df_monthly


def generate_sales_summary_gold(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generates overall business summary key performance indicators (sales_summary.csv).
    
    Metrics:
        - total_customers, total_orders, total_products, total_revenue
        - average_order_value, average_quantity, processing_timestamp
    """
    logger.info("Generating Gold layer: sales_summary.csv...")

    total_customers = int(df["customer_id"].nunique())
    total_orders = int(df["invoice_no"].nunique())
    total_products = int(df["stock_code"].nunique())
    total_revenue = round(float(df["total_price"].sum()), 2)
    average_order_value = round(total_revenue / total_orders, 2) if total_orders > 0 else 0.0
    average_quantity = round(float(df["quantity"].mean()), 2)
    processing_timestamp = datetime.now().astimezone().isoformat()

    summary_data = [{
        "total_customers": total_customers,
        "total_orders": total_orders,
        "total_products": total_products,
        "total_revenue": total_revenue,
        "average_order_value": average_order_value,
        "average_quantity": average_quantity,
        "processing_timestamp": processing_timestamp
    }]

    df_summary = pd.DataFrame(summary_data)
    return df_summary


def generate_gold_layer(
    processed_df_or_path: Tuple[pd.DataFrame, str] = "data/processed/final_dataset.csv",
    output_dir: str = "data/gold"
) -> Dict[str, str]:
    """
    Orchestrates the creation of all 5 Gold Data Layer datasets.
    
    Args:
        processed_df_or_path: Processed DataFrame or file path to final_dataset.csv.
        output_dir: Directory where Gold layer CSVs will be saved.
        
    Returns:
        Dict[str, str]: Map of dataset name to saved file path.
    """
    start_time = datetime.now()
    logger.info("==================================================")
    logger.info("Building RetailSense-AI Gold Data Layer")
    logger.info("==================================================")

    ensure_directory(output_dir)

    if isinstance(processed_df_or_path, str):
        if not os.path.exists(processed_df_or_path):
            raise FileNotFoundError(f"Processed dataset not found at: {processed_df_or_path}")
        df = pd.read_csv(processed_df_or_path)
    else:
        df = processed_df_or_path.copy()

    # 1. Customers Gold
    df_customers = generate_customer_gold(df)
    customers_path = os.path.join(output_dir, "customers.csv")
    df_customers.to_csv(customers_path, index=False)

    # 2. Products Gold
    df_products = generate_product_gold(df)
    products_path = os.path.join(output_dir, "products.csv")
    df_products.to_csv(products_path, index=False)

    # 3. Country Summary Gold
    df_country = generate_country_summary_gold(df)
    country_path = os.path.join(output_dir, "country_summary.csv")
    df_country.to_csv(country_path, index=False)

    # 4. Monthly Sales Gold
    df_monthly = generate_monthly_sales_gold(df)
    monthly_path = os.path.join(output_dir, "monthly_sales.csv")
    df_monthly.to_csv(monthly_path, index=False)

    # 5. Sales Summary Gold
    df_summary = generate_sales_summary_gold(df)
    summary_path = os.path.join(output_dir, "sales_summary.csv")
    df_summary.to_csv(summary_path, index=False)

    duration = (datetime.now() - start_time).total_seconds()
    logger.info(f"Gold Data Layer generated successfully in {round(duration, 2)} seconds.")

    return {
        "customers": customers_path,
        "products": products_path,
        "country_summary": country_path,
        "monthly_sales": monthly_path,
        "sales_summary": summary_path
    }


if __name__ == "__main__":
    generate_gold_layer()
