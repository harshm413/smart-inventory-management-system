# Inventory Reorder System Business Logic

The goal of the business logic is simple:

> Use sales history and current stock to decide which products need reorder, when to reorder, and how much to buy.

This system does not guess. It uses sales data, stock data, and supplier delivery time.

## 1. Current Stock

Current stock means:

> How many units of a product the shop has right now.

Example:

```text
Product: Mama Chicken Noodle
Current Stock: 40 packets
```

Why it matters:

If current stock is too low, the shop may run out soon. If current stock is too high, money is trapped in inventory.

Business meaning:

Current stock tells us the current inventory position.

## 2. Sales Velocity

Sales velocity means:

> How fast a product is selling.

Example:

```text
Product: Alpine Water 1L
Sold in last 30 days: 300 bottles

Sales Velocity = 300 / 30
Sales Velocity = 10 bottles per day
```

Business meaning:

This product sells about 10 bottles per day.

Fast-moving products need closer monitoring because they can run out quickly.

## 3. Moving Average Demand

Moving average demand means:

> The average number of units sold per day over a recent time period.

It smooths daily sales changes.

For example, sales may look like this:

```text
Day 1: 5 units
Day 2: 12 units
Day 3: 8 units
Day 4: 15 units
```

Instead of looking at one day only, we calculate an average.

### 3.1 7-Day Moving Average

Formula:

```text
7-Day Moving Average =
Units sold in last 7 days / 7
```

Example:

```text
Milo Sachet sold 84 units in the last 7 days.

7-Day Moving Average = 84 / 7
7-Day Moving Average = 12 units per day
```

Business meaning:

Recently, the shop sells about 12 Milo Sachets per day.

The 7-day average reacts quickly to recent demand changes.

### 3.2 14-Day Moving Average

Formula:

```text
14-Day Moving Average =
Units sold in last 14 days / 14
```

Example:

```text
Milo Sachet sold 140 units in the last 14 days.

14-Day Moving Average = 140 / 14
14-Day Moving Average = 10 units per day
```

Business meaning:

Over the last two weeks, demand is about 10 units per day.

The 14-day average is more stable than the 7-day average.

### 3.3 Why Moving Average Is Useful

Daily sales are not always stable.

Example:

```text
Monday: 3 units
Tuesday: 20 units
Wednesday: 5 units
Thursday: 0 units
Friday: 18 units
```

If we use only one day, the reorder decision may be wrong.

Moving average helps because it:

- Reduces daily noise
- Shows recent demand trend
- Helps estimate future demand
- Keeps the logic simple and beginner-friendly

Business meaning:

Moving average gives a more reliable estimate of normal daily demand.

## 4. Lead Time

Lead time means:

> How many days it takes the supplier to deliver new stock after the shop places an order.

Example:

```text
Supplier: Yangon FMCG Distributor
Lead Time: 5 days
```

Business meaning:

If the shop orders today, new stock arrives after 5 days.

So the shop must have enough stock to survive those 5 days.

## 5. Safety Stock

Safety stock means:

> Extra stock kept as a buffer to avoid running out.

Why safety stock is needed:

- Supplier may deliver late
- Demand may suddenly increase
- Sales data may not be perfect
- Stock count may have small errors

Simple formula:

```text
Safety Stock =
Average Daily Demand * Safety Days
```

Example:

```text
Average Daily Demand = 10 units per day
Safety Days = 3 days

Safety Stock = 10 * 3
Safety Stock = 30 units
```

Business meaning:

The shop keeps 30 extra units as protection.

## 6. Reorder Point

Reorder point means:

> The stock level where the shop should place a new order.

Formula:

```text
Reorder Point =
Average Daily Demand * Lead Time + Safety Stock
```

This can also be understood as:

```text
Reorder Point =
Stock needed while waiting for supplier + Extra safety buffer
```

Example:

```text
Product: Alpine Water 1L

Average Daily Demand = 10 bottles per day
Lead Time = 5 days
Safety Stock = 30 bottles

Reorder Point = 10 * 5 + 30
Reorder Point = 50 + 30
Reorder Point = 80 bottles
```

Business meaning:

When Alpine Water stock falls to 80 bottles or below, the shop should reorder.

Why?

Because during the 5-day wait, the shop may sell:

```text
10 bottles per day * 5 days = 50 bottles
```

And it also wants 30 bottles as safety stock.

## 7. Stock Coverage Days

Stock coverage days means:

> How many days current stock can last based on average daily demand.

Formula:

```text
Stock Coverage Days =
Current Stock / Average Daily Demand
```

Example:

```text
Product: Milo Sachet

Current Stock = 120 units
Average Daily Demand = 12 units per day

Stock Coverage Days = 120 / 12
Stock Coverage Days = 10 days
```

Business meaning:

The current stock may last about 10 days.

If supplier lead time is 5 days, this product is probably safe.

If stock coverage is only 2 days and supplier lead time is 5 days, there is stockout risk.

## 8. Stockout Risk

Stockout risk means:

> A product is likely to run out before new stock arrives.

Simple rule:

```text
If Stock Coverage Days <= Lead Time:
    Stockout Risk = Yes
```

Example:

```text
Current Stock = 20 units
Average Daily Demand = 10 units per day
Lead Time = 5 days

Stock Coverage Days = 20 / 10
Stock Coverage Days = 2 days
```

Business meaning:

The shop has only 2 days of stock, but supplier delivery takes 5 days.

So this product has high stockout risk.

Possible risk labels:

```text
Critical: stock can last 0 to 3 days
High: current stock is below reorder point
Medium: current stock is near reorder point
Low: enough stock
```

## 9. Overstock Risk

Overstock risk means:

> A product has too much stock compared to how fast it sells.

Example:

```text
Product: Cleaning Brush

Current Stock = 300 units
Average Daily Demand = 2 units per day

Stock Coverage Days = 300 / 2
Stock Coverage Days = 150 days
```

Business meaning:

The shop has enough stock for about 150 days.

That may be too much. Money is stuck in slow-moving inventory.

Simple overstock rule:

```text
If Stock Coverage Days > 90:
    Overstock Risk = Yes
```

Another rule:

```text
If product has high current stock and very low demand:
    Product is slow-moving or overstocked
```

## 10. Reorder Quantity

Reorder quantity means:

> How many units the shop should buy.

We do not want to buy too little or too much.

Simple formula:

```text
Target Stock =
Average Daily Demand * (Lead Time Days + Review Period Days + Safety Days)

Reorder Quantity =
Target Stock - Current Stock
```

Where:

```text
Lead Time Days = supplier delivery time
Review Period Days = how often the shop reviews stock
Safety Days = extra buffer days
```

Example:

```text
Product: Mama Chicken Noodle

Average Daily Demand = 20 packets per day
Lead Time Days = 5 days
Review Period Days = 14 days
Safety Days = 3 days
Current Stock = 100 packets

Target Stock = 20 * (5 + 14 + 3)
Target Stock = 20 * 22
Target Stock = 440 packets

Reorder Quantity = 440 - 100
Reorder Quantity = 340 packets
```

Business meaning:

The shop should buy 340 packets to cover:

- 5 days waiting for supplier
- 14 days until next review
- 3 days safety buffer

If the supplier has a minimum order quantity:

```text
Minimum Order Quantity = 400 packets
Recommended Reorder Quantity = 400 packets
```

## 11. How This Becomes SQL and Python

### In SQL

SQL is good for calculations across many rows.

The project will use SQL to calculate:

```text
Total units sold
7-day moving average
14-day moving average
30-day demand
Current stock
Stock coverage days
Reorder point
Stockout risk flag
Recommended reorder quantity
```

Example SQL idea:

```sql
SELECT
    product_id,
    SUM(quantity_sold) AS units_sold_7d,
    SUM(quantity_sold) / 7.0 AS avg_daily_demand_7d
FROM fact_sales
WHERE sale_date >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY product_id;
```

Business meaning:

This query finds how many units each product sold in the last 7 days and converts that into daily demand.

### Reorder Point in SQL

```sql
SELECT
    product_id,
    avg_daily_demand_14d,
    lead_time_days,
    safety_stock,
    avg_daily_demand_14d * lead_time_days + safety_stock AS reorder_point
FROM inventory_sales_velocity;
```

Business meaning:

This calculates the stock level where each product should be reordered.

### Stock Coverage in SQL

```sql
SELECT
    ids.product_key,
    ids.available_stock,
    psv.avg_daily_demand_14d,
    ids.available_stock / NULLIF(psv.avg_daily_demand_14d, 0) AS stock_coverage_days
FROM inventory_daily_snapshot ids
JOIN product_sales_velocity psv
    ON ids.branch_key = psv.branch_key
   AND ids.product_key = psv.product_key;
```

Business meaning:

This estimates how many days each product can continue selling before stock reaches zero.

`NULLIF` prevents division by zero when a product has no recent sales.

### In Python

Python is good for controlling the whole pipeline.

Python will handle:

```text
Read CSV or Excel files
Validate missing values
Clean product names and IDs
Load data into PostgreSQL
Run SQL scripts
Export final reports
```

Example Python calculation idea:

```python
df["stock_coverage_days"] = (
    df["current_stock"] / df["avg_daily_demand_14d"]
)
```

Example reorder status logic:

```python
def get_reorder_status(row):
    if row["avg_daily_demand_14d"] == 0:
        return "NO_RECENT_SALES"
    if row["current_stock"] <= row["avg_daily_demand_14d"] * 3:
        return "CRITICAL"
    if row["current_stock"] <= row["reorder_point"]:
        return "REORDER_NOW"
    if row["current_stock"] <= row["reorder_point"] * 1.25:
        return "WATCH"
    return "ENOUGH_STOCK"
```

Business meaning:

Python turns the calculated numbers into clear action labels for the report.

## 12. Final Business Logic Flow

```text
1. Read product, sales, stock, inventory, and supplier data
2. Calculate how fast each product sells
3. Calculate average daily demand
4. Check supplier lead time
5. Add safety stock
6. Calculate reorder point
7. Compare current stock against reorder point
8. Detect stockout and overstock risk
9. Calculate recommended reorder quantity
10. Generate report for the shop owner
```

The main idea:

> The system uses demand, stock, and supplier lead time to replace guessing with clear reorder decisions.
