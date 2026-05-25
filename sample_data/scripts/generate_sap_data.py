# scripts/generate_sap_data.py

import pandas as pd
import random
from datetime import datetime, timedelta

# =====================================================
# SINGLE CLIENT CONFIGURATION
# =====================================================

TENANT = {
    "tenant_id": "T001",
    "company_name": "Tata Manufacturing Ltd"
}

# =====================================================
# PLANTS
# =====================================================

PLANTS = [
    "PL01",   # Mumbai Plant
    "PL02",   # Pune Factory
    "PL03",   # Delhi Warehouse
    "PL04"    # Gujarat Unit
]

# =====================================================
# MATERIALS
# =====================================================

MATERIALS = [

    {
        "matnr": "000000000500012",
        "description": "Diesel EN590",
        "type": "fuel",
        "base_unit": "L",
        "movement_types": ["261", "201"],
        "quantity_range": (300, 900),
        "price_range": (88, 95)
    },

    {
        "matnr": "000000000500013",
        "description": "Motor Spirit",
        "type": "fuel",
        "base_unit": "L",
        "movement_types": ["261"],
        "quantity_range": (200, 600),
        "price_range": (95, 110)
    },

    {
        "matnr": "000000000500014",
        "description": "LPG Industrial",
        "type": "fuel",
        "base_unit": "KG",
        "movement_types": ["261"],
        "quantity_range": (100, 400),
        "price_range": (60, 75)
    },

    {
        "matnr": "000000000500015",
        "description": "Structural Steel",
        "type": "procurement",
        "base_unit": "KG",
        "movement_types": ["101"],
        "quantity_range": (1000, 7000),
        "price_range": (55, 85)
    },

    {
        "matnr": "000000000500016",
        "description": "Concrete Mix C30",
        "type": "procurement",
        "base_unit": "M3",
        "movement_types": ["101"],
        "quantity_range": (10, 120),
        "price_range": (4500, 6500)
    }
]

# =====================================================
# CONFIGURATION
# =====================================================

TOTAL_ROWS = 400

ANOMALY_PERCENTAGE = 0.08

START_DATE = datetime(2024, 1, 1)

END_DATE = datetime(2024, 6, 30)

OUTPUT_FILE = "sample_data/sap_fuel_data.csv"

# =====================================================
# HELPERS
# =====================================================


def random_date(start, end):

    delta = end - start

    random_days = random.randint(0, delta.days)

    return start + timedelta(days=random_days)


def seasonal_multiplier(month):

    # Summer months → more diesel usage
    if month in [4, 5, 6]:
        return 1.20

    return 1.0


def generate_quantity(material, month):

    low, high = material["quantity_range"]

    quantity = random.uniform(low, high)

    quantity *= seasonal_multiplier(month)

    return round(quantity, 2)


def german_number_format(value):

    integer_part = int(value)

    decimal_part = int(round(
        (value - integer_part) * 100
    ))

    integer_with_separator = (
        f"{integer_part:,}"
        .replace(",", ".")
    )

    return f"{integer_with_separator},{decimal_part:02d}"


def inject_anomaly(row):

    anomaly = random.choice([

        "negative_quantity",

        "future_date",

        "unknown_unit",

        "massive_outlier",

        "missing_plant",

        "missing_material",

        "invalid_movement_type",

        "duplicate_style"

    ])

    if anomaly == "negative_quantity":

        row["MENGE"] = "-500,00"

    elif anomaly == "future_date":

        row["BLDAT"] = "20270115"

    elif anomaly == "unknown_unit":

        row["MEINS"] = "DRUM"

    elif anomaly == "massive_outlier":

        row["MENGE"] = "50.000,00"

    elif anomaly == "missing_plant":

        row["WERKS"] = ""

    elif anomaly == "missing_material":

        row["MAKTX"] = ""

    elif anomaly == "invalid_movement_type":

        row["BWART"] = "311"

    return row


# =====================================================
# DATA GENERATION
# =====================================================

rows = []

for i in range(TOTAL_ROWS):

    material = random.choice(MATERIALS)

    posting_date = random_date(
        START_DATE,
        END_DATE
    )

    quantity = generate_quantity(
        material,
        posting_date.month
    )

    price = random.uniform(
        *material["price_range"]
    )

    amount = round(quantity * price, 2)

    unit = material["base_unit"]

    # Some liquid fuels in gallons
    if unit == "L" and random.random() < 0.15:

        unit = "GAL"

    row = {

        "TENANT_ID":
            TENANT["tenant_id"],

        "COMPANY_NAME":
            TENANT["company_name"],

        "MANDT": "100",

        "BUKRS":
            random.choice(["1000", "2000"]),

        "WERKS":
            random.choice(PLANTS),

        # SAP posting date
        "BLDAT":
            posting_date.strftime("%Y%m%d"),

        "MATNR":
            material["matnr"],

        "MAKTX":
            material["description"],

        # SAP movement type
        "BWART":
            random.choice(
                material["movement_types"]
            ),

        # Quantity
        "MENGE":
            german_number_format(quantity),

        # Unit
        "MEINS":
            unit,

        # Amount
        "DMBTR":
            german_number_format(amount),

        "WAERS": "INR",

        # Cost center
        "KOSTL":
            f"KST-{random.randint(5001, 5010)}"
    }

    rows.append(row)

# =====================================================
# ANOMALY INJECTION
# =====================================================

anomaly_count = int(
    TOTAL_ROWS * ANOMALY_PERCENTAGE
)

for _ in range(anomaly_count):

    idx = random.randint(
        0,
        len(rows) - 1
    )

    rows[idx] = inject_anomaly(rows[idx])

# =====================================================
# DUPLICATE ROWS
# =====================================================

for _ in range(8):

    duplicate = random.choice(rows)

    rows.append(duplicate.copy())

# =====================================================
# DATAFRAME
# =====================================================

df = pd.DataFrame(rows)

# =====================================================
# EXPORT CSV
# =====================================================

df.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8"
)

print("=" * 60)

print("SAP dataset generated successfully")

print(f"Rows Generated: {len(df)}")

print(f"Output File: {OUTPUT_FILE}")

print("=" * 60)