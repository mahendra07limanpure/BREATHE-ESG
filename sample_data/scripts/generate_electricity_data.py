# scripts/generate_electricity_data.py

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
# SITE / METER MASTER DATA
# =====================================================

SITES = [

    {
        "site_name": "Mumbai Plant",
        "meter_prefix": "MUM",
        "tariff": "Industrial-HT",
        "supplier": "Tata Power"
    },

    {
        "site_name": "Pune Factory",
        "meter_prefix": "PUN",
        "tariff": "Industrial-HT",
        "supplier": "MSEDCL"
    },

    {
        "site_name": "Delhi Warehouse",
        "meter_prefix": "DEL",
        "tariff": "Commercial-LT",
        "supplier": "BSES"
    },

    {
        "site_name": "Gujarat Unit",
        "meter_prefix": "GUJ",
        "tariff": "Industrial-HT",
        "supplier": "Torrent Power"
    }
]

# =====================================================
# CONFIGURATION
# =====================================================

TOTAL_ROWS = 120

ANOMALY_PERCENTAGE = 0.08

START_DATE = datetime(2024, 1, 1)

OUTPUT_FILE = "sample_data/electricity_data.csv"

UNITS = ["kWh", "kVAh"]

# =====================================================
# HELPERS
# =====================================================


def generate_billing_period():

    billing_start = START_DATE + timedelta(
        days=random.randint(0, 150)
    )

    duration = random.choice([
        28,
        29,
        30,
        31
    ])

    billing_end = billing_start + timedelta(
        days=duration
    )

    return billing_start, billing_end


def seasonal_multiplier(month):

    # Summer → higher electricity usage
    if month in [4, 5, 6]:

        return 1.25

    return 1.0


def generate_consumption(month):

    base = random.uniform(
        5000,
        15000
    )

    base *= seasonal_multiplier(month)

    return round(base, 2)


def inject_anomaly(row):

    anomaly = random.choice([

        "zero_consumption",

        "future_invoice",

        "invalid_unit",

        "very_high_usage",

        "missing_meter"

    ])

    if anomaly == "zero_consumption":

        row["units_consumed"] = 0

    elif anomaly == "future_invoice":

        row["invoice_date"] = "2027-01-15"

    elif anomaly == "invalid_unit":

        row["unit"] = "UNKNOWN"

    elif anomaly == "very_high_usage":

        row["units_consumed"] = 999999

    elif anomaly == "missing_meter":

        row["meter_id"] = ""

    return row


# =====================================================
# DATA GENERATION
# =====================================================

rows = []

for i in range(TOTAL_ROWS):

    site = random.choice(SITES)

    billing_start, billing_end = (
        generate_billing_period()
    )

    month = billing_start.month

    consumption = generate_consumption(month)

    row = {

        "tenant_id":
            TENANT["tenant_id"],

        "company_name":
            TENANT["company_name"],

        "account_number":
            f"ACC-{1000+i}",

        "meter_id":
            f"{site['meter_prefix']}-{2000+i}",

        "site_name":
            site["site_name"],

        "billing_period_start":
            billing_start.strftime("%Y-%m-%d"),

        "billing_period_end":
            billing_end.strftime("%Y-%m-%d"),

        "units_consumed":
            consumption,

        "unit":
            random.choice(UNITS),

        "tariff_category":
            site["tariff"],

        "supplier_name":
            site["supplier"],

        "invoice_number":
            f"INV-{5000+i}",

        "invoice_date":
            (
                billing_end
                + timedelta(days=5)
            ).strftime("%Y-%m-%d")
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
        len(rows)-1
    )

    rows[idx] = inject_anomaly(
        rows[idx]
    )

# =====================================================
# DUPLICATE ROWS
# =====================================================

for _ in range(5):

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
    index=False
)

print("=" * 60)

print("Electricity dataset generated successfully")

print(f"Rows Generated: {len(df)}")

print(f"Output File: {OUTPUT_FILE}")

print("=" * 60)