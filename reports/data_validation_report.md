# Data Validation Report

This report summarizes validation results for raw Inventory Reorder System CSV files.

Clean records are saved in `data/processed/`.

Rejected records are saved in `data/rejected/` with a `rejection_reason` column.

## Summary

| File | Raw Rows | Clean Rows | Rejected Rows |
|---|---:|---:|---:|
| `branches.csv` | 5 | 5 | 0 |
| `suppliers.csv` | 20 | 19 | 1 |
| `products.csv` | 120 | 111 | 9 |
| `sales_history.csv` | 15,600 | 14,395 | 1,205 |
| `stock_movements.csv` | 3,698 | 3,423 | 275 |
| `current_inventory.csv` | 602 | 550 | 52 |
| **Total** | **20,045** | **18,503** | **1,542** |

## Rejection Details

### `branches.csv`

No rejected records.

### `suppliers.csv`

| Rejection Reason | Count |
|---|---:|
| lead_time_days must be greater than 0 | 1 |

### `products.csv`

| Rejection Reason | Count |
|---|---:|
| category has inconsistent or invalid spelling | 5 |
| supplier_id does not exist in suppliers.csv | 4 |

### `sales_history.csv`

| Rejection Reason | Count |
|---|---:|
| branch_id does not exist in branches.csv | 1 |
| duplicate sale_id | 6 |
| product_id does not exist in products.csv | 1,197 |
| quantity_sold must be greater than 0 | 1 |

### `stock_movements.csv`

| Rejection Reason | Count |
|---|---:|
| duplicate movement_id | 2 |
| movement_type is not allowed | 1 |
| product_id does not exist in products.csv | 271 |
| quantity must be greater than 0 | 1 |

### `current_inventory.csv`

| Rejection Reason | Count |
|---|---:|
| current_stock must be greater than or equal to 0 | 1 |
| duplicate inventory snapshot for date, branch, and product | 2 |
| product_id does not exist in products.csv | 46 |
| reserved_stock cannot be greater than current_stock | 5 |

## Business Meaning

Rejected records are rows that should not be loaded into PostgreSQL yet.

In a real inventory system, rejected records protect the business from wrong reorder advice. For example, a sale with an invalid product ID cannot be connected to product cost or supplier lead time. A negative stock value can make the system think a product is more urgent than it really is. An invalid movement type can break stock movement analysis.
