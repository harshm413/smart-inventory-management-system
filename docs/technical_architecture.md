# Inventory Reorder System Technical Architecture

## 1. Architecture Objective

The goal of this architecture is to turn raw shop inventory files into reliable reorder recommendations.

The system answers one main business question:

> Which products should the shop reorder now, and how many units should be purchased?

The architecture is intentionally simple:

```text
CSV / Excel Files
        |
        v
ETL Pipeline
        |
        v
PostgreSQL Staging Tables
        |
        v
Clean Data Model
        |
        v
Inventory Analytics Tables
        |
        v
Reports / Dashboard
```

Each layer has one clear responsibility. This makes the project easier to build, debug, explain on GitHub, and discuss in interviews.

## 2. Data Sources Layer

### Purpose

The data sources layer represents the files a real retail shop might export from a POS system, Excel tracker, or manual inventory record.

In a real Myanmar retail business, a shop owner may have:

- Daily sales files from cashier records
- Product lists from Excel
- Supplier contact files
- Current stock counts
- Stock movement records from purchases, returns, or damage

### Source Files

```text
data/raw/
â”œâ”€â”€ sales_history.csv
â”œâ”€â”€ products.csv
â”œâ”€â”€ stock_movements.csv
â”œâ”€â”€ current_inventory.csv
â””â”€â”€ suppliers.csv
```

### 2.1 Sales History CSV

Stores what customers bought.

Example columns:

```text
sale_id
sale_date
branch_id
product_id
quantity_sold
unit_price
total_amount
```

Business meaning:

This file shows actual customer demand. It is the foundation for calculating sales velocity and moving average demand.

### 2.2 Products CSV

Stores product details.

Example columns:

```text
product_id
product_name
category
brand
unit
cost_price
selling_price
supplier_id
minimum_order_quantity
lead_time_days
is_active
```

Business meaning:

This file tells the system what each product is, how much it costs, who supplies it, and how long reorder delivery takes.

### 2.3 Stock Movement CSV

Stores inventory changes.

Example columns:

```text
movement_id
movement_date
branch_id
product_id
movement_type
quantity
reference_note
```

Example movement types:

```text
PURCHASE_IN
SALE_OUT
RETURN_IN
DAMAGE_OUT
ADJUSTMENT_IN
ADJUSTMENT_OUT
```

Business meaning:

This file explains why stock increased or decreased. In real inventory systems, stock movement is more useful than only storing current stock.

### 2.4 Current Inventory CSV

Stores current available stock.

Example columns:

```text
snapshot_date
branch_id
product_id
current_stock
```

Business meaning:

This tells the system how much stock is available today.

### 2.5 Supplier CSV

Stores supplier information.

Example columns:

```text
supplier_id
supplier_name
city
phone
standard_lead_time_days
```

Business meaning:

Supplier lead time affects when the shop should reorder. A product from a slow supplier must be reordered earlier.

## 3. ETL Pipeline Layer

### Purpose

The ETL pipeline moves raw files into PostgreSQL safely and consistently.

ETL means:

```text
Extract -> Transform -> Load
```

For this project, we will use a beginner-friendly version:

```text
Extract files
Validate data
Clean data
Standardize IDs
Load staging tables
Transform analytics tables
```

### ETL Flow

```text
Raw CSV / Excel Files
        |
        v
Extract
        |
        v
Validate
        |
        v
Clean
        |
        v
Standardize IDs
        |
        v
Load to PostgreSQL Staging
        |
        v
Transform to Dimensions and Facts
        |
        v
Create Analytics Tables
```

### 3.1 Extract

Responsible for reading files from `data/raw/`.

Files may be:

- `.csv`
- `.xlsx`

Business meaning:

This is like collecting daily files from the shop owner or POS system.

You learn:

- How raw data enters a pipeline
- How to read CSV and Excel with Python
- How to keep raw data unchanged

### 3.2 Validate

Responsible for checking whether the data is usable.

Example validation checks:

```text
Missing product_id
Missing sale_date
Negative quantity_sold
Invalid movement_type
Duplicate sale_id
Products in sales but missing from products table
Selling price lower than cost price
Current stock below zero
```

Business meaning:

Bad data causes bad reorder advice. If sales quantities are wrong, the system may overbuy or underbuy.

You learn:

- Data quality rules
- Referential checks
- Why validation protects business decisions

### 3.3 Clean

Responsible for fixing simple data problems.

Example cleaning tasks:

```text
Trim spaces
Standardize date format
Convert quantities to integers
Convert prices to numeric values
Standardize category names
Fill optional missing values
Remove invalid duplicate rows
```

Business meaning:

Retail data is often messy. Cleaning turns shop files into analysis-ready data.

You learn:

- Practical Pandas cleaning
- Repeatable cleaning logic
- How to separate raw data from processed data

### 3.4 Standardize Product and Branch IDs

Responsible for making IDs consistent across files.

Example problem:

```text
sales_history.csv uses product_id = P001
stock_movements.csv uses product_id = p-001
current_inventory.csv uses product_id = 001
```

Standardized result:

```text
product_id = P001
```

Branch example:

```text
YGN01
MDY01
NPT01
```

Business meaning:

The same product must have the same ID everywhere. Otherwise, sales and stock cannot be joined correctly.

You learn:

- Why consistent keys matter
- How data modeling depends on clean IDs
- How real systems connect data from multiple sources

### 3.5 Load into PostgreSQL Staging Tables

Responsible for loading cleaned source data into staging tables.

Staging tables are temporary-looking database tables that store source data before final modeling.

Business meaning:

Staging tables allow you to inspect loaded data before turning it into final analytics tables.

You learn:

- Database loading
- Row count checks
- Source-to-database traceability

### 3.6 Transform into Inventory Analytics Tables

Responsible for turning staging data into useful business tables.

This includes:

- Dimension tables
- Fact tables
- Inventory snapshot table
- Reorder recommendation table

Business meaning:

Raw files are not designed for analytics. Transformed tables make business questions easier to answer.

You learn:

- SQL transformations
- Dimensional modeling basics
- Analytics table design

## 4. Database Design Layer

### Purpose

The database layer stores clean, structured inventory data in PostgreSQL.

The design should have:

```text
Staging tables
Dimension tables
Fact tables
Inventory snapshot table
Analytics tables
Reorder recommendation table
```

### 4.1 Staging Tables

Staging tables store cleaned source data close to its original shape.

```text
stg_sales_history
stg_products
stg_stock_movements
stg_current_inventory
stg_suppliers
```

Why this layer exists:

- Preserves source structure
- Helps debugging
- Allows row count comparison
- Separates raw loading from final modeling

Real business example:

If the shop owner says, "Why does this product need reorder?", you can trace the result back to source sales and stock records.

### 4.2 Dimension Tables

Dimension tables describe business entities.

```text
dim_product
dim_supplier
dim_branch
dim_date
```

#### dim_product

Stores product details.

```text
product_key
product_id
product_name
category
brand
unit
cost_price
selling_price
supplier_id
minimum_order_quantity
lead_time_days
is_active
```

#### dim_supplier

Stores supplier details.

```text
supplier_key
supplier_id
supplier_name
city
phone
standard_lead_time_days
```

#### dim_branch

Stores shop or branch details.

```text
branch_key
branch_id
branch_name
city
township
```

#### dim_date

Stores date attributes.

```text
date_key
date
day
month
quarter
year
week_of_year
```

Why dimensions exist:

They make reporting easier. Instead of repeating product names and supplier names in every table, facts can reference clean dimension records.

### 4.3 Fact Tables

Fact tables store business events.

```text
fact_sales
fact_stock_movements
```

#### fact_sales

Stores sales transactions or daily sales rows.

```text
sale_key
sale_id
sale_date
date_key
branch_key
product_key
quantity_sold
unit_price
total_amount
```

Business meaning:

This table shows customer demand.

#### fact_stock_movements

Stores stock movement events.

```text
movement_key
movement_id
movement_date
date_key
branch_key
product_key
movement_type
quantity
reference_note
```

Business meaning:

This table shows how inventory changed over time.

### 4.4 Inventory Snapshot Table

Stores current stock position.

```text
inventory_snapshot
snapshot_date
date_key
branch_key
product_key
current_stock
inventory_value
```

Formula:

```text
inventory_value = current_stock * cost_price
```

Business meaning:

This table answers:

> How much stock do we have right now, and how much money is tied up in it?

### 4.5 Inventory Analytics Tables

These tables store calculated metrics.

```text
product_sales_velocity
inventory_stock_coverage
```

#### product_sales_velocity

```text
calculation_date
branch_key
product_key
qty_sold_7d
qty_sold_14d
qty_sold_30d
avg_daily_demand_7d
avg_daily_demand_14d
avg_daily_demand_30d
```

#### inventory_stock_coverage

```text
analysis_date
branch_key
product_key
current_stock
avg_daily_demand_30d
stock_coverage_days
stockout_risk_flag
```

### 4.6 Reorder Recommendation Table

Stores the final recommendation.

```text
reorder_recommendations
recommendation_date
branch_key
product_key
supplier_key
current_stock
reserved_stock
available_stock
avg_daily_demand
lead_time_days
safety_stock
reorder_point
stock_coverage_days
reorder_needed
recommended_order_qty
priority_level
```

Business meaning:

This is the main output table. It tells the shop owner what action to take.

## 5. Analytics Layer

### Purpose

The analytics layer converts sales and inventory data into business logic.

This is where the system calculates:

- Sales velocity
- Moving average demand
- Stock coverage
- Stockout risk
- Reorder point
- Reorder quantity

### 5.1 Daily Sales Velocity

Formula:

```text
Daily Sales Velocity =
Total Units Sold / Number of Days
```

Business meaning:

Sales velocity tells how fast a product sells.

Example:

```text
A product sold 150 units in 30 days.

Daily Sales Velocity = 150 / 30 = 5 units per day
```

### 5.2 7-Day Moving Average Demand

Formula:

```text
7-Day Average Demand =
Units Sold in Last 7 Days / 7
```

Business meaning:

This shows very recent demand. It is useful for fast-changing products.

Example:

```text
Energy drink sold 70 units in 7 days.

7-Day Average Demand = 70 / 7 = 10 units per day
```

### 5.3 14-Day Moving Average Demand

Formula:

```text
14-Day Average Demand =
Units Sold in Last 14 Days / 14
```

Business meaning:

This gives a more stable recent demand view than 7 days.

Example:

```text
Coffee mix sold 112 units in 14 days.

14-Day Average Demand = 112 / 14 = 8 units per day
```

### 5.4 Stock Coverage Days

Formula:

```text
Stock Coverage Days =
Current Stock / Average Daily Demand
```

Business meaning:

This estimates how many days current stock will last.

Example:

```text
Current stock = 40 units
Average daily demand = 5 units

Stock Coverage Days = 40 / 5 = 8 days
```

If demand is zero:

```text
Stock Coverage Days = NULL or No Recent Demand
```

### 5.5 Stockout Risk Flag

Simple rule:

```text
If stock_coverage_days <= lead_time_days:
    stockout_risk_flag = TRUE
Else:
    stockout_risk_flag = FALSE
```

Business meaning:

If stock will run out before the supplier can deliver, the product is risky.

### 5.6 Reorder Point

Formula:

```text
Reorder Point =
Lead Time Demand + Safety Stock
```

Where:

```text
Lead Time Demand = Average Daily Demand * Lead Time Days
Safety Stock = Average Daily Demand * Safety Days
```

Business meaning:

The reorder point tells the shop when to reorder.

Example:

```text
Average daily demand = 5
Lead time days = 4
Safety days = 3

Lead Time Demand = 5 * 4 = 20
Safety Stock = 5 * 3 = 15

Reorder Point = 20 + 15 = 35 units
```

When stock reaches 35 units, reorder.

### 5.7 Recommended Reorder Quantity

Formula:

```text
Target Stock =
Average Daily Demand * (Lead Time Days + Review Period Days + Safety Days)

Recommended Reorder Quantity =
Target Stock - Current Stock
```

Then apply minimum order quantity:

```text
Final Recommended Quantity =
max(Recommended Reorder Quantity, Minimum Order Quantity)
```

Business meaning:

The system recommends enough quantity to cover supplier delay, normal selling period, and safety buffer.

### 5.8 Recommendation Status

Example logic:

```text
CRITICAL:
current_stock <= avg_daily_demand * 3

REORDER_NOW:
current_stock <= reorder_point

WATCH:
current_stock <= reorder_point * 1.25

ENOUGH_STOCK:
current_stock > reorder_point * 1.25

NO_RECENT_SALES:
avg_daily_demand = 0

SLOW_MOVING:
low demand and high current stock
```

Business meaning:

The shop owner should not only see numbers. They need clear action labels.

## 6. Reporting Layer

### Purpose

The reporting layer turns analytics into business communication.

The shop owner does not need to inspect database tables. They need simple outputs.

### 6.1 Markdown Reorder Report

File:

```text
reports/reorder_report.md
```

Purpose:

A readable summary for GitHub, documentation, and business explanation.

Example sections:

```text
# Daily Inventory Reorder Report

Report Date: 2026-05-06

## Summary KPIs

- Total products: 120
- Products needing reorder: 18
- Critical stock products: 6
- Estimated reorder cost: 2,450,000 MMK

## Critical Items

| Product | Current Stock | Avg Demand | Reorder Point | Recommended Qty |
|---|---:|---:|---:|---:|

## Reorder Recommendations

| Product | Supplier | Risk Level | Status | Recommended Qty |
|---|---|---|---|---|
```

Business meaning:

This report explains what the owner should do today.

### 6.2 CSV Reorder Recommendation Export

File:

```text
reports/reorder_recommendations.csv
```

Purpose:

A structured output that can be opened in Excel.

Columns:

```text
recommendation_date
branch_id
product_id
product_name
category
supplier_name
current_stock
reserved_stock
available_stock
avg_daily_demand
stock_coverage_days
lead_time_days
safety_stock
reorder_point
reorder_needed
recommended_order_qty
priority_level
```

Business meaning:

The shop owner can filter, sort, and send supplier-specific order lists.

### 6.3 Optional Streamlit Dashboard

File:

```text
app.py
```

Dashboard views:

```text
KPI cards
Products needing reorder table
Critical stock table
Slow-moving products table
Inventory value by category chart
Stockout risk by supplier chart
Top-selling products chart
```

Business meaning:

The dashboard gives a quick daily view of inventory health.

Use this only after the CSV and Markdown reports work. The pipeline and database are more important than the dashboard.

## 7. Beginner-Friendly Folder Structure

```text
inventory/
|
|-- app.py
|-- README.md
|-- requirements.txt
|-- .env.example
|-- .gitignore
|
|-- data/
|   |-- raw/
|   |-- processed/
|   |-- rejected/
|
|-- docs/
|   |-- business_inventory_explanation.md
|   |-- business_logic.md
|   |-- project_plan.md
|   |-- sample_data_design.md
|   |-- technical_architecture.md
|
|-- reports/
|   |-- data_validation_report.md
|   |-- reorder_report_YYYY_MM_DD.md
|
|-- sql/
|   |-- 01_create_database.sql
|   |-- 02_create_staging_tables.sql
|   |-- 03_create_warehouse_tables.sql
|   |-- 04_create_inventory_analytics_tables.sql
|   |-- 05_create_kpi_views.sql
|   |-- 06_transform_to_warehouse.sql
|   |-- 07_calculate_sales_velocity.sql
|   |-- 08_refresh_inventory_snapshot.sql
|   |-- 09_calculate_reorder_points.sql
|   |-- 10_stockout_overstock_detection.sql
|
|-- src/
|   |-- __init__.py
|   |-- db.py
|   |-- generate_sample_data.py
|   |-- validate_data.py
|   |-- load_staging.py
|   |-- transform_to_warehouse.py
|   |-- refresh_inventory_snapshot.py
|   |-- calculate_sales_velocity.py
|   |-- calculate_reorder_points.py
|   |-- detect_stockout_overstock.py
|   |-- generate_reorder_report.py
|   |-- run_pipeline.py
|
|-- tests/
|   |-- test_data_validation.py
|   |-- test_inventory_calculations.py
|   |-- test_reorder_logic.py
```
## 8. Folder and File Responsibilities

### `data/raw/`

Stores original source files.

Do not edit these manually after placing them here.

Why it exists:

Raw data must stay unchanged so you can trace pipeline results back to the original files.

### `data/processed/`

Stores cleaned CSV files.

Why it exists:

This separates messy source data from analysis-ready data.

### `data/sample/`

Stores sample Excel files for portfolio demonstration.

Why it exists:

GitHub visitors can understand the project without connecting to a real shop system.

### `sql/`

Stores SQL scripts for database creation and analytics.

Responsibilities:

- Create staging tables
- Create dimension and fact tables
- Transform staging data
- Calculate inventory metrics
- Create reorder recommendations

Why it exists:

SQL is central to data engineering. This folder proves you can model and analyze data in PostgreSQL.

### `src/`

Stores Python pipeline scripts.

Responsibilities:

- Read files
- Validate data
- Clean data
- Load PostgreSQL
- Run transformations
- Generate reports

Why it exists:

Python controls the pipeline workflow.

### `reports/`

Stores final business outputs.

Responsibilities:

- Markdown report for reading
- Data validation report
- Daily reorder recommendation report

Why it exists:

A data project is only useful when it produces a decision-ready output.

### `app.py`

Contains the optional Streamlit dashboard.

Why it exists:

The dashboard is a visual layer for quickly reviewing reorder, stockout, overstock, supplier, and branch KPIs.

### `docs/`

Stores project documentation.

Responsibilities:

- Project plan
- Technical architecture
- Sample data design
- Business logic
- Business inventory explanations

Why it exists:

Good documentation makes this project stronger for GitHub, LinkedIn, and interviews.

### `tests/`

Stores simple tests.

Why it exists:

Even beginner data projects should test important validation rules and inventory formulas.

## 9. How This Looks in a Real Retail Business

Imagine a small Myanmar mini mart with one or more branches.

Every day:

1. Cashiers record product sales.
2. New stock arrives from suppliers.
3. Some items are damaged or adjusted.
4. The shop owner checks current stock.
5. The system calculates which products are selling fast.
6. The system checks whether current stock can survive supplier lead time.
7. The system recommends what to reorder.
8. The owner exports a report and contacts suppliers.

Real business flow:

```text
Customer buys products
        |
        v
Sales are recorded
        |
        v
Stock decreases
        |
        v
Inventory system updates current stock
        |
        v
Reorder system checks demand and stock risk
        |
        v
Owner receives reorder report
        |
        v
Supplier order is placed
```

This project simulates that real workflow using local files, Python, PostgreSQL, and reports.

## 10. What You Should Learn From This Architecture

By building this architecture, you will learn:

- How retail inventory data is structured
- Why product, supplier, branch, sales, and stock movement data must be separated
- How staging tables protect the pipeline
- How dimension and fact tables support analytics
- How to calculate sales velocity using SQL
- How moving averages support simple demand forecasting
- How stock coverage days show business risk
- How reorder points connect demand with supplier lead time
- How to turn analytics into business recommendations
- How to build a portfolio-ready data engineering project without over-engineering

The key lesson:

> A good data engineering project does not just load data. It turns messy business records into reliable decisions.


