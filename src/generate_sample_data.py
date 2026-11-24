"""
Generate realistic sample CSV files for the Inventory Reorder System.

Run from the project root:
    python src/generate_sample_data.py

The script writes CSV files to:
    data/raw/
"""

from __future__ import annotations

import random
from datetime import date, timedelta
from pathlib import Path

import pandas as pd


RANDOM_SEED = 42
random.seed(RANDOM_SEED)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"

START_DATE = date(2026, 2, 6)
END_DATE = date(2026, 5, 6)
SALES_DAYS = (END_DATE - START_DATE).days + 1


def money(value: float) -> int:
    """Round prices to clean Myanmar Kyat-style amounts."""
    return int(round(value / 50) * 50)


def generate_suppliers() -> pd.DataFrame:
    suppliers = [
        ("S001", "Yangon FMCG Distributor", "Yangon"),
        ("S002", "Beverage Wholesale Myanmar", "Yangon"),
        ("S003", "Mandalay Food Supply", "Mandalay"),
        ("S004", "Shwe Household Trading", "Yangon"),
        ("S005", "Personal Care Distributor", "Yangon"),
        ("S006", "Stationery World Myanmar", "Yangon"),
        ("S007", "Ayeyar Rice Supplier", "Pathein"),
        ("S008", "Upper Myanmar Wholesale", "Mandalay"),
        ("S009", "Naypyidaw Retail Supply", "Naypyidaw"),
        ("S010", "Bago Snack Distributor", "Bago"),
        ("S011", "Myanmar Dairy Distribution", "Yangon"),
        ("S012", "Cleaning Goods Partner", "Mandalay"),
        ("S013", "Local Tea Mix Supplier", "Taunggyi"),
        ("S014", "Imported Goods Myanmar", "Yangon"),
        ("S015", "Toy and Stationery Center", "Yangon"),
        ("S016", "Health and Beauty Supply", "Mawlamyine"),
        ("S017", "Dry Food Wholesale", "Monywa"),
        ("S018", "Beverage City Trading", "Mandalay"),
        ("S019", "Small Grocery Supplier", "Yangon"),
        ("S020", "Regional Convenience Supply", "Naypyidaw"),
    ]

    rows = []
    for supplier_id, supplier_name, city in suppliers:
        rows.append(
            {
                "supplier_id": supplier_id,
                "supplier_name": supplier_name,
                "contact_phone": f"09{random.randint(700000000, 799999999)}",
                "city": city,
                "lead_time_days": random.randint(2, 14),
                "minimum_order_value": random.choice(
                    [100000, 150000, 200000, 250000, 300000, 500000]
                ),
            }
        )

    df = pd.DataFrame(rows)

    # Intentional data quality issue: one supplier has missing lead time.
    df.loc[df["supplier_id"] == "S020", "lead_time_days"] = None
    return df


def generate_branches() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "branch_id": "B001",
                "branch_name": "Yangon Downtown Branch",
                "city": "Yangon",
                "township": "Kyauktada",
                "branch_type": "Mini Mart",
            },
            {
                "branch_id": "B002",
                "branch_name": "Hlaing Convenience Branch",
                "city": "Yangon",
                "township": "Hlaing",
                "branch_type": "Convenience Store",
            },
            {
                "branch_id": "B003",
                "branch_name": "Mandalay Central Branch",
                "city": "Mandalay",
                "township": "Chanayethazan",
                "branch_type": "Mini Mart",
            },
            {
                "branch_id": "B004",
                "branch_name": "Naypyidaw Junction Branch",
                "city": "Naypyidaw",
                "township": "Zabuthiri",
                "branch_type": "Convenience Store",
            },
            {
                "branch_id": "B005",
                "branch_name": "Bago Market Branch",
                "city": "Bago",
                "township": "Bago",
                "branch_type": "Neighborhood Store",
            },
        ]
    )


def product_name_pool() -> dict[str, list[tuple[str, str, int]]]:
    return {
        "Food": [
            ("Mama Chicken Noodle", "Mama", 350),
            ("Mama Shrimp Noodle", "Mama", 350),
            ("Yum Yum Seafood Noodle", "Yum Yum", 330),
            ("Premier Coffee Mix", "Premier", 180),
            ("ABC Coffee Mix", "ABC", 160),
            ("Royal Myanmar Tea Mix", "Royal Myanmar", 140),
            ("Paw San Hmwe Rice 5kg", "Local Rice", 16000),
            ("Cooking Oil 1L", "Meizan", 4200),
            ("Fish Sauce 700ml", "Ngant Pya Yay", 1100),
            ("Instant Vermicelli", "Wai Wai", 450),
            ("Peanut Snack", "Shwe Pu Zun", 500),
            ("Potato Chips", "Jack n Jill", 900),
            ("Cream Biscuit", "Julie", 700),
            ("Condensed Milk", "Dairy Champ", 1800),
            ("Canned Sardine", "Ayam", 2200),
            ("Sugar 1kg", "Local", 2400),
            ("Salt 500g", "Local", 500),
            ("Chili Powder 100g", "Local", 900),
            ("Bean Vermicelli", "Pine", 850),
            ("Dried Tea Leaves", "Laphet", 2500),
            ("Tamarind Paste", "Local", 1200),
            ("Pickled Tea Leaf Pack", "Yuzana", 1500),
            ("Egg Noodle Pack", "Local", 600),
            ("Corn Snack", "Mamee", 450),
            ("Butter Cookie Pack", "Danish", 2500),
        ],
        "Drinks": [
            ("Alpine Water 1L", "Alpine", 400),
            ("Alpine Water 500ml", "Alpine", 250),
            ("Coca-Cola Can", "Coca-Cola", 850),
            ("Sprite Bottle 500ml", "Sprite", 700),
            ("Red Bull Can", "Red Bull", 900),
            ("Sponsor Energy Drink", "Sponsor", 800),
            ("M-150 Bottle", "M-150", 750),
            ("Ovaltine UHT", "Ovaltine", 1000),
            ("Milo Sachet", "Milo", 250),
            ("Tea Leaf Drink", "Pokka", 850),
            ("Orange Juice Box", "Tipco", 1200),
            ("Milk Tea Bottle", "Royal-D", 900),
            ("Sparkling Water", "Singha", 800),
            ("Sunkist Orange Can", "Sunkist", 900),
            ("Coffee Can", "Birdy", 1000),
            ("Green Tea Bottle", "Oishi", 900),
            ("Yogurt Drink", "Dutch Mill", 700),
            ("Mineral Water 1.5L", "Alpine", 550),
            ("Lime Soda Can", "Schweppes", 950),
            ("Chocolate Milk", "Dutch Mill", 800),
        ],
        "Household": [
            ("Sunlight Dishwashing Liquid", "Sunlight", 2200),
            ("Fairy Detergent Powder", "Fairy", 2500),
            ("Washing Powder 1kg", "Omo", 3500),
            ("Toilet Cleaner", "Duck", 2800),
            ("Floor Cleaner 1L", "Magiclean", 3200),
            ("Tissue Roll Pack", "Clean", 2500),
            ("Mosquito Coil", "Baygon", 1200),
            ("Air Freshener", "Glade", 3800),
            ("Garbage Bag Roll", "Local", 1800),
            ("Dish Sponge Pack", "Scotch-Brite", 1200),
            ("Laundry Soap", "Shwe Wah", 700),
            ("Bleach Bottle", "Clorox", 3000),
            ("Glass Cleaner", "Windex", 3500),
            ("Plastic Food Wrap", "Local", 1500),
            ("Aluminum Foil", "Local", 2200),
            ("Hand Wash Refill", "Lifebuoy", 2400),
            ("Insect Spray", "Baygon", 4500),
            ("Cleaning Brush", "Local", 1600),
            ("Paper Napkin Pack", "Clean", 1000),
            ("Kitchen Towel Roll", "Clean", 1800),
        ],
        "Personal Care": [
            ("Shwe Pyi Nann Thanakha", "Shwe Pyi Nann", 1800),
            ("Colgate Toothpaste", "Colgate", 1800),
            ("Closeup Toothpaste", "Closeup", 1700),
            ("Lifebuoy Soap", "Lifebuoy", 800),
            ("Dove Soap", "Dove", 1500),
            ("Clear Shampoo Sachet", "Clear", 250),
            ("Sunsilk Shampoo Sachet", "Sunsilk", 220),
            ("Head & Shoulders Sachet", "Head & Shoulders", 300),
            ("Nivea Body Lotion", "Nivea", 5500),
            ("Vaseline Lotion", "Vaseline", 5200),
            ("Toothbrush", "Oral-B", 1200),
            ("Baby Powder", "Johnson", 3200),
            ("Sanitary Pad Pack", "Modess", 2500),
            ("Face Mask Pack", "Local", 1000),
            ("Hand Sanitizer", "Dettol", 2800),
            ("Cotton Buds", "Local", 800),
            ("Hair Gel", "Gatsby", 3500),
            ("Deodorant Roll-On", "Nivea", 4800),
            ("Lip Balm", "Vaseline", 2200),
            ("Face Wash", "Ponds", 4500),
        ],
        "Stationery": [
            ("Double A A4 Paper", "Double A", 9000),
            ("Blue Pen", "Zebra", 300),
            ("Black Pen", "Zebra", 300),
            ("Pencil HB", "Faber-Castell", 250),
            ("Eraser", "Faber-Castell", 300),
            ("Notebook Small", "Local", 700),
            ("Notebook Large", "Local", 1200),
            ("Glue Stick", "UHU", 900),
            ("Correction Tape", "Tombow", 1500),
            ("Highlighter", "Stabilo", 1200),
            ("Stapler", "Kangaro", 3500),
            ("Staple Pins", "Kangaro", 700),
            ("File Folder", "Local", 600),
            ("Envelope Pack", "Local", 1000),
            ("Marker Pen", "Artline", 900),
        ],
    }


def generate_products() -> pd.DataFrame:
    categories = product_name_pool()
    supplier_ids = [f"S{i:03d}" for i in range(1, 21)]

    rows = []
    product_number = 1
    for category, products in categories.items():
        for product_name, brand, base_cost in products:
            selling_price = money(base_cost * random.uniform(1.25, 1.65))
            if category == "Food":
                shelf_life_days = random.choice([90, 120, 180, 365])
                min_order_quantity = random.choice([50, 100, 120, 200])
            elif category == "Drinks":
                shelf_life_days = random.choice([180, 365, 540])
                min_order_quantity = random.choice([24, 48, 72, 120])
            elif category == "Household":
                shelf_life_days = random.choice([720, 900, 9999])
                min_order_quantity = random.choice([10, 12, 24, 48])
            elif category == "Personal Care":
                shelf_life_days = random.choice([365, 540, 720])
                min_order_quantity = random.choice([12, 24, 48])
            else:
                shelf_life_days = 9999
                min_order_quantity = random.choice([10, 20, 50, 100])

            rows.append(
                {
                    "product_id": f"P{product_number:03d}",
                    "product_name": product_name,
                    "category": category,
                    "brand": brand,
                    "unit_cost": base_cost,
                    "selling_price": selling_price,
                    "supplier_id": random.choice(supplier_ids),
                    "shelf_life_days": shelf_life_days,
                    "min_order_quantity": min_order_quantity,
                }
            )
            product_number += 1

    # Add extra local products until we have at least 120 products.
    extra_names = [
        "Local Snack Pack",
        "Myanmar Tea Sachet",
        "Rice Cracker",
        "Coconut Biscuit",
        "Dish Cloth",
        "School Ruler",
        "Herbal Soap",
        "Flavored Soda",
        "Ready Tea Bottle",
        "Instant Soup Cup",
    ]
    while product_number <= 120:
        category = random.choice(list(categories.keys()))
        product_name = f"{random.choice(extra_names)} {product_number}"
        base_cost = random.choice([300, 500, 800, 1000, 1500, 2500, 4000])
        rows.append(
            {
                "product_id": f"P{product_number:03d}",
                "product_name": product_name,
                "category": category,
                "brand": random.choice(["Local", "Shwe", "Royal", "Value", "Family"]),
                "unit_cost": base_cost,
                "selling_price": money(base_cost * random.uniform(1.25, 1.7)),
                "supplier_id": random.choice(supplier_ids),
                "shelf_life_days": random.choice([90, 180, 365, 720, 9999]),
                "min_order_quantity": random.choice([10, 20, 24, 48, 50, 100]),
            }
        )
        product_number += 1

    df = pd.DataFrame(rows)

    # Intentional data quality issues: inconsistent category spelling.
    df.loc[df["product_id"].isin(["P012", "P038"]), "category"] = "food"
    df.loc[df["product_id"].isin(["P071", "P088"]), "category"] = "PersonalCare"
    df.loc[df["product_id"] == "P095", "category"] = "stationery"

    return df


def assign_demand_profiles(products: pd.DataFrame) -> dict[str, dict[str, object]]:
    """Create product demand behavior used by sales and inventory generation."""
    profiles = {}
    product_ids = products["product_id"].tolist()

    fast_movers = set(product_ids[:20])
    slow_movers = set(product_ids[-25:])
    spike_products = set(product_ids[20:35])

    for product_id in product_ids:
        if product_id in fast_movers:
            base_qty = random.randint(8, 22)
            sale_probability = random.uniform(0.72, 0.95)
            profile = "fast"
        elif product_id in slow_movers:
            base_qty = random.randint(1, 3)
            sale_probability = random.uniform(0.08, 0.22)
            profile = "slow"
        else:
            base_qty = random.randint(2, 8)
            sale_probability = random.uniform(0.25, 0.58)
            profile = "normal"

        profiles[product_id] = {
            "profile": profile,
            "base_qty": base_qty,
            "sale_probability": sale_probability,
            "has_spikes": product_id in spike_products,
        }

    return profiles


def generate_sales_history(
    products: pd.DataFrame, branches: pd.DataFrame, profiles: dict[str, dict[str, object]]
) -> pd.DataFrame:
    rows = []
    sale_number = 1
    dates = [START_DATE + timedelta(days=i) for i in range(SALES_DAYS)]
    branch_ids = branches["branch_id"].tolist()
    branch_weights = [0.32, 0.25, 0.2, 0.13, 0.1]

    product_lookup = products.set_index("product_id").to_dict("index")

    for sale_date in dates:
        is_weekend = sale_date.weekday() >= 5

        for branch_id in branch_ids:
            for product_id, profile in profiles.items():
                probability = float(profile["sale_probability"])
                if is_weekend:
                    probability *= 1.15

                # Random demand spikes simulate payday, holidays, or local promotions.
                spike_multiplier = 1
                if bool(profile["has_spikes"]) and sale_date.day in [1, 5, 15, 25]:
                    probability *= 1.7
                    spike_multiplier = random.choice([2, 3, 4])

                # Smaller branches sell less frequently.
                branch_index = branch_ids.index(branch_id)
                probability *= branch_weights[branch_index] / max(branch_weights)

                if random.random() < min(probability, 0.98):
                    base_qty = int(profile["base_qty"])
                    quantity_sold = max(1, int(random.gauss(base_qty, max(1, base_qty * 0.35))))
                    quantity_sold *= spike_multiplier

                    rows.append(
                        {
                            "sale_id": f"SL{sale_number:06d}",
                            "sale_date": sale_date.isoformat(),
                            "branch_id": branch_id,
                            "product_id": product_id,
                            "quantity_sold": quantity_sold,
                            "unit_price": product_lookup[product_id]["selling_price"],
                        }
                    )
                    sale_number += 1

    df = pd.DataFrame(rows)

    # Guarantee at least 10,000 sales rows while preserving realistic randomness.
    while len(df) < 10000:
        product_id = random.choice(products["product_id"].tolist())
        product = product_lookup[product_id]
        random_date = START_DATE + timedelta(days=random.randint(0, SALES_DAYS - 1))
        rows_to_add = {
            "sale_id": f"SL{sale_number:06d}",
            "sale_date": random_date.isoformat(),
            "branch_id": random.choices(branch_ids, weights=branch_weights, k=1)[0],
            "product_id": product_id,
            "quantity_sold": random.randint(1, 8),
            "unit_price": product["selling_price"],
        }
        df = pd.concat([df, pd.DataFrame([rows_to_add])], ignore_index=True)
        sale_number += 1

    # Intentional data quality issues.
    issue_rows = [
        {
            "sale_id": f"SL{sale_number:06d}",
            "sale_date": END_DATE.isoformat(),
            "branch_id": "B001",
            "product_id": "P999",
            "quantity_sold": 10,
            "unit_price": 500,
        },
        {
            "sale_id": f"SL{sale_number + 1:06d}",
            "sale_date": END_DATE.isoformat(),
            "branch_id": "B999",
            "product_id": "P001",
            "quantity_sold": 8,
            "unit_price": 500,
        },
        {
            "sale_id": f"SL{sale_number + 2:06d}",
            "sale_date": END_DATE.isoformat(),
            "branch_id": "B002",
            "product_id": "P002",
            "quantity_sold": -4,
            "unit_price": 500,
        },
    ]
    df = pd.concat([df, pd.DataFrame(issue_rows), df.sample(3, random_state=RANDOM_SEED)], ignore_index=True)

    return df


def generate_stock_movements(
    sales: pd.DataFrame, products: pd.DataFrame, branches: pd.DataFrame
) -> pd.DataFrame:
    rows = []
    movement_number = 1
    product_ids = products["product_id"].tolist()
    branch_ids = branches["branch_id"].tolist()

    # Create purchase movements for replenishment events.
    for movement_date in [START_DATE - timedelta(days=3), START_DATE + timedelta(days=30), START_DATE + timedelta(days=60)]:
        for branch_id in branch_ids:
            for product_id in product_ids:
                if random.random() < 0.72:
                    rows.append(
                        {
                            "movement_id": f"MV{movement_number:06d}",
                            "movement_date": movement_date.isoformat(),
                            "branch_id": branch_id,
                            "product_id": product_id,
                            "movement_type": "purchase",
                            "quantity": random.choice([24, 48, 72, 100, 120, 200, 240]),
                            "reference_note": "Supplier purchase",
                        }
                    )
                    movement_number += 1

    valid_sales = sales[
        sales["product_id"].isin(product_ids)
        & sales["branch_id"].isin(branch_ids)
        & (sales["quantity_sold"] > 0)
    ]

    # Convert many sales rows into sale stock movements.
    sample_size = min(2400, len(valid_sales))
    for _, sale in valid_sales.sample(sample_size, random_state=RANDOM_SEED).iterrows():
        rows.append(
            {
                "movement_id": f"MV{movement_number:06d}",
                "movement_date": sale["sale_date"],
                "branch_id": sale["branch_id"],
                "product_id": sale["product_id"],
                "movement_type": "sale",
                "quantity": int(sale["quantity_sold"]),
                "reference_note": f"Sales {sale['sale_id']}",
            }
        )
        movement_number += 1

    # Add returns, adjustments, and damage records.
    movement_types = ["return", "adjustment_in", "adjustment_out", "damage"]
    while len(rows) < 3000:
        movement_type = random.choice(movement_types)
        quantity = random.randint(1, 12)
        rows.append(
            {
                "movement_id": f"MV{movement_number:06d}",
                "movement_date": (START_DATE + timedelta(days=random.randint(0, SALES_DAYS - 1))).isoformat(),
                "branch_id": random.choice(branch_ids),
                "product_id": random.choice(product_ids),
                "movement_type": movement_type,
                "quantity": quantity,
                "reference_note": f"{movement_type.replace('_', ' ').title()} record",
            }
        )
        movement_number += 1

    df = pd.DataFrame(rows)

    # Intentional data quality issues.
    bad_rows = [
        {
            "movement_id": f"MV{movement_number:06d}",
            "movement_date": END_DATE.isoformat(),
            "branch_id": "B001",
            "product_id": "P001",
            "movement_type": "transfer_out",
            "quantity": 10,
            "reference_note": "Invalid movement type test",
        },
        {
            "movement_id": f"MV{movement_number + 1:06d}",
            "movement_date": END_DATE.isoformat(),
            "branch_id": "B002",
            "product_id": "P002",
            "movement_type": "sale",
            "quantity": -5,
            "reference_note": "Negative quantity test",
        },
        {
            "movement_id": f"MV{movement_number + 2:06d}",
            "movement_date": END_DATE.isoformat(),
            "branch_id": "B001",
            "product_id": "P999",
            "movement_type": "purchase",
            "quantity": 20,
            "reference_note": "Invalid product test",
        },
    ]
    duplicate_row = df.sample(1, random_state=RANDOM_SEED)
    df = pd.concat([df, pd.DataFrame(bad_rows), duplicate_row], ignore_index=True)

    return df


def generate_current_inventory(
    products: pd.DataFrame, branches: pd.DataFrame, profiles: dict[str, dict[str, object]]
) -> pd.DataFrame:
    rows = []
    branch_ids = branches["branch_id"].tolist()

    for branch_id in branch_ids:
        for product_id in products["product_id"].tolist():
            profile = profiles[product_id]["profile"]

            if profile == "fast":
                # Some fast-moving products are intentionally low stock.
                current_stock = random.choice([5, 8, 12, 20, 35, 50, 70])
            elif profile == "slow":
                # Slow-moving products often become overstocked.
                current_stock = random.choice([90, 120, 180, 240, 320, 450])
            else:
                current_stock = random.choice([20, 35, 50, 80, 120, 160])

            rows.append(
                {
                    "inventory_date": END_DATE.isoformat(),
                    "branch_id": branch_id,
                    "product_id": product_id,
                    "current_stock": current_stock,
                    "reserved_stock": random.choice([0, 0, 0, 2, 5, 10]),
                }
            )

    df = pd.DataFrame(rows)

    # Intentional data quality issues: negative stock and invalid product.
    issue_rows = [
        {
            "inventory_date": END_DATE.isoformat(),
            "branch_id": "B001",
            "product_id": "P002",
            "current_stock": -5,
            "reserved_stock": 0,
        },
        {
            "inventory_date": END_DATE.isoformat(),
            "branch_id": "B002",
            "product_id": "P999",
            "current_stock": 20,
            "reserved_stock": 0,
        },
    ]
    df = pd.concat([df, pd.DataFrame(issue_rows)], ignore_index=True)

    return df


def write_csv(df: pd.DataFrame, filename: str) -> None:
    path = RAW_DATA_DIR / filename
    df.to_csv(path, index=False)
    print(f"Created {path.relative_to(PROJECT_ROOT)} with {len(df):,} rows")


def main() -> None:
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    suppliers = generate_suppliers()
    branches = generate_branches()
    products = generate_products()
    profiles = assign_demand_profiles(products)
    sales = generate_sales_history(products, branches, profiles)
    stock_movements = generate_stock_movements(sales, products, branches)
    current_inventory = generate_current_inventory(products, branches, profiles)

    write_csv(products, "products.csv")
    write_csv(branches, "branches.csv")
    write_csv(suppliers, "suppliers.csv")
    write_csv(sales, "sales_history.csv")
    write_csv(stock_movements, "stock_movements.csv")
    write_csv(current_inventory, "current_inventory.csv")

    print("\nSample data generation complete.")
    print("Intentional data quality issues are included for validation practice.")


if __name__ == "__main__":
    main()
