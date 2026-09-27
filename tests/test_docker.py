"""
Unit and Integration Tests for Docker and Docker Compose Containerization Configuration.
"""

import os
from pathlib import Path
import pytest
from database.db_connection import get_db_url

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_docker_configuration_files_exist():
    """Verifies that all required Docker build & orchestration files exist."""
    assert (PROJECT_ROOT / "Dockerfile.api").exists()
    assert (PROJECT_ROOT / "Dockerfile.dashboard").exists()
    assert (PROJECT_ROOT / "docker-compose.yml").exists()
    assert (PROJECT_ROOT / ".dockerignore").exists()
    assert (PROJECT_ROOT / ".env.example").exists()
    assert (PROJECT_ROOT / "requirements-api.txt").exists()
    assert (PROJECT_ROOT / "requirements-dashboard.txt").exists()


def test_dockerignore_excludes():
    """Verifies that .dockerignore excludes raw data, tests, and temporary caches."""
    dockerignore_path = PROJECT_ROOT / ".dockerignore"
    content = dockerignore_path.read_text()

    assert ".git" in content
    assert "mlruns" in content
    assert "tests" in content
    assert "data/raw/*" in content


def test_schema_sql_exists():
    """Verifies database/schema.sql exists for fresh PostgreSQL volume initialization."""
    schema_path = PROJECT_ROOT / "database" / "schema.sql"
    assert schema_path.exists()
    assert len(schema_path.read_text()) > 100


def test_postgres_environment_variable_override(monkeypatch):
    """Verifies database connection builder respects POSTGRES_* environment variables."""
    monkeypatch.setenv("POSTGRES_USER", "docker_user")
    monkeypatch.setenv("POSTGRES_PASSWORD", "docker_pass")
    monkeypatch.setenv("POSTGRES_HOST", "postgres")
    monkeypatch.setenv("POSTGRES_PORT", "5432")
    monkeypatch.setenv("POSTGRES_DB", "docker_db")

    url = get_db_url(use_sqlite_fallback=False)
    assert url == "postgresql://docker_user:docker_pass@postgres:5432/docker_db"
