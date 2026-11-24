/*
Inventory Reorder System
06_transform_to_warehouse.sql

Transform clean staging data into warehouse dimension and fact tables.

Run after:
    02_create_staging_tables.sql
    03_create_warehouse_tables.sql
    Loading processed CSV files into staging tables

This script is rerunnable:
    - dimensions use ON CONFLICT updates
    - facts use ON CONFLICT updates by source business ID
*/

BEGIN;

/* 1. Load supplier dimension. */
INSERT INTO dim_supplier (
    supplier_id,
    supplier_name,
    contact_phone,
    city,
    lead_time_days,
    minimum_order_value
)
SELECT DISTINCT
    supplier_id,
    supplier_name,
    contact_phone,
    city,
    lead_time_days,
    minimum_order_value
FROM stg_suppliers
WHERE supplier_id IS NOT NULL
ON CONFLICT (supplier_id)
DO UPDATE SET
    supplier_name = EXCLUDED.supplier_name,
    contact_phone = EXCLUDED.contact_phone,
    city = EXCLUDED.city,
    lead_time_days = EXCLUDED.lead_time_days,
    minimum_order_value = EXCLUDED.minimum_order_value;

/* 2. Load branch dimension. */
INSERT INTO dim_branch (
    branch_id,
    branch_name,
    city,
    township,
    branch_type
)
SELECT DISTINCT
    branch_id,
    branch_name,
    city,
    township,
    branch_type
FROM stg_branches
WHERE branch_id IS NOT NULL
ON CONFLICT (branch_id)
DO UPDATE SET
    branch_name = EXCLUDED.branch_name,
    city = EXCLUDED.city,
    township = EXCLUDED.township,
    branch_type = EXCLUDED.branch_type;

/*
3. Load product dimension.

The product dimension references dim_supplier using supplier_key.
This is where source supplier_id becomes a warehouse surrogate key.
*/
INSERT INTO dim_product (
    product_id,
    product_name,
    category,
    brand,
    unit_cost,
    selling_price,
    supplier_key,
    shelf_life_days,
    min_order_quantity,
    is_active
)
SELECT DISTINCT
    sp.product_id,
    sp.product_name,
    sp.category,
    sp.brand,
    sp.unit_cost,
    sp.selling_price,
    ds.supplier_key,
    sp.shelf_life_days,
    sp.min_order_quantity,
    TRUE AS is_active
FROM stg_products sp
JOIN dim_supplier ds
    ON sp.supplier_id = ds.supplier_id
WHERE sp.product_id IS NOT NULL
ON CONFLICT (product_id)
DO UPDATE SET
    product_name = EXCLUDED.product_name,
    category = EXCLUDED.category,
    brand = EXCLUDED.brand,
    unit_cost = EXCLUDED.unit_cost,
    selling_price = EXCLUDED.selling_price,
    supplier_key = EXCLUDED.supplier_key,
    shelf_life_days = EXCLUDED.shelf_life_days,
    min_order_quantity = EXCLUDED.min_order_quantity,
    is_active = EXCLUDED.is_active;

/*
4. Load date dimension.

date_key uses YYYYMMDD format.
Example:
    2026-05-06 becomes 20260506
*/
WITH source_dates AS (
    SELECT sale_date AS full_date
    FROM stg_sales_history
    WHERE sale_date IS NOT NULL

    UNION

    SELECT movement_date AS full_date
    FROM stg_stock_movements
    WHERE movement_date IS NOT NULL

    UNION

    SELECT inventory_date AS full_date
    FROM stg_current_inventory
    WHERE inventory_date IS NOT NULL
)
INSERT INTO dim_date (
    date_key,
    full_date,
    day_of_month,
    month_number,
    month_name,
    quarter_number,
    year_number,
    week_of_year,
    day_of_week,
    day_name,
    is_weekend
)
SELECT
    TO_CHAR(full_date, 'YYYYMMDD')::INTEGER AS date_key,
    full_date,
    EXTRACT(DAY FROM full_date)::INTEGER AS day_of_month,
    EXTRACT(MONTH FROM full_date)::INTEGER AS month_number,
    TO_CHAR(full_date, 'Month') AS month_name,
    EXTRACT(QUARTER FROM full_date)::INTEGER AS quarter_number,
    EXTRACT(YEAR FROM full_date)::INTEGER AS year_number,
    EXTRACT(WEEK FROM full_date)::INTEGER AS week_of_year,
    EXTRACT(ISODOW FROM full_date)::INTEGER AS day_of_week,
    TO_CHAR(full_date, 'Day') AS day_name,
    EXTRACT(ISODOW FROM full_date)::INTEGER IN (6, 7) AS is_weekend
FROM source_dates
ON CONFLICT (date_key)
DO UPDATE SET
    full_date = EXCLUDED.full_date,
    day_of_month = EXCLUDED.day_of_month,
    month_number = EXCLUDED.month_number,
    month_name = EXCLUDED.month_name,
    quarter_number = EXCLUDED.quarter_number,
    year_number = EXCLUDED.year_number,
    week_of_year = EXCLUDED.week_of_year,
    day_of_week = EXCLUDED.day_of_week,
    day_name = EXCLUDED.day_name,
    is_weekend = EXCLUDED.is_weekend;

/*
5. Load sales fact.

fact_sales stores customer demand. PostgreSQL calculates total_sales_amount
from quantity_sold * unit_price using the generated column.
*/
INSERT INTO fact_sales (
    sale_id,
    sale_date,
    date_key,
    branch_key,
    product_key,
    quantity_sold,
    unit_price
)
SELECT
    ss.sale_id,
    ss.sale_date,
    dd.date_key,
    db.branch_key,
    dp.product_key,
    ss.quantity_sold,
    ss.unit_price
FROM stg_sales_history ss
JOIN dim_date dd
    ON ss.sale_date = dd.full_date
JOIN dim_branch db
    ON ss.branch_id = db.branch_id
JOIN dim_product dp
    ON ss.product_id = dp.product_id
WHERE ss.sale_id IS NOT NULL
ON CONFLICT (sale_id)
DO UPDATE SET
    sale_date = EXCLUDED.sale_date,
    date_key = EXCLUDED.date_key,
    branch_key = EXCLUDED.branch_key,
    product_key = EXCLUDED.product_key,
    quantity_sold = EXCLUDED.quantity_sold,
    unit_price = EXCLUDED.unit_price;

/*
6. Load stock movement fact.

fact_stock_movement stores inventory events: purchases, sales, returns,
adjustments, and damage.
*/
INSERT INTO fact_stock_movement (
    movement_id,
    movement_date,
    date_key,
    branch_key,
    product_key,
    movement_type,
    quantity,
    reference_note
)
SELECT
    sm.movement_id,
    sm.movement_date,
    dd.date_key,
    db.branch_key,
    dp.product_key,
    sm.movement_type,
    sm.quantity,
    sm.reference_note
FROM stg_stock_movements sm
JOIN dim_date dd
    ON sm.movement_date = dd.full_date
JOIN dim_branch db
    ON sm.branch_id = db.branch_id
JOIN dim_product dp
    ON sm.product_id = dp.product_id
WHERE sm.movement_id IS NOT NULL
ON CONFLICT (movement_id)
DO UPDATE SET
    movement_date = EXCLUDED.movement_date,
    date_key = EXCLUDED.date_key,
    branch_key = EXCLUDED.branch_key,
    product_key = EXCLUDED.product_key,
    movement_type = EXCLUDED.movement_type,
    quantity = EXCLUDED.quantity,
    reference_note = EXCLUDED.reference_note;

COMMIT;

/*
Quick row count check.
Run manually after the script if you want a simple verification:

SELECT 'dim_supplier' AS table_name, COUNT(*) FROM dim_supplier
UNION ALL
SELECT 'dim_branch', COUNT(*) FROM dim_branch
UNION ALL
SELECT 'dim_product', COUNT(*) FROM dim_product
UNION ALL
SELECT 'dim_date', COUNT(*) FROM dim_date
UNION ALL
SELECT 'fact_sales', COUNT(*) FROM fact_sales
UNION ALL
SELECT 'fact_stock_movement', COUNT(*) FROM fact_stock_movement;
*/

