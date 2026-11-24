/*
Inventory Reorder System
03_create_warehouse_tables.sql

Warehouse tables organize cleaned staging data into dimensions and facts.
Dimensions describe business objects. Facts store business events.
*/

CREATE TABLE IF NOT EXISTS dim_supplier (
    supplier_key BIGSERIAL PRIMARY KEY,
    supplier_id VARCHAR(20) NOT NULL UNIQUE,
    supplier_name VARCHAR(200) NOT NULL,
    contact_phone VARCHAR(50),
    city VARCHAR(100),
    lead_time_days INTEGER NOT NULL CHECK (lead_time_days > 0),
    minimum_order_value NUMERIC(14, 2) NOT NULL CHECK (minimum_order_value >= 0),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS dim_branch (
    branch_key BIGSERIAL PRIMARY KEY,
    branch_id VARCHAR(20) NOT NULL UNIQUE,
    branch_name VARCHAR(200) NOT NULL,
    city VARCHAR(100),
    township VARCHAR(100),
    branch_type VARCHAR(100),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS dim_product (
    product_key BIGSERIAL PRIMARY KEY,
    product_id VARCHAR(20) NOT NULL UNIQUE,
    product_name VARCHAR(200) NOT NULL,
    category VARCHAR(100) NOT NULL,
    brand VARCHAR(100),
    unit_cost NUMERIC(12, 2) NOT NULL CHECK (unit_cost >= 0),
    selling_price NUMERIC(12, 2) NOT NULL CHECK (selling_price > 0),
    supplier_key BIGINT NOT NULL REFERENCES dim_supplier(supplier_key),
    shelf_life_days INTEGER,
    min_order_quantity INTEGER NOT NULL CHECK (min_order_quantity > 0),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS dim_date (
    date_key INTEGER PRIMARY KEY,
    full_date DATE NOT NULL UNIQUE,
    day_of_month INTEGER NOT NULL,
    month_number INTEGER NOT NULL,
    month_name VARCHAR(20) NOT NULL,
    quarter_number INTEGER NOT NULL,
    year_number INTEGER NOT NULL,
    week_of_year INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL,
    day_name VARCHAR(20) NOT NULL,
    is_weekend BOOLEAN NOT NULL
);

CREATE TABLE IF NOT EXISTS fact_sales (
    sales_key BIGSERIAL PRIMARY KEY,
    sale_id VARCHAR(30) NOT NULL UNIQUE,
    sale_date DATE NOT NULL,
    date_key INTEGER NOT NULL REFERENCES dim_date(date_key),
    branch_key BIGINT NOT NULL REFERENCES dim_branch(branch_key),
    product_key BIGINT NOT NULL REFERENCES dim_product(product_key),
    quantity_sold INTEGER NOT NULL CHECK (quantity_sold > 0),
    unit_price NUMERIC(12, 2) NOT NULL CHECK (unit_price >= 0),
    total_sales_amount NUMERIC(14, 2) GENERATED ALWAYS AS (quantity_sold * unit_price) STORED,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS fact_stock_movement (
    stock_movement_key BIGSERIAL PRIMARY KEY,
    movement_id VARCHAR(30) NOT NULL UNIQUE,
    movement_date DATE NOT NULL,
    date_key INTEGER NOT NULL REFERENCES dim_date(date_key),
    branch_key BIGINT NOT NULL REFERENCES dim_branch(branch_key),
    product_key BIGINT NOT NULL REFERENCES dim_product(product_key),
    movement_type VARCHAR(50) NOT NULL CHECK (
        movement_type IN (
            'purchase',
            'sale',
            'return',
            'adjustment_in',
            'adjustment_out',
            'damage'
        )
    ),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    reference_note TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_fact_sales_date_product_branch
ON fact_sales (sale_date, product_key, branch_key);

CREATE INDEX IF NOT EXISTS idx_fact_stock_movement_date_product_branch
ON fact_stock_movement (movement_date, product_key, branch_key);

