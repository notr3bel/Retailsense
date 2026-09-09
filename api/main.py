"""
FastAPI REST Service for RetailSense-AI.
Exposes endpoints for inference, model predictions, and health monitoring.
"""

from fastapi import FastAPI

app = FastAPI(
    title="RetailSense-AI API",
    description="End-to-End Retail Intelligence & Prediction API",
    version="0.1.0"
)

@app.get("/")
def read_root():
    return {"message": "Welcome to RetailSense-AI REST API"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
