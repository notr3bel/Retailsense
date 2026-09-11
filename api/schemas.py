"""
Pydantic Data Validation Schemas for RetailSense-AI FastAPI Serving Layer.
Strictly validates input features (extra="forbid" raises HTTP 422 on target leakage or unknown fields).
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict


class CustomerFeatures(BaseModel):
    """
    Pydantic request schema representing 23 customer behavioral features expected by champion model.
    Configured with extra="forbid" to strictly reject target-leaking or extraneous fields (recency_days, customer_id).
    """
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
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
        }
    )

    # 19 Numerical Features
    customer_lifetime_days: float = Field(..., ge=0, description="Total days between first and last purchase")
    total_spent: float = Field(..., ge=0, description="Total revenue spent by customer")
    average_order_value: float = Field(..., ge=0, description="Average revenue per order/invoice")
    max_order_value: float = Field(..., ge=0, description="Maximum single order value")
    min_order_value: float = Field(..., ge=0, description="Minimum single order value")
    total_quantity: float = Field(..., ge=0, description="Total quantity of items purchased")
    average_quantity: float = Field(..., ge=0, description="Average quantity per order")
    total_orders: int = Field(..., ge=0, description="Total completed orders count")
    purchase_frequency: float = Field(..., ge=0, description="Orders per active lifetime day")
    purchase_velocity: float = Field(..., ge=0, description="Order placement velocity")
    average_days_between_orders: float = Field(..., ge=0, description="Average gap between orders")
    unique_products: int = Field(..., ge=0, description="Unique products purchased count")
    category_diversity: int = Field(..., ge=0, description="Number of distinct product categories")
    preferred_month: int = Field(..., ge=1, le=12, description="Most frequent purchase month (1-12)")
    preferred_hour: int = Field(..., ge=0, le=23, description="Most frequent purchase hour (0-23)")
    weekend_purchase_ratio: float = Field(..., ge=0.0, le=1.0, description="Ratio of weekend orders (0.0 to 1.0)")
    revenue_per_day: float = Field(..., ge=0, description="Revenue generated per active day")
    items_per_order: float = Field(..., ge=0, description="Average items per invoice")
    basket_size: float = Field(..., ge=0, description="Average basket monetary size")

    # 4 Categorical Features
    country: str = Field(..., min_length=1, description="Customer country of origin")
    favorite_category: str = Field(..., min_length=1, description="Top purchased product category")
    preferred_weekday: str = Field(..., min_length=1, description="Most frequent purchase weekday")
    customer_value_segment: str = Field(..., min_length=1, description="Customer value segmentation (VIP, High, Medium, Low)")


class PredictionResponse(BaseModel):
    """Prediction output schema for single customer churn inference."""
    churn_prediction: int = Field(..., description="Binary prediction: 1 = Churned, 0 = Active")
    prediction: str = Field(..., description="Human-readable prediction label ('churn' or 'active')")
    churn_probability: float = Field(..., description="Probability of churn (0.0 to 1.0)")
    non_churn_probability: float = Field(..., description="Probability of remaining active (0.0 to 1.0)")
    model: str = Field(..., description="Champion model algorithm name")
    model_version: str = Field(..., description="Model version / run identifier")


class BatchPredictionRequest(BaseModel):
    """Batch inference request schema."""
    customers: List[CustomerFeatures] = Field(..., min_length=1, description="List of customer profiles to evaluate")


class BatchPredictionResponse(BaseModel):
    """Batch inference response schema."""
    predictions: List[PredictionResponse] = Field(..., description="List of customer prediction responses")
    count: int = Field(..., description="Total batch size processed")
    model: str = Field(..., description="Champion model algorithm name")


class HealthResponse(BaseModel):
    """Health check endpoint response schema."""
    status: str = Field(..., description="Service status ('healthy' or 'unhealthy')")
    model_loaded: bool = Field(..., description="Whether champion pipeline is loaded")
    model_name: str = Field(..., description="Champion model name")
    model_path: str = Field(..., description="Model file path")


class ModelInfoResponse(BaseModel):
    """Model info endpoint response schema."""
    model_name: str = Field(..., description="Champion model name")
    model_type: str = Field(..., description="Estimator class name")
    model_version: str = Field(..., description="MLflow run ID or local version string")
    roc_auc: float = Field(..., description="Champion test ROC AUC score")
    accuracy: float = Field(..., description="Champion test accuracy")
    precision: float = Field(..., description="Champion test precision")
    recall: float = Field(..., description="Champion test recall")
    f1_score: float = Field(..., description="Champion test F1 score")
    feature_count: int = Field(..., description="Number of model input features")
    input_features: List[str] = Field(..., description="List of 23 input feature names")
    excluded_features: List[str] = Field(..., description="List of features excluded to prevent leakage")
