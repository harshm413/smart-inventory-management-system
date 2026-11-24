"""
Run the full Inventory Reorder System backend pipeline.

Run from the project root:
    python src/run_pipeline.py

This does not start the Streamlit dashboard. Start it separately with:
    streamlit run app.py
"""

from __future__ import annotations

from validate_data import validate_all_files, print_summary
from load_staging import ensure_database_exists, create_schema, load_staging_tables, print_staging_counts
from transform_to_warehouse import run_transform_sql, print_table_counts
from refresh_inventory_snapshot import run_snapshot_sql, print_snapshot_counts
from calculate_sales_velocity import run_sales_velocity_sql, print_sales_velocity_summary
from calculate_reorder_points import run_reorder_points_sql, print_reorder_summary
from detect_stockout_overstock import run_detection_sql, print_detection_counts
from generate_reorder_report import get_report_date, load_report_data, build_report, write_report
from db import connect


def main() -> None:
    print("1. Validating CSV files")
    validation_results = validate_all_files()
    print_summary(validation_results)

    print("\n2. Creating database and loading staging tables")
    ensure_database_exists()
    create_schema()
    load_staging_tables()
    print_staging_counts()

    with connect() as conn:
        print("\n3. Transforming staging data into warehouse tables")
        run_transform_sql(conn)
        print_table_counts(conn)

        print("\n4. Refreshing inventory snapshot")
        run_snapshot_sql(conn)
        print_snapshot_counts(conn)

        print("\n5. Calculating sales velocity")
        run_sales_velocity_sql(conn)
        print_sales_velocity_summary(conn)

        print("\n6. Calculating reorder points")
        run_reorder_points_sql(conn)
        print_reorder_summary(conn)

        print("\n7. Creating stockout and overstock detection views")
        run_detection_sql(conn)
        print_detection_counts(conn)

        print("\n8. Generating Markdown reorder report")
        report_date = get_report_date(conn)
        report_data = load_report_data(conn)

    report_text = build_report(report_date, report_data)
    report_path = write_report(report_date, report_text)
    print(f"Generated {report_path}")

    print("\nPipeline complete.")


if __name__ == "__main__":
    main()
