"""
FastAPI application package initialization for RetailSense-AI.
"""

from api.main import app
from api.model_service import model_service

__all__ = ["app", "model_service"]
