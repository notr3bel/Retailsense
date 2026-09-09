"""
Unit tests for RetailSense-AI ETL modules (extract, validate, transform, load, report, gold).
"""

import os
import json
import pandas as pd
from etl.validate import validate_dataframe, generate_data_quality_report
from etl.transform import standardize_columns, transform_datasets
from etl.gold import generate_gold_layer, classify_category


def test_standardize_columns():
    df_raw = pd.DataFrame({
        "InvoiceNo": ["536365"],
        "StockCode": ["85123A"],
        "Quantity": [6],
        "UnitPrice": [2.55],
        "CustomerID": [17850],
        "InvoiceDate": ["2010-12-01 08:26:00"]
    })
    df_std = standardize_columns(df_raw)
    expected_cols = ["invoice_no", "stock_code", "quantity", "unit_price", "customer_id", "invoice_date"]
    assert all(col in df_std.columns for col in expected_cols)


def test_validate_dataframe():
    df = pd.DataFrame({
        "quantity": [10, -5, None],
        "unit_price": [2.5, 0, -1.0],
        "customer_id": [123, 124, None]
    })
    report = validate_dataframe(df, dataset_name="TestSet")
    assert report["dataset_name"] == "TestSet"
    assert report["total_rows"] == 3
    assert report["negative_quantities"] == 1
    assert report["negative_prices"] == 1


def test_transform_datasets():
    df_excel = pd.DataFrame({
        "InvoiceNo": ["536365", "C536379", "536366"],
        "StockCode": ["85123A", "D", "22633"],
        "Description": ["WHITE HANGING HEART", "Discount", "HAND WARMER"],
        "Quantity": [6, -1, 12],
        "InvoiceDate": ["2010-12-01 08:26:00", "2010-12-01 09:00:00", "2010-12-01 08:28:00"],
        "UnitPrice": [2.55, 1.50, 1.85],
        "CustomerID": [17850, 17850, 17850],
        "Country": ["United Kingdom", "United Kingdom", "United Kingdom"]
    })
    df_csv = pd.DataFrame({
        "Invoice": ["489434"],
        "StockCode": ["21523"],
        "Description": ["FANCY FONT"],
        "Quantity": [10],
        "InvoiceDate": ["2009-12-01 07:45:00"],
        "Price": [6.95],
        "Customer ID": [13085],
        "Country": ["United Kingdom"]
    })

    df_cleaned, stats, df_merged = transform_datasets(df_excel, df_csv)
    
    assert len(df_cleaned) == 3  # Cancelled order C536379 filtered out
    assert "total_price" in df_cleaned.columns
    assert "customer_id" in df_cleaned.columns
    assert stats["cancelled_orders_removed"] == 1
    assert stats["total_raw_rows"] == 4


def test_generate_data_quality_report(tmp_path):
    json_path = str(tmp_path / "test_report.json")
    csv_path = str(tmp_path / "test_report.csv")

    raw_df = pd.DataFrame({
        "invoice_no": ["536365", "536366"],
        "customer_id": ["17850", None],
        "quantity": [6, 12]
    })
    transform_stats = {
        "total_raw_rows": 2,
        "final_rows": 1,
        "rows_removed": 1,
        "cancelled_orders_removed": 0,
        "duplicates_removed": 0,
        "missing_customer_ids_handled": 1,
        "invalid_quantities_removed": 0,
        "invalid_prices_removed": 0,
        "missing_values_per_column": {"invoice_no": 0, "customer_id": 1, "quantity": 0}
    }

    j_out, c_out = generate_data_quality_report(
        raw_df=raw_df,
        transform_stats=transform_stats,
        execution_time=1.23,
        json_path=json_path,
        csv_path=csv_path
    )

    assert os.path.exists(j_out)
    assert os.path.exists(c_out)

    with open(j_out, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["total_rows_before_cleaning"] == 2
    assert data["total_rows_after_cleaning"] == 1
    assert data["missing_values_per_column"]["customer_id"] == 1
    assert data["execution_time_seconds"] == 1.23

    csv_data = pd.read_csv(c_out)
    assert "column_name" in csv_data.columns
    assert "missing_count" in csv_data.columns
    assert len(csv_data) == 3


def test_classify_category():
    assert classify_category("WHITE HANGING HEART T-LIGHT HOLDER") == "Home & Decor"
    assert classify_category("REGENCY CAKESTAND 3 TIER") == "Kitchen & Dining"
    assert classify_category("JUMBO BAG RED WHITE SPOTTY") == "Bags & Accessories"
    assert classify_category("PAPER CRAFT LITTLE BIRDIE") == "Stationery & Crafts"
    assert classify_category("UNKNOWN PRODUCT XYZ") == "General & Gifts"


def test_generate_gold_layer(tmp_path):
    out_dir = str(tmp_path / "gold")
    df_sample = pd.DataFrame({
        "invoice_no": ["536365", "536365", "536366"],
        "stock_code": ["85123A", "22423", "85123A"],
        "description": ["WHITE HANGING HEART T-LIGHT HOLDER", "REGENCY CAKESTAND 3 TIER", "WHITE HANGING HEART T-LIGHT HOLDER"],
        "quantity": [6, 2, 12],
        "invoice_date": ["2010-12-01 08:26:00", "2010-12-01 08:26:00", "2010-12-01 09:00:00"],
        "unit_price": [2.55, 12.75, 2.55],
        "customer_id": ["17850", "17850", "13085"],
        "country": ["United Kingdom", "United Kingdom", "United Kingdom"],
        "total_price": [15.30, 25.50, 30.60]
    })

    gold_files = generate_gold_layer(processed_df_or_path=df_sample, output_dir=out_dir)

    assert os.path.exists(gold_files["customers"])
    assert os.path.exists(gold_files["products"])
    assert os.path.exists(gold_files["country_summary"])
    assert os.path.exists(gold_files["monthly_sales"])
    assert os.path.exists(gold_files["sales_summary"])

    df_cust = pd.read_csv(gold_files["customers"])
    assert "average_order_value" in df_cust.columns
    assert len(df_cust) == 2

    df_prod = pd.read_csv(gold_files["products"])
    assert "category" in df_prod.columns
    assert len(df_prod) == 2
