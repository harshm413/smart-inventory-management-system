"""
Create stockout, overstock, dead stock, and slow-moving product views.

Run from the project root:
    python src/detect_stockout_overstock.py

Before running:
    1. Load validated CSV files into staging tables with src/load_staging.py.
    2. Transform staging data into warehouse tables with src/transform_to_warehouse.py.
    3. Refresh inventory snapshot with src/refresh_inventory_snapshot.py.
    4. Calculate sales velocity with src/calculate_sales_velocity.py.
    5. Calculate reorder points with src/calculate_reorder_points.py.
    6. Make sure DB_* values are set in .env.

This script runs:
    sql/10_stockout_overstock_detection.sql
"""

from __future__ import annotations

from psycopg2 import sql
from db import connect, run_sql_file

DETECTION_VIEWS = [
    "vw_high_stockout_risk_products",
    "vw_overstock_products",
    "vw_dead_stock_products",
    "vw_slow_moving_products",
]

def run_detection_sql(conn) -> None:
    run_sql_file(conn, "10_stockout_overstock_detection.sql")


def print_detection_counts(conn) -> None:
    print("\nStock risk view counts:")
    with conn.cursor() as cur:
        for view_name in DETECTION_VIEWS:
            cur.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(sql.Identifier(view_name)))
            count = cur.fetchone()[0]
            print(f"{view_name}: {count:,}")


def main() -> None:
    with connect() as conn:
        run_detection_sql(conn)
        print_detection_counts(conn)

    print("\nStockout and overstock detection views complete.")


if __name__ == "__main__":
    main()
