-- ============================================================================
-- RetailSense-AI PostgreSQL Data Warehouse Schema (Star Schema)
-- ============================================================================

-- Drop tables if they exist (Reverse order of dependencies)
DROP TABLE IF EXISTS sales_fact CASCADE;
DROP TABLE IF EXISTS customer_dim CASCADE;
DROP TABLE IF EXISTS product_dim CASCADE;
DROP TABLE IF EXISTS date_dim CASCADE;
DROP TABLE IF EXISTS country_dim CASCADE;

-- 1. Customer Dimension Table
CREATE TABLE customer_dim (
    customer_key SERIAL PRIMARY KEY,
    customer_id VARCHAR(50) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Product Dimension Table
CREATE TABLE product_dim (
    product_key SERIAL PRIMARY KEY,
    stock_code VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Date Dimension Table
CREATE TABLE date_dim (
    date_key INT PRIMARY KEY, -- YYYYMMDD format (e.g. 20091201)
    full_date DATE UNIQUE NOT NULL,
    year INT NOT NULL,
    quarter INT NOT NULL,
    month INT NOT NULL,
    month_name VARCHAR(20) NOT NULL,
    day INT NOT NULL,
    day_of_week INT NOT NULL,
    day_name VARCHAR(20) NOT NULL,
    is_weekend BOOLEAN NOT NULL
);

-- 4. Country Dimension Table
CREATE TABLE country_dim (
    country_key SERIAL PRIMARY KEY,
    country_name VARCHAR(100) UNIQUE NOT NULL
);

-- 5. Sales Fact Table
CREATE TABLE sales_fact (
    sales_id BIGSERIAL PRIMARY KEY,
    invoice_no VARCHAR(50) NOT NULL,
    customer_key INT NOT NULL REFERENCES customer_dim(customer_key) ON DELETE CASCADE,
    product_key INT NOT NULL REFERENCES product_dim(product_key) ON DELETE CASCADE,
    date_key INT NOT NULL REFERENCES date_dim(date_key) ON DELETE CASCADE,
    country_key INT NOT NULL REFERENCES country_dim(country_key) ON DELETE CASCADE,
    quantity INT NOT NULL,
    unit_price NUMERIC(12, 4) NOT NULL,
    total_price NUMERIC(12, 4) NOT NULL,
    invoice_date TIMESTAMP NOT NULL
);

-- ============================================================================
-- Indexes for Query Optimization
-- ============================================================================
CREATE INDEX idx_sales_fact_customer ON sales_fact(customer_key);
CREATE INDEX idx_sales_fact_product ON sales_fact(product_key);
CREATE INDEX idx_sales_fact_date ON sales_fact(date_key);
CREATE INDEX idx_sales_fact_country ON sales_fact(country_key);
CREATE INDEX idx_sales_fact_invoice ON sales_fact(invoice_no);
CREATE INDEX idx_customer_dim_id ON customer_dim(customer_id);
CREATE INDEX idx_product_dim_stock ON product_dim(stock_code);
