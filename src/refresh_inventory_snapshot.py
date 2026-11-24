"""
Refresh inventory_daily_snapshot in PostgreSQL.

Run from the project root:
    python src/refresh_inventory_snapshot.py

Before running:
    1. Load validated CSV files into staging tables with src/load_staging.py.
    2. Transform staging data into warehouse tables with src/transform_to_warehouse.py.
    3. Make sure DB_* values are set in .env.

This script runs:
    sql/08_refresh_inventory_snapshot.sql
"""

from __future__ import annotations

from psycopg2 import sql
from db import connect, run_sql_file


SNAPSHOT_TABLES = ["inventory_daily_snapshot"]


def run_snapshot_sql(conn) -> None:
    run_sql_file(conn, "08_refresh_inventory_snapshot.sql")


def print_snapshot_counts(conn) -> None:
    print("\nInventory snapshot row counts:")
    with conn.cursor() as cur:
        for table_name in SNAPSHOT_TABLES:
            cur.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(sql.Identifier(table_name)))
            count = cur.fetchone()[0]
            print(f"{table_name}: {count:,}")


def main() -> None:
    with connect() as conn:
        run_snapshot_sql(conn)
        print_snapshot_counts(conn)

    print("\nInventory snapshot refresh complete.")


if __name__ == "__main__":
    main()
