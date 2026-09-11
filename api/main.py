"""
FastAPI REST Application for RetailSense-AI.
Exposes endpoints for health monitoring, model metadata, single prediction, and batch inference.
"""

from contextlib import asynccontextmanager
from typing import Dict, Any
from fastapi import FastAPI, HTTPException, status, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from etl.utils import setup_logger
from api.config import APP_TITLE, APP_DESCRIPTION, APP_VERSION, MAX_BATCH_SIZE
from api.schemas import (
    CustomerFeatures,
    PredictionResponse,
    BatchPredictionRequest,
    BatchPredictionResponse,
    HealthResponse,
    ModelInfoResponse
)
from api.model_service import model_service

logger = setup_logger("API_Main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI Lifespan context manager.
    Ensures model pipeline is loaded on server startup.
    """
    logger.info("Initializing RetailSense-AI FastAPI Application...")
    if not model_service.is_ready():
        model_service.load_model()
    yield
    logger.info("Shutting down RetailSense-AI FastAPI Application.")


app = FastAPI(
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)


# Exception Handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handles Pydantic validation errors (including extra="forbid" field rejections like recency_days).
    Returns clean HTTP 422 JSON response without internal stack trace leakage.
    """
    logger.warning(f"Validation error on endpoint [{request.url.path}]: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Input validation failed. Please check field names, types, and constraints.",
            "errors": exc.errors()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    Handles uncaught internal server errors.
    Logs error internally and returns clean HTTP 500 JSON response.
    """
    logger.error(f"Internal server error on endpoint [{request.url.path}]: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please try again later."}
    )


# API Endpoints
@app.get("/", tags=["General"])
def read_root() -> Dict[str, Any]:
    """Root endpoint welcoming API clients and providing documentation links."""
    return {
        "message": "Welcome to RetailSense-AI Churn Prediction REST API",
        "version": APP_VERSION,
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "health_url": "/health"
    }


@app.get("/health", response_model=HealthResponse, tags=["Monitoring"])
def health_check() -> HealthResponse:
    """
    Health check endpoint returning service operational status and model readiness.
    """
    health = model_service.get_health_status()
    if not health.model_loaded:
        logger.error("Health check failed: Model pipeline is not loaded.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model service is currently unavailable or model artifact is missing."
        )
    return health


@app.get("/model/info", response_model=ModelInfoResponse, tags=["Model Info"])
def get_model_info() -> ModelInfoResponse:
    """
    Returns model metadata, evaluation metrics, and feature configuration.
    """
    if not model_service.is_ready():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model service is unavailable."
        )
    return model_service.get_model_info()


@app.post(
    "/predict",
    response_model=PredictionResponse,
    status_code=status.HTTP_200_OK,
    tags=["Inference"]
)
def predict_churn(customer: CustomerFeatures) -> PredictionResponse:
    """
    Executes real-time single customer churn prediction using champion XGBoost pipeline.
    
    Accepts 23 behavioral features. Extra fields (e.g. recency_days, customer_id) raise HTTP 422.
    """
    if not model_service.is_ready():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model service is unavailable."
        )

    try:
        response = model_service.predict(customer)
        return response
    except Exception as e:
        logger.error(f"Single prediction error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction execution failed: {str(e)}"
        )


@app.post(
    "/predict/batch",
    response_model=BatchPredictionResponse,
    status_code=status.HTTP_200_OK,
    tags=["Inference"]
)
def predict_churn_batch(payload: BatchPredictionRequest) -> BatchPredictionResponse:
    """
    Executes high-throughput batch customer churn prediction.
    
    Maximum allowed batch size: 1000 customer records per request.
    """
    if not model_service.is_ready():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model service is unavailable."
        )

    if len(payload.customers) > MAX_BATCH_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Batch size limit exceeded. Maximum allowed batch size is {MAX_BATCH_SIZE} records."
        )

    try:
        response = model_service.predict_batch(payload.customers)
        return response
    except Exception as e:
        logger.error(f"Batch prediction error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch prediction execution failed: {str(e)}"
        )
