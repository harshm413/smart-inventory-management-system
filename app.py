"""
Streamlit dashboard for the Inventory Reorder System.

Run from the project root:
    streamlit run app.py

Before running:
    1. Run the PostgreSQL pipeline scripts.
    2. Make sure DB_* values are set in .env.
"""

from __future__ import annotations

from typing import Any

import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
import streamlit as st

from src.db import connection_params


def run_query(query: str) -> pd.DataFrame:
    """Run one SQL query and return the result as a DataFrame."""
    with psycopg2.connect(**connection_params()) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            rows = cur.fetchall()
    return pd.DataFrame([dict(row) for row in rows])


@st.cache_data(show_spinner=False)
def load_dashboard_data() -> dict[str, pd.DataFrame]:
    """Load all dashboard data from PostgreSQL views."""
    return {
        "inventory": run_query("SELECT * FROM vw_latest_inventory_snapshot"),
        "reorder": run_query("SELECT * FROM vw_latest_reorder_recommendations"),
        "stockout": run_query("SELECT * FROM vw_high_stockout_risk_products"),
        "overstock": run_query("SELECT * FROM vw_overstock_products"),
        "dead_stock": run_query("SELECT * FROM vw_dead_stock_products"),
        "slow_moving": run_query("SELECT * FROM vw_slow_moving_products"),
        "supplier": run_query("SELECT * FROM vw_supplier_kpis"),
        "branch": run_query("SELECT * FROM vw_branch_kpis"),
    }


def money(value: Any) -> str:
    """Format money values for KPI cards and tables."""
    if pd.isna(value):
        value = 0
    return f"{float(value):,.2f}"


def clean_number(value: Any) -> str:
    """Format count values for KPI cards."""
    if pd.isna(value):
        value = 0
    return f"{int(value):,}"


def unique_values(dataframes: list[pd.DataFrame], column: str) -> list[str]:
    """Collect sorted filter values from every DataFrame that has the column."""
    values: set[str] = set()
    for df in dataframes:
        if column in df.columns and not df.empty:
            values.update(df[column].dropna().astype(str).tolist())
    return sorted(values)


def apply_filters(
    df: pd.DataFrame,
    branches: list[str],
    categories: list[str],
    suppliers: list[str],
    priorities: list[str],
) -> pd.DataFrame:
    """Apply sidebar filters only when the DataFrame has the matching column."""
    filtered = df.copy()

    if branches and "branch_name" in filtered.columns:
        filtered = filtered[filtered["branch_name"].isin(branches)]
    if categories and "category" in filtered.columns:
        filtered = filtered[filtered["category"].isin(categories)]
    if suppliers and "supplier_name" in filtered.columns:
        filtered = filtered[filtered["supplier_name"].isin(suppliers)]
    if priorities and "priority_level" in filtered.columns:
        filtered = filtered[filtered["priority_level"].isin(priorities)]

    return filtered


def show_bar_chart(df: pd.DataFrame, label_column: str, value_column: str, title: str) -> None:
    """Show a simple Streamlit bar chart, or a message if there is no data."""
    st.subheader(title)
    if df.empty:
        st.info("No data for this chart.")
        return

    chart_df = df[[label_column, value_column]].copy()
    chart_df[value_column] = pd.to_numeric(chart_df[value_column], errors="coerce").fillna(0)
    chart_df = chart_df.sort_values(value_column, ascending=False)
    chart_df = chart_df.set_index(label_column)
    st.bar_chart(chart_df)


def show_table(df: pd.DataFrame, columns: list[str], title: str) -> None:
    """Show a clean table with selected columns."""
    st.subheader(title)
    if df.empty:
        st.info("No records found.")
        return

    visible_columns = [column for column in columns if column in df.columns]
    st.dataframe(df[visible_columns], use_container_width=True, hide_index=True)


def main() -> None:
    st.set_page_config(page_title="Inventory Reorder Dashboard", layout="wide")
    st.title("Inventory Reorder Dashboard")

    try:
        data = load_dashboard_data()
    except Exception as exc:
        st.error("Could not load dashboard data from PostgreSQL.")
        st.caption(str(exc))
        st.stop()

    inventory_df = data["inventory"]
    reorder_df = data["reorder"]
    stockout_df = data["stockout"]
    overstock_df = data["overstock"]
    dead_stock_df = data["dead_stock"]
    slow_moving_df = data["slow_moving"]

    all_detail_frames = [inventory_df, reorder_df, stockout_df, overstock_df, dead_stock_df, slow_moving_df]

    with st.sidebar:
        st.header("Filters")

        branch_options = unique_values(all_detail_frames, "branch_name")
        category_options = unique_values(all_detail_frames, "category")
        supplier_options = unique_values(all_detail_frames, "supplier_name")
        priority_options = unique_values([reorder_df], "priority_level")

        selected_branches = st.multiselect("Branch", branch_options)
        selected_categories = st.multiselect("Category", category_options)
        selected_suppliers = st.multiselect("Supplier", supplier_options)
        selected_priorities = st.multiselect("Priority Level", priority_options)

        if st.button("Refresh data"):
            st.cache_data.clear()
            st.rerun()

    inventory_filtered = apply_filters(
        inventory_df, selected_branches, selected_categories, selected_suppliers, selected_priorities
    )
    reorder_filtered = apply_filters(
        reorder_df, selected_branches, selected_categories, selected_suppliers, selected_priorities
    )
    stockout_filtered = apply_filters(
        stockout_df, selected_branches, selected_categories, selected_suppliers, selected_priorities
    )
    overstock_filtered = apply_filters(
        overstock_df, selected_branches, selected_categories, selected_suppliers, selected_priorities
    )
    dead_stock_filtered = apply_filters(
        dead_stock_df, selected_branches, selected_categories, selected_suppliers, selected_priorities
    )
    slow_moving_filtered = apply_filters(
        slow_moving_df, selected_branches, selected_categories, selected_suppliers, selected_priorities
    )

    # KPI cards are calculated after filters, so they match the current screen.
    reorder_needed = (
        reorder_filtered[reorder_filtered["reorder_needed"].fillna(False)]
        if "reorder_needed" in reorder_filtered.columns and not reorder_filtered.empty
        else reorder_filtered
    )
    high_stockout = (
        stockout_filtered[stockout_filtered["stockout_risk_level"] == "High Risk"]
        if "stockout_risk_level" in stockout_filtered.columns
        else stockout_filtered
    )

    total_inventory_value = inventory_filtered["inventory_value"].sum() if "inventory_value" in inventory_filtered else 0
    estimated_reorder_cost = (
        reorder_needed["estimated_reorder_cost"].sum() if "estimated_reorder_cost" in reorder_needed else 0
    )

    st.header("Overview")
    kpi_cols = st.columns(5)
    kpi_cols[0].metric("Total Inventory Value", money(total_inventory_value))
    kpi_cols[1].metric("Products Needing Reorder", clean_number(len(reorder_needed)))
    kpi_cols[2].metric("High Stockout Risk Products", clean_number(len(high_stockout)))
    kpi_cols[3].metric("Overstock Products", clean_number(len(overstock_filtered)))
    kpi_cols[4].metric("Estimated Reorder Cost", money(estimated_reorder_cost))

    if "projected_stockout_flag" in reorder_filtered.columns:
        projected_stockouts = reorder_filtered[reorder_filtered["projected_stockout_flag"].fillna(False)]
        st.caption(
            f"Forecast note: {clean_number(len(projected_stockouts))} products are projected to run out within 7 days."
        )

    st.header("Charts")
    chart_left, chart_right = st.columns(2)

    stockout_by_branch = (
        stockout_filtered.groupby("branch_name", as_index=False)
        .size()
        .rename(columns={"size": "stockout_risk_count"})
        if "branch_name" in stockout_filtered.columns and not stockout_filtered.empty
        else pd.DataFrame(columns=["branch_name", "stockout_risk_count"])
    )
    with chart_left:
        show_bar_chart(stockout_by_branch, "branch_name", "stockout_risk_count", "Stockout Risk by Branch")

    reorder_cost_by_supplier = (
        reorder_needed.groupby("supplier_name", as_index=False)["estimated_reorder_cost"].sum()
        if "supplier_name" in reorder_needed.columns and not reorder_needed.empty
        else pd.DataFrame(columns=["supplier_name", "estimated_reorder_cost"])
    )
    with chart_right:
        show_bar_chart(reorder_cost_by_supplier, "supplier_name", "estimated_reorder_cost", "Reorder Cost by Supplier")

    chart_left, chart_right = st.columns(2)

    inventory_value_by_category = (
        inventory_filtered.groupby("category", as_index=False)["inventory_value"].sum()
        if "category" in inventory_filtered.columns and not inventory_filtered.empty
        else pd.DataFrame(columns=["category", "inventory_value"])
    )
    with chart_left:
        show_bar_chart(inventory_value_by_category, "category", "inventory_value", "Inventory Value by Category")

    top_reorder_products = (
        reorder_needed.groupby("product_name", as_index=False)["recommended_order_qty"]
        .sum()
        .sort_values("recommended_order_qty", ascending=False)
        .head(10)
        if "product_name" in reorder_needed.columns and not reorder_needed.empty
        else pd.DataFrame(columns=["product_name", "recommended_order_qty"])
    )
    with chart_right:
        show_bar_chart(top_reorder_products, "product_name", "recommended_order_qty", "Top Products Needing Reorder")

    overstock_value = reorder_filtered[reorder_filtered["stock_coverage_days"] > 60].copy()
    if not overstock_value.empty:
        overstock_value["overstock_value"] = overstock_value["available_stock"] * overstock_value["unit_cost"]
        overstock_value_by_category = overstock_value.groupby("category", as_index=False)["overstock_value"].sum()
    else:
        overstock_value_by_category = pd.DataFrame(columns=["category", "overstock_value"])

    show_bar_chart(overstock_value_by_category, "category", "overstock_value", "Overstock Value by Category")

    st.header("Reorder Recommendations")
    show_table(
        reorder_needed,
        [
            "branch_name",
            "product_id",
            "product_name",
            "category",
            "available_stock",
            "avg_daily_demand",
            "forecast_daily_demand",
            "forecast_7_day_demand",
            "projected_stock_after_7_days",
            "projected_stockout_flag",
            "reorder_point",
            "recommended_order_qty",
            "estimated_reorder_cost",
            "priority_level",
        ],
        "Products Needing Reorder",
    )

    st.header("Stockout Risk")
    show_table(
        stockout_filtered,
        [
            "branch_name",
            "product_id",
            "product_name",
            "available_stock",
            "avg_daily_demand_7d",
            "lead_time_days",
            "stock_coverage_days",
            "stockout_risk_level",
            "recommended_order_qty",
        ],
        "High-risk Products and Lead Time Comparison",
    )

    st.header("Overstock / Dead Stock")
    overstock_col, dead_stock_col = st.columns(2)
    with overstock_col:
        show_table(
            slow_moving_filtered,
            [
                "branch_name",
                "product_id",
                "product_name",
                "category",
                "available_stock",
                "avg_daily_demand_30d",
                "stock_coverage_days",
            ],
            "Slow-moving Products",
        )
    with dead_stock_col:
        show_table(
            dead_stock_filtered,
            [
                "branch_name",
                "product_id",
                "product_name",
                "category",
                "available_stock",
                "avg_daily_demand_30d",
                "stock_coverage_days",
            ],
            "Dead Stock Products",
        )

    show_table(
        overstock_filtered,
        [
            "branch_name",
            "product_id",
            "product_name",
            "category",
            "supplier_name",
            "available_stock",
            "avg_daily_demand_30d",
            "stock_coverage_days",
        ],
        "Overstock Products",
    )

    st.header("Supplier Purchase Plan")
    if not reorder_needed.empty:
        supplier_purchase_plan = (
            reorder_needed.groupby("supplier_name", as_index=False)
            .agg(
                products_to_reorder=("product_id", "nunique"),
                total_quantity=("recommended_order_qty", "sum"),
                estimated_cost=("estimated_reorder_cost", "sum"),
                avg_lead_time_days=("lead_time_days", "mean"),
                high_priority_products=("priority_level", lambda values: (values == "High").sum()),
            )
            .sort_values("estimated_cost", ascending=False)
        )
        supplier_purchase_plan["lead_time_impact"] = supplier_purchase_plan["avg_lead_time_days"].apply(
            lambda days: "High" if days >= 10 else "Medium" if days >= 5 else "Low"
        )
    else:
        supplier_purchase_plan = pd.DataFrame(
            columns=[
                "supplier_name",
                "products_to_reorder",
                "total_quantity",
                "estimated_cost",
                "avg_lead_time_days",
                "lead_time_impact",
                "high_priority_products",
            ]
        )

    show_table(
        supplier_purchase_plan,
        [
            "supplier_name",
            "products_to_reorder",
            "total_quantity",
            "estimated_cost",
            "avg_lead_time_days",
            "lead_time_impact",
            "high_priority_products",
        ],
        "Suppliers Needing Purchase Orders",
    )

    st.header("Branch Analysis")
    branch_inventory_value = (
        inventory_filtered.groupby(["branch_name", "city"], as_index=False)["inventory_value"].sum()
        if {"branch_name", "city", "inventory_value"}.issubset(inventory_filtered.columns)
        and not inventory_filtered.empty
        else pd.DataFrame(columns=["branch_name", "city", "inventory_value"])
    )
    branch_stockout_count = (
        stockout_filtered.groupby("branch_name", as_index=False)
        .size()
        .rename(columns={"size": "stockout_risk_count"})
        if "branch_name" in stockout_filtered.columns and not stockout_filtered.empty
        else pd.DataFrame(columns=["branch_name", "stockout_risk_count"])
    )
    branch_reorder_cost = (
        reorder_needed.groupby("branch_name", as_index=False)
        .agg(
            reorder_cost=("estimated_reorder_cost", "sum"),
            products_needing_reorder=("product_id", "nunique"),
        )
        if "branch_name" in reorder_needed.columns and not reorder_needed.empty
        else pd.DataFrame(columns=["branch_name", "reorder_cost", "products_needing_reorder"])
    )

    branch_analysis = branch_inventory_value.merge(branch_stockout_count, on="branch_name", how="outer")
    branch_analysis = branch_analysis.merge(branch_reorder_cost, on="branch_name", how="outer")

    # Fill numeric KPI columns one by one to avoid pandas object downcasting warnings.
    for column in [
        "inventory_value",
        "stockout_risk_count",
        "reorder_cost",
        "products_needing_reorder",
    ]:
        if column in branch_analysis.columns:
            branch_analysis[column] = pd.to_numeric(branch_analysis[column], errors="coerce").fillna(0)

    if "city" in branch_analysis.columns:
        branch_analysis["city"] = branch_analysis["city"].fillna("")

    show_table(
        branch_analysis,
        [
            "branch_name",
            "city",
            "inventory_value",
            "stockout_risk_count",
            "reorder_cost",
            "products_needing_reorder",
        ],
        "Branches Needing Attention",
    )


if __name__ == "__main__":
    main()
