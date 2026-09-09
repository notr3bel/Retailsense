"""
Database Schema Definition & Table Creation Script for RetailSense-AI.
Defines SQLAlchemy ORM Star Schema models and creates tables in PostgreSQL.
"""

from typing import Optional
from sqlalchemy import Column, Integer, String, Numeric, DateTime, Date, Boolean, ForeignKey, Index
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.engine import Engine
from database.db_connection import get_db_engine, test_connection
from etl.utils import setup_logger

logger = setup_logger("DB_CreateTables")

Base = declarative_base()


class CustomerDim(Base):
    """Customer Dimension Table"""
    __tablename__ = "customer_dim"

    customer_key = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(String(50), unique=True, nullable=False, index=True)

    sales = relationship("SalesFact", back_populates="customer")


class ProductDim(Base):
    """Product Dimension Table"""
    __tablename__ = "product_dim"

    product_key = Column(Integer, primary_key=True, autoincrement=True)
    stock_code = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(500), nullable=True)

    sales = relationship("SalesFact", back_populates="product")


class DateDim(Base):
    """Date Dimension Table"""
    __tablename__ = "date_dim"

    date_key = Column(Integer, primary_key=True)  # Format YYYYMMDD
    full_date = Column(Date, unique=True, nullable=False)
    year = Column(Integer, nullable=False)
    quarter = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    month_name = Column(String(20), nullable=False)
    day = Column(Integer, nullable=False)
    day_of_week = Column(Integer, nullable=False)
    day_name = Column(String(20), nullable=False)
    is_weekend = Column(Boolean, nullable=False)

    sales = relationship("SalesFact", back_populates="date_dim")


class CountryDim(Base):
    """Country Dimension Table"""
    __tablename__ = "country_dim"

    country_key = Column(Integer, primary_key=True, autoincrement=True)
    country_name = Column(String(100), unique=True, nullable=False)

    sales = relationship("SalesFact", back_populates="country")


class SalesFact(Base):
    """Sales Fact Table"""
    __tablename__ = "sales_fact"

    sales_id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_no = Column(String(50), nullable=False, index=True)
    customer_key = Column(Integer, ForeignKey("customer_dim.customer_key"), nullable=False, index=True)
    product_key = Column(Integer, ForeignKey("product_dim.product_key"), nullable=False, index=True)
    date_key = Column(Integer, ForeignKey("date_dim.date_key"), nullable=False, index=True)
    country_key = Column(Integer, ForeignKey("country_dim.country_key"), nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(12, 4), nullable=False)
    total_price = Column(Numeric(12, 4), nullable=False)
    invoice_date = Column(DateTime, nullable=False)

    # ORM Relationships
    customer = relationship("CustomerDim", back_populates="sales")
    product = relationship("ProductDim", back_populates="sales")
    date_dim = relationship("DateDim", back_populates="sales")
    country = relationship("CountryDim", back_populates="sales")


def create_tables(engine: Optional[Engine] = None) -> None:
    """
    Creates all Star Schema database tables using SQLAlchemy ORM Metadata.
    
    Args:
        engine: Optional SQLAlchemy Engine. If None, retrieves engine via get_db_engine().
    """
    if engine is None:
        engine = get_db_engine()

    logger.info("Initializing table creation in database...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("All Star Schema tables (customer_dim, product_dim, date_dim, country_dim, sales_fact) created successfully.")
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        raise


if __name__ == "__main__":
    engine = get_db_engine()
    if not test_connection(engine):
        logger.warning("PostgreSQL server not reachable. Using SQLite database file for table creation test...")
        engine = get_db_engine(db_url="sqlite:///database/retailsense_dw.db")

    create_tables(engine)
