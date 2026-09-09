"""
Unit & Integration Tests for Customer Feature Engineering Module.
"""

import os
import json
import pytest
import pandas as pd
from datetime import datetime, timedelta
from ml.feature_engineering import generate_customer_features, compute_average_days_between_orders


@pytest.fixture
def sample_feature_transactions():
    """Generates synthetic transactions for feature engineering tests."""
    base_date = datetime(2026, 9, 1)
    
    data = [
        # Customer 101: 3 orders over 20 days
        {"customer_id": 101, "invoice_no": "INV-101-1", "stock_code": "P1", "description": "PAPER CRAFT", "quantity": 10, "unit_price": 5.0, "total_price": 50.0, "invoice_date": base_date - timedelta(days=20), "country": "UK"},
        {"customer_id": 101, "invoice_no": "INV-101-2", "stock_code": "P2", "description": "PARTY BALLOON", "quantity": 5, "unit_price": 4.0, "total_price": 20.0, "invoice_date": base_date - timedelta(days=10), "country": "UK"},
        {"customer_id": 101, "invoice_no": "INV-101-3", "stock_code": "P1", "description": "PAPER CRAFT", "quantity": 15, "unit_price": 5.0, "total_price": 75.0, "invoice_date": base_date, "country": "UK"},
        
        # Customer 102: Single order
        {"customer_id": 102, "invoice_no": "INV-102-1", "stock_code": "P3", "description": "MUG CAKESTAND", "quantity": 2, "unit_price": 10.0, "total_price": 20.0, "invoice_date": base_date - timedelta(days=5), "country": "France"},
        
        # Customer 103: High spend VIP
        {"customer_id": 103, "invoice_no": "INV-103-1", "stock_code": "P4", "description": "VINTAGE CLOCK", "quantity": 100, "unit_price": 50.0, "total_price": 5000.0, "invoice_date": base_date - timedelta(days=2), "country": "Germany"},
    ]
    return pd.DataFrame(data)


def test_feature_engineering_pipeline(sample_feature_transactions, tmp_path):
    """Verifies feature generation logic, formulas, segmentation, and output files."""
    output_csv = str(tmp_path / "test_customer_features.csv")
    output_report = str(tmp_path / "test_feature_report.json")

    features_df, report = generate_customer_features(
        input_data=sample_feature_transactions,
        output_csv_path=output_csv,
        output_report_path=output_report
    )

    # 1. Output CSV Creation
    assert os.path.exists(output_csv)
    assert os.path.exists(output_report)

    # 2. Feature Count (28 columns)
    expected_cols = [
        "customer_id", "country", "first_purchase", "last_purchase", "customer_lifetime_days",
        "total_spent", "average_order_value", "max_order_value", "min_order_value",
        "total_quantity", "average_quantity", "total_orders", "purchase_frequency",
        "purchase_velocity", "average_days_between_orders", "recency_days",
        "unique_products", "favorite_product", "favorite_category", "category_diversity",
        "preferred_month", "preferred_weekday", "preferred_hour", "weekend_purchase_ratio",
        "revenue_per_day", "items_per_order", "customer_value_segment", "basket_size"
    ]
    assert len(features_df.columns) == 28
    assert list(features_df.columns) == expected_cols

    # 3. No Duplicate Customers & No Missing customer_id
    assert len(features_df) == 3
    assert features_df["customer_id"].nunique() == 3
    assert features_df["customer_id"].isna().sum() == 0

    # 4. Check Customer 101 Calculations
    c101 = features_df[features_df["customer_id"] == 101].iloc[0]
    
    # customer_lifetime_days: (base_date - (base_date - 20 days)) + 1 = 21 days
    assert c101["customer_lifetime_days"] == 21
    assert c101["total_orders"] == 3
    assert c101["total_quantity"] == 30
    assert c101["total_spent"] == 145.0
    
    # purchase_velocity = total_orders / customer_lifetime_days = 3 / 21
    assert c101["purchase_velocity"] == pytest.approx(round(3 / 21, 4))
    
    # revenue_per_day = total_spent / customer_lifetime_days = 145.0 / 21
    assert c101["revenue_per_day"] == pytest.approx(round(145.0 / 21, 2))
    
    # basket_size = total_quantity / total_orders = 30 / 3 = 10.0
    assert c101["basket_size"] == 10.0
    
    # average_days_between_orders: 2 intervals of 10 days = 10.0
    assert c101["average_days_between_orders"] == 10.0

    # 5. Check Customer 102 (Single Order)
    c102 = features_df[features_df["customer_id"] == 102].iloc[0]
    assert c102["customer_lifetime_days"] == 1
    assert c102["average_days_between_orders"] == 0.0

    # 6. Quartile Segmentation
    assert "customer_value_segment" in features_df.columns
    assert set(features_df["customer_value_segment"].dropna().unique()).issubset({"Low", "Medium", "High", "VIP"})

    # 7. Report Structure
    assert report["total_customers"] == 3
    assert report["number_of_features"] == 27
    assert report["total_columns"] == 28
    assert len(report["feature_names"]) == 28


def test_compute_average_days_between_orders():
    """Unit test for average_days_between_orders helper."""
    df = pd.DataFrame([
        {"customer_id": 1, "invoice_date": pd.to_datetime("2026-01-01")},
        {"customer_id": 1, "invoice_date": pd.to_datetime("2026-01-05")}, # +4
        {"customer_id": 1, "invoice_date": pd.to_datetime("2026-01-11")}, # +6 -> avg 5.0
        {"customer_id": 2, "invoice_date": pd.to_datetime("2026-01-01")}, # single order -> 0.0
    ])

    result = compute_average_days_between_orders(df)
    assert result[1] == 5.0
    assert result[2] == 0.0
