from datetime import datetime, date

# =====================================================
# EMISSION FACTORS
# Source: IPCC AR6 / MoEFCC India
# All quantities must be in standard units before
# applying these (litres for fuel, kg for LPG/CNG)
# =====================================================
EMISSION_FACTORS = {
    "diesel": {"kg_co2e": 2.68, "per_unit": "L"},
    "petrol": {"kg_co2e": 2.31, "per_unit": "L"},
    "lpg":    {"kg_co2e": 2.98, "per_unit": "KG"},
    "cng":    {"kg_co2e": 2.54, "per_unit": "KG"},
}

# =====================================================
# UNIT CONVERSION
# Returns (converted_quantity, standard_unit, is_known)
# Separates the label from the math — bug fix #1
# =====================================================
KNOWN_UNITS = {"L", "LTR", "LTRS", "KG", "GAL", "M3", "KGS"}

def convert_unit(quantity, unit):
    """
    Converts raw quantity + unit into standard unit.
    Returns (normalised_quantity, normalised_unit, is_recognised)
    """
    if quantity is None or unit is None:
        return (None, None, False)

    unit = str(unit).strip().upper()

    # Unit not in our known list → flag it
    if unit not in KNOWN_UNITS:
        return (quantity, unit, False)   # is_recognised = False → will be flagged

    # Litres variants → L (no quantity change needed for L and LTR)
    if unit in ("L", "LTR", "LTRS"):
        return (quantity, "L", True)

    # Gallons → Litres (THE MISSING MATH — bug fix #1)
    if unit == "GAL":
        return (round(quantity * 3.785, 3), "L", True)

    # Cubic metres → Litres (bug fix #3)
    if unit == "M3":
        return (round(quantity * 1000, 3), "L", True)

    # Kilograms variants
    if unit in ("KG", "KGS"):
        return (quantity, "KG", True)

    return (quantity, unit, False)


# =====================================================
# SAP DATE PARSER
# SAP exports dates as YYYYMMDD with no separators
# Example: "20240115" → date(2024, 1, 15)
# =====================================================
def parse_sap_date(value):
    if value is None:
        return None
    value = str(value).strip()
    if len(value) != 8 or not value.isdigit():
        return None   # malformed date — caller will flag
    try:
        return datetime.strptime(value, "%Y%m%d").date()
    except ValueError:
        return None


# =====================================================
# QUANTITY PARSER
# Bug fix #2: your sample CSV uses English decimals
# (500.000) not German format (500,000).
# We detect the format instead of blindly applying
# German parsing to everything.
# =====================================================
def parse_quantity(value):
    if value is None:
        return None
    value = str(value).strip()
    if value == "":
        return None

    # German format: has both dot (thousands) AND comma (decimal)
    # Example: "1.200,50"
    if "," in value and "." in value:
        value = value.replace(".", "").replace(",", ".")
        return float(value)

    # German format: only comma as decimal separator
    # Example: "500,50"
    if "," in value and "." not in value:
        value = value.replace(",", ".")
        return float(value)

    # English format: dot as decimal (your sample CSV)
    # Example: "500.000" → 500.0
    return float(value)


# =====================================================
# ACTIVITY TYPE FROM MATERIAL NAME
# =====================================================
def determine_activity_type(material_name):
    if not material_name:
        return "unknown"
    name = str(material_name).strip().lower()

    if "diesel" in name:
        return "diesel"
    if "motor spirit" in name or "petrol" in name or "gasoline" in name:
        return "petrol"
    if "lpg" in name:
        return "lpg"
    if "cng" in name or "compressed natural gas" in name:
        return "cng"
    if "steel" in name:
        return "steel"
    if "concrete" in name:
        return "concrete"

    return "unknown"


# =====================================================
# SCOPE FROM ACTIVITY
# Bug fix: unknown activity → flag, not silent scope_3
# =====================================================
def determine_scope(activity):
    scope_map = {
        "diesel": "scope_1",
        "petrol": "scope_1",
        "lpg":    "scope_1",
        "cng":    "scope_1",
        "steel":    "scope_3",
        "concrete": "scope_3",
    }
    return scope_map.get(activity, None)   # None = unknown, will be flagged


# =====================================================
# PLANT MASTER LOOKUP
# Maps SAP WERKS code → readable site name
# Falls back to the code itself if not found
# =====================================================
def get_site_name(werks_code):
    """
    Tries to look up the plant code in PlantMaster DB table.
    Falls back to raw code if not found — still usable.
    """
    if not werks_code:
        return ""
    try:
        from ingestion.models import PlantMaster
        plant = PlantMaster.objects.filter(
            werks=str(werks_code).strip()
        ).first()
        if plant:
            return plant.site_name
    except Exception:
        pass
    return str(werks_code).strip()   # fallback to raw code


# =====================================================
# FLAG CHECKER
# Returns (status, flag_reason) for this row
# Called INSIDE the parser so every row is checked
# =====================================================
def check_flags(parsed, all_quantities=None):
    """
    Runs all 7 checks on a parsed row.
    Returns ("flagged", reason_string) or ("pending", None)

    all_quantities: list of all quantities for same material
                    used for statistical outlier check
    """
    qty  = parsed.get("quantity_normalised")
    unit = parsed.get("unit_normalised")
    dt   = parsed.get("record_date")
    activity = parsed.get("activity_type")
    unit_recognised = parsed.get("_unit_recognised", True)
    scope = parsed.get("scope")

    # Check 1 — negative quantity (SAP reversal entry)
    if qty is not None and qty < 0:
        return ("flagged", "Negative quantity — possible SAP reversal/return entry")

    # Check 2 — zero quantity
    if qty is not None and qty == 0:
        return ("flagged", "Zero quantity — placeholder or empty row")

    # Check 3 — future date
    if dt is not None and dt > date.today():
        return ("flagged", f"Future date {dt} — likely data entry error")

    # Check 4 — stale date (before 2020 is almost certainly wrong)
    if dt is not None and dt.year < 2020:
        return ("flagged", f"Date {dt} is outside expected reporting period")

    # Check 5 — unknown unit
    if not unit_recognised:
        return ("flagged", f"Unrecognised unit '{parsed.get('unit_raw')}' — cannot normalise")

    # Check 6 — unknown activity (no emission factor)
    if activity == "unknown":
        return ("flagged", f"Unknown material '{parsed.get('_material_name')}' — no emission factor found")

    # Check 7 — unknown scope
    if scope is None:
        return ("flagged", "Could not determine GHG scope for this activity")

    # Check 8 — statistical outlier (needs context from other rows)
    if all_quantities and qty is not None and len(all_quantities) > 3:
        import statistics
        mean = statistics.mean(all_quantities)
        stdev = statistics.stdev(all_quantities)
        if stdev > 0 and qty > mean + (3 * stdev):
            return ("flagged", f"Quantity {qty} is unusually high (>{round(mean + 3*stdev, 1)}) — verify with source team")

    return ("pending", None)


# =====================================================
# MAIN PARSER
# Call this once per CSV row
# =====================================================
def parse_sap_row(row):
    """
    Parses one row from a SAP MB51 flat-file CSV.
    Returns a dict ready to be saved as an EmissionRecord.
    """

    # ── Step 1: extract raw values ──────────────
    quantity_raw  = row.get("MENGE")
    unit_raw      = row.get("MEINS")
    material_name = row.get("MAKTX", "")
    werks         = row.get("WERKS", "")
    date_raw      = row.get("BLDAT")

    # ── Step 2: parse quantity (format-aware) ───
    qty_parsed = parse_quantity(quantity_raw)

    # ── Step 3: convert units (label + math) ───
    qty_norm, unit_norm, unit_recognised = convert_unit(qty_parsed, unit_raw)

    # ── Step 4: determine activity and scope ───
    activity = determine_activity_type(material_name)
    scope    = determine_scope(activity)

    # ── Step 5: emission factor + CO2 calc ─────
    factor_info = EMISSION_FACTORS.get(activity)
    if factor_info and qty_norm is not None:
        emission_factor = factor_info["kg_co2e"]
        co2_kg          = round(qty_norm * emission_factor, 4)
    else:
        emission_factor = 0.0
        co2_kg          = 0.0

    # ── Step 6: site name from PlantMaster ─────
    site_name = get_site_name(werks)

    # ── Step 7: build the parsed dict ──────────
    parsed = {
        "source_type": "sap_fuel",
        "scope":       scope or "scope_1",   # default scope_1 for fuel

        "activity_type": activity,
        "site_name":     site_name,
        "record_date":   parse_sap_date(date_raw),

        # raw — exactly as uploaded
        "quantity_raw": qty_parsed,
        "unit_raw":     unit_raw,

        # normalised — after conversion
        "quantity_normalised": qty_norm,
        "unit_normalised":     unit_norm,

        # CO2 calculation
        "emission_factor": emission_factor,
        "co2_kg":          co2_kg,

        # original row verbatim
        "raw_data": dict(row),

        # internal flags used by check_flags below
        "_unit_recognised": unit_recognised,
        "_material_name":   material_name,
    }

    return parsed


# =====================================================
# BATCH PARSER
# Parses entire CSV file, runs flag checks,
# returns list of dicts ready to bulk-create in DB
# =====================================================
def parse_sap_file(df):
    """
    df: pandas DataFrame of the uploaded SAP CSV

    Returns list of dicts ready to save as EmissionRecords.
    Removes internal _ keys before returning.
    """
    rows = df.to_dict(orient="records")
    parsed_rows = [parse_sap_row(row) for row in rows]

    # Build per-material quantity lists for outlier check
    from collections import defaultdict
    qty_by_activity = defaultdict(list)
    for p in parsed_rows:
        qty = p.get("quantity_normalised")
        act = p.get("activity_type")
        if qty is not None and qty > 0:
            qty_by_activity[act].append(qty)

    # Run flag checks on every row
    results = []
    for parsed in parsed_rows:
        activity = parsed.get("activity_type")
        all_quantities = qty_by_activity.get(activity, [])

        status, flag_reason = check_flags(parsed, all_quantities)

        parsed["status"]      = status
        parsed["flag_reason"] = flag_reason

        # Remove internal keys before saving
        parsed.pop("_unit_recognised", None)
        parsed.pop("_material_name", None)

        results.append(parsed)

    return results