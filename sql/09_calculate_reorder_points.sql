/*
Inventory Reorder System
09_calculate_reorder_points.sql

Calculate reorder points and recommended order quantities by branch and product.

Run after:
    04_create_inventory_analytics_tables.sql
    06_transform_to_warehouse.sql
    07_calculate_sales_velocity.sql
    08_refresh_inventory_snapshot.sql

This script is rerunnable:
    - it uses avg_daily_demand_14d from product_sales_velocity
    - it upserts one recommendation row per date, branch, and product
*/

BEGIN;

CREATE TABLE IF NOT EXISTS reorder_recommendations (
    recommendation_key BIGSERIAL PRIMARY KEY,
    recommendation_date DATE NOT NULL,
    date_key INTEGER NOT NULL REFERENCES dim_date(date_key),
    branch_key BIGINT NOT NULL REFERENCES dim_branch(branch_key),
    product_key BIGINT NOT NULL REFERENCES dim_product(product_key),
    supplier_key BIGINT NOT NULL REFERENCES dim_supplier(supplier_key),
    current_stock INTEGER NOT NULL CHECK (current_stock >= 0),
    reserved_stock INTEGER NOT NULL CHECK (reserved_stock >= 0),
    available_stock INTEGER NOT NULL CHECK (available_stock >= 0),
    avg_daily_demand NUMERIC(12, 2) NOT NULL DEFAULT 0 CHECK (avg_daily_demand >= 0),
    lead_time_days INTEGER NOT NULL CHECK (lead_time_days > 0),
    safety_stock NUMERIC(12, 2) NOT NULL CHECK (safety_stock >= 0),
    reorder_point INTEGER NOT NULL CHECK (reorder_point >= 0),
    stock_coverage_days NUMERIC(12, 2),
    reorder_needed BOOLEAN NOT NULL DEFAULT FALSE,
    recommended_order_qty INTEGER NOT NULL CHECK (recommended_order_qty >= 0),
    forecast_daily_demand NUMERIC(12, 2) NOT NULL DEFAULT 0 CHECK (forecast_daily_demand >= 0),
    forecast_7_day_demand NUMERIC(12, 2) NOT NULL DEFAULT 0 CHECK (forecast_7_day_demand >= 0),
    projected_stock_after_7_days NUMERIC(12, 2) NOT NULL DEFAULT 0,
    projected_stockout_flag BOOLEAN NOT NULL DEFAULT FALSE,
    priority_level VARCHAR(30) NOT NULL CHECK (
        priority_level IN ('High', 'Medium', 'Low', 'No Action')
    ),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_reorder_recommendations UNIQUE (recommendation_date, branch_key, product_key)
);

/*
Compatibility for databases created before this simplified reorder schema.
Old columns are left in place if they exist, but they are made nullable so
the new insert can focus on the requested reorder point fields.
*/
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'reorder_recommendations'
          AND column_name = 'avg_daily_demand'
    ) THEN
        ALTER TABLE reorder_recommendations
        ADD COLUMN avg_daily_demand NUMERIC(12, 2) NOT NULL DEFAULT 0 CHECK (avg_daily_demand >= 0);
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'reorder_recommendations'
          AND column_name = 'reorder_needed'
    ) THEN
        ALTER TABLE reorder_recommendations
        ADD COLUMN reorder_needed BOOLEAN NOT NULL DEFAULT FALSE;
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'reorder_recommendations'
          AND column_name = 'recommended_order_qty'
    ) THEN
        ALTER TABLE reorder_recommendations
        ADD COLUMN recommended_order_qty INTEGER NOT NULL DEFAULT 0 CHECK (recommended_order_qty >= 0);
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'reorder_recommendations'
          AND column_name = 'forecast_daily_demand'
    ) THEN
        ALTER TABLE reorder_recommendations
        ADD COLUMN forecast_daily_demand NUMERIC(12, 2) NOT NULL DEFAULT 0 CHECK (forecast_daily_demand >= 0);
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'reorder_recommendations'
          AND column_name = 'forecast_7_day_demand'
    ) THEN
        ALTER TABLE reorder_recommendations
        ADD COLUMN forecast_7_day_demand NUMERIC(12, 2) NOT NULL DEFAULT 0 CHECK (forecast_7_day_demand >= 0);
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'reorder_recommendations'
          AND column_name = 'projected_stock_after_7_days'
    ) THEN
        ALTER TABLE reorder_recommendations
        ADD COLUMN projected_stock_after_7_days NUMERIC(12, 2) NOT NULL DEFAULT 0;
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'reorder_recommendations'
          AND column_name = 'projected_stockout_flag'
    ) THEN
        ALTER TABLE reorder_recommendations
        ADD COLUMN projected_stockout_flag BOOLEAN NOT NULL DEFAULT FALSE;
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'reorder_recommendations'
          AND column_name = 'priority_level'
    ) THEN
        ALTER TABLE reorder_recommendations
        ADD COLUMN priority_level VARCHAR(30) NOT NULL DEFAULT 'No Action'
            CHECK (priority_level IN ('High', 'Medium', 'Low', 'No Action'));
    END IF;

    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'reorder_recommendations'
          AND column_name = 'recommended_reorder_qty'
    ) THEN
        ALTER TABLE reorder_recommendations
        ALTER COLUMN recommended_reorder_qty DROP NOT NULL;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'reorder_recommendations'
          AND column_name = 'estimated_reorder_cost'
    ) THEN
        ALTER TABLE reorder_recommendations
        ALTER COLUMN estimated_reorder_cost DROP NOT NULL;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'reorder_recommendations'
          AND column_name = 'stockout_risk_level'
    ) THEN
        ALTER TABLE reorder_recommendations
        ALTER COLUMN stockout_risk_level DROP NOT NULL;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'reorder_recommendations'
          AND column_name = 'recommendation_status'
    ) THEN
        ALTER TABLE reorder_recommendations
        ALTER COLUMN recommendation_status DROP NOT NULL;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_reorder_recommendations_date_priority
ON reorder_recommendations (recommendation_date, priority_level);

WITH latest_inventory AS (
    SELECT MAX(inventory_date) AS recommendation_date
    FROM inventory_daily_snapshot
),
latest_velocity AS (
    SELECT MAX(calculation_date) AS calculation_date
    FROM product_sales_velocity
),
reorder_inputs AS (
    SELECT
        ids.inventory_date AS recommendation_date,
        ids.date_key,
        ids.branch_key,
        ids.product_key,
        dp.supplier_key,
        ids.current_stock,
        ids.reserved_stock,
        ids.available_stock,
        COALESCE(psv.avg_daily_demand_7d, 0) AS avg_daily_demand_7d,
        COALESCE(psv.avg_daily_demand_14d, 0) AS avg_daily_demand,
        COALESCE(psv.avg_daily_demand_30d, 0) AS avg_daily_demand_30d,
        ds.lead_time_days,
        dp.min_order_quantity
    FROM latest_inventory li
    JOIN inventory_daily_snapshot ids
        ON li.recommendation_date = ids.inventory_date
    JOIN dim_product dp
        ON ids.product_key = dp.product_key
    JOIN dim_supplier ds
        ON dp.supplier_key = ds.supplier_key
    CROSS JOIN latest_velocity lv
    LEFT JOIN product_sales_velocity psv
        ON ids.branch_key = psv.branch_key
       AND ids.product_key = psv.product_key
       AND psv.calculation_date = lv.calculation_date
    WHERE dp.is_active = TRUE
),
reorder_calculations AS (
    SELECT
        recommendation_date,
        date_key,
        branch_key,
        product_key,
        supplier_key,
        current_stock,
        reserved_stock,
        available_stock,
        avg_daily_demand_7d,
        avg_daily_demand,
        avg_daily_demand_30d,
        lead_time_days,
        ROUND(avg_daily_demand * 3, 2) AS safety_stock,
        CEIL((avg_daily_demand * lead_time_days) + (avg_daily_demand * 3))::INTEGER AS reorder_point,
        CASE
            WHEN avg_daily_demand > 0
                THEN ROUND(available_stock / avg_daily_demand, 2)
            ELSE NULL
        END AS stock_coverage_days,
        /*
        Simple forecast, not machine learning:
        recent 7-day demand gets the highest weight, then 14-day and 30-day demand.
        */
        ROUND(
            (0.5 * avg_daily_demand_7d)
            + (0.3 * avg_daily_demand)
            + (0.2 * avg_daily_demand_30d),
            2
        ) AS forecast_daily_demand,
        min_order_quantity
    FROM reorder_inputs
),
final_recommendations AS (
    SELECT
        recommendation_date,
        date_key,
        branch_key,
        product_key,
        supplier_key,
        current_stock,
        reserved_stock,
        available_stock,
        avg_daily_demand,
        lead_time_days,
        safety_stock,
        reorder_point,
        stock_coverage_days,
        available_stock <= reorder_point AS reorder_needed,
        forecast_daily_demand,
        ROUND(forecast_daily_demand * 7, 2) AS forecast_7_day_demand,
        ROUND(available_stock - (forecast_daily_demand * 7), 2) AS projected_stock_after_7_days,
        forecast_daily_demand > 0
            AND available_stock - (forecast_daily_demand * 7) <= 0 AS projected_stockout_flag,
        CASE
            WHEN available_stock <= reorder_point THEN
                GREATEST(min_order_quantity, (reorder_point * 2) - available_stock)
            ELSE 0
        END::INTEGER AS recommended_order_qty,
        CASE
            WHEN stock_coverage_days IS NULL THEN 'No Action'
            WHEN stock_coverage_days <= lead_time_days THEN 'High'
            WHEN stock_coverage_days <= lead_time_days + 3 THEN 'Medium'
            WHEN stock_coverage_days <= lead_time_days + 7 THEN 'Low'
            ELSE 'No Action'
        END AS priority_level
    FROM reorder_calculations
)
INSERT INTO reorder_recommendations (
    recommendation_date,
    date_key,
    branch_key,
    product_key,
    supplier_key,
    current_stock,
    reserved_stock,
    available_stock,
    avg_daily_demand,
    lead_time_days,
    safety_stock,
    reorder_point,
    stock_coverage_days,
    reorder_needed,
    recommended_order_qty,
    forecast_daily_demand,
    forecast_7_day_demand,
    projected_stock_after_7_days,
    projected_stockout_flag,
    priority_level
)
SELECT
    recommendation_date,
    date_key,
    branch_key,
    product_key,
    supplier_key,
    current_stock,
    reserved_stock,
    available_stock,
    avg_daily_demand,
    lead_time_days,
    safety_stock,
    reorder_point,
    stock_coverage_days,
    reorder_needed,
    recommended_order_qty,
    forecast_daily_demand,
    forecast_7_day_demand,
    projected_stock_after_7_days,
    projected_stockout_flag,
    priority_level
FROM final_recommendations
ON CONFLICT (recommendation_date, branch_key, product_key)
DO UPDATE SET
    date_key = EXCLUDED.date_key,
    supplier_key = EXCLUDED.supplier_key,
    current_stock = EXCLUDED.current_stock,
    reserved_stock = EXCLUDED.reserved_stock,
    available_stock = EXCLUDED.available_stock,
    avg_daily_demand = EXCLUDED.avg_daily_demand,
    lead_time_days = EXCLUDED.lead_time_days,
    safety_stock = EXCLUDED.safety_stock,
    reorder_point = EXCLUDED.reorder_point,
    stock_coverage_days = EXCLUDED.stock_coverage_days,
    reorder_needed = EXCLUDED.reorder_needed,
    recommended_order_qty = EXCLUDED.recommended_order_qty,
    forecast_daily_demand = EXCLUDED.forecast_daily_demand,
    forecast_7_day_demand = EXCLUDED.forecast_7_day_demand,
    projected_stock_after_7_days = EXCLUDED.projected_stock_after_7_days,
    projected_stockout_flag = EXCLUDED.projected_stockout_flag,
    priority_level = EXCLUDED.priority_level;

COMMIT;

/*
Quick check:

SELECT
    rr.recommendation_date,
    db.branch_id,
    dp.product_id,
    rr.available_stock,
    rr.avg_daily_demand,
    rr.lead_time_days,
    rr.safety_stock,
    rr.reorder_point,
    rr.stock_coverage_days,
    rr.reorder_needed,
    rr.recommended_order_qty,
    rr.forecast_daily_demand,
    rr.forecast_7_day_demand,
    rr.projected_stock_after_7_days,
    rr.projected_stockout_flag,
    rr.priority_level
FROM reorder_recommendations rr
JOIN dim_branch db
    ON rr.branch_key = db.branch_key
JOIN dim_product dp
    ON rr.product_key = dp.product_key
WHERE rr.recommendation_date = (
    SELECT MAX(recommendation_date)
    FROM reorder_recommendations
)
ORDER BY
    rr.reorder_needed DESC,
    CASE rr.priority_level
        WHEN 'High' THEN 1
        WHEN 'Medium' THEN 2
        WHEN 'Low' THEN 3
        ELSE 4
    END,
    rr.stock_coverage_days NULLS LAST
LIMIT 20;
*/
