"""
Transform PostgreSQL staging tables into warehouse tables.

Run from the project root:
    python src/transform_to_warehouse.py

Before running:
    1. Load validated CSV files into staging tables with src/load_staging.py.
    2. Make sure DB_* values are set in .env.

This script runs:
    sql/06_transform_to_warehouse.sql
"""

from __future__ import annotations

from psycopg2 import sql
from db import connect, run_sql_file

WAREHOUSE_TABLES = [
    "dim_supplier",
    "dim_branch",
    "dim_product",
    "dim_date",
    "fact_sales",
    "fact_stock_movement",
]

def run_transform_sql(conn) -> None:
    run_sql_file(conn, "06_transform_to_warehouse.sql")


def print_table_counts(conn) -> None:
    print("\nWarehouse row counts:")
    with conn.cursor() as cur:
        for table_name in WAREHOUSE_TABLES:
            cur.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(sql.Identifier(table_name)))
            count = cur.fetchone()[0]
            print(f"{table_name}: {count:,}")


def main() -> None:
    with connect() as conn:
        run_transform_sql(conn)
        print_table_counts(conn)

    print("\nWarehouse transformation complete.")


if __name__ == "__main__":
    main()
