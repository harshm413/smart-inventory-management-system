# Inventory Reorder System Project Plan

## 1. Project Objective

Build a beginner-friendly but professional data engineering project that helps a Myanmar retail shop owner decide:

- Which products need reordering
- When to reorder them
- How much to reorder
- Which items are at risk of stockout
- Which items are slow-moving or overstocked

The system will use sales history, inventory stock movement, and supplier lead time data to generate reorder recommendations.

No machine learning will be used in the first version. The project will focus on practical inventory analytics, SQL modeling, and business rules.

## 2. Business Problem

A shop owner currently makes inventory decisions by guessing.

This causes:

- Popular products to run out of stock
- Slow-moving products to stay on shelves too long
- Cash to be trapped in dead stock
- Customers to leave when products are unavailable
- Suppliers to be contacted too late
- Inventory decisions to depend on memory instead of data

### Business Goal

Use historical sales and current stock data to answer:

> Which products should I reorder today, and how many units should I buy?

## 3. Example Business Scenario

The project will use realistic Myanmar retail data from a small shop or mini mart.

Example product categories:

- Rice and cooking oil
- Instant noodles
- Coffee mix and tea mix
- Bottled water and soft drinks
- Snacks
- Personal care items
- Cleaning products
- Baby products
- Phone top-up cards or accessories

Example products:

- Mama Chicken Noodle
- Paw San Hmwe Rice 5kg
- Alpine Water 1L
- Milo Sachet
- Red Bull Can
- Shwe Wah Soap
- Sunlight Dishwashing Liquid

Example suppliers:

- Yangon FMCG Distributor
- Mandalay Wholesale Center
- Local Rice Supplier
- Beverage Distributor

## 4. Technical Architecture

The system should stay simple and local-first.

```text
CSV / Excel Files
        |
        v
Python Data Pipeline
        |
        v
Data Validation and Cleaning
        |
        v
PostgreSQL Database
        |
        v
SQL Analytics + Python Reorder Logic
        |
        v
Reorder Report CSV / Excel
        |
        v
Optional Dashboard
```

### Main Tools

- Python
- Pandas
- PostgreSQL
- SQL
- CSV / Excel files
- Optional: Streamlit or Power BI later

## 5. Folder Structure

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
## 6. Data Model

### 6.1 Products Table

Stores product master data.

```text
products
- product_id
- product_name
- category
- brand
- unit
- cost_price
- selling_price
- supplier_id
- minimum_order_quantity
- lead_time_days
- is_active
```

Business meaning:

- `cost_price`: how much the shop pays
- `selling_price`: customer price
- `lead_time_days`: how long supplier takes to deliver
- `minimum_order_quantity`: smallest quantity supplier accepts

### 6.2 Suppliers Table

Stores supplier information.

```text
suppliers
- supplier_id
- supplier_name
- city
- phone
- standard_lead_time_days
```

Business meaning:

Supplier lead time is important because reorder decisions must happen before stock reaches zero.

### 6.3 Sales Table

Stores daily product sales.

```text
sales
- sale_id
- sale_date
- product_id
- quantity_sold
- unit_price
- total_sales_amount
```

Business meaning:

Sales history shows real customer demand.

### 6.4 Stock Movements Table

Stores all stock changes.

```text
stock_movements
- movement_id
- movement_date
- product_id
- movement_type
- quantity
- reference_note
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

This table explains why stock increased or decreased. It is more flexible than only storing current stock.

### 6.5 Inventory Snapshot Table

Stores current stock position.

```text
inventory_snapshot
- snapshot_date
- product_id
- current_stock
```

Business meaning:

This tells us how many units are available now.

### 6.6 Reorder Recommendations Table

Stores final reorder results.

```text
reorder_recommendations
- recommendation_date
- product_id
- current_stock
- avg_daily_demand
- lead_time_days
- safety_stock
- reorder_point
- recommended_order_qty
- stockout_risk_level
- recommendation_status
```

Business meaning:

This is the final decision table for the shop owner.

## 7. Inventory Logic

### 7.1 Moving Average Demand

Moving average demand estimates how many units a product sells per day.

Formula:

```text
Average Daily Demand =
Total units sold in recent period / Number of days in period
```

Example:

```text
Mama Noodle sold 210 units in the last 30 days.

Average Daily Demand = 210 / 30 = 7 units per day
```

Business meaning:

The shop sells about 7 units per day, so future stock planning should expect similar demand.

### 7.2 Lead Time Demand

Lead time demand estimates how many units will sell while waiting for the supplier.

Formula:

```text
Lead Time Demand =
Average Daily Demand * Supplier Lead Time Days
```

Example:

```text
Average Daily Demand = 7 units
Lead Time = 5 days

Lead Time Demand = 7 * 5 = 35 units
```

Business meaning:

If the shop orders today, it may sell 35 units before new stock arrives.

### 7.3 Safety Stock

Safety stock protects the shop from unexpected demand or supplier delays.

Simple beginner formula:

```text
Safety Stock =
Average Daily Demand * Safety Days
```

Example:

```text
Average Daily Demand = 7 units
Safety Days = 3 days

Safety Stock = 7 * 3 = 21 units
```

Business meaning:

The shop keeps 21 extra units as a buffer.

### 7.4 Reorder Point

The reorder point tells us when to reorder.

Formula:

```text
Reorder Point =
Lead Time Demand + Safety Stock
```

Example:

```text
Lead Time Demand = 35 units
Safety Stock = 21 units

Reorder Point = 56 units
```

Business meaning:

When stock falls to 56 units or below, the shop should reorder.

### 7.5 Stockout Risk

Stockout risk checks if current stock is too low.

Simple rule:

```text
If current_stock <= reorder_point:
    product needs reorder
```

Risk levels:

```text
Critical: current stock <= 3 days of demand
High: current stock <= reorder point
Medium: current stock <= reorder point * 1.25
Low: current stock > reorder point * 1.25
```

Business meaning:

This helps the owner focus on urgent items first.

### 7.6 Recommended Order Quantity

The system should recommend enough stock to cover the next buying cycle.

Simple formula:

```text
Target Stock =
Average Daily Demand * (Lead Time Days + Review Period Days + Safety Days)

Recommended Order Quantity =
Target Stock - Current Stock
```

Then apply minimum order quantity:

```text
Final Recommended Quantity =
max(Recommended Order Quantity, Minimum Order Quantity)
```

Example:

```text
Average Daily Demand = 7
Lead Time = 5 days
Review Period = 14 days
Safety Days = 3 days

Target Stock = 7 * (5 + 14 + 3)
Target Stock = 154 units

Current Stock = 40 units

Recommended Quantity = 154 - 40 = 114 units
```

Business meaning:

The shop should buy enough to survive supplier waiting time, the next review cycle, and a small safety buffer.

## 8. Pipeline Stages

### Stage 1: Data Collection

Input files:

```text
products.csv
suppliers.csv
sales_history.csv
stock_movements.csv
current_inventory.csv
```

What happens:

- Collect sample retail inventory data
- Prepare realistic Myanmar product names and suppliers
- Store files in `data/raw/`

What you learn as a Data Engineer:

- How operational business data is structured
- Why product and supplier master data matters
- How raw files enter a data pipeline

### Stage 2: Data Validation

Validation checks:

- Missing product IDs
- Negative quantities
- Invalid dates
- Duplicate sales records
- Products in sales but missing from product master
- Stock movements with unknown movement types
- Selling price lower than cost price

What you learn:

- Data quality is part of data engineering
- Bad source data causes bad business decisions
- Validation protects the database and reports

### Stage 3: Data Cleaning

Cleaning actions:

- Standardize date formats
- Trim spaces from product names
- Convert quantities to numbers
- Replace missing optional values
- Remove or flag invalid rows
- Standardize category names

What you learn:

- Clean data makes analytics reliable
- Small formatting problems can break pipelines
- Cleaning rules should be repeatable

### Stage 4: Load Data into PostgreSQL

Load cleaned data into PostgreSQL tables:

```text
products
suppliers
sales
stock_movements
inventory_snapshot
```

What you learn:

- How to move data from files into a relational database
- How PostgreSQL supports analytics
- How staging and final tables differ

### Stage 5: Build Inventory Data Model

Create structured tables with relationships:

```text
products -> suppliers
sales -> products
stock_movements -> products
inventory_snapshot -> products
```

What you learn:

- Inventory systems need both master data and transaction data
- Sales and stock movement are different but related
- Good table design makes business questions easier to answer

### Stage 6: Calculate Demand

Calculate:

- 7-day average demand
- 30-day average demand
- Total units sold
- Sales frequency
- Days since last sale

What you learn:

- Moving averages smooth daily sales noise
- Recent sales are more useful for reorder decisions
- Demand is the foundation of inventory planning

### Stage 7: Detect Stockout Risk

Compare current stock against reorder point and demand.

Outputs:

- Critical stock items
- High-risk items
- Products with enough stock
- Products with no recent demand

What you learn:

- Stockout risk is a business rule, not just a number
- Urgent products should be prioritized
- Inventory decisions should consider both stock and sales velocity

### Stage 8: Calculate Reorder Recommendations

Calculate:

- Lead time demand
- Safety stock
- Reorder point
- Target stock
- Recommended reorder quantity

What you learn:

- Reorder logic connects business operations with data
- Supplier lead time affects inventory decisions
- Simple formulas can create strong business value

### Stage 9: Generate Reorder Report

Report columns:

```text
product_id
product_name
category
supplier_name
current_stock
avg_daily_demand_30d
lead_time_days
safety_stock
reorder_point
recommended_order_qty
stockout_risk_level
recommendation_status
```

Example recommendation status:

```text
REORDER_NOW
WATCH
ENOUGH_STOCK
SLOW_MOVING
NO_RECENT_SALES
```

What you learn:

- Analytics must become an action
- Business users need clear recommendations
- Reports should be simple and decision-focused

### Stage 10: Optional Dashboard

Dashboard KPIs:

- Total SKUs
- Products needing reorder
- Critical stock items
- Estimated reorder cost
- Slow-moving products
- Dead stock value
- Top-selling products
- Stockout risk by category
- Inventory value by category

What you learn:

- Dashboards summarize operational health
- KPIs help business owners act quickly
- Visual reporting is useful after the data model is stable

## 9. KPI List

### Inventory KPIs

- Total Products
- Current Inventory Value
- Products Below Reorder Point
- Critical Stock Products
- Overstocked Products
- Slow-Moving Products
- Dead Stock Products

### Sales KPIs

- Total Units Sold
- Total Sales Amount
- Average Daily Demand
- Top 10 Fast-Moving Products
- Products With No Sales in Last 30 Days

### Reorder KPIs

- Total Recommended Order Quantity
- Estimated Reorder Cost
- Number of Suppliers to Contact
- Reorder Products by Risk Level
- Expected Days Until Stockout

## 10. Report Format

The main report should be simple enough for a shop owner.

### Reorder Report Example

```text
Date: 2026-05-06

Product: Mama Chicken Noodle
Category: Instant Noodles
Current Stock: 42 units
Average Daily Demand: 7 units
Lead Time: 5 days
Safety Stock: 21 units
Reorder Point: 56 units
Recommended Order Quantity: 112 units
Risk Level: High
Status: REORDER_NOW
Supplier: Yangon FMCG Distributor
```

### Report Files

```text
reports/reorder_report_YYYY_MM_DD.md
reports/data_validation_report.md
```

## 11. Step-by-Step Build Roadmap

### Phase 1: Project Setup

Goal:

Set up the folder structure, README, requirements file, and sample data plan.

Deliverables:

```text
Project folder
README draft
Data dictionary
Sample data design
```

You learn:

- How to structure a portfolio data engineering project
- How to explain business value before writing code

### Phase 2: Create Realistic Sample Data

Goal:

Create Myanmar retail sample data for products, suppliers, sales, and stock movement.

Deliverables:

```text
products.csv
suppliers.csv
sales_history.csv
stock_movements.csv
current_inventory.csv
```

You learn:

- How to design realistic source data
- How sales, stock, and suppliers connect

### Phase 3: Data Validation and Cleaning

Goal:

Build checks that catch common data issues.

Deliverables:

```text
validation rules
cleaned CSV files
data quality summary
```

You learn:

- How to protect pipelines from bad input
- How to document data quality problems

### Phase 4: PostgreSQL Schema Design

Goal:

Create normalized inventory tables.

Deliverables:

```text
PostgreSQL tables
Primary keys
Foreign keys
Schema SQL file
```

You learn:

- Inventory data modeling
- Relational design for analytics
- Transaction vs master tables

### Phase 5: Load Pipeline

Goal:

Load cleaned CSV/Excel data into PostgreSQL.

Deliverables:

```text
Python load script
PostgreSQL loaded tables
Row count checks
```

You learn:

- ETL pipeline basics
- Database loading
- Pipeline verification

### Phase 6: Demand Analytics

Goal:

Calculate recent demand using moving averages.

Deliverables:

```text
7-day demand
30-day demand
Sales velocity table
```

You learn:

- Moving average calculation
- Demand analysis
- SQL aggregation

### Phase 7: Reorder Logic

Goal:

Calculate reorder points and recommended quantities.

Deliverables:

```text
reorder recommendation table
risk classification
business rules documentation
```

You learn:

- Reorder point calculation
- Safety stock logic
- Business recommendation rules

### Phase 8: Reorder Report

Goal:

Generate a business-friendly report.

Deliverables:

```text
reorder_report_YYYY_MM_DD.md
simple business explanation
supplier-wise purchase list
```

You learn:

- How analytics becomes business action
- How to design clear operational reports

### Phase 9: Optional Dashboard

Goal:

Build a simple dashboard for inventory KPIs.

Deliverables:

```text
app.py
KPI cards
reorder table
category charts
```

You learn:

- Dashboard reporting
- KPI communication
- Portfolio presentation

### Phase 10: GitHub and LinkedIn Packaging

Goal:

Make the project portfolio-ready.

Deliverables:

```text
clean README
architecture diagram
sample screenshots
business explanation
technical explanation
LinkedIn project summary
```

You learn:

- How to present data engineering work professionally
- How to explain business impact
- How to show technical skills clearly

## 12. Final Portfolio Positioning

This project should be presented as:

> A local-first inventory analytics and reorder recommendation system for Myanmar retail shops using Python, PostgreSQL, Pandas, and SQL.

The strongest portfolio skills shown will be:

- Data modeling
- ETL pipeline design
- PostgreSQL analytics
- Business rule implementation
- Inventory analytics
- Reporting
- Practical decision support

The first version should stay simple, clear, and useful. Machine learning can be added later only after the rule-based system works well.


