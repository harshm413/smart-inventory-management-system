/*
Inventory Reorder System
10_stockout_overstock_detection.sql

Create stockout, overstock, dead stock, and slow-moving product views.

Run after:
    07_calculate_sales_velocity.sql
    09_calculate_reorder_points.sql

These views use:
    - latest reorder_recommendations for stock, lead time, and coverage
    - latest product_sales_velocity for 7-day and 30-day demand
*/

DROP VIEW IF EXISTS vw_high_stockout_risk_products;
DROP VIEW IF EXISTS vw_overstock_products;
DROP VIEW IF EXISTS vw_dead_stock_products;
DROP VIEW IF EXISTS vw_slow_moving_products;

/*
Products with stockout risk.

The view name highlights high risk, but the risk_level column also keeps
Medium Risk and Low Risk rows so the owner can prioritize the full watchlist.
*/
CREATE OR REPLACE VIEW vw_high_stockout_risk_products AS
WITH latest_recommendation AS (
    SELECT MAX(recommendation_date) AS recommendation_date
    FROM reorder_recommendations
),
latest_velocity AS (
    SELECT MAX(calculation_date) AS calculation_date
    FROM product_sales_velocity
),
stock_risk AS (
    SELECT
        rr.recommendation_date,
        db.branch_id,
        db.branch_name,
        dp.product_id,
        dp.product_name,
        dp.category,
        ds.supplier_id,
        ds.supplier_name,
        rr.available_stock,
        psv.avg_daily_demand_7d,
        rr.avg_daily_demand AS avg_daily_demand_14d,
        psv.avg_daily_demand_30d,
        rr.lead_time_days,
        rr.stock_coverage_days,
        rr.reorder_point,
        rr.reorder_needed,
        rr.recommended_order_qty,
        CASE
            WHEN rr.available_stock <= psv.avg_daily_demand_7d * rr.lead_time_days THEN 'High Risk'
            WHEN rr.stock_coverage_days <= rr.lead_time_days + 3 THEN 'Medium Risk'
            WHEN rr.stock_coverage_days <= rr.lead_time_days + 7 THEN 'Low Risk'
            ELSE 'No Risk'
        END AS stockout_risk_level
    FROM latest_recommendation lr
    JOIN reorder_recommendations rr
        ON lr.recommendation_date = rr.recommendation_date
    JOIN dim_branch db
        ON rr.branch_key = db.branch_key
    JOIN dim_product dp
        ON rr.product_key = dp.product_key
    JOIN dim_supplier ds
        ON rr.supplier_key = ds.supplier_key
    CROSS JOIN latest_velocity lv
    JOIN product_sales_velocity psv
        ON rr.branch_key = psv.branch_key
       AND rr.product_key = psv.product_key
       AND psv.calculation_date = lv.calculation_date
)
SELECT
    recommendation_date,
    branch_id,
    branch_name,
    product_id,
    product_name,
    category,
    supplier_id,
    supplier_name,
    available_stock,
    avg_daily_demand_7d,
    avg_daily_demand_14d,
    avg_daily_demand_30d,
    lead_time_days,
    stock_coverage_days,
    reorder_point,
    reorder_needed,
    recommended_order_qty,
    stockout_risk_level
FROM stock_risk
WHERE stockout_risk_level <> 'No Risk'
ORDER BY
    CASE stockout_risk_level
        WHEN 'High Risk' THEN 1
        WHEN 'Medium Risk' THEN 2
        WHEN 'Low Risk' THEN 3
        ELSE 4
    END,
    stock_coverage_days NULLS LAST,
    branch_id,
    product_id;

/*
Products with more than 60 days of stock coverage.
*/
CREATE OR REPLACE VIEW vw_overstock_products AS
WITH latest_recommendation AS (
    SELECT MAX(recommendation_date) AS recommendation_date
    FROM reorder_recommendations
),
latest_velocity AS (
    SELECT MAX(calculation_date) AS calculation_date
    FROM product_sales_velocity
)
SELECT
    rr.recommendation_date,
    db.branch_id,
    db.branch_name,
    dp.product_id,
    dp.product_name,
    dp.category,
    ds.supplier_id,
    ds.supplier_name,
    rr.available_stock,
    rr.avg_daily_demand AS avg_daily_demand_14d,
    psv.avg_daily_demand_30d,
    rr.stock_coverage_days,
    'Overstock' AS overstock_status
FROM latest_recommendation lr
JOIN reorder_recommendations rr
    ON lr.recommendation_date = rr.recommendation_date
JOIN dim_branch db
    ON rr.branch_key = db.branch_key
JOIN dim_product dp
    ON rr.product_key = dp.product_key
JOIN dim_supplier ds
    ON rr.supplier_key = ds.supplier_key
CROSS JOIN latest_velocity lv
JOIN product_sales_velocity psv
    ON rr.branch_key = psv.branch_key
   AND rr.product_key = psv.product_key
   AND psv.calculation_date = lv.calculation_date
WHERE rr.stock_coverage_days > 60
ORDER BY
    rr.stock_coverage_days DESC,
    rr.available_stock DESC,
    branch_id,
    product_id;

/*
Products with stock on hand but no sales demand in the last 30 days.
*/
CREATE OR REPLACE VIEW vw_dead_stock_products AS
WITH latest_recommendation AS (
    SELECT MAX(recommendation_date) AS recommendation_date
    FROM reorder_recommendations
),
latest_velocity AS (
    SELECT MAX(calculation_date) AS calculation_date
    FROM product_sales_velocity
)
SELECT
    rr.recommendation_date,
    db.branch_id,
    db.branch_name,
    dp.product_id,
    dp.product_name,
    dp.category,
    ds.supplier_id,
    ds.supplier_name,
    rr.available_stock,
    psv.avg_daily_demand_30d,
    rr.stock_coverage_days,
    'Dead Stock Risk' AS dead_stock_status
FROM latest_recommendation lr
JOIN reorder_recommendations rr
    ON lr.recommendation_date = rr.recommendation_date
JOIN dim_branch db
    ON rr.branch_key = db.branch_key
JOIN dim_product dp
    ON rr.product_key = dp.product_key
JOIN dim_supplier ds
    ON rr.supplier_key = ds.supplier_key
CROSS JOIN latest_velocity lv
JOIN product_sales_velocity psv
    ON rr.branch_key = psv.branch_key
   AND rr.product_key = psv.product_key
   AND psv.calculation_date = lv.calculation_date
WHERE psv.avg_daily_demand_30d = 0
  AND rr.available_stock > 0
ORDER BY
    rr.available_stock DESC,
    branch_id,
    product_id;

/*
Products still selling, but slowly compared with current stock.
*/
CREATE OR REPLACE VIEW vw_slow_moving_products AS
WITH latest_recommendation AS (
    SELECT MAX(recommendation_date) AS recommendation_date
    FROM reorder_recommendations
),
latest_velocity AS (
    SELECT MAX(calculation_date) AS calculation_date
    FROM product_sales_velocity
)
SELECT
    rr.recommendation_date,
    db.branch_id,
    db.branch_name,
    dp.product_id,
    dp.product_name,
    dp.category,
    ds.supplier_id,
    ds.supplier_name,
    rr.available_stock,
    rr.avg_daily_demand AS avg_daily_demand_14d,
    psv.avg_daily_demand_30d,
    rr.stock_coverage_days,
    'Slow-Moving' AS slow_moving_status
FROM latest_recommendation lr
JOIN reorder_recommendations rr
    ON lr.recommendation_date = rr.recommendation_date
JOIN dim_branch db
    ON rr.branch_key = db.branch_key
JOIN dim_product dp
    ON rr.product_key = dp.product_key
JOIN dim_supplier ds
    ON rr.supplier_key = ds.supplier_key
CROSS JOIN latest_velocity lv
JOIN product_sales_velocity psv
    ON rr.branch_key = psv.branch_key
   AND rr.product_key = psv.product_key
   AND psv.calculation_date = lv.calculation_date
WHERE psv.avg_daily_demand_30d > 0
  AND rr.stock_coverage_days > 45
ORDER BY
    rr.stock_coverage_days DESC,
    rr.available_stock DESC,
    branch_id,
    product_id;

/*
Quick checks:

SELECT COUNT(*) FROM vw_high_stockout_risk_products;
SELECT COUNT(*) FROM vw_overstock_products;
SELECT COUNT(*) FROM vw_dead_stock_products;
SELECT COUNT(*) FROM vw_slow_moving_products;
*/
