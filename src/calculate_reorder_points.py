"""
Calculate reorder recommendations in PostgreSQL.

Run from the project root:
    python src/calculate_reorder_points.py

Before running:
    1. Load validated CSV files into staging tables with src/load_staging.py.
    2. Transform staging data into warehouse tables with src/transform_to_warehouse.py.
    3. Refresh inventory snapshot with src/refresh_inventory_snapshot.py.
    4. Calculate sales velocity with src/calculate_sales_velocity.py.
    5. Make sure DB_* values are set in .env.

This script runs:
    sql/09_calculate_reorder_points.sql
"""

from __future__ import annotations

from db import connect, run_sql_file


def run_reorder_points_sql(conn) -> None:
    run_sql_file(conn, "09_calculate_reorder_points.sql")


def print_reorder_summary(conn) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                recommendation_date,
                COUNT(*) AS row_count,
                COUNT(*) FILTER (WHERE reorder_needed) AS reorder_count,
                COUNT(*) FILTER (WHERE priority_level = 'High') AS high_count,
                COUNT(*) FILTER (WHERE priority_level = 'Medium') AS medium_count,
                COUNT(*) FILTER (WHERE priority_level = 'Low') AS low_count
            FROM reorder_recommendations
            WHERE recommendation_date = (
                SELECT MAX(recommendation_date)
                FROM reorder_recommendations
            )
            GROUP BY recommendation_date
            """
        )
        summary = cur.fetchone()

        if summary is None:
            print("\nNo reorder recommendation rows were created.")
            return

        (
            recommendation_date,
            row_count,
            reorder_count,
            high_count,
            medium_count,
            low_count,
        ) = summary

        print("\nReorder recommendation summary:")
        print(f"recommendation_date: {recommendation_date}")
        print(f"reorder_recommendations rows: {row_count:,}")
        print(f"reorder_needed rows: {reorder_count:,}")
        print(f"High priority: {high_count:,}")
        print(f"Medium priority: {medium_count:,}")
        print(f"Low priority: {low_count:,}")

        cur.execute(
            """
            SELECT
                db.branch_id,
                dp.product_id,
                dp.product_name,
                rr.available_stock,
                rr.avg_daily_demand,
                rr.lead_time_days,
                rr.reorder_point,
                rr.stock_coverage_days,
                rr.forecast_daily_demand,
                rr.forecast_7_day_demand,
                rr.projected_stock_after_7_days,
                rr.projected_stockout_flag,
                rr.reorder_needed,
                rr.recommended_order_qty,
                rr.priority_level
            FROM reorder_recommendations rr
            JOIN dim_branch db
                ON rr.branch_key = db.branch_key
            JOIN dim_product dp
                ON rr.product_key = dp.product_key
            WHERE rr.recommendation_date = %s
            ORDER BY
                rr.reorder_needed DESC,
                CASE rr.priority_level
                    WHEN 'High' THEN 1
                    WHEN 'Medium' THEN 2
                    WHEN 'Low' THEN 3
                    ELSE 4
                END,
                rr.stock_coverage_days NULLS LAST,
                db.branch_id,
                dp.product_id
            LIMIT 10
            """,
            (recommendation_date,),
        )
        top_rows = cur.fetchall()

    print("\nTop reorder recommendation rows:")
    for row in top_rows:
        (
            branch_id,
            product_id,
            product_name,
            available_stock,
            avg_daily_demand,
            lead_time_days,
            reorder_point,
            stock_coverage_days,
            forecast_daily_demand,
            forecast_7_day_demand,
            projected_stock_after_7_days,
            projected_stockout_flag,
            reorder_needed,
            recommended_order_qty,
            priority_level,
        ) = row
        print(
            f"{branch_id} | {product_id} | {product_name} | "
            f"available={available_stock}, demand={avg_daily_demand}/day, "
            f"lead_time={lead_time_days}d, reorder_point={reorder_point}, "
            f"forecast={forecast_daily_demand}/day, "
            f"7d_demand={forecast_7_day_demand}, "
            f"projected_stock={projected_stock_after_7_days}, "
            f"projected_stockout={projected_stockout_flag}, "
            f"coverage={stock_coverage_days}, needed={reorder_needed}, "
            f"order_qty={recommended_order_qty}, priority={priority_level}"
        )


def main() -> None:
    with connect() as conn:
        run_reorder_points_sql(conn)
        print_reorder_summary(conn)

    print("\nReorder point calculation complete.")


if __name__ == "__main__":
    main()
