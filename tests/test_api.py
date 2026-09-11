"""
Unit and Integration Tests for RetailSense-AI FastAPI REST Application.
Tests endpoints (/health, /model/info, /predict, /predict/batch), validation error handling (extra="forbid"),
and verifies prediction parity with direct best_model.pkl pipeline inference.
"""

import joblib
import pytest
import pandas as pd
from fastapi.testclient import TestClient
from api.main import app
from api.config import MODEL_PATH
from api.model_service import model_service

client = TestClient(app)

SAMPLE_CUSTOMER_PAYLOAD = {
    "country": "United Kingdom",
    "customer_lifetime_days": 120.0,
    "total_spent": 1500.0,
    "average_order_value": 250.0,
    "max_order_value": 500.0,
    "min_order_value": 50.0,
    "total_quantity": 100.0,
    "average_quantity": 20.0,
    "total_orders": 6,
    "purchase_frequency": 0.05,
    "purchase_velocity": 0.05,
    "average_days_between_orders": 20.0,
    "unique_products": 15,
    "favorite_category": "Home & Decor",
    "category_diversity": 4,
    "preferred_month": 6,
    "preferred_weekday": "Monday",
    "preferred_hour": 14,
    "weekend_purchase_ratio": 0.1,
    "revenue_per_day": 12.5,
    "items_per_order": 16.7,
    "customer_value_segment": "High",
    "basket_size": 250.0
}


def test_read_root():
    """Test GET / endpoint returns welcome message."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data


def test_health_check():
    """Test GET /health returns operational status and model readiness."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["model_loaded"] is True
    assert "model_name" in data


def test_model_info():
    """Test GET /model/info returns model metrics, feature count, and excluded features."""
    response = client.get("/model/info")
    assert response.status_code == 200
    data = response.json()
    assert "model_name" in data
    assert "roc_auc" in data
    assert data["roc_auc"] >= 0.5
    assert data["feature_count"] == 23
    assert "recency_days" in data["excluded_features"]


def test_predict_single_customer():
    """Test POST /predict returns valid churn prediction and probability bounds."""
    response = client.post("/predict", json=SAMPLE_CUSTOMER_PAYLOAD)
    assert response.status_code == 200
    data = response.json()

    assert "churn_prediction" in data
    assert data["churn_prediction"] in (0, 1)
    assert data["prediction"] in ("churn", "active")
    
    # Verify probabilities sum to ~1.0 and stay within [0, 1]
    prob_c = data["churn_probability"]
    prob_a = data["non_churn_probability"]
    assert 0.0 <= prob_c <= 1.0
    assert 0.0 <= prob_a <= 1.0
    assert round(prob_c + prob_a, 4) == 1.0


def test_predict_parity_with_direct_pipeline():
    """Verifies that API prediction results match direct best_model.pkl pipeline prediction."""
    # 1. API Prediction
    response = client.post("/predict", json=SAMPLE_CUSTOMER_PAYLOAD)
    assert response.status_code == 200
    api_data = response.json()

    # 2. Direct Pipeline Prediction
    assert MODEL_PATH.exists()
    pipeline = joblib.load(MODEL_PATH)
    df_input = pd.DataFrame([SAMPLE_CUSTOMER_PAYLOAD])
    
    direct_pred = int(pipeline.predict(df_input)[0])
    direct_probs = pipeline.predict_proba(df_input)[0]

    direct_prob_active = round(float(direct_probs[0]), 4)
    direct_prob_churn = round(float(direct_probs[1]), 4)

    # 3. Assert Exact Match
    assert api_data["churn_prediction"] == direct_pred
    assert api_data["churn_probability"] == direct_prob_churn
    assert api_data["non_churn_probability"] == direct_prob_active


def test_predict_batch():
    """Test POST /predict/batch returns multiple prediction responses."""
    batch_payload = {"customers": [SAMPLE_CUSTOMER_PAYLOAD, SAMPLE_CUSTOMER_PAYLOAD, SAMPLE_CUSTOMER_PAYLOAD]}
    response = client.post("/predict/batch", json=batch_payload)
    assert response.status_code == 200
    data = response.json()

    assert data["count"] == 3
    assert len(data["predictions"]) == 3
    for pred in data["predictions"]:
        assert pred["churn_prediction"] in (0, 1)


def test_predict_extra_field_rejection_forbid():
    """Test Pydantic extra='forbid' constraint rejects target-leaking or unknown fields with HTTP 422."""
    leaky_payload = SAMPLE_CUSTOMER_PAYLOAD.copy()
    leaky_payload["recency_days"] = 100.0  # Leaky field must be rejected

    response = client.post("/predict", json=leaky_payload)
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data

    id_payload = SAMPLE_CUSTOMER_PAYLOAD.copy()
    id_payload["customer_id"] = 12345  # Identifier field must be rejected

    response_id = client.post("/predict", json=id_payload)
    assert response_id.status_code == 422


def test_predict_missing_field_rejection():
    """Test missing required field raises HTTP 422 validation error."""
    incomplete_payload = SAMPLE_CUSTOMER_PAYLOAD.copy()
    del incomplete_payload["country"]

    response = client.post("/predict", json=incomplete_payload)
    assert response.status_code == 422


def test_predict_batch_oversized_rejection():
    """Test batch size exceeding limit raises HTTP 400 Bad Request."""
    oversized_batch = {"customers": [SAMPLE_CUSTOMER_PAYLOAD] * 1001}
    response = client.post("/predict/batch", json=oversized_batch)
    assert response.status_code == 400
    data = response.json()
    assert "Batch size limit exceeded" in data["detail"]
