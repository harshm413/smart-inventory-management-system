"""
Validate raw CSV files before loading inventory data into PostgreSQL.

Run from the project root:
    python src/validate_data.py

Inputs:
    data/raw/*.csv

Outputs:
    data/processed/*.csv
    data/rejected/*_rejected.csv
    reports/data_validation_report.md
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
REJECTED_DATA_DIR = PROJECT_ROOT / "data" / "rejected"
REPORTS_DIR = PROJECT_ROOT / "reports"

ALLOWED_CATEGORIES = {"Food", "Drinks", "Household", "Personal Care", "Stationery"}
ALLOWED_MOVEMENT_TYPES = {
    "purchase",
    "sale",
    "return",
    "adjustment_in",
    "adjustment_out",
    "damage",
}


def is_blank(series: pd.Series) -> pd.Series:
    """Return True for missing values or empty strings."""
    return series.isna() | series.astype(str).str.strip().eq("")


def to_number(series: pd.Series) -> pd.Series:
    """Convert a column to numbers; invalid values become NaN."""
    return pd.to_numeric(series, errors="coerce")


def valid_date(series: pd.Series) -> pd.Series:
    """Return True when a column can be parsed as a valid date."""
    return pd.to_datetime(series, errors="coerce").notna()


def add_reason(reasons: pd.Series, condition: pd.Series, message: str) -> None:
    """Append a rejection reason for rows where condition is True."""
    condition = condition.fillna(True)
    reasons.loc[condition] = reasons.loc[condition].apply(
        lambda current: message if current == "" else f"{current}; {message}"
    )


def require_columns(df: pd.DataFrame, filename: str, required_columns: list[str]) -> None:
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"{filename} is missing required columns: {missing_columns}")


def split_clean_rejected(df: pd.DataFrame, reasons: pd.Series) -> tuple[pd.DataFrame, pd.DataFrame]:
    rejected_mask = reasons.ne("")
    clean_df = df.loc[~rejected_mask].copy()
    rejected_df = df.loc[rejected_mask].copy()
    rejected_df["rejection_reason"] = reasons.loc[rejected_mask]
    return clean_df, rejected_df


def normalize_dates(df: pd.DataFrame, date_columns: list[str]) -> pd.DataFrame:
    """Standardize valid date columns to YYYY-MM-DD for clean output files."""
    df = df.copy()
    for column in date_columns:
        if column in df.columns:
            df[column] = pd.to_datetime(df[column], errors="coerce").dt.date.astype(str)
    return df


def validate_branches(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    required_columns = ["branch_id", "branch_name", "city", "township", "branch_type"]
    require_columns(df, "branches.csv", required_columns)

    reasons = pd.Series("", index=df.index)
    add_reason(reasons, is_blank(df["branch_id"]), "branch_id is missing")
    add_reason(reasons, is_blank(df["branch_name"]), "branch_name is empty")
    add_reason(
        reasons,
        df.duplicated(subset=["branch_id"], keep=False) & ~is_blank(df["branch_id"]),
        "duplicate branch_id",
    )
    return split_clean_rejected(df, reasons)


def validate_suppliers(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    required_columns = [
        "supplier_id",
        "supplier_name",
        "contact_phone",
        "city",
        "lead_time_days",
        "minimum_order_value",
    ]
    require_columns(df, "suppliers.csv", required_columns)

    reasons = pd.Series("", index=df.index)
    lead_time_days = to_number(df["lead_time_days"])
    minimum_order_value = to_number(df["minimum_order_value"])

    add_reason(reasons, is_blank(df["supplier_id"]), "supplier_id is missing")
    add_reason(reasons, is_blank(df["supplier_name"]), "supplier_name is empty")
    add_reason(reasons, lead_time_days.isna() | (lead_time_days <= 0), "lead_time_days must be greater than 0")
    add_reason(
        reasons,
        minimum_order_value.isna() | (minimum_order_value < 0),
        "minimum_order_value must be greater than or equal to 0",
    )
    add_reason(
        reasons,
        df.duplicated(subset=["supplier_id"], keep=False) & ~is_blank(df["supplier_id"]),
        "duplicate supplier_id",
    )

    clean_df, rejected_df = split_clean_rejected(df, reasons)
    clean_df["lead_time_days"] = to_number(clean_df["lead_time_days"]).astype(int)
    clean_df["minimum_order_value"] = to_number(clean_df["minimum_order_value"])
    return clean_df, rejected_df


def validate_products(df: pd.DataFrame, valid_supplier_ids: set[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    required_columns = [
        "product_id",
        "product_name",
        "category",
        "brand",
        "unit_cost",
        "selling_price",
        "supplier_id",
        "shelf_life_days",
        "min_order_quantity",
    ]
    require_columns(df, "products.csv", required_columns)

    reasons = pd.Series("", index=df.index)
    unit_cost = to_number(df["unit_cost"])
    selling_price = to_number(df["selling_price"])
    min_order_quantity = to_number(df["min_order_quantity"])

    add_reason(reasons, is_blank(df["product_id"]), "product_id is missing")
    add_reason(reasons, is_blank(df["product_name"]), "product_name is empty")
    add_reason(reasons, unit_cost.isna() | (unit_cost < 0), "unit_cost must be greater than or equal to 0")
    add_reason(reasons, selling_price.isna() | (selling_price <= 0), "selling_price must be greater than 0")
    add_reason(reasons, ~df["supplier_id"].isin(valid_supplier_ids), "supplier_id does not exist in suppliers.csv")
    add_reason(
        reasons,
        min_order_quantity.isna() | (min_order_quantity <= 0),
        "min_order_quantity must be greater than 0",
    )
    add_reason(reasons, ~df["category"].isin(ALLOWED_CATEGORIES), "category has inconsistent or invalid spelling")
    add_reason(
        reasons,
        df.duplicated(subset=["product_id"], keep=False) & ~is_blank(df["product_id"]),
        "duplicate product_id",
    )

    clean_df, rejected_df = split_clean_rejected(df, reasons)
    clean_df["unit_cost"] = to_number(clean_df["unit_cost"])
    clean_df["selling_price"] = to_number(clean_df["selling_price"])
    clean_df["shelf_life_days"] = to_number(clean_df["shelf_life_days"])
    clean_df["min_order_quantity"] = to_number(clean_df["min_order_quantity"]).astype(int)
    return clean_df, rejected_df


def validate_sales_history(
    df: pd.DataFrame, valid_branch_ids: set[str], valid_product_ids: set[str]
) -> tuple[pd.DataFrame, pd.DataFrame]:
    required_columns = ["sale_id", "sale_date", "branch_id", "product_id", "quantity_sold", "unit_price"]
    require_columns(df, "sales_history.csv", required_columns)

    reasons = pd.Series("", index=df.index)
    quantity_sold = to_number(df["quantity_sold"])
    unit_price = to_number(df["unit_price"])

    add_reason(reasons, is_blank(df["sale_id"]), "sale_id is missing")
    add_reason(reasons, ~valid_date(df["sale_date"]), "sale_date is not a valid date")
    add_reason(reasons, ~df["branch_id"].isin(valid_branch_ids), "branch_id does not exist in branches.csv")
    add_reason(reasons, ~df["product_id"].isin(valid_product_ids), "product_id does not exist in products.csv")
    add_reason(reasons, quantity_sold.isna() | (quantity_sold <= 0), "quantity_sold must be greater than 0")
    add_reason(reasons, unit_price.isna() | (unit_price < 0), "unit_price must be greater than or equal to 0")
    add_reason(
        reasons,
        df.duplicated(subset=["sale_id"], keep=False) & ~is_blank(df["sale_id"]),
        "duplicate sale_id",
    )

    clean_df, rejected_df = split_clean_rejected(df, reasons)
    clean_df = normalize_dates(clean_df, ["sale_date"])
    clean_df["quantity_sold"] = to_number(clean_df["quantity_sold"]).astype(int)
    clean_df["unit_price"] = to_number(clean_df["unit_price"])
    return clean_df, rejected_df


def validate_stock_movements(
    df: pd.DataFrame, valid_branch_ids: set[str], valid_product_ids: set[str]
) -> tuple[pd.DataFrame, pd.DataFrame]:
    required_columns = [
        "movement_id",
        "movement_date",
        "branch_id",
        "product_id",
        "movement_type",
        "quantity",
        "reference_note",
    ]
    require_columns(df, "stock_movements.csv", required_columns)

    reasons = pd.Series("", index=df.index)
    quantity = to_number(df["quantity"])

    add_reason(reasons, is_blank(df["movement_id"]), "movement_id is missing")
    add_reason(reasons, ~valid_date(df["movement_date"]), "movement_date is not a valid date")
    add_reason(reasons, ~df["branch_id"].isin(valid_branch_ids), "branch_id does not exist in branches.csv")
    add_reason(reasons, ~df["product_id"].isin(valid_product_ids), "product_id does not exist in products.csv")
    add_reason(reasons, ~df["movement_type"].isin(ALLOWED_MOVEMENT_TYPES), "movement_type is not allowed")
    add_reason(reasons, quantity.isna() | (quantity <= 0), "quantity must be greater than 0")
    add_reason(
        reasons,
        df.duplicated(subset=["movement_id"], keep=False) & ~is_blank(df["movement_id"]),
        "duplicate movement_id",
    )

    clean_df, rejected_df = split_clean_rejected(df, reasons)
    clean_df = normalize_dates(clean_df, ["movement_date"])
    clean_df["quantity"] = to_number(clean_df["quantity"]).astype(int)
    return clean_df, rejected_df


def validate_current_inventory(
    df: pd.DataFrame, valid_branch_ids: set[str], valid_product_ids: set[str]
) -> tuple[pd.DataFrame, pd.DataFrame]:
    required_columns = ["inventory_date", "branch_id", "product_id", "current_stock", "reserved_stock"]
    require_columns(df, "current_inventory.csv", required_columns)

    reasons = pd.Series("", index=df.index)
    current_stock = to_number(df["current_stock"])
    reserved_stock = to_number(df["reserved_stock"])

    add_reason(reasons, ~valid_date(df["inventory_date"]), "inventory_date is not a valid date")
    add_reason(reasons, ~df["branch_id"].isin(valid_branch_ids), "branch_id does not exist in branches.csv")
    add_reason(reasons, ~df["product_id"].isin(valid_product_ids), "product_id does not exist in products.csv")
    add_reason(
        reasons,
        current_stock.isna() | (current_stock < 0),
        "current_stock must be greater than or equal to 0",
    )
    add_reason(
        reasons,
        reserved_stock.isna() | (reserved_stock < 0),
        "reserved_stock must be greater than or equal to 0",
    )
    add_reason(reasons, reserved_stock > current_stock, "reserved_stock cannot be greater than current_stock")
    add_reason(
        reasons,
        df.duplicated(subset=["inventory_date", "branch_id", "product_id"], keep=False),
        "duplicate inventory snapshot for date, branch, and product",
    )

    clean_df, rejected_df = split_clean_rejected(df, reasons)
    clean_df = normalize_dates(clean_df, ["inventory_date"])
    clean_df["current_stock"] = to_number(clean_df["current_stock"]).astype(int)
    clean_df["reserved_stock"] = to_number(clean_df["reserved_stock"]).astype(int)
    return clean_df, rejected_df


def read_raw_csv(filename: str) -> pd.DataFrame:
    path = RAW_DATA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Missing input file: {path}")
    return pd.read_csv(path)


def write_output(filename: str, clean_df: pd.DataFrame, rejected_df: pd.DataFrame) -> None:
    clean_path = PROCESSED_DATA_DIR / filename
    rejected_path = REJECTED_DATA_DIR / filename.replace(".csv", "_rejected.csv")

    clean_df.to_csv(clean_path, index=False)
    rejected_df.to_csv(rejected_path, index=False)


def rejection_summary(rejected_df: pd.DataFrame) -> dict[str, int]:
    summary: dict[str, int] = {}
    if rejected_df.empty:
        return summary

    for reason_text in rejected_df["rejection_reason"]:
        for reason in str(reason_text).split("; "):
            summary[reason] = summary.get(reason, 0) + 1
    return summary


def build_report(results: dict[str, dict[str, object]]) -> str:
    lines = [
        "# Data Validation Report",
        "",
        "This report summarizes validation results for raw Inventory Reorder System CSV files.",
        "",
        "Clean records are saved in `data/processed/`.",
        "",
        "Rejected records are saved in `data/rejected/` with a `rejection_reason` column.",
        "",
        "## Summary",
        "",
        "| File | Raw Rows | Clean Rows | Rejected Rows |",
        "|---|---:|---:|---:|",
    ]

    total_raw = 0
    total_clean = 0
    total_rejected = 0
    for filename, result in results.items():
        raw_rows = int(result["raw_rows"])
        clean_rows = int(result["clean_rows"])
        rejected_rows = int(result["rejected_rows"])
        total_raw += raw_rows
        total_clean += clean_rows
        total_rejected += rejected_rows
        lines.append(f"| `{filename}` | {raw_rows:,} | {clean_rows:,} | {rejected_rows:,} |")

    lines.extend(
        [
            f"| **Total** | **{total_raw:,}** | **{total_clean:,}** | **{total_rejected:,}** |",
            "",
            "## Rejection Details",
            "",
        ]
    )

    for filename, result in results.items():
        lines.append(f"### `{filename}`")
        lines.append("")
        reason_counts = result["reason_counts"]
        if not reason_counts:
            lines.append("No rejected records.")
            lines.append("")
            continue

        lines.append("| Rejection Reason | Count |")
        lines.append("|---|---:|")
        for reason, count in sorted(reason_counts.items()):
            lines.append(f"| {reason} | {count:,} |")
        lines.append("")

    lines.extend(
        [
            "## Business Meaning",
            "",
            "Rejected records are rows that should not be loaded into PostgreSQL yet.",
            "",
            "In a real inventory system, rejected records protect the business from wrong reorder advice. "
            "For example, a sale with an invalid product ID cannot be connected to product cost or supplier lead time. "
            "A negative stock value can make the system think a product is more urgent than it really is. "
            "An invalid movement type can break stock movement analysis.",
            "",
        ]
    )
    return "\n".join(lines)


def validate_all_files() -> dict[str, dict[str, object]]:
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    REJECTED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    branches_raw = read_raw_csv("branches.csv")
    suppliers_raw = read_raw_csv("suppliers.csv")
    products_raw = read_raw_csv("products.csv")
    sales_raw = read_raw_csv("sales_history.csv")
    stock_movements_raw = read_raw_csv("stock_movements.csv")
    current_inventory_raw = read_raw_csv("current_inventory.csv")

    results: dict[str, dict[str, object]] = {}

    branches_clean, branches_rejected = validate_branches(branches_raw)
    valid_branch_ids = set(branches_clean["branch_id"].astype(str))
    write_output("branches.csv", branches_clean, branches_rejected)
    results["branches.csv"] = {
        "raw_rows": len(branches_raw),
        "clean_rows": len(branches_clean),
        "rejected_rows": len(branches_rejected),
        "reason_counts": rejection_summary(branches_rejected),
    }

    suppliers_clean, suppliers_rejected = validate_suppliers(suppliers_raw)
    valid_supplier_ids = set(suppliers_clean["supplier_id"].astype(str))
    write_output("suppliers.csv", suppliers_clean, suppliers_rejected)
    results["suppliers.csv"] = {
        "raw_rows": len(suppliers_raw),
        "clean_rows": len(suppliers_clean),
        "rejected_rows": len(suppliers_rejected),
        "reason_counts": rejection_summary(suppliers_rejected),
    }

    products_clean, products_rejected = validate_products(products_raw, valid_supplier_ids)
    valid_product_ids = set(products_clean["product_id"].astype(str))
    write_output("products.csv", products_clean, products_rejected)
    results["products.csv"] = {
        "raw_rows": len(products_raw),
        "clean_rows": len(products_clean),
        "rejected_rows": len(products_rejected),
        "reason_counts": rejection_summary(products_rejected),
    }

    sales_clean, sales_rejected = validate_sales_history(sales_raw, valid_branch_ids, valid_product_ids)
    write_output("sales_history.csv", sales_clean, sales_rejected)
    results["sales_history.csv"] = {
        "raw_rows": len(sales_raw),
        "clean_rows": len(sales_clean),
        "rejected_rows": len(sales_rejected),
        "reason_counts": rejection_summary(sales_rejected),
    }

    stock_clean, stock_rejected = validate_stock_movements(
        stock_movements_raw, valid_branch_ids, valid_product_ids
    )
    write_output("stock_movements.csv", stock_clean, stock_rejected)
    results["stock_movements.csv"] = {
        "raw_rows": len(stock_movements_raw),
        "clean_rows": len(stock_clean),
        "rejected_rows": len(stock_rejected),
        "reason_counts": rejection_summary(stock_rejected),
    }

    inventory_clean, inventory_rejected = validate_current_inventory(
        current_inventory_raw, valid_branch_ids, valid_product_ids
    )
    write_output("current_inventory.csv", inventory_clean, inventory_rejected)
    results["current_inventory.csv"] = {
        "raw_rows": len(current_inventory_raw),
        "clean_rows": len(inventory_clean),
        "rejected_rows": len(inventory_rejected),
        "reason_counts": rejection_summary(inventory_rejected),
    }

    report_text = build_report(results)
    report_path = REPORTS_DIR / "data_validation_report.md"
    report_path.write_text(report_text, encoding="utf-8")

    return results


def print_summary(results: dict[str, dict[str, object]]) -> None:
    print("Data validation complete.\n")
    for filename, result in results.items():
        print(
            f"{filename}: "
            f"{result['clean_rows']:,} clean rows, "
            f"{result['rejected_rows']:,} rejected rows"
        )
    print("\nOutputs written to data/processed, data/rejected, and reports/data_validation_report.md")


def main() -> None:
    results = validate_all_files()
    print_summary(results)


if __name__ == "__main__":
    main()
