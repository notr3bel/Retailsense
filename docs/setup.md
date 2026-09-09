# 🛠️ Setup & Installation Guide - RetailSense-AI

Follow this step-by-step installation guide to set up **RetailSense-AI** locally on Windows, macOS, or Linux.

---

## Environment Prerequisites

- **Python**: Version `3.10` or higher
- **PostgreSQL**: Version `14.0` or higher (Optional: SQLite fallback built-in)
- **Git**: Latest release
- **Virtualenv**: Python `venv` module

---

## Step 1: Clone Repository

```bash
git clone https://github.com/notr3bel/Retailsense.git
cd Retailsense
```

---

## Step 2: Create Virtual Environment

### Windows PowerShell:
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Linux / macOS:
```bash
python3 -m venv venv
source venv/bin/activate
```

---

## Step 3: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## Step 4: Database Configuration (PostgreSQL)

If using PostgreSQL, create a `.env` file in the project root:

```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=retailsense_dw
```

To initialize database schema and load tables:
```bash
python -m database.create_tables
python -m database.load_postgres
```

*Note: If PostgreSQL connection credentials are not detected, RetailSense-AI falls back seamlessly to SQLite at `database/retailsense_dw.db`.*

---

## Step 5: Execute ETL Pipeline

To execute raw data ingestion, validation, transformation, and Gold Layer creation:

```bash
python -m etl.pipeline
```

---

## Step 6: Launch Streamlit BI Dashboard

```bash
streamlit run dashboard/app.py
```

Access the dashboard at `http://localhost:8501`.
