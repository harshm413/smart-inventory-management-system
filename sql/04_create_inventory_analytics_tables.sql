/*
Inventory Reorder System
04_create_inventory_analytics_tables.sql

Analytics tables store inventory metrics used for stockout detection and
reorder recommendations.
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
DROP VIEW IF EXISTS vw_high_stockout_risk_products;
DROP VIEW IF EXISTS vw_overstock_products;
DROP VIEW IF EXISTS vw_dead_stock_products;
DROP VIEW IF EXISTS vw_slow_moving_products;
DROP VIEW IF EXISTS vw_latest_reorder_recommendations;
DROP VIEW IF EXISTS vw_fast_moving_products;
DROP VIEW IF EXISTS vw_latest_inventory_snapshot;

CREATE TABLE IF NOT EXISTS inventory_daily_snapshot (
    snapshot_key BIGSERIAL PRIMARY KEY,
    inventory_date DATE NOT NULL,
    date_key INTEGER NOT NULL REFERENCES dim_date(date_key),
    branch_key BIGINT NOT NULL REFERENCES dim_branch(branch_key),
    product_key BIGINT NOT NULL REFERENCES dim_product(product_key),
    current_stock INTEGER NOT NULL CHECK (current_stock >= 0),
    reserved_stock INTEGER NOT NULL CHECK (reserved_stock >= 0),
    available_stock INTEGER GENERATED ALWAYS AS (current_stock - reserved_stock) STORED,
    inventory_value NUMERIC(14, 2) NOT NULL CHECK (inventory_value >= 0),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_inventory_daily_snapshot UNIQUE (inventory_date, branch_key, product_key),
    CONSTRAINT chk_reserved_not_greater_than_current CHECK (reserved_stock <= current_stock)
);

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
Compatibility for existing databases that still have the older reorder
recommendation columns.
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
          AND column_name = 'safety_stock'
          AND data_type <> 'numeric'
    ) THEN
        ALTER TABLE reorder_recommendations
        ALTER COLUMN safety_stock TYPE NUMERIC(12, 2)
        USING safety_stock::NUMERIC(12, 2);
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

CREATE INDEX IF NOT EXISTS idx_inventory_daily_snapshot_date
ON inventory_daily_snapshot (inventory_date);

CREATE INDEX IF NOT EXISTS idx_product_sales_velocity_date
ON product_sales_velocity (calculation_date);

CREATE INDEX IF NOT EXISTS idx_reorder_recommendations_date_priority
ON reorder_recommendations (recommendation_date, priority_level);
