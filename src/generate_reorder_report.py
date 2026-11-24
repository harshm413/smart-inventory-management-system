"""
Generate a daily reorder recommendation report.

Run from the project root:
    python src/generate_reorder_report.py

Before running:
    1. Load staging data with src/load_staging.py.
    2. Transform warehouse data with src/transform_to_warehouse.py.
    3. Refresh inventory snapshot with src/refresh_inventory_snapshot.py.
    4. Calculate sales velocity with src/calculate_sales_velocity.py.
    5. Calculate reorder points with src/calculate_reorder_points.py.
    6. Create stockout and overstock views with src/detect_stockout_overstock.py.
    7. Make sure DB_* values are set in .env.

Output:
    reports/reorder_report_YYYY_MM_DD.md
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from psycopg2.extras import RealDictCursor
from db import PROJECT_ROOT, connect


REPORTS_DIR = PROJECT_ROOT / "reports"


def fetch_one(conn, query: str) -> dict[str, Any] | None:
    """Run a query that returns one row."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query)
        row = cur.fetchone()
    return dict(row) if row else None


def fetch_all(conn, query: str) -> list[dict[str, Any]]:
    """Run a query that returns many rows."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query)
        rows = cur.fetchall()
    return [dict(row) for row in rows]


def money(value: Any) -> str:
    """Format money values for the report."""
    if value is None:
        value = 0
    return f"{float(value):,.2f}"


def number(value: Any) -> str:
    """Format whole numbers for the report."""
    if value is None:
        value = 0
    return f"{int(value):,}"


def decimal(value: Any) -> str:
    """Format decimal values without making the report too noisy."""
    if value is None:
        return "N/A"
    return f"{float(value):,.2f}"


def markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    """Build a simple Markdown table."""
    if not rows:
        return "_No records found._\n"

    header_line = "| " + " | ".join(headers) + " |"
    separator_line = "| " + " | ".join("---" for _ in headers) + " |"
    row_lines = ["| " + " | ".join(str(value) for value in row) + " |" for row in rows]
    return "\n".join([header_line, separator_line, *row_lines]) + "\n"


def get_report_date(conn) -> date:
    """Use the latest recommendation date as the business report date."""
    row = fetch_one(
        conn,
        """
        SELECT MAX(recommendation_date) AS report_date
        FROM reorder_recommendations
        """,
    )
    if row and row["report_date"]:
        return row["report_date"]
    return date.today()


def load_report_data(conn) -> dict[str, Any]:
    """Load all data needed by the Markdown report."""
    return {
        "reorder_summary": fetch_one(
            conn,
            """
            SELECT *
            FROM vw_reorder_summary
            """,
        ),
        "stockout_summary": fetch_one(
            conn,
            """
            SELECT *
            FROM vw_stockout_risk_kpis
            """,
        ),
        "overstock_summary": fetch_one(
            conn,
            """
            SELECT *
            FROM vw_overstock_risk_kpis
            """,
        ),
        "products_needing_reorder": fetch_all(
            conn,
            """
            SELECT
                branch_id,
                branch_name,
                product_id,
                product_name,
                supplier_name,
                available_stock,
                stock_coverage_days,
                forecast_daily_demand,
                forecast_7_day_demand,
                projected_stock_after_7_days,
                projected_stockout_flag,
                lead_time_days,
                reorder_point,
                recommended_order_qty,
                estimated_reorder_cost,
                priority_level
            FROM vw_latest_reorder_recommendations
            WHERE reorder_needed
            ORDER BY
                CASE priority_level
                    WHEN 'High' THEN 1
                    WHEN 'Medium' THEN 2
                    WHEN 'Low' THEN 3
                    ELSE 4
                END,
                stock_coverage_days NULLS LAST,
                branch_id,
                product_id
            """,
        ),
        "high_stockout_risks": fetch_all(
            conn,
            """
            SELECT
                branch_id,
                branch_name,
                product_id,
                product_name,
                supplier_name,
                available_stock,
                avg_daily_demand_7d,
                lead_time_days,
                stock_coverage_days,
                recommended_order_qty
            FROM vw_high_stockout_risk_products
            WHERE stockout_risk_level = 'High Risk'
            ORDER BY
                stock_coverage_days NULLS LAST,
                branch_id,
                product_id
            """,
        ),
        "overstock_products": fetch_all(
            conn,
            """
            SELECT
                branch_id,
                branch_name,
                product_id,
                product_name,
                supplier_name,
                available_stock,
                avg_daily_demand_30d,
                stock_coverage_days
            FROM vw_overstock_products
            ORDER BY
                stock_coverage_days DESC,
                available_stock DESC,
                branch_id,
                product_id
            """,
        ),
        "dead_stock_products": fetch_all(
            conn,
            """
            SELECT
                branch_id,
                branch_name,
                product_id,
                product_name,
                supplier_name,
                available_stock,
                avg_daily_demand_30d
            FROM vw_dead_stock_products
            ORDER BY
                available_stock DESC,
                branch_id,
                product_id
            """,
        ),
        "supplier_purchase_list": fetch_all(
            conn,
            """
            SELECT
                supplier_id,
                supplier_name,
                reorder_quantity_by_supplier,
                estimated_purchase_cost_by_supplier,
                avg_lead_time_days,
                supplier_lead_time_impact
            FROM vw_supplier_kpis
            WHERE reorder_quantity_by_supplier > 0
            ORDER BY
                estimated_purchase_cost_by_supplier DESC,
                supplier_name
            """,
        ),
    }


def build_executive_summary(data: dict[str, Any]) -> str:
    """Create the short summary section at the top of the report."""
    reorder = data["reorder_summary"] or {}
    stockout = data["stockout_summary"] or {}
    overstock = data["overstock_summary"] or {}

    return "\n".join(
        [
            f"- Products needing reorder: {number(reorder.get('products_needing_reorder'))}",
            f"- High priority reorder items: {number(reorder.get('high_priority_reorder_count'))}",
            f"- Medium priority reorder items: {number(reorder.get('medium_priority_reorder_count'))}",
            f"- Estimated reorder cost: {money(reorder.get('estimated_reorder_cost'))}",
            f"- High stockout risk products: {number(stockout.get('products_at_high_stockout_risk'))}",
            f"- Overstocked products: {number(overstock.get('overstocked_products'))}",
            f"- Dead stock products: {number(overstock.get('dead_stock_products'))}",
            f"- Estimated money stuck in overstock: {money(overstock.get('estimated_money_stuck_in_overstock'))}",
        ]
    )


def build_products_needing_reorder(rows: list[dict[str, Any]]) -> str:
    table_rows = [
        [
            row["branch_id"],
            row["product_id"],
            row["product_name"],
            row["supplier_name"],
            number(row["available_stock"]),
            decimal(row["stock_coverage_days"]),
            decimal(row["forecast_daily_demand"]),
            decimal(row["forecast_7_day_demand"]),
            decimal(row["projected_stock_after_7_days"]),
            row["projected_stockout_flag"],
            number(row["lead_time_days"]),
            number(row["recommended_order_qty"]),
            money(row["estimated_reorder_cost"]),
            row["priority_level"],
        ]
        for row in rows
    ]
    return markdown_table(
        [
            "Branch",
            "Product",
            "Name",
            "Supplier",
            "Available",
            "Coverage Days",
            "Forecast / Day",
            "7-Day Forecast",
            "Stock After 7 Days",
            "7-Day Stockout",
            "Lead Time",
            "Order Qty",
            "Cost",
            "Priority",
        ],
        table_rows,
    )


def build_high_stockout_risks(rows: list[dict[str, Any]]) -> str:
    table_rows = [
        [
            row["branch_id"],
            row["product_id"],
            row["product_name"],
            number(row["available_stock"]),
            decimal(row["avg_daily_demand_7d"]),
            number(row["lead_time_days"]),
            decimal(row["stock_coverage_days"]),
            number(row["recommended_order_qty"]),
        ]
        for row in rows
    ]
    return markdown_table(
        [
            "Branch",
            "Product",
            "Name",
            "Available",
            "7-Day Demand",
            "Lead Time",
            "Coverage Days",
            "Order Qty",
        ],
        table_rows,
    )


def build_overstock_products(rows: list[dict[str, Any]]) -> str:
    table_rows = [
        [
            row["branch_id"],
            row["product_id"],
            row["product_name"],
            row["supplier_name"],
            number(row["available_stock"]),
            decimal(row["avg_daily_demand_30d"]),
            decimal(row["stock_coverage_days"]),
        ]
        for row in rows
    ]
    return markdown_table(
        ["Branch", "Product", "Name", "Supplier", "Available", "30-Day Demand", "Coverage Days"],
        table_rows,
    )


def build_dead_stock_products(rows: list[dict[str, Any]]) -> str:
    table_rows = [
        [
            row["branch_id"],
            row["product_id"],
            row["product_name"],
            row["supplier_name"],
            number(row["available_stock"]),
            decimal(row["avg_daily_demand_30d"]),
        ]
        for row in rows
    ]
    return markdown_table(
        ["Branch", "Product", "Name", "Supplier", "Available", "30-Day Demand"],
        table_rows,
    )


def build_supplier_purchase_list(rows: list[dict[str, Any]]) -> str:
    table_rows = [
        [
            row["supplier_id"],
            row["supplier_name"],
            number(row["reorder_quantity_by_supplier"]),
            money(row["estimated_purchase_cost_by_supplier"]),
            decimal(row["avg_lead_time_days"]),
            row["supplier_lead_time_impact"],
        ]
        for row in rows
    ]
    return markdown_table(
        ["Supplier", "Name", "Order Qty", "Purchase Cost", "Avg Lead Time", "Lead Time Impact"],
        table_rows,
    )


def build_business_explanation(data: dict[str, Any]) -> str:
    """Create simple natural-language explanations from the report data."""
    explanations: list[str] = []

    high_risk = data["high_stockout_risks"][:3]
    for row in high_risk:
        explanations.append(
            f"- {row['product_name']} at {row['branch_name']} may run out in "
            f"{decimal(row['stock_coverage_days'])} days, but supplier lead time is "
            f"{number(row['lead_time_days'])} days. Reorder immediately."
        )

    overstock = data["overstock_products"][:3]
    for row in overstock:
        explanations.append(
            f"- {row['product_name']} at {row['branch_name']} has enough stock for "
            f"{decimal(row['stock_coverage_days'])} days. Avoid buying more this month."
        )

    dead_stock = data["dead_stock_products"][:3]
    for row in dead_stock:
        explanations.append(
            f"- {row['product_name']} at {row['branch_name']} has not sold in 30 days "
            f"but still has {number(row['available_stock'])} units in stock. "
            "Consider promotion or discount."
        )

    if not explanations:
        explanations.append("- No urgent reorder, overstock, or dead stock action was found today.")

    return "\n".join(explanations)


def build_report(report_date: date, data: dict[str, Any]) -> str:
    """Combine all report sections into one Markdown document."""
    reorder = data["reorder_summary"] or {}

    return f"""# Daily Reorder Recommendation Report

## 1. Report Date

{report_date}

## 2. Executive Summary

{build_executive_summary(data)}

## 3. Products Needing Reorder Today

{build_products_needing_reorder(data["products_needing_reorder"])}

## 4. High Priority Stockout Risks

{build_high_stockout_risks(data["high_stockout_risks"])}

## 5. Overstock Products

{build_overstock_products(data["overstock_products"])}

## 6. Dead Stock Products

{build_dead_stock_products(data["dead_stock_products"])}

## 7. Recommended Order Quantities

Use the order quantity column in the reorder table. It already considers the reorder point and supplier minimum order quantity.

{build_products_needing_reorder(data["products_needing_reorder"])}

## 8. Estimated Reorder Cost

Total estimated reorder cost: **{money(reorder.get("estimated_reorder_cost"))}**

This is calculated as recommended order quantity multiplied by product unit cost.

## 9. Supplier-wise Purchase List

{build_supplier_purchase_list(data["supplier_purchase_list"])}

## 10. Simple Business Explanation

{build_business_explanation(data)}
"""


def write_report(report_date: date, report_text: str) -> Path:
    """Write the Markdown report to the reports folder."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"reorder_report_{report_date.strftime('%Y_%m_%d')}.md"
    report_path = REPORTS_DIR / filename
    report_path.write_text(report_text, encoding="utf-8")
    return report_path


def main() -> None:
    with connect() as conn:
        report_date = get_report_date(conn)
        data = load_report_data(conn)

    report_text = build_report(report_date, data)
    report_path = write_report(report_date, report_text)

    print(f"Generated {report_path.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
