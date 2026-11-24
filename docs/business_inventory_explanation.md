# Business Inventory Explanation

This document explains the inventory numbers in simple business language.

Audience:

- Myanmar shop owner
- Non-technical family business owner
- Beginner data learner

The main idea is simple:

> Use stock, sales, and supplier delivery time to decide what to buy, how much to buy, and when to buy.

## 1. Current Stock

Current stock means:

> How many units of a product the shop has right now.

Example:

```text
Product: Mama Chicken Noodle
Current Stock: 40 packets
```

Why it matters:

Current stock tells the owner the shop's current inventory position. If current stock is too low, the shop may run out. If current stock is too high, money is stuck in inventory.

Example business action:

If current stock is low for a fast-selling product, prepare to reorder. If current stock is very high for a slow-selling product, stop buying more for now.

## 2. Available Stock

Available stock means:

> Stock that can actually be sold to customers.

Formula:

```text
Available Stock = Current Stock - Reserved Stock
```

Example:

```text
Current Stock: 50 units
Reserved Stock: 10 units

Available Stock = 50 - 10
Available Stock = 40 units
```

Why it matters:

The shop should make reorder decisions using available stock, not only current stock. Reserved stock may already be kept for orders, damaged checks, or internal use.

Example business action:

If current stock looks high but available stock is low, the owner should still consider reordering.

## 3. Sales Velocity

Sales velocity means:

> How fast a product is selling.

Example:

```text
Product: Alpine Water 1L
Sold in last 30 days: 300 bottles

Sales Velocity = 300 / 30
Sales Velocity = 10 bottles per day
```

Why it matters:

A fast-selling product can run out quickly. A slow-selling product can trap money for a long time.

Example business action:

Check fast-selling products every day or every few days. Do not wait until the shelf is empty.

## 4. Moving Average Demand

Moving average demand means:

> Average sales per day over recent days.

It helps smooth daily sales changes.

Example:

```text
Sold in last 7 days: 70 units

7-Day Moving Average = 70 / 7
7-Day Moving Average = 10 units per day
```

Why it matters:

One day of sales can be unusual. The shop may sell a lot on one day and very little the next day. Moving average gives a more stable number for planning.

Common windows:

- 7-day average: reacts quickly to recent changes
- 14-day average: balanced and useful for reorder decisions
- 30-day average: more stable for slow-moving products

Example business action:

Use 14-day average demand as the normal daily demand when deciding reorder quantity.

## 5. Lead Time

Lead time means:

> How many days the supplier takes to deliver after the shop places an order.

Example:

```text
Supplier: Yangon FMCG Distributor
Lead Time: 5 days
```

Why it matters:

If the supplier needs 5 days to deliver, the shop must have enough stock to keep selling during those 5 days.

Example business action:

For suppliers with long lead time, reorder earlier. Do not wait until stock is very low.

## 6. Safety Stock

Safety stock means:

> Extra stock kept to prevent stockout.

It is a buffer.

Why it matters:

Safety stock protects the shop when:

- Sales suddenly increase
- Supplier delivery is late
- Stock count is not perfect
- Demand changes during holidays or paydays

Example:

```text
Average Daily Demand: 10 units
Safety Days: 3 days

Safety Stock = 10 * 3
Safety Stock = 30 units
```

Example business action:

Keep more safety stock for important fast-moving products such as water, noodles, rice, cooking oil, or popular snacks.

## 7. Reorder Point

Reorder point means:

> The stock level where the shop should place a new order.

Formula:

```text
Reorder Point =
Average Daily Demand * Supplier Lead Time + Safety Stock
```

Example:

```text
Average Daily Demand: 10 units per day
Supplier Lead Time: 5 days
Safety Stock: 30 units

Reorder Point = 10 * 5 + 30
Reorder Point = 80 units
```

Business meaning:

When available stock reaches 80 units or lower, the shop should reorder.

Example business action:

If available stock is below the reorder point, place a purchase order or transfer stock from another branch.

## 8. Stock Coverage Days

Stock coverage days means:

> How many days current available stock can last.

Formula:

```text
Stock Coverage Days =
Available Stock / Average Daily Demand
```

Example:

```text
Available Stock: 100 units
Average Daily Demand: 10 units per day

Stock Coverage Days = 100 / 10
Stock Coverage Days = 10 days
```

Why it matters:

This is easy for a shop owner to understand. Instead of saying "100 units", the system says "about 10 days of stock".

Example business action:

If stock coverage is 2 days but supplier lead time is 5 days, reorder immediately.

## 9. Stockout Risk

Stockout risk means:

> A product may run out soon.

Example:

```text
Available Stock: 20 units
Average Daily Demand: 10 units per day
Supplier Lead Time: 5 days

Stock Coverage Days = 2 days
```

Business meaning:

The shop has only 2 days of stock, but delivery takes 5 days. This product is at high stockout risk.

Why it matters:

Stockout causes:

- Lost sales
- Unhappy customers
- Customers buying from competitors
- Empty shelves

Example business action:

Reorder immediately or transfer stock from another branch.

## 10. Overstock Risk

Overstock risk means:

> The shop has too much stock compared to demand.

Example:

```text
Available Stock: 300 units
Average Daily Demand: 4 units per day

Stock Coverage Days = 300 / 4
Stock Coverage Days = 75 days
```

Business meaning:

The shop has enough stock for about 75 days. This may be too much.

Why it matters:

Overstock traps cash that could be used for faster-selling products.

Example business action:

Stop buying more this month. Consider discount, bundle offer, or transfer to a branch with better sales.

## 11. Dead Stock

Dead stock means:

> Stock that is not selling.

Example:

```text
Product: Product C
Sold in last 30 days: 0 units
Available Stock: 40 units
```

Business meaning:

The product has stock, but customers are not buying it.

Why it is dangerous:

Dead stock is dangerous because:

- Money is stuck
- Shelf space is wasted
- Product may expire or become damaged
- The shop may miss better buying opportunities

Example business action:

Try promotion, discount, bundle with fast-moving products, return to supplier, or stop ordering this product.

## 12. Reorder Recommendation

Reorder recommendation means:

> What to buy, how much to buy, and when to buy.

The system uses:

- Available stock
- Sales velocity
- Moving average demand
- Supplier lead time
- Safety stock
- Reorder point
- Minimum order quantity

Example:

```text
Product: Alpine Water 1L
Available Stock: 30 bottles
Reorder Point: 80 bottles
Recommended Order Quantity: 150 bottles
Priority: High
```

Business meaning:

Available stock is below the reorder point, so the owner should buy more now.

Example business action:

Place a purchase order with the supplier today. If cash is limited, buy high-priority items first.

## Final Simple Rule

For a shop owner, the system can be read like this:

```text
High stockout risk = buy or transfer stock now
Medium risk = watch closely and plan purchase
Low risk = include in next normal order
Overstock = stop buying and reduce stock
Dead stock = promote, discount, return, or stop ordering
```

The goal is not to make the system complicated.

The goal is to help the owner make better daily buying decisions.
