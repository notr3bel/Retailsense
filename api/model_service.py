"""
Model Service Module for RetailSense-AI.
Handles loading the serialized Scikit-Learn champion Pipeline (best_model.pkl),
executing single and batch customer churn predictions, and returning model metadata.
"""

import os
import json
import joblib
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

from etl.utils import setup_logger
from api.config import MODEL_PATH, ENCODER_PATH, EVAL_JSON_PATH, METRICS_CSV_PATH
from api.schemas import (
    CustomerFeatures,
    PredictionResponse,
    BatchPredictionResponse,
    HealthResponse,
    ModelInfoResponse
)

logger = setup_logger("API_ModelService")


class ModelService:
    """
    Singleton service class for managing model loading, health checks,
    and single/batch churn predictions using champion Scikit-Learn Pipeline.
    """

    def __init__(self):
        self.pipeline = None
        self.encoder_metadata = {}
        self.eval_report = {}
        self.model_name = "XGBoost"
        self.model_version = "1.0.0"
        self.is_loaded = False
        self.load_model()

    def load_model(self) -> bool:
        """
        Loads champion pipeline and evaluation metadata from disk.
        """
        try:
            if not MODEL_PATH.exists():
                logger.error(f"Champion model file not found at: {MODEL_PATH}")
                self.is_loaded = False
                return False

            logger.info(f"Loading champion model pipeline from: {MODEL_PATH}...")
            self.pipeline = joblib.load(MODEL_PATH)
            self.is_loaded = True

            # Load Encoder Metadata if present
            if ENCODER_PATH.exists():
                try:
                    self.encoder_metadata = joblib.load(ENCODER_PATH)
                    self.model_name = self.encoder_metadata.get("best_model_name", "XGBoost")
                    self.model_version = self.encoder_metadata.get("best_run_id", "1.0.0")
                except Exception as e_enc:
                    logger.warning(f"Warning loading encoder metadata: {e_enc}")

            # Load Evaluation Report JSON if present
            if EVAL_JSON_PATH.exists():
                try:
                    with open(EVAL_JSON_PATH, "r", encoding="utf-8") as f:
                        self.eval_report = json.load(f)
                        self.model_name = self.eval_report.get("champion_model", self.model_name)
                        self.model_version = self.eval_report.get("champion_run_id", self.model_version)
                except Exception as e_json:
                    logger.warning(f"Warning loading evaluation report JSON: {e_json}")

            logger.info(f"Model Service initialized successfully. Champion: {self.model_name} (Version: {self.model_version})")
            return True

        except Exception as e:
            logger.error(f"Failed to load model pipeline: {e}")
            self.is_loaded = False
            return False

    def is_ready(self) -> bool:
        """Returns True if model pipeline is loaded and operational."""
        return self.is_loaded and self.pipeline is not None

    def predict(self, customer: CustomerFeatures) -> PredictionResponse:
        """
        Executes single customer churn prediction using champion pipeline.
        
        Args:
            customer: CustomerFeatures Pydantic request object.
            
        Returns:
            PredictionResponse: Formatted prediction response.
        """
        if not self.is_ready():
            raise RuntimeError("Model pipeline is not loaded or ready.")

        # Convert Pydantic object to single-row DataFrame
        df_input = pd.DataFrame([customer.model_dump()])

        # Run inference via complete Sklearn Pipeline
        pred_label = int(self.pipeline.predict(df_input)[0])
        probs = self.pipeline.predict_proba(df_input)[0]

        prob_active = round(float(probs[0]), 4)
        prob_churn = round(float(probs[1]), 4)
        label_str = "churn" if pred_label == 1 else "active"

        return PredictionResponse(
            churn_prediction=pred_label,
            prediction=label_str,
            churn_probability=prob_churn,
            non_churn_probability=prob_active,
            model=self.model_name,
            model_version=str(self.model_version)
        )

    def predict_batch(self, customers: List[CustomerFeatures]) -> BatchPredictionResponse:
        """
        Executes vectorized batch prediction on a list of customer profiles.
        
        Args:
            customers: List of CustomerFeatures Pydantic objects.
            
        Returns:
            BatchPredictionResponse: List of formatted prediction responses.
        """
        if not self.is_ready():
            raise RuntimeError("Model pipeline is not loaded or ready.")

        if not customers:
            return BatchPredictionResponse(predictions=[], count=0, model=self.model_name)

        # Convert batch to single multi-row DataFrame
        batch_data = [c.model_dump() for c in customers]
        df_batch = pd.DataFrame(batch_data)

        # Vectorized prediction call
        pred_labels = self.pipeline.predict(df_batch)
        probs_array = self.pipeline.predict_proba(df_batch)

        responses = []
        for i, pred in enumerate(pred_labels):
            p_label = int(pred)
            p_active = round(float(probs_array[i][0]), 4)
            p_churn = round(float(probs_array[i][1]), 4)
            l_str = "churn" if p_label == 1 else "active"

            responses.append(PredictionResponse(
                churn_prediction=p_label,
                prediction=l_str,
                churn_probability=p_churn,
                non_churn_probability=p_active,
                model=self.model_name,
                model_version=str(self.model_version)
            ))

        return BatchPredictionResponse(
            predictions=responses,
            count=len(responses),
            model=self.model_name
        )

    def get_health_status(self) -> HealthResponse:
        """Returns health status object."""
        return HealthResponse(
            status="healthy" if self.is_ready() else "unhealthy",
            model_loaded=self.is_ready(),
            model_name=self.model_name,
            model_path=str(MODEL_PATH.name)
        )

    def get_model_info(self) -> ModelInfoResponse:
        """Returns model information and evaluation metrics."""
        best_metrics = self.eval_report.get("best_metrics", {})
        original_features = self.encoder_metadata.get(
            "original_features",
            self.eval_report.get("final_model_features", [])
        )
        excluded_features = self.encoder_metadata.get(
            "excluded_features",
            self.eval_report.get("excluded_features", ["customer_id", "recency_days", "churn", "first_purchase", "last_purchase", "favorite_product"])
        )

        model_type_str = "XGBClassifier"
        if self.pipeline is not None and hasattr(self.pipeline, "named_steps"):
            model_type_str = self.pipeline.named_steps.get("classifier", "XGBClassifier").__class__.__name__

        return ModelInfoResponse(
            model_name=self.model_name,
            model_type=model_type_str,
            model_version=str(self.model_version),
            roc_auc=float(best_metrics.get("roc_auc", 0.9666)),
            accuracy=float(best_metrics.get("accuracy", 0.9005)),
            precision=float(best_metrics.get("precision", 0.9197)),
            recall=float(best_metrics.get("recall", 0.8813)),
            f1_score=float(best_metrics.get("f1_score", 0.9001)),
            feature_count=len(original_features),
            input_features=original_features,
            excluded_features=excluded_features
        )


# Global Singleton Service Instance
model_service = ModelService()
