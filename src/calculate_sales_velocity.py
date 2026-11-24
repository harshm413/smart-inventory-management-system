"""
Calculate product sales velocity in PostgreSQL.

Run from the project root:
    python src/calculate_sales_velocity.py

Before running:
    1. Load validated CSV files into staging tables with src/load_staging.py.
    2. Transform staging data into warehouse tables with src/transform_to_warehouse.py.
    3. Make sure DB_* values are set in .env.

This script runs:
    sql/07_calculate_sales_velocity.sql
"""

from __future__ import annotations

from db import connect, run_sql_file


def run_sales_velocity_sql(conn) -> None:
    run_sql_file(conn, "07_calculate_sales_velocity.sql")


def print_sales_velocity_summary(conn) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                calculation_date,
                COUNT(*) AS row_count
            FROM product_sales_velocity
            WHERE calculation_date = (
                SELECT MAX(calculation_date)
                FROM product_sales_velocity
            )
            GROUP BY calculation_date
            """
        )
        summary = cur.fetchone()

        if summary is None:
            print("\nNo sales velocity rows were created.")
            return

        calculation_date, row_count = summary
        print("\nSales velocity summary:")
        print(f"calculation_date: {calculation_date}")
        print(f"product_sales_velocity rows: {row_count:,}")

        cur.execute(
            """
            SELECT
                db.branch_id,
                dp.product_id,
                dp.product_name,
                psv.qty_sold_7d,
                psv.qty_sold_14d,
                psv.qty_sold_30d,
                psv.avg_daily_demand_7d,
                psv.avg_daily_demand_14d,
                psv.avg_daily_demand_30d
            FROM product_sales_velocity psv
            JOIN dim_branch db
                ON psv.branch_key = db.branch_key
            JOIN dim_product dp
                ON psv.product_key = dp.product_key
            WHERE psv.calculation_date = %s
            ORDER BY
                psv.avg_daily_demand_14d DESC,
                psv.avg_daily_demand_7d DESC,
                db.branch_id,
                dp.product_id
            LIMIT 10
            """,
            (calculation_date,),
        )
        top_rows = cur.fetchall()

    print("\nTop product sales velocity rows:")
    for row in top_rows:
        (
            branch_id,
            product_id,
            product_name,
            qty_sold_7d,
            qty_sold_14d,
            qty_sold_30d,
            avg_7d,
            avg_14d,
            avg_30d,
        ) = row
        print(
            f"{branch_id} | {product_id} | {product_name} | "
            f"7d={qty_sold_7d} ({avg_7d}/day), "
            f"14d={qty_sold_14d} ({avg_14d}/day), "
            f"30d={qty_sold_30d} ({avg_30d}/day)"
        )


def main() -> None:
    with connect() as conn:
        run_sales_velocity_sql(conn)
        print_sales_velocity_summary(conn)

    print("\nSales velocity calculation complete.")


if __name__ == "__main__":
    main()
