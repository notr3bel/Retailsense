"""
Database Connection Utility for RetailSense-AI.
Configures SQLAlchemy engine and session factory using environment variables.
"""

import os
import logging
from typing import Optional
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from etl.utils import setup_logger

load_dotenv()
logger = setup_logger("DB_Connection")


def get_db_url(use_sqlite_fallback: bool = False) -> str:
    """
    Constructs the database connection string from environment variables.
    
    Args:
        use_sqlite_fallback: If True, returns SQLite fallback connection string.
        
    Returns:
        str: SQLAlchemy connection URL.
    """
    if use_sqlite_fallback:
        sqlite_path = os.path.abspath("database/retailsense_dw.db")
        return f"sqlite:///{sqlite_path}"

    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "postgres")
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "retailsense_db")

    return f"postgresql://{user}:{password}@{host}:{port}/{db_name}"


def get_db_engine(db_url: Optional[str] = None, pool_size: int = 10, max_overflow: int = 20) -> Engine:
    """
    Creates and returns a SQLAlchemy Database Engine.
    
    Args:
        db_url: Connection URL string. If None, builds URL from .env.
        pool_size: Connection pool size.
        max_overflow: Max overflow connections.
        
    Returns:
        Engine: SQLAlchemy Engine instance.
    """
    if db_url is None:
        db_url = get_db_url()

    # Determine if SQLite or PostgreSQL
    if db_url.startswith("sqlite"):
        engine = create_engine(db_url, echo=False)
    else:
        engine = create_engine(
            db_url,
            pool_size=pool_size,
            max_overflow=max_overflow,
            echo=False,
            future=True
        )

    return engine


def get_db_session(engine: Optional[Engine] = None) -> Session:
    """
    Creates a new SQLAlchemy Session.
    
    Args:
        engine: SQLAlchemy Engine instance.
        
    Returns:
        Session: Active database session.
    """
    if engine is None:
        engine = get_db_engine()
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def test_connection(engine: Optional[Engine] = None) -> bool:
    """
    Tests database connectivity by executing a lightweight query.
    
    Args:
        engine: SQLAlchemy engine instance.
        
    Returns:
        bool: True if connection is successful, False otherwise.
    """
    if engine is None:
        engine = get_db_engine()

    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            value = result.scalar()
            if value == 1:
                logger.info("Database connection test successful.")
                return True
    except Exception as e:
        logger.warning(f"Database connection attempt failed: {e}")
        return False
    return False
