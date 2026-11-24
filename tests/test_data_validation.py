from pathlib import Path
import sys

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.validate_data import validate_sales_history


RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
REJECTED_DATA_DIR = PROJECT_ROOT / "data" / "rejected"

EXPECTED_COLUMNS = {
    "branches.csv": ["branch_id", "branch_name", "city", "township", "branch_type"],
    "suppliers.csv": [
        "supplier_id",
        "supplier_name",
        "contact_phone",
        "city",
        "lead_time_days",
        "minimum_order_value",
    ],
    "products.csv": [
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
    "sales_history.csv": ["sale_id", "sale_date", "branch_id", "product_id", "quantity_sold", "unit_price"],
    "stock_movements.csv": [
        "movement_id",
        "movement_date",
        "branch_id",
        "product_id",
        "movement_type",
        "quantity",
        "reference_note",
    ],
    "current_inventory.csv": ["inventory_date", "branch_id", "product_id", "current_stock", "reserved_stock"],
}


def test_generated_csv_files_exist():
    for filename in EXPECTED_COLUMNS:
        assert (RAW_DATA_DIR / filename).exists()


def test_required_columns_exist():
    for filename, required_columns in EXPECTED_COLUMNS.items():
        df = pd.read_csv(RAW_DATA_DIR / filename, nrows=5)
        for column in required_columns:
            assert column in df.columns


def test_sales_data_has_rows():
    sales = pd.read_csv(RAW_DATA_DIR / "sales_history.csv")
    assert len(sales) > 0


def test_validation_rejects_invalid_sales_rows():
    sales = pd.DataFrame(
        [
            {
                "sale_id": "SL001",
                "sale_date": "2026-05-01",
                "branch_id": "B001",
                "product_id": "P001",
                "quantity_sold": 5,
                "unit_price": 1000,
            },
            {
                "sale_id": "SL002",
                "sale_date": "not-a-date",
                "branch_id": "B001",
                "product_id": "P001",
                "quantity_sold": 5,
                "unit_price": 1000,
            },
            {
                "sale_id": "SL003",
                "sale_date": "2026-05-01",
                "branch_id": "BAD_BRANCH",
                "product_id": "P001",
                "quantity_sold": -1,
                "unit_price": 1000,
            },
        ]
    )

    clean, rejected = validate_sales_history(
        sales,
        valid_branch_ids={"B001"},
        valid_product_ids={"P001"},
    )

    assert len(clean) == 1
    assert len(rejected) == 2
    assert "rejection_reason" in rejected.columns
    assert rejected["rejection_reason"].str.contains("sale_date is not a valid date").any()
    assert rejected["rejection_reason"].str.contains("quantity_sold must be greater than 0").any()


def test_cleaned_files_are_created():
    for filename in EXPECTED_COLUMNS:
        rejected_filename = filename.replace(".csv", "_rejected.csv")
        assert (PROCESSED_DATA_DIR / filename).exists()
        assert (REJECTED_DATA_DIR / rejected_filename).exists()
