/*
Inventory Reorder System
07_calculate_sales_velocity.sql

Calculate product sales velocity by branch.

Run after:
    03_create_warehouse_tables.sql
    04_create_inventory_analytics_tables.sql
    06_transform_to_warehouse.sql

This script is rerunnable:
    - it calculates demand as of the latest sales date in fact_sales
    - it upserts one row per calculation date, branch, and product
    - it keeps products with no recent sales by storing zero quantities
*/

BEGIN;

/*
Keep this script compatible with databases created before the analytics
table column names were standardized.
*/
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'product_sales_velocity'
          AND column_name = 'analysis_date'
    ) AND NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'product_sales_velocity'
          AND column_name = 'calculation_date'
    ) THEN
        ALTER TABLE product_sales_velocity
        RENAME COLUMN analysis_date TO calculation_date;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'product_sales_velocity'
          AND column_name = 'units_sold_7d'
    ) AND NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'product_sales_velocity'
          AND column_name = 'qty_sold_7d'
    ) THEN
        ALTER TABLE product_sales_velocity
        RENAME COLUMN units_sold_7d TO qty_sold_7d;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'product_sales_velocity'
          AND column_name = 'units_sold_14d'
    ) AND NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'product_sales_velocity'
          AND column_name = 'qty_sold_14d'
    ) THEN
        ALTER TABLE product_sales_velocity
        RENAME COLUMN units_sold_14d TO qty_sold_14d;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'product_sales_velocity'
          AND column_name = 'units_sold_30d'
    ) AND NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'product_sales_velocity'
          AND column_name = 'qty_sold_30d'
    ) THEN
        ALTER TABLE product_sales_velocity
        RENAME COLUMN units_sold_30d TO qty_sold_30d;
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS product_sales_velocity (
    velocity_key BIGSERIAL PRIMARY KEY,
    calculation_date DATE NOT NULL,
    date_key INTEGER NOT NULL REFERENCES dim_date(date_key),
    branch_key BIGINT NOT NULL REFERENCES dim_branch(branch_key),
    product_key BIGINT NOT NULL REFERENCES dim_product(product_key),
    qty_sold_7d INTEGER NOT NULL DEFAULT 0 CHECK (qty_sold_7d >= 0),
    qty_sold_14d INTEGER NOT NULL DEFAULT 0 CHECK (qty_sold_14d >= 0),
    qty_sold_30d INTEGER NOT NULL DEFAULT 0 CHECK (qty_sold_30d >= 0),
    avg_daily_demand_7d NUMERIC(12, 2) NOT NULL DEFAULT 0 CHECK (avg_daily_demand_7d >= 0),
    avg_daily_demand_14d NUMERIC(12, 2) NOT NULL DEFAULT 0 CHECK (avg_daily_demand_14d >= 0),
    avg_daily_demand_30d NUMERIC(12, 2) NOT NULL DEFAULT 0 CHECK (avg_daily_demand_30d >= 0),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_product_sales_velocity UNIQUE (calculation_date, branch_key, product_key)
);

CREATE INDEX IF NOT EXISTS idx_product_sales_velocity_date
ON product_sales_velocity (calculation_date);

/*
Use the latest sale date as the calculation date so the result is stable
for sample data and historical reruns.
*/
WITH calculation AS (
    SELECT MAX(sale_date) AS calculation_date
    FROM fact_sales
),
sales_velocity AS (
    SELECT
        c.calculation_date,
        dd.date_key,
        db.branch_key,
        dp.product_key,
        COALESCE(SUM(fs.quantity_sold) FILTER (
            WHERE fs.sale_date > c.calculation_date - INTERVAL '7 days'
              AND fs.sale_date <= c.calculation_date
        ), 0)::INTEGER AS qty_sold_7d,
        COALESCE(SUM(fs.quantity_sold) FILTER (
            WHERE fs.sale_date > c.calculation_date - INTERVAL '14 days'
              AND fs.sale_date <= c.calculation_date
        ), 0)::INTEGER AS qty_sold_14d,
        COALESCE(SUM(fs.quantity_sold) FILTER (
            WHERE fs.sale_date > c.calculation_date - INTERVAL '30 days'
              AND fs.sale_date <= c.calculation_date
        ), 0)::INTEGER AS qty_sold_30d
    FROM calculation c
    JOIN dim_date dd
        ON c.calculation_date = dd.full_date
    CROSS JOIN dim_branch db
    CROSS JOIN dim_product dp
    LEFT JOIN fact_sales fs
        ON fs.branch_key = db.branch_key
       AND fs.product_key = dp.product_key
       AND fs.sale_date > c.calculation_date - INTERVAL '30 days'
       AND fs.sale_date <= c.calculation_date
    WHERE c.calculation_date IS NOT NULL
      AND dp.is_active = TRUE
    GROUP BY
        c.calculation_date,
        dd.date_key,
        db.branch_key,
        dp.product_key
)
INSERT INTO product_sales_velocity (
    calculation_date,
    date_key,
    branch_key,
    product_key,
    qty_sold_7d,
    qty_sold_14d,
    qty_sold_30d,
    avg_daily_demand_7d,
    avg_daily_demand_14d,
    avg_daily_demand_30d
)
SELECT
    calculation_date,
    date_key,
    branch_key,
    product_key,
    qty_sold_7d,
    qty_sold_14d,
    qty_sold_30d,
    ROUND(qty_sold_7d / 7.0, 2) AS avg_daily_demand_7d,
    ROUND(qty_sold_14d / 14.0, 2) AS avg_daily_demand_14d,
    ROUND(qty_sold_30d / 30.0, 2) AS avg_daily_demand_30d
FROM sales_velocity
ON CONFLICT (calculation_date, branch_key, product_key)
DO UPDATE SET
    date_key = EXCLUDED.date_key,
    qty_sold_7d = EXCLUDED.qty_sold_7d,
    qty_sold_14d = EXCLUDED.qty_sold_14d,
    qty_sold_30d = EXCLUDED.qty_sold_30d,
    avg_daily_demand_7d = EXCLUDED.avg_daily_demand_7d,
    avg_daily_demand_14d = EXCLUDED.avg_daily_demand_14d,
    avg_daily_demand_30d = EXCLUDED.avg_daily_demand_30d;

COMMIT;

/*
Quick check:

SELECT
    psv.calculation_date,
    db.branch_id,
    dp.product_id,
    psv.qty_sold_7d,
    psv.qty_sold_14d,
    psv.qty_sold_30d,
    psv.avg_daily_demand_7d,
    psv.avg_daily_demand_14d,
    psv.avg_daily_demand_30d
FROM product_sales_velocity psv
JOIN dim_branch db
    ON psv.branch_key = db.branch_key
JOIN dim_product dp
    ON psv.product_key = dp.product_key
WHERE psv.calculation_date = (
    SELECT MAX(calculation_date)
    FROM product_sales_velocity
)
ORDER BY
    psv.avg_daily_demand_14d DESC,
    db.branch_id,
    dp.product_id
LIMIT 20;
*/
