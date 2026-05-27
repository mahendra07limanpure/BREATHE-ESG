from datetime import datetime, date
import math
from collections import defaultdict


# =====================================================
# EMISSION FACTORS
# Source: DEFRA 2023 UK Government GHG Conversion
# These are the most widely used factors globally
# for business travel reporting
# =====================================================
EMISSION_FACTORS = {
    "flight_economy":  0.255,   # kg CO2e per km per passenger
    "flight_business": 0.357,   # kg CO2e per km per passenger
    "flight_first":    0.510,   # kg CO2e per km per passenger
    "hotel":           31.0,    # kg CO2e per night
    "cab":             0.149,   # kg CO2e per km
    "taxi":            0.149,
    "train":           0.041,   # kg CO2e per km
    "bus":             0.089,   # kg CO2e per km
}

# =====================================================
# IATA AIRPORT COORDINATES
# Used to compute great-circle distance when the
# CSV only provides airport codes, not distance
# Source: OpenFlights airport database
# =====================================================
AIRPORT_COORDS = {
    # India
    "BOM": (19.0896, 72.8656),   # Mumbai
    "DEL": (28.5562, 77.1000),   # Delhi
    "BLR": (13.1979, 77.7063),   # Bangalore
    "MAA": (12.9900, 80.1693),   # Chennai
    "CCU": (22.6547, 88.4467),   # Kolkata
    "HYD": (17.2403, 78.4294),   # Hyderabad
    "AMD": (23.0772, 72.6347),   # Ahmedabad
    "PNQ": (18.5822, 73.9197),   # Pune
    "GOI": (15.3808, 73.8314),   # Goa
    "COK": (10.1520, 76.4019),   # Kochi
    # International
    "LHR": (51.4775, -0.4614),   # London Heathrow
    "DXB": (25.2532, 55.3657),   # Dubai
    "SIN": (1.3644, 103.9915),   # Singapore
    "JFK": (40.6413, -73.7781),  # New York JFK
    "CDG": (49.0097,  2.5479),   # Paris Charles de Gaulle
    "FRA": (50.0379,  8.5622),   # Frankfurt
    "NRT": (35.7720, 140.3929),  # Tokyo Narita
    "SYD": (-33.9399, 151.1753), # Sydney
    "HKG": (22.3080, 113.9185),  # Hong Kong
    "KUL": (2.7456,  101.7099),  # Kuala Lumpur
}

KNOWN_CATEGORIES = {"flight", "hotel", "cab", "taxi", "train", "bus"}


# =====================================================
# DATE PARSER
# Travel CSVs use YYYY-MM-DD format
# =====================================================
def parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(str(value).strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


# =====================================================
# HAVERSINE FORMULA
# Calculates great-circle distance between two
# lat/lon points in kilometres
#
# Why Haversine: it accounts for Earth's curvature
# giving ~0.5% accuracy which is sufficient for
# emissions estimation
# =====================================================
def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371   # Earth radius in km
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (math.sin(d_lat / 2) ** 2
         + math.cos(math.radians(lat1))
         * math.cos(math.radians(lat2))
         * math.sin(d_lon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 1)


# =====================================================
# DISTANCE RESOLVER
# Step 1: use distance_km from CSV if provided
# Step 2: compute from IATA codes using Haversine
# Step 3: flag if neither is possible
#
# ICAO routing factor 1.09 applied to great-circle
# distance — accounts for real flight paths not
# being perfectly straight
# =====================================================
ROUTING_FACTOR = 1.09   # ICAO standard indirect routing factor

def resolve_distance(row):
    """
    Returns (distance_km, resolution_method, flag_note)
    resolution_method: "csv" | "haversine" | "unknown"
    flag_note: None or reason string if flagging needed
    """
    # Try distance from CSV first
    raw_dist = row.get("distance_km")
    if raw_dist not in (None, ""):
        try:
            dist = float(raw_dist)
            # Check for NaN (empty CSV fields become NaN after pandas read)
            if math.isnan(dist):
                pass  # Fall through to IATA code resolution
            elif dist <= 0:
                return (None, "unknown",
                        "Distance is zero or negative — cannot calculate emissions")
            elif dist > 20000:
                return (None, "unknown",
                        f"Distance {dist} km is implausibly high — possible data entry error")
            else:
                return (dist, "csv", None)
        except (ValueError, TypeError):
            pass

    # Try computing from IATA codes
    origin = str(row.get("origin", "")).strip().upper()
    dest   = str(row.get("destination", "")).strip().upper()

    if origin and dest:
        origin_coords = AIRPORT_COORDS.get(origin)
        dest_coords   = AIRPORT_COORDS.get(dest)

        if origin_coords and dest_coords:
            gc_dist = haversine_km(*origin_coords, *dest_coords)
            actual_dist = round(gc_dist * ROUTING_FACTOR, 1)
            note = (f"Distance computed from IATA codes {origin}→{dest} "
                    f"({gc_dist} km great-circle × {ROUTING_FACTOR} routing factor = {actual_dist} km)")
            return (actual_dist, "haversine", None)

        # One or both airport codes not in our database
        if origin and origin not in AIRPORT_COORDS:
            return (None, "unknown",
                    f"Airport code '{origin}' not found in IATA database")
        if dest and dest not in AIRPORT_COORDS:
            return (None, "unknown",
                    f"Airport code '{dest}' not found in IATA database")

    # Neither distance nor valid airport codes
    return (None, "unknown",
            "Missing origin, destination, and distance — cannot calculate emissions")


# =====================================================
# CABIN CLASS RESOLVER
# Determines which emission factor to apply
# Defaults to economy if not specified
# =====================================================
def resolve_cabin_class(row):
    """
    Returns (emission_factor_key, flag_note)
    """
    # Try both 'cabin_class' and 'booking_class' field names
    cabin = str(row.get("cabin_class") or row.get("booking_class", "")).strip().lower()

    if "business" in cabin:
        return ("flight_business", None)
    if "first" in cabin:
        return ("flight_first", None)
    if "economy" in cabin or cabin == "":
        # Empty cabin class — use economy but flag
        if cabin == "":
            return ("flight_economy",
                    "Cabin class not specified — defaulted to economy (lower estimate)")
        return ("flight_economy", None)

    return ("flight_economy",
            f"Unrecognised cabin class '{cabin}' — defaulted to economy")


# =====================================================
# CATEGORY NORMALISER
# Maps raw category strings to standard values
# =====================================================
def normalise_category(raw_category):
    """
    Returns (standard_category, is_known)
    """
    if not raw_category:
        return ("unknown", False)

    cat = str(raw_category).strip().lower()

    mapping = {
        "flight":     "flight",
        "air":        "flight",
        "airplane":   "flight",
        "plane":      "flight",
        "airfare":    "flight",
        "hotel":      "hotel",
        "accommodation": "hotel",
        "lodging":    "hotel",
        "stay":       "hotel",
        "cab":        "cab",
        "taxi":       "cab",
        "uber":       "cab",
        "ola":        "cab",
        "ride":       "cab",
        "ground transportation": "cab",
        "train":      "train",
        "rail":       "train",
        "bus":        "bus",
        "coach":      "bus",
    }
    standard = mapping.get(cat)
    if standard:
        return (standard, True)

    return (cat, False)   # unknown category


# =====================================================
# NIGHTS PARSER
# For hotel rows — validates nights > 0
# =====================================================
def parse_nights(value):
    if value in (None, ""):
        return None
    try:
        n = int(float(str(value).strip()))
        return n if n > 0 else None
    except (ValueError, TypeError):
        return None


# =====================================================
# FLAG CHECKER
# Returns (status, flag_reason)
# =====================================================
def check_flags(parsed, all_distances=None):
    category = parsed.get("activity_type")
    qty      = parsed.get("quantity_normalised")
    dt       = parsed.get("record_date")
    amount   = parsed.get("_amount")
    cat_known    = parsed.get("_category_known", True)
    dist_method  = parsed.get("_distance_method", "csv")
    flag_note    = parsed.get("_flag_note")

    # Check 1 — unknown category (no emission factor)
    if not cat_known:
        return ("flagged",
                f"Unknown travel category '{parsed.get('_raw_category')}' — no emission factor available")

    # Check 2 — future trip date
    if dt is not None and dt > date.today():
        return ("flagged", f"Trip date {dt} is in the future — data entry error?")

    # Check 3 — stale date
    if dt is not None and dt.year < 2020:
        return ("flagged", f"Trip date {dt} is outside expected reporting period")

    # Check 4 — negative amount (refund row)
    if amount is not None and amount < 0:
        return ("flagged", "Negative amount — likely a refund or credit, not a trip")

    # Check 5 — cannot calculate distance (flagged by resolver)
    if flag_note:
        return ("flagged", flag_note)

    # Check 6 — zero or missing quantity
    if qty is None or qty <= 0:
        if category == "hotel":
            return ("flagged", "Zero or missing nights — cannot calculate hotel emissions")
        else:
            return ("flagged", "Zero or missing distance — cannot calculate travel emissions")

    # Check 7 — hotel with 0 nights
    if category == "hotel" and qty == 0:
        return ("flagged", "Hotel nights = 0 — data entry error")

    # Check 8 — distance computed from IATA codes (inform analyst)
    if dist_method == "haversine":
        return ("flagged",
                f"Distance estimated from airport codes using Haversine formula — "
                f"verify against actual flight distance")

    # Check 9 — outlier distance for cab (cab >500 km is suspicious)
    if category == "cab" and qty is not None and qty > 500:
        return ("flagged",
                f"Cab distance {qty} km is unusually high — possible data entry error")

    # Check 10 — statistical outlier across all rows
    if all_distances and qty is not None and len(all_distances) > 3:
        import statistics
        mean  = statistics.mean(all_distances)
        stdev = statistics.stdev(all_distances)
        if stdev > 0 and qty > mean + (3 * stdev):
            return ("flagged",
                    f"Distance/nights {qty} is unusually high "
                    f"(>{round(mean + 3*stdev, 1)}) — verify with employee")

    return ("pending", None)


# =====================================================
# SINGLE ROW PARSER
# =====================================================
def parse_travel_row(row):
    """
    Parses one row from a Concur-style travel CSV.
    Returns a single dict ready to save as EmissionRecord.
    """

    # ── Step 1: normalise category ──────────────
    # Try both 'category' and 'expense_type' field names
    raw_category = row.get("category") or row.get("expense_type", "")
    category, cat_known = normalise_category(raw_category)

    # ── Step 2: parse date ──────────────────────
    record_date = parse_date(row.get("trip_date"))

    # ── Step 3: parse amount ────────────────────
    try:
        amount = float(row.get("amount_inr", 0) or 0)
    except (ValueError, TypeError):
        amount = None

    # ── Step 4: resolve quantity and CO2 ────────
    emission_factor = 0.0
    co2_kg          = 0.0
    qty_raw         = None
    qty_norm        = None
    unit_norm       = None
    flag_note       = None
    dist_method     = "csv"
    cabin_flag      = None

    if category == "flight":
        # Resolve distance
        distance, dist_method, flag_note = resolve_distance(row)
        qty_raw  = row.get("distance_km")
        qty_norm = distance
        unit_norm = "km"

        # Resolve cabin class → emission factor
        ef_key, cabin_flag = resolve_cabin_class(row)
        emission_factor = EMISSION_FACTORS.get(ef_key, 0.255)

        # Combine flag notes
        if cabin_flag and not flag_note:
            flag_note = cabin_flag
        elif cabin_flag and flag_note:
            flag_note = flag_note + f" | {cabin_flag}"

        if distance is not None:
            co2_kg = round(distance * emission_factor, 4)

    elif category == "hotel":
        nights   = parse_nights(row.get("nights"))
        qty_raw  = row.get("nights")
        qty_norm = float(nights) if nights is not None else None
        unit_norm = "nights"
        emission_factor = EMISSION_FACTORS["hotel"]
        if nights is not None and nights > 0:
            co2_kg = round(nights * emission_factor, 4)

    elif category in ("cab", "taxi", "train", "bus"):
        raw_dist = row.get("distance_km")
        try:
            dist    = float(raw_dist) if raw_dist not in (None, "") else None
            # Check for NaN from pandas empty fields
            if dist is not None and math.isnan(dist):
                dist = None
        except (ValueError, TypeError):
            dist    = None
        qty_raw   = raw_dist
        qty_norm  = dist
        unit_norm = "km"
        ef_key    = category if category in EMISSION_FACTORS else "cab"
        emission_factor = EMISSION_FACTORS[ef_key]
        if dist is not None and dist > 0:
            co2_kg = round(dist * emission_factor, 4)

    else:
        # Unknown category — still save what we have
        qty_raw  = None
        qty_norm = None
        unit_norm = None

    # ── Step 5: build parsed dict ───────────────
    parsed = {
        "source_type":         "travel",
        "scope":               "scope_3",
        "activity_type":       category,
        "site_name":           str(row.get("destination", "")).strip(),
        "record_date":         record_date,

        # raw
        "quantity_raw":        qty_raw,
        "unit_raw":            unit_norm,

        # normalised
        "quantity_normalised": qty_norm,
        "unit_normalised":     unit_norm,

        # CO2
        "emission_factor":     emission_factor,
        "co2_kg":              co2_kg,

        # original row
        "raw_data":            dict(row),

        # internals for flag checker
        "_category_known":  cat_known,
        "_raw_category":    raw_category,
        "_distance_method": dist_method,
        "_flag_note":       flag_note,
        "_amount":          amount,
    }

    return parsed


# =====================================================
# BATCH PARSER
# =====================================================
def parse_travel_file(df):
    """
    df: pandas DataFrame of uploaded travel CSV.
    Returns list of dicts ready to save as EmissionRecords.
    """
    rows = df.to_dict(orient="records")

    # First pass: parse all rows
    all_parsed = [parse_travel_row(row) for row in rows]

    # Build quantity lists per category for outlier check
    qty_by_category = defaultdict(list)
    for p in all_parsed:
        qty = p.get("quantity_normalised")
        cat = p.get("activity_type")
        if qty is not None and qty > 0:
            qty_by_category[cat].append(qty)

    # Second pass: run flag checks
    results = []
    for parsed in all_parsed:
        cat = parsed.get("activity_type")
        all_quantities = qty_by_category.get(cat, [])

        status, flag_reason = check_flags(parsed, all_quantities)
        parsed["status"]      = status
        parsed["flag_reason"] = flag_reason

        # Remove internal keys
        for key in ("_category_known", "_raw_category",
                    "_distance_method", "_flag_note", "_amount"):
            parsed.pop(key, None)

        results.append(parsed)

    return results