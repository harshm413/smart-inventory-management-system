/*
Inventory Reorder System
08_refresh_inventory_snapshot.sql

Refresh inventory_daily_snapshot from current inventory staging data.

Run after:
    04_create_inventory_analytics_tables.sql
    06_transform_to_warehouse.sql

This script is rerunnable:
    - it upserts one snapshot row per inventory date, branch, and product
    - available_stock is calculated by the generated column in the table
*/

BEGIN;

INSERT INTO inventory_daily_snapshot (
    inventory_date,
    date_key,
    branch_key,
    product_key,
    current_stock,
    reserved_stock,
    inventory_value
)
SELECT
    sci.inventory_date,
    dd.date_key,
    db.branch_key,
    dp.product_key,
    sci.current_stock,
    sci.reserved_stock,
    sci.current_stock * dp.unit_cost AS inventory_value
FROM stg_current_inventory sci
JOIN dim_date dd
    ON sci.inventory_date = dd.full_date
JOIN dim_branch db
    ON sci.branch_id = db.branch_id
JOIN dim_product dp
    ON sci.product_id = dp.product_id
ON CONFLICT (inventory_date, branch_key, product_key)
DO UPDATE SET
    date_key = EXCLUDED.date_key,
    current_stock = EXCLUDED.current_stock,
    reserved_stock = EXCLUDED.reserved_stock,
    inventory_value = EXCLUDED.inventory_value;

COMMIT;

/*
Quick check:

SELECT
    inventory_date,
    COUNT(*) AS snapshot_rows,
    SUM(current_stock) AS total_current_stock,
    SUM(available_stock) AS total_available_stock,
    SUM(inventory_value) AS total_inventory_value
FROM inventory_daily_snapshot
WHERE inventory_date = (
    SELECT MAX(inventory_date)
    FROM inventory_daily_snapshot
)
GROUP BY inventory_date;
*/
