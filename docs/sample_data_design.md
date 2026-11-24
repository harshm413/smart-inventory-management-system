# Inventory Reorder System Sample Data Design

The sample data should feel like a real Myanmar retail business, but still be small enough for beginner-friendly learning.

The business has multiple branches and sells:

- Food
- Drinks
- Household items
- Personal care items
- Stationery

The data will include clean records and intentional bad records. That is important because a real data engineering project must detect and handle messy source data.

## 1. `products.csv`

### Why This Table Exists

`products.csv` is the product master table.

It stores the official list of products the business sells.

Without this table, the system cannot know:

- Product names
- Categories
- Product costs
- Selling prices
- Supplier relationships
- Shelf life
- Minimum order quantity

### Columns

```text
product_id
product_name
category
brand
unit_cost
selling_price
supplier_id
shelf_life_days
min_order_quantity
```

### Business Questions It Helps Answer

- What products does the shop sell?
- Which category does each product belong to?
- How much profit margin does each product have?
- Which supplier provides each product?
- Which products have short shelf life?
- What is the minimum quantity the shop should reorder?

### Example Records

```csv
product_id,product_name,category,brand,unit_cost,selling_price,supplier_id,shelf_life_days,min_order_quantity
P001,Mama Chicken Noodle,Food,Mama,350,500,S001,180,120
P002,Yum Yum Seafood Noodle,Food,Yum Yum,330,500,S001,180,120
P003,Alpine Water 1L,Drinks,Alpine,400,700,S002,365,48
P004,Shwe Pyi Nann Thanakha,Personal Care,Shwe Pyi Nann,1800,2500,S003,720,12
P005,Sunlight Dishwashing Liquid,Household,Sunlight,2200,3200,S004,900,12
P006,Premier Coffee Mix,Food,Premier,180,300,S001,365,100
P007,Red Bull Can,Drinks,Red Bull,900,1300,S002,365,24
P008,Double A A4 Paper,Stationery,Double A,9000,12000,S005,9999,5
P009,Blue Pen,Stationery,Zebra,300,500,S005,9999,50
P010,Colgate Toothpaste,Personal Care,Colgate,1800,2800,S003,720,24
P011,Fairy Detergent Powder,Household,Fairy,2500,3500,S004,900,10
P012,ABC Coffee Mix,food,ABC,160,250,S001,365,100
,P013 Missing ID Test,Food,Test Brand,500,700,S001,180,20
P014,Unknown Supplier Product,Food,Local,500,750,S999,180,20
P015,Category Typo Product,PersonalCare,Local,1000,1500,S003,365,10
```

### Intentional Data Quality Issues

```text
Missing product_id
Supplier ID that does not exist: S999
Inconsistent category spelling: food instead of Food
Inconsistent category spelling: PersonalCare instead of Personal Care
```

## 2. `branches.csv`

### Why This Table Exists

`branches.csv` stores information about each shop location.

This project includes multiple branches because real retail businesses often need reorder decisions by location.

A product may sell fast in Yangon but slowly in Mandalay.

### Columns

```text
branch_id
branch_name
city
township
branch_type
```

### Business Questions It Helps Answer

- Which branch needs reorder?
- Which city has the highest sales?
- Are some products branch-specific?
- Which branch has more stockout risk?
- How does demand differ by location?

### Example Records

```csv
branch_id,branch_name,city,township,branch_type
B001,Yangon Downtown Branch,Yangon,Kyauktada,Mini Mart
B002,Hlaing Branch,Yangon,Hlaing,Convenience Store
B003,Mandalay Central Branch,Mandalay,Chanayethazan,Mini Mart
B004,Naypyidaw Branch,Naypyidaw,Zabuthiri,Convenience Store
```

### Intentional Data Quality Issues

For the first version, this table can stay mostly clean. Branch data will be used to validate whether sales and stock records use valid branch IDs.

Possible issue to add later:

```text
Sales record with branch_id = B999
```

## 3. `suppliers.csv`

### Why This Table Exists

`suppliers.csv` stores supplier delivery and ordering information.

Supplier data is critical because reorder decisions depend on lead time.

If one supplier delivers in 2 days and another delivers in 7 days, reorder points should be different.

### Columns

```text
supplier_id
supplier_name
contact_phone
city
lead_time_days
minimum_order_value
```

### Business Questions It Helps Answer

- Which supplier should the shop contact?
- How long does delivery take?
- Which products need earlier reorder because supplier lead time is long?
- What is the minimum purchase amount required?
- How much reorder cost may be needed by supplier?

### Example Records

```csv
supplier_id,supplier_name,contact_phone,city,lead_time_days,minimum_order_value
S001,Yangon FMCG Distributor,09770111222,Yangon,3,300000
S002,Beverage Wholesale Myanmar,09770222333,Yangon,2,250000
S003,Personal Care Distributor,09770333444,Yangon,5,200000
S004,Household Goods Supplier,09770444555,Mandalay,6,250000
S005,Stationery World Myanmar,09770555666,Yangon,4,150000
S006,Incomplete Supplier,09770666777,Naypyidaw,,100000
```

### Intentional Data Quality Issues

```text
Supplier S006 has missing lead_time_days
Products may reference missing supplier S999
```

## 4. `sales_history.csv`

### Why This Table Exists

`sales_history.csv` stores product sales by branch and date.

This is the main demand table.

Without sales history, the system cannot calculate:

- Sales velocity
- Moving average demand
- Fast-moving products
- Slow-moving products
- Reorder quantity

### Columns

```text
sale_id
sale_date
branch_id
product_id
quantity_sold
unit_price
```

### Business Questions It Helps Answer

- Which products sell fastest?
- Which products have no recent sales?
- Which branches sell more?
- What is average daily demand?
- Are some products seasonal or location-specific?
- Which products should be prioritized for reorder?

### Example Records

```csv
sale_id,sale_date,branch_id,product_id,quantity_sold,unit_price
SL001,2026-04-20,B001,P001,20,500
SL002,2026-04-20,B001,P003,15,700
SL003,2026-04-20,B001,P006,35,300
SL004,2026-04-21,B001,P001,18,500
SL005,2026-04-21,B001,P007,12,1300
SL006,2026-04-22,B002,P002,16,500
SL007,2026-04-22,B002,P003,20,700
SL008,2026-04-23,B002,P006,30,300
SL009,2026-04-23,B003,P008,2,12000
SL010,2026-04-24,B003,P009,10,500
SL011,2026-04-24,B003,P005,3,3200
SL012,2026-04-25,B004,P010,4,2800
SL013,2026-04-25,B004,P011,5,3500
SL014,2026-04-26,B001,P001,25,500
SL015,2026-04-26,B001,P003,18,700
SL016,2026-04-27,B002,P006,40,300
SL017,2026-04-27,B002,P007,14,1300
SL018,2026-04-28,B003,P009,12,500
SL019,2026-04-28,B004,P004,3,2500
SL020,2026-04-29,B004,P010,5,2800
SL021,2026-04-30,B001,P001,22,500
SL022,2026-04-30,B001,P006,32,300
SL023,2026-05-01,B002,P002,15,500
SL024,2026-05-01,B002,P003,24,700
SL025,2026-05-02,B003,P008,1,12000
SL026,2026-05-02,B003,P009,9,500
SL027,2026-05-03,B004,P011,4,3500
SL028,2026-05-03,B004,P010,6,2800
SL029,2026-05-04,B001,P999,10,500
SL030,2026-05-04,B002,,5,700
SL031,2026-05-05,B999,P001,8,500
```

### Intentional Data Quality Issues

```text
Sale for product_id P999, which does not exist
Missing product_id
Sale for branch_id B999, which does not exist
```

## 5. `stock_movements.csv`

### Why This Table Exists

`stock_movements.csv` records every stock change.

Stock can increase or decrease for many reasons, not only sales.

Examples:

```text
purchase = stock increases
sale = stock decreases
return = stock increases
damage = stock decreases
adjustment_in = correction that increases stock
adjustment_out = correction that decreases stock
```

This table is useful for auditing inventory.

### Columns

```text
movement_id
movement_date
branch_id
product_id
movement_type
quantity
reference_note
```

### Business Questions It Helps Answer

- Why did stock change?
- How much stock was purchased?
- How much stock was lost due to damage?
- Are there manual stock adjustments?
- Do stock movements match sales?
- Which products have frequent damage or corrections?

### Example Records

```csv
movement_id,movement_date,branch_id,product_id,movement_type,quantity,reference_note
MV001,2026-04-18,B001,P001,purchase,240,Initial purchase
MV002,2026-04-18,B001,P003,purchase,120,Initial purchase
MV003,2026-04-18,B001,P006,purchase,300,Initial purchase
MV004,2026-04-20,B001,P001,sale,20,Sales SL001
MV005,2026-04-20,B001,P003,sale,15,Sales SL002
MV006,2026-04-20,B001,P006,sale,35,Sales SL003
MV007,2026-04-21,B001,P001,sale,18,Sales SL004
MV008,2026-04-21,B001,P007,purchase,72,Initial purchase
MV009,2026-04-21,B001,P007,sale,12,Sales SL005
MV010,2026-04-22,B002,P002,purchase,180,Initial purchase
MV011,2026-04-22,B002,P002,sale,16,Sales SL006
MV012,2026-04-22,B002,P003,purchase,144,Initial purchase
MV013,2026-04-22,B002,P003,sale,20,Sales SL007
MV014,2026-04-23,B002,P006,purchase,300,Initial purchase
MV015,2026-04-23,B002,P006,sale,30,Sales SL008
MV016,2026-04-24,B003,P008,purchase,20,Initial purchase
MV017,2026-04-24,B003,P009,purchase,100,Initial purchase
MV018,2026-04-24,B003,P009,sale,10,Sales SL010
MV019,2026-04-24,B003,P005,damage,2,Damaged bottle
MV020,2026-04-25,B004,P010,purchase,48,Initial purchase
MV021,2026-04-25,B004,P010,sale,4,Sales SL012
MV022,2026-04-25,B004,P011,purchase,40,Initial purchase
MV023,2026-04-25,B004,P011,sale,5,Sales SL013
MV024,2026-04-26,B001,P001,sale,25,Sales SL014
MV025,2026-04-26,B001,P003,sale,18,Sales SL015
MV026,2026-04-27,B002,P006,sale,40,Sales SL016
MV027,2026-04-27,B002,P007,sale,14,Sales SL017
MV028,2026-04-28,B003,P009,sale,12,Sales SL018
MV029,2026-04-28,B004,P004,purchase,36,Initial purchase
MV030,2026-04-28,B004,P004,sale,3,Sales SL019
MV031,2026-04-29,B004,P010,sale,5,Sales SL020
MV032,2026-04-30,B001,P001,sale,22,Sales SL021
MV033,2026-04-30,B001,P006,sale,32,Sales SL022
MV034,2026-05-01,B002,P002,sale,15,Sales SL023
MV035,2026-05-01,B002,P003,sale,24,Sales SL024
MV036,2026-05-02,B003,P008,sale,1,Sales SL025
MV037,2026-05-02,B003,P009,sale,9,Sales SL026
MV038,2026-05-03,B004,P011,sale,4,Sales SL027
MV039,2026-05-03,B004,P010,sale,6,Sales SL028
MV040,2026-05-04,B001,P001,transfer_out,10,Invalid movement type test
MV041,2026-05-04,B001,P001,sale,22,Duplicate movement test
MV041,2026-05-04,B001,P001,sale,22,Duplicate movement test
MV042,2026-05-05,B002,P003,adjustment_out,5,Stock count correction
MV043,2026-05-05,B003,P009,return,2,Customer return
```

### Intentional Data Quality Issues

```text
Invalid movement type: transfer_out
Duplicate movement_id: MV041
Duplicate stock movement row
```

## 6. `current_inventory.csv`

### Why This Table Exists

`current_inventory.csv` stores today's available stock by branch and product.

This table is the starting point for reorder decisions.

Sales history tells us demand. Current inventory tells us how much stock we have now.

### Columns

```text
inventory_date
branch_id
product_id
current_stock
reserved_stock
```

### Business Questions It Helps Answer

- How much stock is available now?
- Which branch has low stock?
- Which products are close to stockout?
- How many units are reserved and not available for normal sale?
- Which products have negative or suspicious stock?

### Example Records

```csv
inventory_date,branch_id,product_id,current_stock,reserved_stock
2026-05-06,B001,P001,35,5
2026-05-06,B001,P003,69,0
2026-05-06,B001,P006,201,10
2026-05-06,B001,P007,46,0
2026-05-06,B002,P002,149,0
2026-05-06,B002,P003,95,5
2026-05-06,B002,P006,230,0
2026-05-06,B002,P007,58,0
2026-05-06,B003,P008,19,0
2026-05-06,B003,P009,71,0
2026-05-06,B003,P005,25,0
2026-05-06,B004,P004,33,0
2026-05-06,B004,P010,33,0
2026-05-06,B004,P011,31,0
2026-05-06,B001,P002,-5,0
2026-05-06,B002,P999,20,0
```

### Intentional Data Quality Issues

```text
Current stock lower than zero: -5
Inventory record for product_id P999, which does not exist
```

## 7. Data Quality Issues Summary

The sample data intentionally includes these problems:

```text
Missing product IDs
Negative stock
Invalid movement types
Duplicate stock movements
Sales for products that do not exist
Supplier lead time missing
Current stock lower than zero
Inconsistent product category spelling
Invalid branch IDs
Products referencing suppliers that do not exist
```

These issues are useful because they will allow us to build real validation logic later.

## 8. How This Helps the Project

This sample data design supports the full Inventory Reorder System.

It allows the project to calculate:

```text
Sales velocity
7-day moving average demand
14-day moving average demand
Current stock
Stock coverage days
Stockout risk
Overstock risk
Reorder point
Recommended reorder quantity
Supplier reorder list
```

It also allows the pipeline to practice real data engineering checks:

```text
Primary key checks
Foreign key checks
Missing value checks
Duplicate checks
Negative quantity checks
Allowed value checks
Category standardization
```

What you learn as a Data Engineer:

- Raw source data is often messy
- Validation rules protect business decisions
- Master data and transaction data must connect correctly
- Inventory data requires both sales and stock movement records
- Sample data should include business realism, not random rows
