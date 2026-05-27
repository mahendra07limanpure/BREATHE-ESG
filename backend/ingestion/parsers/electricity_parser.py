from datetime import datetime, date
from collections import defaultdict


# =====================================================
# EMISSION FACTOR
# Source: CEA India 2023 CO2 Baseline Document
# India grid average: 0.82 kg CO2 per kWh
# =====================================================
ELECTRICITY_EMISSION_FACTOR = 0.82   # kg CO2e per kWh

# Default power factor used to convert kVAh → kWh
# Real power factor is on the electricity bill (0.85–0.95)
# We use 0.9 as a conservative default and FLAG the row
# so the analyst can verify the actual power factor
POWER_FACTOR_DEFAULT = 0.90

KNOWN_UNITS = {"KWH", "KVAH", "UNITS"}   # "UNITS" = same as kWh on older meters


# =====================================================
# DATE PARSER
# Handles YYYY-MM-DD format from utility portal CSVs
# Returns None and flags if malformed — does NOT crash
# =====================================================
def parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(str(value).strip(), "%Y-%m-%d").date()
    except ValueError:
        return None   # caller will flag this row


# =====================================================
# UNIT CONVERSION
# Bug fix: kVAh → kWh requires power factor math,
# not just a label rename
#
# Returns (normalised_quantity, normalised_unit,
#          is_recognised, conversion_note)
# =====================================================
def convert_unit(quantity, unit):
    if quantity is None or unit is None:
        return (None, None, False, None)

    unit_upper = str(unit).strip().upper()

    # Standard kWh — no conversion needed
    if unit_upper in ("KWH", "UNITS"):
        return (quantity, "kWh", True, None)

    # kVAh → kWh: multiply by power factor
    # Bug fix: the number changes, not just the label
    if unit_upper == "KVAH":
        converted = round(quantity * POWER_FACTOR_DEFAULT, 3)
        note = (
            f"Converted {quantity} kVAh → {converted} kWh "
            f"using default power factor {POWER_FACTOR_DEFAULT}. "
            f"Verify actual power factor from bill."
        )
        return (converted, "kWh", True, note)

    # Unknown unit
    return (quantity, unit, False, None)


# =====================================================
# BILLING PERIOD APPORTIONMENT
# Key feature: splits a cross-month billing period
# into separate rows — one per calendar month
#
# Example:
#   start=2024-01-15, end=2024-02-14, units=3200
#   → row 1: Jan 2024 = 3200 * (17/31) = 1754.8 kWh
#   → row 2: Feb 2024 = 3200 * (14/31) = 1445.2 kWh
# =====================================================
def apportion_by_month(quantity, start_date, end_date):
    """
    Splits quantity proportionally across calendar months.
    Returns list of (year, month, apportioned_quantity, period_days).
    """
    if start_date is None or end_date is None:
        return []

    if start_date > end_date:
        return []

    total_days = (end_date - start_date).days + 1
    if total_days <= 0:
        return []

    # Check if same calendar month — no split needed
    if start_date.year == end_date.year and start_date.month == end_date.month:
        return [(start_date.year, start_date.month, quantity, total_days)]

    # Split across months
    portions = []
    current = start_date

    while current <= end_date:
        # Find last day of current month
        if current.month == 12:
            month_end = date(current.year + 1, 1, 1)
        else:
            month_end = date(current.year, current.month + 1, 1)

        # Days in this month that fall within our billing period
        segment_end  = min(end_date, month_end - __import__('datetime').timedelta(days=1))
        days_in_segment = (segment_end - current).days + 1

        apportioned = round(quantity * (days_in_segment / total_days), 3)
        portions.append((current.year, current.month, apportioned, days_in_segment))

        # Move to first day of next month
        current = month_end

    return portions


# =====================================================
# ACTIVITY TYPE FROM TARIFF
# =====================================================
def determine_activity_type(tariff):
    if not tariff:
        return "electricity"
    tariff = str(tariff).strip().lower()
    if "industrial" in tariff:
        return "industrial_electricity"
    if "commercial" in tariff:
        return "commercial_electricity"
    if "residential" in tariff:
        return "residential_electricity"
    return "electricity"

# =====================================================
# FLAG CHECKER FOR ELECTRICITY ROWS
# Returns (status, flag_reason)
# =====================================================
def check_flags(parsed, all_quantities=None, conversion_note=None):
    qty  = parsed.get("quantity_normalised")
    dt   = parsed.get("record_date")
    unit_recognised = parsed.get("_unit_recognised", True)

    # Check 1 — negative consumption
    if qty is not None and qty < 0:
        return ("flagged", "Negative consumption — credit note or billing system error")

    # Check 2 — zero consumption
    if qty is not None and qty == 0:
        return ("flagged", "Zero units consumed — meter possibly unread or building closed")

    # Check 3 — future billing period
    if dt is not None and dt > date.today():
        return ("flagged", f"Billing period end date {dt} is in the future")

    # Check 4 — stale date
    if dt is not None and dt.year < 2020:
        return ("flagged", f"Billing date {dt} is outside expected reporting period")

    # Check 5 — unknown unit
    if not unit_recognised:
        return ("flagged", f"Unrecognised unit '{parsed.get('unit_raw')}' — cannot normalise to kWh")

    # Check 6 — kVAh conversion used (flag for analyst to verify power factor)
    if conversion_note:
        return ("flagged", conversion_note)

    # ─── CHECK 7 REMOVED ───────────────────────────
    # Cross-month billing is NORMAL for Indian utilities
    # The parser already handles it correctly via apportionment
    # Flagging it confused analysts — 90% of rows were flagged
    # ───────────────────────────────────────────────

    # Check 7 (was 8) — statistical outlier
    if all_quantities and qty is not None and len(all_quantities) > 3:
        import statistics
        mean  = statistics.mean(all_quantities)
        stdev = statistics.stdev(all_quantities)
        if stdev > 0 and qty > mean + (3 * stdev):
            return ("flagged",
                    f"Consumption {qty} kWh is unusually high "
                    f"(>{round(mean + 3*stdev, 1)} kWh) — possible meter fault")

    return ("pending", None)

# =====================================================
# SINGLE ROW PARSER
# Returns a LIST of dicts (one row can become multiple
# when billing period crosses calendar months)
# =====================================================
def parse_electricity_row(row):
    """
    Parses one row from a utility portal CSV.
    Returns a LIST because a cross-month billing period
    produces one EmissionRecord per calendar month.
    """
    # ── Step 1: extract raw values ──────────────
    units_raw      = row.get("units_consumed")
    unit_raw       = row.get("unit", "kWh")
    tariff         = row.get("tariff_category", "")
    meter_id       = row.get("meter_id", "")
    account        = row.get("account_number", "")
    start_str      = row.get("billing_period_start")
    end_str        = row.get("billing_period_end")

    # ── Step 2: parse dates ─────────────────────
    start_date = parse_date(start_str)
    end_date   = parse_date(end_str)

    # ── Step 3: parse quantity ──────────────────
    try:
        qty_raw = float(units_raw) if units_raw not in (None, "") else None
    except (ValueError, TypeError):
        qty_raw = None

    # ── Step 4: convert unit (label + math) ────
    qty_norm, unit_norm, unit_recognised, conversion_note = convert_unit(qty_raw, unit_raw)

    # ── Step 5: apportion across months ────────
    portions = apportion_by_month(qty_norm or 0, start_date, end_date)
    is_cross_month = len(portions) > 1

    # If apportionment failed (bad dates), make one row
    if not portions:
        portions = [(
            end_date.year if end_date else None,
            end_date.month if end_date else None,
            qty_norm,
            None
        )]

    # ── Step 6: build one record per month ─────
    activity = determine_activity_type(tariff)
    results  = []

    for (year, month, apportioned_qty, days) in portions:

        # CO2 calculation
        if apportioned_qty is not None and apportioned_qty >= 0:
            co2_kg = round(apportioned_qty * ELECTRICITY_EMISSION_FACTOR, 4)
        else:
            co2_kg = 0.0

        # record_date = last day of that month
        if year and month:
            if month == 12:
                record_date = date(year + 1, 1, 1) - __import__('datetime').timedelta(days=1)
            else:
                record_date = date(year, month + 1, 1) - __import__('datetime').timedelta(days=1)
        else:
            record_date = end_date

        parsed = {
            "source_type":         "electricity",
            "scope":               "scope_2",
            "activity_type":       activity,
            "site_name":           f"{account} / {meter_id}",
            "record_date":         record_date,

            # raw values
            "quantity_raw":        qty_raw,
            "unit_raw":            unit_raw,

            # normalised values
            "quantity_normalised": apportioned_qty,
            "unit_normalised":     unit_norm or "kWh",

            # CO2
            "emission_factor":     ELECTRICITY_EMISSION_FACTOR,
            "co2_kg":              co2_kg,

            # original row
            "raw_data":            dict(row),

            # internals for flag checker
            "_unit_recognised": unit_recognised,
           
        }

        status, flag_reason = check_flags(
            parsed,
            conversion_note=conversion_note
        )
        parsed["status"]      = status
        parsed["flag_reason"] = flag_reason

        # Clean internal keys
        parsed.pop("_unit_recognised", None)
        parsed.pop("_is_cross_month", None)

        results.append(parsed)

    return results


# =====================================================
# BATCH PARSER
# Handles full CSV file
# Runs outlier check across all rows after parsing
# =====================================================
def parse_electricity_file(df):
    """
    df: pandas DataFrame of uploaded electricity CSV.
    Returns flat list of dicts ready to save as EmissionRecords.
    """
    rows = df.to_dict(orient="records")

    # First pass: parse all rows
    all_parsed = []
    for row in rows:
        records = parse_electricity_row(row)   # returns a list
        all_parsed.extend(records)

    # Second pass: outlier check using all quantities together
    all_quantities = [
        p["quantity_normalised"]
        for p in all_parsed
        if p.get("quantity_normalised") is not None
        and p["quantity_normalised"] > 0
    ]

    for parsed in all_parsed:
        if parsed.get("status") == "pending":
            qty = parsed.get("quantity_normalised")
            if qty and len(all_quantities) > 3:
                import statistics
                mean  = statistics.mean(all_quantities)
                stdev = statistics.stdev(all_quantities)
                if stdev > 0 and qty > mean + (3 * stdev):
                    parsed["status"]      = "flagged"
                    parsed["flag_reason"] = (
                        f"Consumption {qty} kWh is unusually high "
                        f"(>{round(mean + 3*stdev, 1)} kWh) — possible meter fault"
                    )

    return all_parsed