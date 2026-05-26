import os
import logging
import pandas as pd
import math
from django.db import transaction

from ingestion.models import (
    UploadBatch,
    EmissionRecord,
    AuditLog,
)

from ingestion.parsers.sap_parser import parse_sap_file
from ingestion.parsers.electricity_parser import parse_electricity_file
from ingestion.parsers.travel_parser import parse_travel_file

logger = logging.getLogger(__name__)

# =====================================================
# PARSER ROUTER
# =====================================================
PARSER_MAPPING = {
    "sap_fuel":    parse_sap_file,
    "electricity": parse_electricity_file,
    "travel":      parse_travel_file,
}


# =====================================================
# CSV LOADER
# Tries UTF-8 first, falls back to latin-1
# SAP exports from Indian systems often use latin-1
# =====================================================
def load_csv(file_path):
    """
    Loads CSV with encoding fallback.
    Returns pandas DataFrame.
    Raises ValueError if file cannot be read.
    """
    for encoding in ("utf-8-sig", "utf-8", "latin-1", "cp1252"):
        try:
            df = pd.read_csv(file_path, encoding=encoding)
            # Strip whitespace from column names
            # SAP exports often have trailing spaces in headers
            df.columns = df.columns.str.strip()
            logger.info(
                f"Loaded {file_path} with encoding={encoding}, "
                f"shape={df.shape}"
            )
            return df
        except UnicodeDecodeError:
            continue
        except Exception as e:
            raise ValueError(f"Could not read CSV file: {e}")

    raise ValueError(
        f"Could not decode {file_path} with any supported encoding. "
        f"Try saving the file as UTF-8 in Excel before uploading."
    )


# =====================================================
# SAFE FLOAT
# Coerces None/bad values to 0.0
# Prevents FloatField crash on bulk_create
# =====================================================
def safe_float(value, default=0.0):
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


# =====================================================
# SAFE SCOPE
# Returns a valid scope string or "scope_1" default
# =====================================================
def safe_scope(value, source_type):
    valid = {"scope_1", "scope_2", "scope_3"}
    if value in valid:
        return value
    # Sensible defaults per source type
    defaults = {
        "sap_fuel":    "scope_1",
        "electricity": "scope_2",
        "travel":      "scope_3",
    }
    return defaults.get(source_type, "scope_1")


# =====================================================
# DUPLICATE BATCH CHECK
# Warns if same filename + source_type already exists
# Returns (is_duplicate, existing_batch_id)
# =====================================================
def check_duplicate_batch(file_name, source_type):
    existing = UploadBatch.objects.filter(
        file_name=file_name,
        source_type=source_type,
    ).order_by("-uploaded_at").first()

    if existing:
        return True, existing.id
    return False, None

# =====================================================
# CLEAN JSON
# Replaces NaN with None for PostgreSQL JSONB
# =====================================================

def clean_json_data(data):

    if isinstance(data, dict):

        return {
            k: clean_json_data(v)
            for k, v in data.items()
        }

    elif isinstance(data, list):

        return [
            clean_json_data(v)
            for v in data
        ]

    elif isinstance(data, float):

        if math.isnan(data):
            return None

    return data

# =====================================================
# BUILD EMISSION RECORD
# Safely builds one EmissionRecord from a parsed dict
# Returns (EmissionRecord, had_error, error_note)
# =====================================================
def build_record(row, upload_batch):
    """
    Converts one parsed dict → EmissionRecord object.
    Never raises — catches errors and marks row as flagged.
    """
    try:
        # Guard against None record_date
        record_date = row.get("record_date")
        if record_date is None:
            return (None, True, "Could not parse date — row skipped")

        source_type = row.get("source_type", upload_batch.source_type)

        record = EmissionRecord(
            upload_batch        = upload_batch,
            source_type         = source_type,
            scope               = safe_scope(
                                    row.get("scope"),
                                    source_type
                                  ),
            activity_type       = row.get("activity_type") or "unknown",
            site_name           = row.get("site_name") or "",
            record_date         = record_date,

            # raw — exactly as uploaded
            quantity_raw = safe_float(row.get("quantity_raw")),
            unit_raw     = row.get("unit_raw") or "",

            # normalised — after conversion
            quantity_normalised = safe_float(row.get("quantity_normalised")),
            unit_normalised     = row.get("unit_normalised") or "",

            # CO2
            emission_factor     = safe_float(row.get("emission_factor")),
            co2_kg              = safe_float(row.get("co2_kg")),

            # status from flag checker
            status              = row.get("status", "pending"),
            flag_reason         = row.get("flag_reason"),
            is_locked           = False,

            # original row verbatim
            raw_data = clean_json_data(
    row.get("raw_data") or {}
),
        )
        return (record, False, None)

    except Exception as e:
        logger.error(f"Error building record from row {row}: {e}")
        return (None, True, str(e))


# =====================================================
# MAIN INGESTION FUNCTION
# =====================================================
def ingest_file(
    file_path,
    source_type,
    uploaded_by="analyst",
    allow_duplicate=False,
):
    """
    Full ingestion pipeline for one uploaded CSV file.

    Steps:
      1. Load CSV with encoding fallback
      2. Route to correct parser
      3. Parse all rows (with per-row error handling)
      4. Create UploadBatch record
      5. Bulk-insert EmissionRecords
      6. Write AuditLog for every flagged row
      7. Return summary dict

    Everything inside a transaction — rolls back fully on crash.

    Args:
        file_path    : absolute path to the uploaded CSV
        source_type  : "sap_fuel" | "electricity" | "travel"
        uploaded_by  : analyst name or email
        allow_duplicate : if False, raises on duplicate filename

    Returns:
        dict with upload_batch_id, total_rows, flagged_rows,
        skipped_rows, and status summary
    """

    # ── Step 1: validate source type ────────────
    if source_type not in PARSER_MAPPING:
        raise ValueError(
            f"Unknown source_type '{source_type}'. "
            f"Must be one of: {list(PARSER_MAPPING.keys())}"
        )

    # ── Step 2: check for duplicate upload ──────
    file_name = os.path.basename(file_path)
    is_dup, dup_batch_id = check_duplicate_batch(file_name, source_type)

    if is_dup and not allow_duplicate:
        raise ValueError(
            f"File '{file_name}' was already uploaded "
            f"(batch #{dup_batch_id}). "
            f"Pass allow_duplicate=True to upload again."
        )

    # ── Step 3: load CSV ─────────────────────────
    df = load_csv(file_path)

    if df.empty:
        raise ValueError(f"CSV file '{file_name}' is empty.")

    # ── Step 4: parse rows ───────────────────────
    parser = PARSER_MAPPING[source_type]

    try:
        parsed_rows = parser(df)
    except Exception as e:
        raise ValueError(f"Parser failed for {source_type}: {e}")

    if not parsed_rows:
        raise ValueError("Parser returned zero rows.")

    # ── Step 5: everything in one transaction ────
    with transaction.atomic():

        # Create upload batch
        upload_batch = UploadBatch.objects.create(
            source_type  = source_type,
            file_name    = file_name,
            uploaded_by  = uploaded_by,
            total_rows   = 0,    # updated after building records
            flagged_rows = 0,    # updated after building records
        )

        # Build records with per-row error handling
        records      = []
        skipped_rows = []
        audit_entries = []

        for i, row in enumerate(parsed_rows):
            record, had_error, error_note = build_record(row, upload_batch)

            if had_error:
                # Row could not be built at all — log and skip
                skipped_rows.append({
                    "row_index": i,
                    "reason":    error_note,
                    "raw":       row.get("raw_data", {}),
                })
                logger.warning(f"Skipped row {i}: {error_note}")
                continue

            records.append(record)

        if not records:
            raise ValueError(
                f"All {len(parsed_rows)} rows failed to parse. "
                f"Check your CSV format."
            )

        # Bulk insert all records in one DB call
        EmissionRecord.objects.bulk_create(records)

        # Count flagged rows after insert
        flagged_count = sum(
            1 for r in records if r.status == "flagged"
        )

        # Update batch with final counts
        upload_batch.total_rows   = len(records)
        upload_batch.flagged_rows = flagged_count
        upload_batch.save()

        # Write AuditLog for every flagged row
        # This creates the audit trail showing when + why
        # each row was auto-flagged at ingest time
        for record in records:
            if record.status == "flagged":
                audit_entries.append(
                    AuditLog(
                        record       = record,
                        action       = "flagged",
                        performed_by = "system",
                        old_value    = "pending",
                        new_value    = "flagged",
                        note         = record.flag_reason or "Auto-flagged on ingest",
                    )
                )

        if audit_entries:
            AuditLog.objects.bulk_create(audit_entries)

        logger.info(
            f"Ingested {file_name}: "
            f"{len(records)} records, "
            f"{flagged_count} flagged, "
            f"{len(skipped_rows)} skipped"
        )

        return {
            "upload_batch_id": upload_batch.id,
            "source_type":     source_type,
            "file_name":       file_name,
            "total_rows":      len(records),
            "flagged_rows":    flagged_count,
            "pending_rows":    len(records) - flagged_count,
            "skipped_rows":    len(skipped_rows),
            "skipped_detail":  skipped_rows,   # useful for debugging
        }