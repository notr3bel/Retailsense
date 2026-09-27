# RetailSense-AI Docker Containerization Architecture

This document provides complete technical documentation for the **Docker & Docker Compose Containerization Layer** in **RetailSense-AI**.

---

## 🏛️ Microservice Container Architecture

RetailSense-AI is containerized into three decoupled microservices orchestrated via **Docker Compose**:

```text
                           Docker Compose Network
                                     │
          ┌──────────────────────────┼──────────────────────────┐
          │                          │                          │
          ▼                          ▼                          ▼
   retailsense-postgres       retailsense-api          retailsense-dashboard
    (PostgreSQL 15 DW)      (FastAPI Model Serving)     (Streamlit BI Interface)
   Port: 5432:5432           Port: 8000:8000             Port: 8501:8501
   DNS: postgres             DNS: api                    DNS: dashboard
          │                          │                          │
          │                          ▼                          │
   postgres_data             best_model.pkl                     │
    (Named Volume)           (Loaded once at startup)            │
          │                                                     │
          └──────────────────────────┬──────────────────────────┘
                                     │
                                     ▼
                      Container-to-Container DNS:
                       dashboard ──► http://api:8000
                       api ──► postgres:5432
```

---

## 🚀 Key Container Features

1. **Deterministic Zero-Retrain Runtime**: `docker compose up` loads pre-trained `models/best_model.pkl` once at startup. It does **NOT** retrain ML models or re-run 1.17M row ETL loops.
2. **Pinned Dependency Versions**: `requirements-api.txt` and `requirements-dashboard.txt` use pinned/constrained package versions (`scikit-learn`, `xgboost`, `pandas`, `numpy`, `joblib`, `fastapi`, `pydantic`, `streamlit`) matching the working local environment.
3. **Fresh Database Schema Initialization**: `database/schema.sql` is mounted to `/docker-entrypoint-initdb.d/schema.sql` and executes automatically when the PostgreSQL container is initialized for the first time. The named Docker volume `postgres_data` preserves tables across container restarts.
4. **Selective Dashboard Copies**: Only runtime analytical artifacts (`data/gold/*.csv`, `data/processed/final_dataset.csv`, `data/ml/*.csv`, `reports/`) are copied into the dashboard image. Raw 1.17M datasets are excluded.
5. **Decoupled Architecture**: MLflow and Airflow remain local experiment tracking and workflow tools and are **not** required as runtime container dependencies for model inference or dashboard views.

---

## 📋 Docker Compose Services & Ports

| Service Name | Container Name | Image / Build | Host Port | Container Port | Purpose |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`postgres`** | `retailsense-postgres` | `postgres:15-alpine` | `5432` | `5432` | PostgreSQL Star Schema DW |
| **`api`** | `retailsense-api` | `Dockerfile.api` | `8000` | `8000` | FastAPI Champion Model Inference API |
| **`dashboard`** | `retailsense-dashboard` | `Dockerfile.dashboard` | `8501` | `8501` | Streamlit BI & MLOps Dashboard |

---

## ⚙️ Quick Start Guide

### 1. Environment Configuration

Copy the template environment file `.env.example` to `.env`:

```bash
cp .env.example .env
```

### 2. Validate Compose Configuration

```bash
docker compose config
```

### 3. Build & Launch Microservices

```bash
# Build all images
docker compose build

# Start services in background
docker compose up -d

# Check running status & health
docker compose ps
```

---

## 🔍 Service Access URLs

- **Streamlit BI Dashboard**: `http://localhost:8501`
- **FastAPI Interactive Docs**: `http://localhost:8000/docs`
- **FastAPI Health Check**: `http://localhost:8000/health`
- **PostgreSQL Database**: `localhost:5432` (`DB_NAME=retailsense_db`, `USER=postgres`)

---

## 🌐 Container-to-Container Connectivity

Inside the Docker Compose network, services communicate using Compose DNS service names:

- **Dashboard to API**: `http://api:8000/health`
- **API to PostgreSQL**: `postgres:5432`

### Connectivity Verification Commands

```bash
# Test dashboard -> api internal DNS resolution
docker compose exec dashboard curl -s http://api:8000/health

# Test postgres readiness
docker compose exec postgres pg_isready -U postgres -d retailsense_db
```

---

## 🛑 Stopping & Restarting Services

```bash
# Stop containers (preserves database data volume)
docker compose down

# Restart containers (data volume postgres_data persists)
docker compose up -d

# Stop containers AND destroy data volume (clean slate)
docker compose down -v
```
