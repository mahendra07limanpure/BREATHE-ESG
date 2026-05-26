# MODEL.md — Data Model and Design Rationale

**Author:** Mahendra Limanpure · B.Tech, IIT Roorkee  
**Client modelled:** Tata Manufacturing Ltd (`TENANT_ID: T001`)  
**Assignment:** Breathe ESG Tech Intern Prototype

---

## Overview

This document explains every table in the database, every significant field,
and — more importantly — **why** each design decision was made.

The data model must satisfy five requirements from the assignment brief:

| Requirement | How it is satisfied |
|---|---|
| Multi-tenancy | Conscious single-tenant decision — documented below |
| Scope 1/2/3 categorisation | `scope` field on every `EmissionRecord` row |
| Source-of-truth tracking | `UploadBatch` table linked to every record |
| Unit normalisation | Dual fields: `quantity_raw` + `quantity_normalised` |
| Audit trail | Insert-only `AuditLog` table |

---

## Multi-Tenancy Decision

The assignment requires the model to handle multi-tenancy. This prototype
implements **single-tenant architecture** by design, not by oversight.

**Why:**  
The sample data represents one real organisation — Tata Manufacturing Ltd.
Adding a `Tenant` foreign key to every table in a 4-day prototype would add
significant complexity (tenant-scoped queries, tenant middleware, per-tenant
onboarding flows) without demonstrating anything new about the core data
pipeline, which is what this assignment evaluates.

**What is stored instead:**  
The company identity (`TENANT_ID: T001`, `company_name: Tata Manufacturing Ltd`)
is preserved verbatim in the `raw_data` JSONField of every `EmissionRecord`.
This means the source data is never stripped of its organisational context.

**How multi-tenancy would be added in production:**  
It requires exactly one change to this model — adding a `Tenant` FK to
`UploadBatch` and `EmissionRecord`. Every query would then gain a
`.filter(tenant=request.tenant)` clause. The rest of the model is
already designed to support this cleanly.

**What I would ask the PM:**  
- Will clients share one database or have isolated databases?
- Should analysts from one client ever see aggregated cross-client data?

---

## Table 1: UploadBatch

```
Purpose: Source-of-truth tracking.
         One row per uploaded CSV file.
         Every EmissionRecord links back to the batch that created it.
```

### Fields

| Field | Type | Why |
|---|---|---|
| `source_type` | CharField (choices) | `sap_fuel`, `electricity`, or `travel` — determines which parser runs |
| `file_name` | CharField | Original filename as uploaded — used for duplicate detection |
| `uploaded_by` | CharField | Analyst name or email — accountability for who uploaded |
| `uploaded_at` | DateTimeField (auto) | Exact timestamp of upload — part of the audit chain |
| `total_rows` | IntegerField | Updated after ingestion — lets dashboard show batch-level summary |
| `flagged_rows` | IntegerField | Pre-computed count — avoids expensive COUNT query on every dashboard load |

### Why this table exists

Without `UploadBatch`, the question *"where did this row come from?"*
is unanswerable. If an analyst finds a suspicious record in the dashboard,
they need to know: which file contained it, when it was uploaded, and who
uploaded it. This table answers all three.

It also enables **duplicate upload detection** — if the same filename
is uploaded twice for the same source type, the ingestion service raises
a warning before creating duplicate records.

### Relationship

```
UploadBatch (1) ──────────── (many) EmissionRecord
```

Every `EmissionRecord` has a `ForeignKey` to `UploadBatch`. Deleting a
batch (`CASCADE`) removes all its records — this is intentional: if an
upload was entirely wrong, the analyst can delete the batch cleanly.

---

## Table 2: EmissionRecord

```
Purpose: Core table. One row per line of ingested CSV data.
         Stores raw values, normalised values, CO2 calculation,
         review status, and the original row verbatim.
```

This is the table the analyst sees in the dashboard. Every design
decision here is about making the analyst's review job reliable and
traceable.

### Source and Scope fields

```python
source_type = CharField(choices=["sap_fuel", "electricity", "travel"])
scope       = CharField(choices=["scope_1", "scope_2", "scope_3"])
```

**`source_type`** records which system the data came from. This is set
by the parser at ingest time and never changes. It drives the dashboard
filter tabs (SAP / Electricity / Travel).

**`scope`** records the GHG Protocol category. It is set automatically
at parse time, not manually by the analyst:

| Source | Scope | Reasoning |
|---|---|---|
| SAP fuel (diesel, petrol, LPG) | Scope 1 | Direct combustion in company-owned assets |
| SAP procurement (steel, concrete) | Scope 3 | Upstream embodied emissions in purchased goods |
| Electricity | Scope 2 | Indirect emissions from purchased grid electricity |
| Corporate travel | Scope 3 | Indirect emissions from employee business travel |

Scope is derived from the activity type during parsing, so the analyst
never needs to assign it manually. This removes a class of human error.

### Unit Normalisation fields

```python
quantity_raw        = FloatField()    # exactly as it came from the CSV
unit_raw            = CharField()     # exactly as it came from the CSV
quantity_normalised = FloatField()    # after conversion to standard unit
unit_normalised     = CharField()     # standard unit (L, kWh, km, nights)
```

**Why keep both raw and normalised?**

The raw values are the legal source of truth — they are what the client's
system actually recorded. If a row arrived as `132.086 GAL`, that number
must be preserved even after it is converted to `499.6 L` for the
emission calculation.

If an auditor later questions a CO2 figure, the analyst can show:
- Original value: `132.086 GAL` (from raw_data)
- Conversion applied: `× 3.785 = 499.6 L`
- Emission factor: `× 2.68 kg CO2/L = 1338.9 kg CO2`

Without `quantity_raw`, the intermediate conversion step is invisible.

**Conversions applied by the parsers:**

| From | To | Factor | Source |
|---|---|---|---|
| GAL (gallons) | L | × 3.785 | US gallon definition |
| M3 (cubic metres) | L | × 1000 | SI unit |
| LTRS, LTR (typo variants) | Flagged | — | Unknown → analyst reviews |
| kVAh | kWh | × 0.90 (default power factor) | Flagged for analyst verification |

### CO2 Calculation fields

```python
emission_factor = FloatField()   # kg CO2e per normalised unit
co2_kg          = FloatField()   # = quantity_normalised × emission_factor
```

Emission factors are hardcoded in the parser files, sourced from
internationally recognised publications:

| Activity | Factor | Unit | Source |
|---|---|---|---|
| Diesel | 2.68 | kg CO2e / litre | IPCC AR6 / MoEFCC India |
| Petrol (Motor Spirit) | 2.31 | kg CO2e / litre | IPCC AR6 / MoEFCC India |
| LPG Industrial | 2.98 | kg CO2e / kg | IPCC AR6 |
| Structural Steel | 1.85 | kg CO2e / kg | IPCC AR6 (Scope 3) |
| Concrete Mix | 0.13 | kg CO2e / kg | IPCC AR6 (Scope 3) |
| Electricity (India grid) | 0.82 | kg CO2e / kWh | CEA India 2023 |
| Flight economy | 0.255 | kg CO2e / km·pax | DEFRA 2023 |
| Flight business | 0.357 | kg CO2e / km·pax | DEFRA 2023 |
| Hotel | 31.0 | kg CO2e / night | DEFRA 2023 |
| Cab / taxi | 0.149 | kg CO2e / km | DEFRA 2023 |

Both `emission_factor` and `co2_kg` are stored on the record — not
recomputed at query time. This is important: if the emission factor
reference values are updated in a future version, historical records
retain the factor that was in force when they were calculated. Recalculation
at query time would silently change historical figures.

### Review Status fields

```python
status      = CharField(choices=["pending", "flagged", "approved", "rejected"])
flag_reason = TextField(nullable)
is_locked   = BooleanField(default=False)
```

**Why four statuses and not a boolean?**

A boolean `is_flagged` (as in the original code) cannot represent the
full lifecycle of a record:

```
PENDING  → ingested, clean, awaiting analyst bulk-approval
FLAGGED  → ingested, suspicious, requires individual analyst review
APPROVED → analyst verified, is_locked=True, counted in CO2 totals
REJECTED → analyst determined this row is wrong, excluded from totals
```

A boolean collapses `pending` and `approved` into the same `False` state,
making it impossible to distinguish "not yet reviewed" from "reviewed and
confirmed". This would corrupt the CO2 total — unapproved rows would be
included.

**`is_locked`** is set to `True` when a record is approved. After locking,
the `approve()` and `reject()` methods on the model enforce immutability —
a locked record cannot be changed without going through the AuditLog.
This is the technical enforcement of the audit requirement.

**`flag_reason`** stores a human-readable explanation of why the row was
flagged. Examples from the automatic checker:

```
"Negative quantity — possible SAP reversal/return entry"
"Unrecognised unit 'DRUM' — cannot normalise"
"Quantity 50000.0 is unusually high (>1823.4) — verify with source team"
"Future date 2027-01-15 — likely data entry error"
```

The analyst sees this reason in the dashboard before deciding to approve
or reject.

### Traceability fields

```python
raw_data   = JSONField()              # complete original CSV row
created_at = DateTimeField(auto_now_add=True)
updated_at = DateTimeField(auto_now=True)
```

**`raw_data`** stores the entire original CSV row as a JSON object.
Nothing from the source is discarded. This serves three purposes:

1. **Auditability** — an auditor can always see exactly what the source
   system sent, even if the parsed values look different after normalisation.
2. **Debugging** — if a parser has a bug, the original data is still there
   to re-parse without re-uploading the file.
3. **Future fields** — if a new field becomes relevant (e.g. cost centre
   `KOSTL` from SAP), it is already in `raw_data` and can be extracted
   without re-ingestion.

**`updated_at`** tracks the last modification time of the record.
Combined with the `AuditLog`, this creates two layers of change tracking:
the field-level timestamp and the action-level log.

---

## Table 3: AuditLog

```
Purpose: Append-only audit trail.
         Every approve, reject, edit, and auto-flag action
         is recorded here and never deleted.
```

### Fields

| Field | Type | Why |
|---|---|---|
| `record` | ForeignKey → EmissionRecord | Which record was acted on |
| `action` | CharField (choices) | `approved`, `rejected`, `edited`, `flagged` |
| `performed_by` | CharField | `"analyst"` for human actions, `"system"` for auto-flags |
| `old_value` | TextField (nullable) | Value before the action |
| `new_value` | TextField (nullable) | Value after the action |
| `note` | TextField | Human comment or system flag reason |
| `timestamp` | DateTimeField (auto) | When the action occurred |

### Why this table is insert-only

ESG audit reports are legal documents in jurisdictions that mandate
GHG disclosure (BRSR under SEBI, forthcoming CSRD). An auditor reviewing
a company's Scope 1 figure needs to be able to reconstruct the full
decision history for every record that contributed to that figure.

If the AuditLog were mutable (rows could be updated or deleted),
that reconstruction would be impossible — a bad actor could erase
approval history. The application enforces insert-only by never calling
`.update()` or `.delete()` on this table. The `ordering = ["timestamp"]`
meta ensures the log always reads chronologically.

### What gets logged

| Event | `performed_by` | `action` | `note` |
|---|---|---|---|
| Row auto-flagged during ingest | `"system"` | `"flagged"` | Flag reason string |
| Analyst approves a record | `"analyst"` | `"approved"` | Optional comment |
| Analyst rejects a record | `"analyst"` | `"rejected"` | Optional comment |
| Analyst edits a value | `"analyst"` | `"edited"` | Old and new value stored |

---

## Table 4: PlantMaster

```
Purpose: SAP plant code lookup table.
         Maps WERKS codes to human-readable site names.
```

### Why this table exists

SAP exports plant codes as short codes (`PL01`, `PL02`, `PL03`, `PL04`).
These codes are meaningful only within the client's SAP configuration.
Without a lookup table, the dashboard would show `PL01` instead of
`Mumbai Plant`, making it impossible for an analyst to identify which
facility a record belongs to.

**Fields:**

| Field | Type | Why |
|---|---|---|
| `werks` | CharField (unique) | SAP plant code — unique constraint prevents duplicates |
| `site_name` | CharField | Human-readable name e.g. `"Mumbai Plant"` |
| `city` | CharField | Optional — useful for state-level electricity factors |
| `state` | CharField | Optional — used to select correct CEA state grid factor |

**Tata Manufacturing Ltd plant codes in sample data:**

| WERKS | Site name | City | State |
|---|---|---|---|
| PL01 | Mumbai Plant | Mumbai | Maharashtra |
| PL02 | Pune Factory | Pune | Maharashtra |
| PL03 | Delhi Warehouse | Delhi | Delhi |
| PL04 | Gujarat Unit | Ahmedabad | Gujarat |

The parser calls `PlantMaster.objects.filter(werks=...).first()` and
falls back to the raw code if no entry exists — so missing plant master
entries degrade gracefully rather than crashing.

---

## CO2 Total Calculation

Only `approved` records are included in the CO2 total. Records with
status `pending`, `flagged`, or `rejected` are explicitly excluded.
This is enforced by filtering on `status="approved"` in every
aggregation query.

```python
from django.db.models import Sum
from ingestion.models import EmissionRecord

def get_co2_summary():
    approved = EmissionRecord.objects.filter(status="approved")
    return {
        "total_kg":     approved.aggregate(Sum("co2_kg"))["co2_kg__sum"] or 0,
        "total_tonnes": (approved.aggregate(Sum("co2_kg"))["co2_kg__sum"] or 0) / 1000,
        "scope_1_kg":   approved.filter(scope="scope_1").aggregate(Sum("co2_kg"))["co2_kg__sum"] or 0,
        "scope_2_kg":   approved.filter(scope="scope_2").aggregate(Sum("co2_kg"))["co2_kg__sum"] or 0,
        "scope_3_kg":   approved.filter(scope="scope_3").aggregate(Sum("co2_kg"))["co2_kg__sum"] or 0,
    }
```

**Why only approved records?**

Including `pending` rows would count data the analyst has not yet
verified. Including `flagged` rows would count data the system itself
identified as suspicious. Either would produce a CO2 figure that could
not be defended to an auditor.

The review dashboard exists precisely to gate records from
`pending/flagged` → `approved` before they contribute to the total.

---

## Entity Relationship Summary

```
UploadBatch
    │
    │  one batch per uploaded file
    │  (source_type, file_name, uploaded_by, uploaded_at)
    │
    ├──── EmissionRecord (many)
    │         │
    │         │  one record per CSV row
    │         │  (scope, activity_type, quantity_raw,
    │         │   quantity_normalised, co2_kg, status,
    │         │   is_locked, raw_data)
    │         │
    │         └──── AuditLog (many)
    │                   (action, performed_by, old_value,
    │                    new_value, note, timestamp)
    │
PlantMaster  (standalone lookup)
    (werks → site_name, city, state)
```

---

## What this model deliberately does not include

These are documented fully in `TRADEOFFS.md`:

1. **Tenant table** — single-tenant prototype; FK can be added in one migration.
2. **EmissionFactor table** — factors are hardcoded in parser files;
   a versioned DB table would be the production approach.
3. **User authentication table** — `uploaded_by` and `performed_by` are
   plain `CharField` values, not FKs to a User model. Django's built-in
   auth system would replace this in production.