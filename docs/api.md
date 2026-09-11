# RetailSense-AI FastAPI Model Serving Architecture

This document provides technical documentation for the **FastAPI Model Serving Layer** in **RetailSense-AI**.

---

## 🏛️ REST API Architecture & Serving Flow

The FastAPI serving layer exposes real-time single and batch customer churn predictions by loading the serialized champion **XGBoost Scikit-Learn Pipeline** (`models/best_model.pkl`).

```text
       MLflow Tracking
       (Training Side)
              │
              ▼
    models/best_model.pkl
 (Complete Sklearn Pipeline)
              │
              ▼
   FastAPI Model Service Layer
 (Joblib loaded once at startup)
              │
  ┌───────────┼───────────┬───────────┐
  ▼           ▼           ▼           ▼
GET /     GET /health  GET /model/info POST /predict  POST /predict/batch
                          │                 │                  │
                          └─────────────────┴──────────────────┘
                                            │
                                            ▼
                                Customer Churn Predictions
                                 (Prediction + Probability)
```

> [!IMPORTANT]
> **Standalone Serving**: The API directly executes predictions via `best_model.pkl`. It does **NOT** require an active MLflow server to process inference requests.
> **Target Leakage Safeguard**: Input schemas use Pydantic `extra="forbid"`. Supplying unknown fields or target-leaking features (`recency_days`, `customer_id`, `churn`, `first_purchase`, `last_purchase`, `favorite_product`) results in an **HTTP 422 Validation Error**.

---

## 🚀 API Endpoints Overview

| Method | Endpoint | Description | Request Payload | Response |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/` | API Root & Documentation Links | None | Welcome JSON |
| `GET` | `/health` | Service Operational & Model Readiness Status | None | `HealthResponse` |
| `GET` | `/model/info` | Champion Model Metrics, Feature Counts & Metadata | None | `ModelInfoResponse` |
| `POST` | `/predict` | Real-time Single Customer Churn Inference | `CustomerFeatures` | `PredictionResponse` |
| `POST` | `/predict/batch` | High-Throughput Batch Churn Inference | `BatchPredictionRequest` | `BatchPredictionResponse` |

---

## 📋 Request & Response Schemas

### 1. Single Customer Request Payload (`POST /predict`)

Accepts the exact 23 model-input features (19 numerical, 4 categorical):

```json
{
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
```

### 2. Single Prediction Response (`POST /predict`)

```json
{
  "churn_prediction": 1,
  "prediction": "churn",
  "churn_probability": 0.9747,
  "non_churn_probability": 0.0253,
  "model": "XGBoost",
  "model_version": "8dd519d29f1847e7a7cdacb9d05418c5"
}
```

### 3. Batch Request Payload (`POST /predict/batch`)

Maximum allowed batch size: `1000` customer records per request.

```json
{
  "customers": [
    { ...customer_1_features... },
    { ...customer_2_features... }
  ]
}
```

---

## 🖥️ Running the API Server

Developers can launch the FastAPI application locally using Uvicorn:

```bash
# 1. Activate environment
# 2. Start Uvicorn development server
uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
```

### Interactive Documentation & Swagger UI
- **Swagger UI**: `http://127.0.0.1:8000/docs`
- **ReDoc**: `http://127.0.0.1:8000/redoc`
- **OpenAPI Schema**: `http://127.0.0.1:8000/openapi.json`

---

## 🧪 Example API Calls

### cURL Single Prediction Example

```bash
curl -X POST "http://127.0.0.1:8000/predict" \
     -H "Content-Type: application/json" \
     -d '{
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
     }'
```

### Python Request Example

```python
import requests

url = "http://127.0.0.1:8000/predict"
payload = {
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

response = requests.post(url, json=payload)
print(response.json())
```
