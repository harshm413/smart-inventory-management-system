"""
Load validated CSV files into PostgreSQL staging tables.

Run from the project root:
    python src/load_staging.py

Before running:
    1. Install PostgreSQL.
    2. Create a .env file or set DB_* environment variables.
    3. Run src/validate_data.py so data/processed/*.csv exists.

This script:
    - creates the target database if it does not exist
    - creates staging, warehouse, analytics tables, and KPI views
    - truncates staging tables
    - loads data/processed CSV files into staging tables
"""

from __future__ import annotations

import pandas as pd
from psycopg2 import sql

from db import PROJECT_ROOT, DB_NAME, DB_MAINTENANCE_DB, connect, run_sql_file


PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"

LOAD_ORDER = [
    {
        "csv_file": "suppliers.csv",
        "table_name": "stg_suppliers",
        "columns": [
            "supplier_id",
            "supplier_name",
            "contact_phone",
            "city",
            "lead_time_days",
            "minimum_order_value",
        ],
    },
    {
        "csv_file": "branches.csv",
        "table_name": "stg_branches",
        "columns": [
            "branch_id",
            "branch_name",
            "city",
            "township",
            "branch_type",
        ],
    },
    {
        "csv_file": "products.csv",
        "table_name": "stg_products",
        "columns": [
            "product_id",
            "product_name",
            "category",
            "brand",
            "unit_cost",
            "selling_price",
            "supplier_id",
            "shelf_life_days",
            "min_order_quantity",
        ],
    },
    {
        "csv_file": "sales_history.csv",
        "table_name": "stg_sales_history",
        "columns": [
            "sale_id",
            "sale_date",
            "branch_id",
            "product_id",
            "quantity_sold",
            "unit_price",
        ],
    },
    {
        "csv_file": "stock_movements.csv",
        "table_name": "stg_stock_movements",
        "columns": [
            "movement_id",
            "movement_date",
            "branch_id",
            "product_id",
            "movement_type",
            "quantity",
            "reference_note",
        ],
    },
    {
        "csv_file": "current_inventory.csv",
        "table_name": "stg_current_inventory",
        "columns": [
            "inventory_date",
            "branch_id",
            "product_id",
            "current_stock",
            "reserved_stock",
        ],
    },
]


def ensure_database_exists() -> None:
    """Create the target database when it does not already exist."""
    conn = connect(DB_MAINTENANCE_DB)
    try:
        # CREATE DATABASE must run outside a transaction block.
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_NAME,))
            exists = cur.fetchone() is not None
            if not exists:
                cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(DB_NAME)))
                print(f"Created database: {DB_NAME}")
            else:
                print(f"Database already exists: {DB_NAME}")
    finally:
        conn.close()

def create_schema() -> None:
    """Create staging, warehouse, analytics tables, and KPI views."""
    sql_files = [
        "02_create_staging_tables.sql",
        "03_create_warehouse_tables.sql",
        "04_create_inventory_analytics_tables.sql",
        "05_create_kpi_views.sql",
    ]
    with connect(DB_NAME) as conn:
        for filename in sql_files:
            run_sql_file(conn, filename)


def validate_processed_files_exist() -> None:
    missing_files = []
    for item in LOAD_ORDER:
        path = PROCESSED_DATA_DIR / item["csv_file"]
        if not path.exists():
            missing_files.append(str(path.relative_to(PROJECT_ROOT)))

    if missing_files:
        raise FileNotFoundError(
            "Missing processed files. Run src/validate_data.py first.\n"
            + "\n".join(missing_files)
        )


def check_csv_columns(csv_file: str, expected_columns: list[str]) -> int:
    """Check CSV columns before loading and return row count."""
    path = PROCESSED_DATA_DIR / csv_file
    df = pd.read_csv(path, nrows=5)
    actual_columns = list(df.columns)
    if actual_columns != expected_columns:
        raise ValueError(
            f"{csv_file} has unexpected columns.\n"
            f"Expected: {expected_columns}\n"
            f"Actual:   {actual_columns}"
        )

    return sum(1 for _ in path.open("r", encoding="utf-8")) - 1


def truncate_staging_tables(conn) -> None:
    table_names = [item["table_name"] for item in LOAD_ORDER]
    with conn.cursor() as cur:
        cur.execute(
            sql.SQL("TRUNCATE TABLE {}").format(
                sql.SQL(", ").join(sql.Identifier(table_name) for table_name in table_names)
            )
        )
    conn.commit()
    print("Truncated staging tables")


def copy_csv_to_table(conn, csv_file: str, table_name: str, columns: list[str]) -> int:
    """Load one processed CSV into a PostgreSQL staging table."""
    path = PROCESSED_DATA_DIR / csv_file
    row_count = check_csv_columns(csv_file, columns)

    copy_sql = sql.SQL(
        """
        COPY {} ({})
        FROM STDIN
        WITH (
            FORMAT CSV,
            HEADER TRUE,
            NULL ''
        )
        """
    ).format(
        sql.Identifier(table_name),
        sql.SQL(", ").join(sql.Identifier(column) for column in columns),
    )

    with path.open("r", encoding="utf-8") as file_handle:
        with conn.cursor() as cur:
            cur.copy_expert(copy_sql.as_string(conn), file_handle)

    conn.commit()
    print(f"Loaded {row_count:,} rows into {table_name}")
    return row_count


def load_staging_tables() -> None:
    validate_processed_files_exist()

    with connect(DB_NAME) as conn:
        truncate_staging_tables(conn)
        for item in LOAD_ORDER:
            copy_csv_to_table(
                conn=conn,
                csv_file=item["csv_file"],
                table_name=item["table_name"],
                columns=item["columns"],
            )


def print_staging_counts() -> None:
    with connect(DB_NAME) as conn:
        with conn.cursor() as cur:
            print("\nStaging row counts:")
            for item in LOAD_ORDER:
                table_name = item["table_name"]
                cur.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(sql.Identifier(table_name)))
                count = cur.fetchone()[0]
                print(f"{table_name}: {count:,}")


def main() -> None:
    ensure_database_exists()
    create_schema()
    load_staging_tables()
    print_staging_counts()
    print("\nPostgreSQL staging load complete.")


if __name__ == "__main__":
    main()
