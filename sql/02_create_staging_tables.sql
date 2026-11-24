/*
Inventory Reorder System
02_create_staging_tables.sql

Staging tables hold cleaned CSV data before it is transformed into warehouse
dimension and fact tables.

Run after connecting to the inventory_reorder_system database.
*/

CREATE TABLE IF NOT EXISTS stg_products (
    product_id VARCHAR(20),
    product_name VARCHAR(200),
    category VARCHAR(100),
    brand VARCHAR(100),
    unit_cost NUMERIC(12, 2),
    selling_price NUMERIC(12, 2),
    supplier_id VARCHAR(20),
    shelf_life_days INTEGER,
    min_order_quantity INTEGER
);

CREATE TABLE IF NOT EXISTS stg_branches (
    branch_id VARCHAR(20),
    branch_name VARCHAR(200),
    city VARCHAR(100),
    township VARCHAR(100),
    branch_type VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS stg_suppliers (
    supplier_id VARCHAR(20),
    supplier_name VARCHAR(200),
    contact_phone VARCHAR(50),
    city VARCHAR(100),
    lead_time_days INTEGER,
    minimum_order_value NUMERIC(14, 2)
);

CREATE TABLE IF NOT EXISTS stg_sales_history (
    sale_id VARCHAR(30),
    sale_date DATE,
    branch_id VARCHAR(20),
    product_id VARCHAR(20),
    quantity_sold INTEGER,
    unit_price NUMERIC(12, 2)
);

CREATE TABLE IF NOT EXISTS stg_stock_movements (
    movement_id VARCHAR(30),
    movement_date DATE,
    branch_id VARCHAR(20),
    product_id VARCHAR(20),
    movement_type VARCHAR(50),
    quantity INTEGER,
    reference_note TEXT
);

CREATE TABLE IF NOT EXISTS stg_current_inventory (
    inventory_date DATE,
    branch_id VARCHAR(20),
    product_id VARCHAR(20),
    current_stock INTEGER,
    reserved_stock INTEGER
);

