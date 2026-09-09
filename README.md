# RetailSense-AI 🛍️

**RetailSense-AI** is an end-to-end MLOps retail intelligence and analytics platform. It integrates data ingestion pipelines, machine learning model lifecycle management, REST API inference services, and interactive dashboards to deliver real-time retail insights.

---

## 🏗️ System Architecture

```text
┌────────────────┐     ┌────────────────┐     ┌──────────────────┐
│  Raw Data      │ ──> │ Airflow / ETL  │ ──> │ Staging &        │
│  Ingestion     │     │ Orchestration  │     │ Processed Data   │
└────────────────┘     └────────────────┘     └──────────────────┘
                                                       │
                                                       ▼
┌────────────────┐     ┌────────────────┐     ┌──────────────────┐
│  Streamlit     │ <── │ FastAPI        │ <── │ Machine Learning │
│  Dashboard UI  │     │ Serving Layer  │     │ Models & MLflow  │
└────────────────┘     └────────────────┘     └──────────────────┘
```

---

## 📁 Directory Structure

```text
RetailSense-AI/
├── data/                  # Data storage layer
│   ├── raw/               # Raw ingested datasets
│   ├── staging/           # Pre-processed/cleaned intermediate data
│   └── processed/         # Feature-engineered final datasets ready for modeling
│
├── airflow/               # Workflow orchestration layer
│   ├── dags/              # Airflow Directed Acyclic Graphs (DAGs)
│   └── logs/              # Task execution logs
│
├── database/              # Relational database schema, connection pools, & migrations
├── etl/                   # Data ingestion and transformation pipelines
├── models/                # Machine learning training, evaluation, & inference scripts
├── dashboard/             # Streamlit interactive UI application
├── api/                   # FastAPI prediction service & endpoint handlers
├── reports/               # Generated analytical reports, metrics, & figures
├── docker/                # Containerization manifests (Dockerfile, docker-compose.yml)
├── notebooks/             # Jupyter notebooks for EDA & model experimentation
├── tests/                 # Unit & integration test suites (Pytest)
│
├── .env                   # Environment variable secrets (ignored by git)
├── .gitignore             # Version control ignore specifications
├── requirements.txt       # Python project dependencies
├── README.md              # Project documentation & reference guide
└── main.py                # Main application bootstrap script
```

---

## ⚙️ Tech Stack

- **Language:** Python 3.11+
- **Data & Feature Processing:** `pandas`, `numpy`
- **Machine Learning & Tracking:** `scikit-learn`, `xgboost`, `mlflow`
- **Orchestration:** `apache-airflow`
- **Backend API:** `fastapi`, `uvicorn`, `pydantic`
- **Interactive UI:** `streamlit`
- **Database:** PostgreSQL (`sqlalchemy`, `psycopg2-binary`)
- **Containerization:** Docker & Docker Compose
- **Testing:** `pytest`, `httpx`

---

## 🚀 Setup & Installation Instructions

### 1. Prerequisites
- Python 3.11+ installed
- Git installed
- Docker Desktop (optional for containerized deployment)

### 2. Environment Setup

```bash
# Clone the repository
git clone https://github.com/your-username/RetailSense-AI.git
cd RetailSense-AI

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Variables
Verify or adjust configurations in `.env`:
```ini
APP_NAME=RetailSense-AI
ENV=development
PORT=8000
DB_HOST=localhost
DB_PORT=5432
```

---

## 🧪 Running Tests & Services

### Run Unit Tests
```bash
pytest
```

### Run FastAPI Service
```bash
uvicorn api.main:app --reload
```

### Run Streamlit Dashboard
```bash
streamlit run dashboard/app.py
```

### Run Docker Services
```bash
docker-compose -f docker/docker-compose.yml up --build
```
