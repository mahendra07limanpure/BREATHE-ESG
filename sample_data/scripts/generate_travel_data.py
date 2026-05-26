# scripts/generate_travel_data.py

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
# EMPLOYEE MASTER DATA
# =====================================================

EMPLOYEES = [

    {
        "employee_id": "EMP001",
        "employee_name": "Rahul Sharma",
        "department": "Engineering"
    },

    {
        "employee_id": "EMP002",
        "employee_name": "Priya Mehta",
        "department": "Sales"
    },

    {
        "employee_id": "EMP003",
        "employee_name": "Amit Verma",
        "department": "Operations"
    },

    {
        "employee_id": "EMP004",
        "employee_name": "Neha Singh",
        "department": "Finance"
    }
]

# =====================================================
# FLIGHT ROUTES
# =====================================================

FLIGHTS = [

    {
        "origin": "BOM",
        "destination": "DEL",
        "distance_km": 1148,
        "vendor": "IndiGo"
    },

    {
        "origin": "DEL",
        "destination": "BLR",
        "distance_km": 1740,
        "vendor": "Air India"
    },

    {
        "origin": "BOM",
        "destination": "DXB",
        "distance_km": 1930,
        "vendor": "Emirates"
    },

    {
        "origin": "LHR",
        "destination": "JFK",
        "distance_km": 5576,
        "vendor": "British Airways"
    },

    {
        "origin": "SIN",
        "destination": "SYD",
        "distance_km": 6298,
        "vendor": "Singapore Airlines"
    }
]

# =====================================================
# CONFIGURATION
# =====================================================

TOTAL_ROWS = 180

ANOMALY_PERCENTAGE = 0.08

START_DATE = datetime(2024, 1, 1)

OUTPUT_FILE = "sample_data/travel_data.csv"

EXPENSE_TYPES = [
    "Flight",
    "Hotel",
    "Cab"
]

BOOKING_CLASSES = [
    "Economy",
    "Business"
]

HOTELS = [
    "Marriott",
    "Hilton",
    "Hyatt"
]

CAB_VENDORS = [
    "Uber",
    "Ola"
]

# =====================================================
# HELPERS
# =====================================================


def random_trip_date():

    return START_DATE + timedelta(
        days=random.randint(0, 150)
    )


def inject_anomaly(row):

    anomaly = random.choice([

        "invalid_airport",

        "missing_distance",

        "future_trip",

        "very_high_amount",

        "missing_nights"

    ])

    if anomaly == "invalid_airport":

        row["destination"] = "XYZ"

    elif anomaly == "missing_distance":

        row["distance_km"] = ""

    elif anomaly == "future_trip":

        row["trip_date"] = "2027-01-15"

    elif anomaly == "very_high_amount":

        row["amount_inr"] = 999999

    elif anomaly == "missing_nights":

        row["nights"] = ""

    return row


# =====================================================
# DATA GENERATION
# =====================================================

rows = []

for i in range(TOTAL_ROWS):

    employee = random.choice(
        EMPLOYEES
    )

    expense_type = random.choice(
        EXPENSE_TYPES
    )

    trip_date = random_trip_date()

    row = {

        "tenant_id":
            TENANT["tenant_id"],

        "company_name":
            TENANT["company_name"],

        "report_id":
            f"REP-{10000+i}",

        "employee_id":
            employee["employee_id"],

        "employee_name":
            employee["employee_name"],

        "department":
            employee["department"],

        "category":
            expense_type,

        "trip_date":
            trip_date.strftime("%Y-%m-%d"),

        "origin": "",

        "destination": "",

        "distance_km": "",

        "nights": "",

        "cabin_class": "",

        "vendor_name": "",

        "amount_inr": 0,

        "currency": "INR"
    }

    # =================================================
    # FLIGHT
    # =================================================

    if expense_type == "Flight":

        flight = random.choice(
            FLIGHTS
        )

        booking_class = random.choice(
            BOOKING_CLASSES
        )

        multiplier = (
            1.0
            if booking_class == "Economy"
            else 1.8
        )

        amount = round(
            flight["distance_km"]
            * multiplier
            * random.uniform(6, 12),
            2
        )

        row.update({

            "origin":
                flight["origin"],

            "destination":
                flight["destination"],

            "distance_km":
                flight["distance_km"],

            "cabin_class":
                booking_class,

            "vendor_name":
                flight["vendor"],

            "amount_inr":
                amount
        })

    # =================================================
    # HOTEL
    # =================================================

    elif expense_type == "Hotel":

        nights = random.randint(1, 6)

        amount = round(
            nights
            * random.uniform(4000, 12000),
            2
        )

        row.update({

            "destination":
                random.choice([
                    "Mumbai",
                    "Delhi",
                    "Dubai",
                    "London"
                ]),

            "nights":
                nights,

            "vendor_name":
                random.choice(HOTELS),

            "amount_inr":
                amount
        })

    # =================================================
    # CAB
    # =================================================

    elif expense_type == "Cab":

        distance = round(
            random.uniform(5, 45),
            2
        )

        amount = round(
            distance
            * random.uniform(15, 35),
            2
        )

        row.update({

            "destination":
                random.choice([
                    "Mumbai",
                    "Delhi",
                    "Bangalore"
                ]),

            "distance_km":
                distance,

            "vendor_name":
                random.choice(
                    CAB_VENDORS
                ),

            "amount_inr":
                amount
        })

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

print("Travel dataset generated successfully")

print(f"Rows Generated: {len(df)}")

print(f"Output File: {OUTPUT_FILE}")

print("=" * 60)