# SQL Learning Queries for the Inventory Reorder System

This guide helps you practice SQL using the Inventory Reorder System data.

The queries start from basic `SELECT` statements and slowly move toward joins, aggregations, business KPIs, CTEs, window functions, and query performance.

Before running these queries, make sure the pipeline has already loaded data into PostgreSQL:

```powershell
python src/run_pipeline.py
```

You can run the SQL queries in pgAdmin, DBeaver, or any PostgreSQL SQL editor.

## Database Tables Used

Main warehouse tables:

```text
dim_product
dim_branch
dim_supplier
dim_date
fact_sales
fact_stock_movement
```

Inventory analytics tables:

```text
inventory_daily_snapshot
product_sales_velocity
reorder_recommendations
```

Useful views:

```text
vw_latest_inventory_snapshot
vw_latest_reorder_recommendations
vw_high_stockout_risk_products
vw_overstock_products
vw_dead_stock_products
vw_slow_moving_products
vw_branch_kpis
vw_supplier_kpis
```

## Learning Path

Learn in this order:

1. Basic `SELECT`
2. Filtering with `WHERE`
3. Sorting with `ORDER BY`
4. Counting rows with `COUNT`
5. Aggregation with `SUM`, `AVG`, `MIN`, `MAX`
6. Grouping with `GROUP BY`
7. Joining tables with `JOIN`
8. Business logic with `CASE`
9. CTEs with `WITH`
10. Window functions like `RANK`
11. Performance checking with `EXPLAIN ANALYZE`

---

# 1. Beginner Queries

## 1.1 View All Products

Business question:

What products does the shop sell?

SQL concepts:

- `SELECT`
- choosing columns
- `ORDER BY`

```sql
SELECT
    product_id,
    product_name,
    category,
    brand,
    unit_cost,
    selling_price
FROM dim_product
ORDER BY product_id;
```

What to observe:

- Each product has a product ID, name, category, cost, and selling price.
- `unit_cost` is what the shop pays.
- `selling_price` is what the customer pays.

## 1.2 Count Rows in Main Tables

Business question:

Did data load into the important tables?

SQL concepts:

- `COUNT`
- `UNION ALL`
- table row checking

```sql
SELECT 'products' AS table_name, COUNT(*) AS row_count FROM dim_product
UNION ALL
SELECT 'branches', COUNT(*) FROM dim_branch
UNION ALL
SELECT 'suppliers', COUNT(*) FROM dim_supplier
UNION ALL
SELECT 'sales', COUNT(*) FROM fact_sales
UNION ALL
SELECT 'stock_movements', COUNT(*) FROM fact_stock_movement;
```

What to observe:

- If a row count is `0`, that table may not have loaded correctly.
- This is a simple data pipeline health check.

## 1.3 Find Products with Low Available Stock

Business question:

Which products may need attention because stock is low?

SQL concepts:

- `WHERE`
- filtering
- sorting low values first

```sql
SELECT
    branch_name,
    product_name,
    category,
    current_stock,
    reserved_stock,
    available_stock
FROM vw_latest_inventory_snapshot
WHERE available_stock < 20
ORDER BY available_stock ASC;
```

What to observe:

- `available_stock` is stock that can still be sold.
- Low stock does not always mean reorder is needed. You also need demand and supplier lead time.

## 1.4 Find Highest Inventory Value Products

Business question:

Where is most inventory money stored?

SQL concepts:

- `ORDER BY DESC`
- `LIMIT`

```sql
SELECT
    branch_name,
    product_name,
    category,
    available_stock,
    inventory_value
FROM vw_latest_inventory_snapshot
ORDER BY inventory_value DESC
LIMIT 20;
```

What to observe:

- High inventory value means more money is tied up in stock.
- These products should be watched carefully.

---

# 2. Intermediate Queries

## 2.1 Sales by Branch

Business question:

Which branch sells the most?

SQL concepts:

- `JOIN`
- `SUM`
- `GROUP BY`

```sql
SELECT
    db.branch_name,
    SUM(fs.quantity_sold) AS total_qty_sold,
    SUM(fs.total_sales_amount) AS total_sales_amount
FROM fact_sales fs
JOIN dim_branch db
    ON fs.branch_key = db.branch_key
GROUP BY db.branch_name
ORDER BY total_sales_amount DESC;
```

What to observe:

- This shows branch sales performance.
- A high-selling branch may need more frequent replenishment.

## 2.2 Sales by Category

Business question:

Which product categories generate the most sales?

SQL concepts:

- joining fact and dimension tables
- grouping by category

```sql
SELECT
    dp.category,
    SUM(fs.quantity_sold) AS total_qty_sold,
    SUM(fs.total_sales_amount) AS total_sales_amount
FROM fact_sales fs
JOIN dim_product dp
    ON fs.product_key = dp.product_key
GROUP BY dp.category
ORDER BY total_sales_amount DESC;
```

What to observe:

- Strong categories may need more stock planning.
- Weak categories may need promotion or smaller purchase quantities.

## 2.3 Daily Sales Trend

Business question:

How do sales change day by day?

SQL concepts:

- date grouping
- trend observation

```sql
SELECT
    sale_date,
    SUM(quantity_sold) AS total_qty_sold,
    SUM(total_sales_amount) AS total_sales_amount
FROM fact_sales
GROUP BY sale_date
ORDER BY sale_date;
```

What to observe:

- Some days may have higher sales than others.
- This can help with weekend or holiday planning.

## 2.4 Top Selling Products

Business question:

Which products are selling fastest?

SQL concepts:

- `JOIN`
- `GROUP BY`
- `LIMIT`

```sql
SELECT
    dp.product_id,
    dp.product_name,
    dp.category,
    SUM(fs.quantity_sold) AS total_qty_sold,
    SUM(fs.total_sales_amount) AS total_sales_amount
FROM fact_sales fs
JOIN dim_product dp
    ON fs.product_key = dp.product_key
GROUP BY
    dp.product_id,
    dp.product_name,
    dp.category
ORDER BY total_qty_sold DESC
LIMIT 20;
```

What to observe:

- These are important products for customer demand.
- Stockout on these products can hurt sales.

## 2.5 Profit Margin by Product

Business question:

Which products have better profit per unit?

SQL concepts:

- calculated columns
- `ROUND`

```sql
SELECT
    product_id,
    product_name,
    category,
    unit_cost,
    selling_price,
    selling_price - unit_cost AS profit_per_unit,
    ROUND(((selling_price - unit_cost) / selling_price) * 100, 2) AS margin_percent
FROM dim_product
ORDER BY margin_percent DESC;
```

What to observe:

- High-margin products are profitable.
- Low-margin products may still be important if they sell fast.

---

# 3. Inventory Analytics Queries

## 3.1 Observe Moving Average Demand

Business question:

How fast is each product selling recently?

SQL concepts:

- analytics table query
- comparing 7-day, 14-day, and 30-day demand

```sql
SELECT
    db.branch_name,
    dp.product_name,
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
ORDER BY psv.avg_daily_demand_14d DESC
LIMIT 30;
```

What to observe:

- `avg_daily_demand_7d` reacts quickly to recent sales.
- `avg_daily_demand_30d` is smoother.
- This helps compare short-term and longer-term demand.

## 3.2 Observe Reorder Point Logic

Business question:

Why does the system recommend reordering?

SQL concepts:

- business formula columns
- boolean flags
- priority levels

```sql
SELECT
    branch_name,
    product_name,
    available_stock,
    avg_daily_demand,
    lead_time_days,
    safety_stock,
    reorder_point,
    stock_coverage_days,
    reorder_needed,
    priority_level
FROM vw_latest_reorder_recommendations
ORDER BY
    reorder_needed DESC,
    stock_coverage_days ASC NULLS LAST;
```

What to observe:

- If `available_stock <= reorder_point`, `reorder_needed` becomes true.
- `stock_coverage_days` shows how many days stock may last.
- High priority means the product may run out before the supplier delivers.

## 3.3 Products Needing Reorder Today

Business question:

What should the shop buy now?

SQL concepts:

- `WHERE`
- `CASE` for custom sorting

```sql
SELECT
    branch_name,
    product_name,
    supplier_name,
    available_stock,
    reorder_point,
    recommended_order_qty,
    estimated_reorder_cost,
    priority_level
FROM vw_latest_reorder_recommendations
WHERE reorder_needed = TRUE
ORDER BY
    CASE priority_level
        WHEN 'High' THEN 1
        WHEN 'Medium' THEN 2
        WHEN 'Low' THEN 3
        ELSE 4
    END,
    estimated_reorder_cost DESC;
```

What to observe:

- Start with `High` priority products.
- Group by supplier later to prepare purchase orders.

## 3.4 High Stockout Risk Products

Business question:

Which products may run out soon?

SQL concepts:

- using a KPI view
- filtering by risk level

```sql
SELECT
    branch_name,
    product_name,
    supplier_name,
    available_stock,
    avg_daily_demand_7d,
    lead_time_days,
    stock_coverage_days,
    stockout_risk_level
FROM vw_high_stockout_risk_products
WHERE stockout_risk_level = 'High Risk'
ORDER BY stock_coverage_days ASC NULLS LAST;
```

What to observe:

- These products should be checked first.
- If coverage days are lower than lead time, reorder is urgent.

## 3.5 Overstock Products

Business question:

Which products have too much stock?

SQL concepts:

- using an overstock view
- sorting by coverage days

```sql
SELECT
    branch_name,
    product_name,
    category,
    available_stock,
    avg_daily_demand_30d,
    stock_coverage_days
FROM vw_overstock_products
ORDER BY stock_coverage_days DESC;
```

What to observe:

- High coverage days means stock may last too long.
- Avoid buying more until stock reduces.

## 3.6 Dead Stock Products

Business question:

Which products are not selling?

SQL concepts:

- using a dead stock view
- business risk detection

```sql
SELECT
    branch_name,
    product_name,
    category,
    available_stock,
    avg_daily_demand_30d,
    dead_stock_status
FROM vw_dead_stock_products
ORDER BY available_stock DESC;
```

What to observe:

- Dead stock has stock available but no recent sales.
- The owner may need discount, promotion, return to supplier, or stop buying.

---

# 4. Advanced Queries

## 4.1 Rank Top Products Inside Each Branch

Business question:

What are the top 5 products in each branch?

SQL concepts:

- CTE with `WITH`
- `RANK`
- window function
- `PARTITION BY`

```sql
WITH product_sales AS (
    SELECT
        db.branch_name,
        dp.product_name,
        SUM(fs.quantity_sold) AS total_qty_sold
    FROM fact_sales fs
    JOIN dim_branch db
        ON fs.branch_key = db.branch_key
    JOIN dim_product dp
        ON fs.product_key = dp.product_key
    GROUP BY
        db.branch_name,
        dp.product_name
),
ranked AS (
    SELECT
        *,
        RANK() OVER (
            PARTITION BY branch_name
            ORDER BY total_qty_sold DESC
        ) AS sales_rank
    FROM product_sales
)
SELECT *
FROM ranked
WHERE sales_rank <= 5
ORDER BY branch_name, sales_rank;
```

What to observe:

- `PARTITION BY branch_name` restarts the rank for each branch.
- This is useful when each branch has different demand.

## 4.2 Compare Short-Term Demand and Long-Term Demand

Business question:

Is product demand increasing or decreasing?

SQL concepts:

- `CASE`
- comparing calculated values
- demand trend classification

```sql
SELECT
    db.branch_name,
    dp.product_name,
    psv.avg_daily_demand_7d,
    psv.avg_daily_demand_30d,
    psv.avg_daily_demand_7d - psv.avg_daily_demand_30d AS demand_change,
    CASE
        WHEN psv.avg_daily_demand_7d > psv.avg_daily_demand_30d THEN 'Demand Increasing'
        WHEN psv.avg_daily_demand_7d < psv.avg_daily_demand_30d THEN 'Demand Decreasing'
        ELSE 'Stable'
    END AS demand_trend
FROM product_sales_velocity psv
JOIN dim_branch db
    ON psv.branch_key = db.branch_key
JOIN dim_product dp
    ON psv.product_key = dp.product_key
ORDER BY ABS(psv.avg_daily_demand_7d - psv.avg_daily_demand_30d) DESC;
```

What to observe:

- If 7-day demand is higher than 30-day demand, recent demand is increasing.
- If 7-day demand is lower, demand may be slowing down.

## 4.3 Supplier Purchase Plan

Business question:

How much should the shop order from each supplier?

SQL concepts:

- grouping by supplier
- supplier-level KPI

```sql
SELECT
    supplier_name,
    COUNT(*) AS products_to_order,
    SUM(recommended_order_qty) AS total_order_qty,
    SUM(estimated_reorder_cost) AS estimated_purchase_cost,
    AVG(lead_time_days) AS avg_lead_time_days
FROM vw_latest_reorder_recommendations
WHERE reorder_needed = TRUE
GROUP BY supplier_name
ORDER BY estimated_purchase_cost DESC;
```

What to observe:

- This is close to a real purchase order summary.
- Suppliers with higher lead time need earlier planning.

## 4.4 Running Daily Sales Total

Business question:

How much sales amount has accumulated over time?

SQL concepts:

- window aggregation
- running total

```sql
SELECT
    sale_date,
    SUM(total_sales_amount) AS daily_sales,
    SUM(SUM(total_sales_amount)) OVER (
        ORDER BY sale_date
    ) AS running_total_sales
FROM fact_sales
GROUP BY sale_date
ORDER BY sale_date;
```

What to observe:

- `daily_sales` shows one day.
- `running_total_sales` keeps adding each day.

## 4.5 Branch Health Summary

Business question:

Which branch needs the most attention?

SQL concepts:

- KPI view
- branch-level aggregation

```sql
SELECT
    branch_name,
    SUM(inventory_value_by_branch) AS inventory_value,
    SUM(stockout_risk_by_branch) AS stockout_risk_count,
    SUM(reorder_cost_by_branch) AS reorder_cost,
    SUM(products_needing_reorder) AS products_needing_reorder
FROM vw_branch_kpis
GROUP BY branch_name
ORDER BY stockout_risk_count DESC, reorder_cost DESC;
```

What to observe:

- A branch with many stockout risks needs urgent review.
- A branch with high inventory value may have too much money tied up in stock.

## 4.6 Check Query Performance

Business question:

How does PostgreSQL run this query?

SQL concepts:

- `EXPLAIN ANALYZE`
- query plan
- performance learning

```sql
EXPLAIN ANALYZE
SELECT
    dp.product_name,
    SUM(fs.quantity_sold) AS total_qty_sold
FROM fact_sales fs
JOIN dim_product dp
    ON fs.product_key = dp.product_key
GROUP BY dp.product_name
ORDER BY total_qty_sold DESC;
```

What to observe:

- PostgreSQL shows how it scans, joins, groups, and sorts the data.
- Use this later when learning indexes and performance tuning.

---

# 5. Practice Exercises

Try modifying the queries yourself.

## Exercise 1

Show only products in the `Food` category.

Hint:

```sql
WHERE category = 'Food'
```

## Exercise 2

Find the top 10 products by sales amount instead of quantity sold.

Hint:

```sql
ORDER BY total_sales_amount DESC
LIMIT 10
```

## Exercise 3

Find products where selling price is less than 20 percent above unit cost.

Hint:

```sql
WHERE selling_price < unit_cost * 1.2
```

## Exercise 4

Find products with stock coverage less than supplier lead time.

Hint:

```sql
WHERE stock_coverage_days <= lead_time_days
```

## Exercise 5

Create a supplier reorder list for only `High` priority products.

Hint:

```sql
WHERE reorder_needed = TRUE
  AND priority_level = 'High'
```

---

# 6. Important SQL Ideas from This Project

## Fact Tables

Fact tables store events.

Examples:

- `fact_sales`
- `fact_stock_movement`

They usually contain dates, product keys, branch keys, quantities, and amounts.

## Dimension Tables

Dimension tables describe business objects.

Examples:

- `dim_product`
- `dim_branch`
- `dim_supplier`
- `dim_date`

They make reports easier to read because they contain names, categories, and descriptions.

## Analytics Tables

Analytics tables store calculated results.

Examples:

- `product_sales_velocity`
- `reorder_recommendations`

These tables help the shop owner make decisions faster.

## Views

Views are saved SQL queries.

Examples:

- `vw_latest_reorder_recommendations`
- `vw_high_stockout_risk_products`

Views make dashboards and reports easier because complex logic is already prepared.

---

# 7. Recommended Learning Order for This Project

1. Read data from `dim_product`.
2. Filter products by category.
3. Count rows in each table.
4. Join `fact_sales` with `dim_product`.
5. Group sales by product and category.
6. Query moving average demand from `product_sales_velocity`.
7. Query reorder recommendations.
8. Study stockout and overstock views.
9. Practice CTEs and window functions.
10. Use `EXPLAIN ANALYZE` to learn query performance.

The goal is not only to write SQL. The goal is to understand how SQL answers real business questions.
