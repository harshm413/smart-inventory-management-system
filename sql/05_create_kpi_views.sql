/*
Inventory Reorder System
05_create_kpi_views.sql

KPI views summarize inventory, reorder, stockout, overstock, supplier,
and branch health for reports or dashboards.
*/

DROP VIEW IF EXISTS vw_reorder_by_supplier;
DROP VIEW IF EXISTS vw_reorder_priority_by_category;
DROP VIEW IF EXISTS vw_reorder_kpis;
DROP VIEW IF EXISTS vw_inventory_kpis;
DROP VIEW IF EXISTS vw_branch_kpis;
DROP VIEW IF EXISTS vw_supplier_kpis;
DROP VIEW IF EXISTS vw_overstock_risk_kpis;
DROP VIEW IF EXISTS vw_stockout_risk_kpis;
DROP VIEW IF EXISTS vw_reorder_summary;
DROP VIEW IF EXISTS vw_inventory_summary;
DROP VIEW IF EXISTS vw_stockout_risk_by_category;
DROP VIEW IF EXISTS vw_latest_reorder_recommendations;
DROP VIEW IF EXISTS vw_fast_moving_products;
DROP VIEW IF EXISTS vw_latest_inventory_snapshot;

CREATE OR REPLACE VIEW vw_latest_inventory_snapshot AS
SELECT
    ids.inventory_date,
    db.branch_id,
    db.branch_name,
    db.city,
    dp.product_id,
    dp.product_name,
    dp.category,
    dp.brand,
    ids.current_stock,
    ids.reserved_stock,
    ids.available_stock,
    ids.inventory_value
FROM inventory_daily_snapshot ids
JOIN dim_branch db
    ON ids.branch_key = db.branch_key
JOIN dim_product dp
    ON ids.product_key = dp.product_key
WHERE ids.inventory_date = (
    SELECT MAX(inventory_date)
    FROM inventory_daily_snapshot
);

CREATE OR REPLACE VIEW vw_latest_reorder_recommendations AS
SELECT
    rr.recommendation_date,
    db.branch_id,
    db.branch_name,
    db.city,
    dp.product_id,
    dp.product_name,
    dp.category,
    dp.unit_cost,
    ds.supplier_id,
    ds.supplier_name,
    rr.current_stock,
    rr.reserved_stock,
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
    rr.recommended_order_qty * dp.unit_cost AS estimated_reorder_cost,
    rr.priority_level
FROM reorder_recommendations rr
JOIN dim_branch db
    ON rr.branch_key = db.branch_key
JOIN dim_product dp
    ON rr.product_key = dp.product_key
JOIN dim_supplier ds
    ON rr.supplier_key = ds.supplier_key
WHERE rr.recommendation_date = (
    SELECT MAX(recommendation_date)
    FROM reorder_recommendations
);

CREATE OR REPLACE VIEW vw_fast_moving_products AS
SELECT
    psv.calculation_date,
    db.branch_id,
    db.branch_name,
    dp.product_id,
    dp.product_name,
    dp.category,
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
ORDER BY psv.avg_daily_demand_14d DESC;

/*
1. Inventory Summary

Answers:
    How much stock and stock value does the shop currently hold?
*/
CREATE OR REPLACE VIEW vw_inventory_summary AS
SELECT
    inventory_date,
    COUNT(DISTINCT product_id) AS total_products,
    COALESCE(SUM(inventory_value), 0) AS total_stock_value,
    COALESCE(SUM(available_stock), 0) AS total_available_stock,
    COALESCE(SUM(reserved_stock), 0) AS total_reserved_stock
FROM vw_latest_inventory_snapshot
GROUP BY inventory_date;

/*
2. Reorder Summary

Answers:
    How many products need reorder and how much will the recommended order cost?
*/
CREATE OR REPLACE VIEW vw_reorder_summary AS
SELECT
    recommendation_date,
    COUNT(*) FILTER (WHERE reorder_needed) AS products_needing_reorder,
    COUNT(*) FILTER (
        WHERE reorder_needed
          AND priority_level = 'High'
    ) AS high_priority_reorder_count,
    COUNT(*) FILTER (
        WHERE reorder_needed
          AND priority_level = 'Medium'
    ) AS medium_priority_reorder_count,
    COALESCE(SUM(estimated_reorder_cost) FILTER (WHERE reorder_needed), 0) AS estimated_reorder_cost
FROM vw_latest_reorder_recommendations
GROUP BY recommendation_date;

/*
3. Stockout Risk

Answers:
    Which products are likely to run out soon?
*/
CREATE OR REPLACE VIEW vw_stockout_risk_kpis AS
WITH latest_velocity AS (
    SELECT MAX(calculation_date) AS calculation_date
    FROM product_sales_velocity
),
stockout_base AS (
    SELECT
        rr.recommendation_date,
        rr.branch_id,
        rr.product_id,
        rr.available_stock,
        rr.lead_time_days,
        rr.stock_coverage_days,
        rr.reorder_needed,
        psv.avg_daily_demand_7d,
        psv.avg_daily_demand_30d
    FROM vw_latest_reorder_recommendations rr
    JOIN dim_branch db
        ON rr.branch_id = db.branch_id
    JOIN dim_product dp
        ON rr.product_id = dp.product_id
    CROSS JOIN latest_velocity lv
    JOIN product_sales_velocity psv
        ON db.branch_key = psv.branch_key
       AND dp.product_key = psv.product_key
       AND psv.calculation_date = lv.calculation_date
)
SELECT
    recommendation_date,
    COUNT(*) FILTER (
        WHERE available_stock <= avg_daily_demand_7d * lead_time_days
    ) AS products_at_high_stockout_risk,
    COUNT(*) FILTER (
        WHERE stock_coverage_days < 3
    ) AS products_with_less_than_3_days_coverage,
    COUNT(*) FILTER (
        WHERE avg_daily_demand_7d > avg_daily_demand_30d
          AND reorder_needed
    ) AS fast_moving_low_stock_products
FROM stockout_base
GROUP BY recommendation_date;

/*
4. Overstock Risk

Answers:
    Where is too much cash tied up in excess or slow inventory?
*/
CREATE OR REPLACE VIEW vw_overstock_risk_kpis AS
WITH latest_velocity AS (
    SELECT MAX(calculation_date) AS calculation_date
    FROM product_sales_velocity
),
overstock_base AS (
    SELECT
        rr.recommendation_date,
        rr.available_stock,
        rr.unit_cost,
        rr.stock_coverage_days,
        psv.avg_daily_demand_30d
    FROM vw_latest_reorder_recommendations rr
    JOIN dim_branch db
        ON rr.branch_id = db.branch_id
    JOIN dim_product dp
        ON rr.product_id = dp.product_id
    CROSS JOIN latest_velocity lv
    JOIN product_sales_velocity psv
        ON db.branch_key = psv.branch_key
       AND dp.product_key = psv.product_key
       AND psv.calculation_date = lv.calculation_date
)
SELECT
    recommendation_date,
    COUNT(*) FILTER (
        WHERE stock_coverage_days > 60
    ) AS overstocked_products,
    COUNT(*) FILTER (
        WHERE avg_daily_demand_30d > 0
          AND stock_coverage_days > 45
    ) AS slow_moving_products,
    COUNT(*) FILTER (
        WHERE avg_daily_demand_30d = 0
          AND available_stock > 0
    ) AS dead_stock_products,
    COALESCE(SUM(available_stock * unit_cost) FILTER (
        WHERE stock_coverage_days > 60
    ), 0) AS estimated_money_stuck_in_overstock
FROM overstock_base
GROUP BY recommendation_date;

/*
5. Supplier View

Answers:
    Which suppliers need orders, how much will those orders cost, and how much
    does supplier lead time affect risk?
*/
CREATE OR REPLACE VIEW vw_supplier_kpis AS
SELECT
    recommendation_date,
    supplier_id,
    supplier_name,
    COALESCE(SUM(recommended_order_qty) FILTER (WHERE reorder_needed), 0) AS reorder_quantity_by_supplier,
    COALESCE(SUM(estimated_reorder_cost) FILTER (WHERE reorder_needed), 0) AS estimated_purchase_cost_by_supplier,
    AVG(lead_time_days) AS avg_lead_time_days,
    MAX(lead_time_days) AS max_lead_time_days,
    COUNT(*) FILTER (
        WHERE reorder_needed
          AND priority_level = 'High'
    ) AS high_priority_products,
    CASE
        WHEN AVG(lead_time_days) >= 10 THEN 'High Lead Time Impact'
        WHEN AVG(lead_time_days) >= 5 THEN 'Medium Lead Time Impact'
        ELSE 'Low Lead Time Impact'
    END AS supplier_lead_time_impact
FROM vw_latest_reorder_recommendations
GROUP BY
    recommendation_date,
    supplier_id,
    supplier_name;

/*
6. Branch View

Answers:
    Which branches have the highest stockout risk, inventory value, and reorder cost?
*/
CREATE OR REPLACE VIEW vw_branch_kpis AS
WITH branch_inventory AS (
    SELECT
        inventory_date,
        branch_id,
        branch_name,
        city,
        SUM(inventory_value) AS inventory_value_by_branch
    FROM vw_latest_inventory_snapshot
    GROUP BY
        inventory_date,
        branch_id,
        branch_name,
        city
),
latest_velocity AS (
    SELECT MAX(calculation_date) AS calculation_date
    FROM product_sales_velocity
),
branch_reorder AS (
    SELECT
        recommendation_date,
        rr.branch_id,
        rr.branch_name,
        rr.city,
        COUNT(*) FILTER (
            WHERE rr.available_stock <= psv.avg_daily_demand_7d * rr.lead_time_days
        ) AS stockout_risk_by_branch,
        COALESCE(SUM(rr.estimated_reorder_cost) FILTER (WHERE rr.reorder_needed), 0) AS reorder_cost_by_branch,
        COUNT(*) FILTER (WHERE rr.reorder_needed) AS products_needing_reorder
    FROM vw_latest_reorder_recommendations rr
    JOIN dim_branch db
        ON rr.branch_id = db.branch_id
    JOIN dim_product dp
        ON rr.product_id = dp.product_id
    CROSS JOIN latest_velocity lv
    JOIN product_sales_velocity psv
        ON db.branch_key = psv.branch_key
       AND dp.product_key = psv.product_key
       AND psv.calculation_date = lv.calculation_date
    GROUP BY
        rr.recommendation_date,
        rr.branch_id,
        rr.branch_name,
        rr.city
)
SELECT
    br.recommendation_date,
    br.branch_id,
    br.branch_name,
    br.city,
    br.stockout_risk_by_branch,
    COALESCE(bi.inventory_value_by_branch, 0) AS inventory_value_by_branch,
    br.reorder_cost_by_branch,
    br.products_needing_reorder
FROM branch_reorder br
LEFT JOIN branch_inventory bi
    ON br.branch_id = bi.branch_id;

/*
Backward-compatible KPI view names used by earlier project steps.
*/
CREATE OR REPLACE VIEW vw_inventory_kpis AS
SELECT
    inventory_date,
    total_products,
    total_stock_value AS total_inventory_value,
    total_available_stock,
    total_reserved_stock
FROM vw_inventory_summary;

CREATE OR REPLACE VIEW vw_reorder_kpis AS
SELECT
    recommendation_date,
    products_needing_reorder,
    high_priority_reorder_count AS high_priority_products,
    medium_priority_reorder_count AS medium_priority_products,
    estimated_reorder_cost
FROM vw_reorder_summary;

CREATE OR REPLACE VIEW vw_reorder_by_supplier AS
SELECT
    recommendation_date,
    supplier_id,
    supplier_name,
    reorder_quantity_by_supplier AS total_order_qty,
    estimated_purchase_cost_by_supplier
FROM vw_supplier_kpis
WHERE reorder_quantity_by_supplier > 0;

CREATE OR REPLACE VIEW vw_reorder_priority_by_category AS
SELECT
    recommendation_date,
    category,
    priority_level,
    COUNT(*) AS product_count,
    SUM(recommended_order_qty) AS total_order_qty
FROM vw_latest_reorder_recommendations
GROUP BY
    recommendation_date,
    category,
    priority_level;
