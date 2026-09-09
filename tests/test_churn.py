"""
Unit & Integration Tests for Customer Churn Label Generation Module.
"""

import os
import json
import pytest
import pandas as pd
from datetime import datetime, timedelta
from ml.churn_label import generate_churn_labels


@pytest.fixture
def sample_transaction_df():
    """Generates synthetic transactions spanning active and churned timeframes."""
    max_date = datetime(2026, 9, 1)
    
    data = [
        # Customer 101: Active (Purchased 10 days ago)
        {"customer_id": 101, "invoice_no": "INV-001", "invoice_date": max_date - timedelta(days=100), "quantity": 5, "total_price": 50.0},
        {"customer_id": 101, "invoice_no": "INV-002", "invoice_date": max_date - timedelta(days=10), "quantity": 3, "total_price": 30.0},
        
        # Customer 102: Churned (Purchased 120 days ago)
        {"customer_id": 102, "invoice_no": "INV-003", "invoice_date": max_date - timedelta(days=150), "quantity": 10, "total_price": 100.0},
        {"customer_id": 102, "invoice_no": "INV-004", "invoice_date": max_date - timedelta(days=120), "quantity": 2, "total_price": 20.0},
        
        # Customer 103: Boundary Churned (Exactly 90 days ago)
        {"customer_id": 103, "invoice_no": "INV-005", "invoice_date": max_date - timedelta(days=90), "quantity": 1, "total_price": 15.0},
        
        # Customer 104: Boundary Active (89 days ago)
        {"customer_id": 104, "invoice_no": "INV-006", "invoice_date": max_date - timedelta(days=89), "quantity": 4, "total_price": 40.0},
        
        # Anchor Max Date Transaction
        {"customer_id": 105, "invoice_no": "INV-007", "invoice_date": max_date, "quantity": 1, "total_price": 10.0},
    ]
    return pd.DataFrame(data)


def test_generate_churn_labels_logic(sample_transaction_df, tmp_path):
    """Verifies RFM metrics computation and churn labelling business rules."""
    output_csv = str(tmp_path / "test_customer_churn.csv")
    output_report = str(tmp_path / "test_churn_report.json")

    churn_df, report = generate_churn_labels(
        input_data=sample_transaction_df,
        output_csv_path=output_csv,
        output_report_path=output_report,
        churn_threshold_days=90
    )

    # 1. Verify Row Count
    assert len(churn_df) == 5
    assert set(churn_df["customer_id"]) == {101, 102, 103, 104, 105}

    # 2. Verify Customer 101 (Active)
    c101 = churn_df[churn_df["customer_id"] == 101].iloc[0]
    assert c101["recency_days"] == 10
    assert c101["churn"] == 0
    assert c101["total_orders"] == 2
    assert c101["total_quantity"] == 8
    assert c101["total_spent"] == 80.0

    # 3. Verify Customer 102 (Churned)
    c102 = churn_df[churn_df["customer_id"] == 102].iloc[0]
    assert c102["recency_days"] == 120
    assert c102["churn"] == 1

    # 4. Verify Boundary Cases (90 days vs 89 days)
    c103 = churn_df[churn_df["customer_id"] == 103].iloc[0]
    assert c103["recency_days"] == 90
    assert c103["churn"] == 1

    c104 = churn_df[churn_df["customer_id"] == 104].iloc[0]
    assert c104["recency_days"] == 89
    assert c104["churn"] == 0

    # 5. Verify Output File Creation & Report Structure
    assert os.path.exists(output_csv)
    assert os.path.exists(output_report)

    with open(output_report, "r", encoding="utf-8") as f:
        rep_data = json.load(f)

    assert rep_data["total_customers"] == 5
    assert rep_data["churned_customers"] == 2  # Customer 102 and 103
    assert rep_data["active_customers"] == 3   # Customer 101, 104, 105
    assert rep_data["churn_rate"] == 0.4
    assert rep_data["churn_rate_pct"] == "40.0%"


def test_empty_dataframe_handling(tmp_path):
    """Ensures graceful handling when input DataFrame is empty."""
    empty_df = pd.DataFrame(columns=["customer_id", "invoice_date", "total_price"])
    output_csv = str(tmp_path / "empty_churn.csv")
    output_report = str(tmp_path / "empty_report.json")

    churn_df, report = generate_churn_labels(
        input_data=empty_df,
        output_csv_path=output_csv,
        output_report_path=output_report
    )

    assert churn_df.empty
    assert report["total_customers"] == 0
    assert report["churn_rate"] == 0.0
