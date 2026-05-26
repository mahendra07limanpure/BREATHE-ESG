# DECISIONS.md — Design Decisions and Ambiguity Resolutions

**Author:** Mahendra Limanpure  
**Date:** May 25, 2026  
**Project:** Breathe ESG Tech Intern Assignment

---

## Overview

This document captures every significant design decision made during the prototype development, including what ambiguities existed, what choices were made, the rationale, and what would be asked of the PM in production.

---

## Decision 1: SAP Export Format — CSV Flat File vs. IDoc vs. OData

### The Ambiguity
SAP is the dominant ERP system for large Indian enterprises. It provides multiple export mechanisms, each with different complexity and accessibility profiles.

### Options Evaluated

| Mechanism | Complexity | Accessibility | Requires SAP Access | Realistic? |
|-----------|-----------|---|---|---|
| **IDoc (chosen)** | High | Low | Yes | No (prototype) |
| **OData/REST API** | Medium | Medium | Yes | No (prototype) |
| **BAPI (Remote Function)** | High | Low | Yes | No |
| **CSV Flat File** | Low | High | No | **Yes ✓** |

### Decision: CSV Flat File (MB51 Transaction)

**Why:**
- Most realistic onboarding scenario: Finance officer runs SAP transaction MB51, exports to spreadsheet, uploads file
- No live SAP credentials required — security win for external ESG vendor
- No middleware or SDK needed — prototype feasibility
- Matches how real clients actually share SAP data with external parties

**Implementation:**
- Parse SAP transaction MB51 (Material Documents) export
- Handle German column headers (BLDAT, MENGE, MEINS, MATNR, MAKTX, WERKS)
- Support date format YYYYMMDD without separators
- Handle unit inconsistencies (L, GAL, M3, KG)

**Tradeoff:**
Not a real-time integration — requires periodic file uploads rather than continuous sync.

**Question for PM in Production:**
"Will the client extract SAP data daily/weekly, or on-demand? Should we add scheduled exports or webhook triggers?"

---

## Decision 2: Electricity Data Source — CSV Portal vs. PDF Bill vs. API

### The Ambiguity
Indian facilities teams interact with electricity data in three ways: email PDF bills, download portal CSVs, or access utility APIs (rare). Each has different parsing complexity.

### Options Evaluated

| Mode | Parsing Complexity | Availability | Data Quality | Chosen? |
|------|---|---|---|---|
| **PDF Bill** | Very High | High (all utilities email) | Medium (contains billing periods, tariff) | No |
| **Portal CSV** | Low | Medium (most major utilities) | High (structured, machine-readable) | **Yes ✓** |
| **API** | Medium | Low (India lags on utility APIs) | High | No |

### Decision: Portal CSV Export

**Why:**
- Utilities like TATA Power, MSEDCL, BSES provide portal CSV exports
- Zero regex/OCR complexity — structured data rows instead of PDF parsing
- Captures meter ID, consumption units (kWh/kVAh), billing period start/end, tariff category
- Realistic for India's current state of utility digitalization

**Implementation:**
- Parse columns: meter_id, account_number, billing_period_start, billing_period_end, units_consumed, unit, tariff_category
- Handle kVAh → kWh conversion with default power factor 0.9 (flagged for analyst verification)
- Apportion consumption by calendar month when billing period crosses month boundary
- Detect meter unread (zero consumption) vs. meter fault (unusually high consumption)

**What Breaks in Production:**
- Utility changes CSV format between exports — no versioning notification
- Missing portal access due to account lockout
- Conflicting tariff structures (different rates in same period)

**Questions for PM in Production:**
1. "Should we support PDF parsing as fallback, or is CSV-only acceptable?"
2. "How do we handle tariff changes mid-billing-period?"
3. "Should state-specific CEA grid emission factors be applied, or national average?"

---

## Decision 3: Travel Data Source — Concur CSV vs. Navan API vs. Manual Entry

### The Ambiguity
Corporate travel platforms (Concur, Navan, SAP Concur, etc.) expose travel expense records via CSV exports or APIs. Distance is sometimes recorded, sometimes just airport codes.

### Options Evaluated

| Mechanism | Data Completeness | Setup Friction | Realistic? |
|-----------|---|---|---|
| **API (OAuth)** | Complete | High | Medium (API often restricted) |
| **CSV Export** | Complete | Low | **Yes ✓** |
| **Manual Paste** | Incomplete | Very High | No |

### Decision: CSV Export (Concur-style)

**Why:**
- Most travel platforms offer CSV export in their analytics/reporting interface
- No API authentication setup required
- Includes all fields: trip date, origin/destination (IATA codes or city names), distance_km, cabin_class, nights, amount_inr, vendor_name
- Matches how travel admins typically share data: monthly or quarterly exports

**Implementation:**
- Parse columns: trip_date, category (Flight/Hotel/Cab), origin, destination, distance_km, cabin_class, nights, amount_inr
- Resolve missing distances using Haversine formula from IATA airport coordinates + ICAO routing factor 1.09
- Map cabin class → emission factor (economy 0.255, business 0.357, first 0.510 kg CO2e/km)
- Normalize category variants: "flight" vs "airplane" vs "air", "taxi" vs "cab" vs "uber"

**What Breaks in Production:**
- Unknown airport codes (not in IATA database)
- Domestic vs. international indicator missing — affects RFI calculation
- Private/charter flights not in standard category list
- Hotel location mismatch — GPS coordinates expected but city name given

**Questions for PM in Production:**
1. "What's the default for missing cabin class — economy (conservative) or flag for review (safe)?"
2. "How do we handle private jet charters or road trips without distance?"
3. "Should we track round-trip vs. one-way flights separately?"

---

## Decision 4: Unit Normalization — Dual Storage vs. Recalculation at Query Time

### The Ambiguity
Should we store both raw and normalized quantities, or parse raw and recalculate at query time?

### Decision: Store Both (quantity_raw + quantity_normalised)

**Why:**
1. **Audit trail:** Original data must be preserved for auditor review
2. **Historical accuracy:** If emission factors are updated in future versions, old records retain the factor in force at calculation time. Recalculation at query time would silently change historical figures.
3. **Debugging:** If parser has a bug, raw data is still there; can re-parse without re-uploading the file
4. **Transparency:** Analyst sees both original value and conversion applied (e.g., "132.086 GAL → 499.6 L × 2.68 = 1338.9 kg CO2")

**Conversions Applied:**

| From | To | Factor | Source |
|------|-------|---|---|
| GAL (gallons) | L | × 3.785 | US gallon definition |
| M3 (cubic metres) | L | × 1000 | SI unit |
| kVAh | kWh | × 0.90 (default) | Power factor; flagged for analyst |
| LTR, LTRS (typos) | — | — | Flagged as unknown |

**What This Enables:**
- Auditor can reconstruct CO2 calculation step-by-step from raw data
- Parser bugs don't corrupt historical records
- Future emission factor updates apply only to new rows

---

## Decision 5: Scope Assignment — Automatic vs. Manual

### The Ambiguity
Should scope (1/2/3) be assigned by the analyst manually, or derived automatically from the activity type?

### Decision: Automatic from Activity Type at Parse Time

**Why:**
- Removes a class of human error
- Scope is deterministic: fuel combustion is always Scope 1, electricity is always Scope 2
- Faster analyst workflow (one less decision per row)

**Mapping:**

| Source | Activity | Scope | Reasoning |
|--------|----------|-------|-----------|
| SAP fuel | Diesel, Petrol, LPG | Scope 1 | Direct combustion in company-owned assets |
| SAP procurement | Steel, Concrete | Scope 3 | Upstream embodied emissions in purchased goods |
| Electricity | Grid consumption | Scope 2 | Indirect emissions from purchased electricity |
| Travel | Flights, Hotels, Cabs | Scope 3 | Indirect emissions from employee travel |

**What This Means:**
- Parser sets scope_field at ingest time; analyst cannot override
- If scope assignment is wrong, it's a parser bug, not an analyst decision
- Supports regulatory compliance: GRI/BRSR/CSRD scope definitions are fixed

---

## Decision 6: Flagging — Row-Level Automatic Checks vs. File-Level Heuristics

### The Ambiguity
Should suspicious rows be flagged individually with specific reasons, or should entire files be flagged for analyst review?

### Decision: Row-Level, 7 Automatic Checks

**Why:**
- Analyst efficiency: 95% of rows may be clean; they should batch-approve, not review the whole file
- Specificity: Each flag reason tells analyst exactly what to look for
- Auditability: Each flagged row has a reason in the audit log

**The Seven Automatic Checks:**

1. **Negative quantity** → Possible SAP reversal/return entry (valid, but needs verification)
2. **Zero quantity** → Meter unread, placeholder, or data entry error
3. **Future date** → Typo or data entry error (trip date in 2027?)
4. **Stale date** (before 2020) → Outside expected reporting period
5. **Unknown unit** → Cannot normalize (e.g., "DRUM" instead of "L")
6. **Unknown activity** → No emission factor available
7. **Statistical outlier** → Quantity > mean + 3σ for that activity (possible sensor fault or entry error)

**Analyst Workflow:**
```
PENDING (clean, automatic approval queue)
  ├─→ [Analyst] Bulk approve 50 at a time
  └─→ APPROVED → locked for audit

FLAGGED (suspicious)
  ├─→ [Analyst] Review reason, edit if needed, or reject
  └─→ APPROVED or REJECTED → locked
```

---

## Decision 7: Multi-Tenancy — Single-Tenant Prototype vs. Multi-Tenant Design

### The Ambiguity
Should the prototype handle multi-tenant data isolation, or assume a single client?

### Decision: Single-Tenant by Design, Multi-Tenant in Production (1-line migration)

**Why:**
- 4-day prototype constraint: multi-tenant adds complexity (tenant middleware, scoped queries, per-tenant onboarding)
- Core value is in the ingestion pipeline, not tenant isolation
- Adding multi-tenancy requires exactly one change: add `tenant_id` FK to UploadBatch and EmissionRecord
- All other logic remains the same; queries gain `.filter(tenant=request.tenant)`

**Current Implementation:**
- Client identity (TENANT_ID: T001, company_name: Tata Manufacturing Ltd) preserved in raw_data JSONField
- No tenant_id on tables yet

**Production Path:**
```sql
ALTER TABLE ingestion_uploadbatch ADD COLUMN tenant_id UUID NOT NULL;
ALTER TABLE ingestion_emissionrecord ADD COLUMN tenant_id UUID NOT NULL;
CREATE INDEX idx_uploadbatch_tenant ON ingestion_uploadbatch(tenant_id);
CREATE INDEX idx_emissionrecord_tenant ON ingestion_emissionrecord(tenant_id);
```

**Question for PM:**
"Will clients share one database or have isolated databases? Should analysts from one client ever see aggregated cross-client data?"

---

## Decision 8: Emission Factors — Hardcoded vs. Versioned Database Table

### The Ambiguity
Should emission factors be hardcoded in parser files or stored in a database table?

### Decision: Hardcoded for Prototype; Versioned Table in Production

**Why (Prototype):**
- Fewer database tables to manage
- Factors don't change during 4-day sprint
- Parser logic is self-contained

**Why (Production):**
- When IPCC updates factors (next AR7 ~ 2028), old records must retain old factors
- Analysts need audit trail of factor changes
- Versioned table: `EmissionFactor(activity_type, factor_value, effective_date, source, notes)`

**Current Hardcoded Factors:**

| Activity | Factor | Unit | Source |
|----------|--------|------|--------|
| Diesel | 2.68 | kg CO2e/L | IPCC AR6 / MoEFCC |
| Petrol | 2.31 | kg CO2e/L | IPCC AR6 |
| LPG | 2.98 | kg CO2e/kg | IPCC AR6 |
| Steel | 1.85 | kg CO2e/kg | IPCC AR6 |
| Concrete | 0.13 | kg CO2e/kg | IPCC AR6 |
| Electricity (India) | 0.82 | kg CO2e/kWh | CEA 2023 |
| Flight Economy | 0.255 | kg CO2e/km·pax | DEFRA 2023 |
| Flight Business | 0.357 | kg CO2e/km·pax | DEFRA 2023 |
| Hotel | 31.0 | kg CO2e/night | DEFRA 2023 |
| Cab/Taxi | 0.149 | kg CO2e/km | DEFRA 2023 |

---

## Decision 9: Audit Trail — AuditLog Insert-Only vs. Mutable

### The Ambiguity
Can the audit log be updated, or only appended?

### Decision: Insert-Only (Immutable)

**Why:**
- ESG reports are legal documents (BRSR, CSRD compliance)
- Auditors need to reconstruct decision history
- If audit log were mutable, a bad actor could erase approval history
- Implementation: never call `.update()` or `.delete()` on AuditLog table

**What Gets Logged:**
- Row auto-flagged during ingest (system action)
- Analyst approves row (analyst action)
- Analyst rejects row (analyst action)
- Analyst edits a value (analyst action, old + new value stored)

**Database Constraint:**
```sql
CREATE TABLE audit_log (
  id SERIAL PRIMARY KEY,
  record_id INT NOT NULL REFERENCES emission_record(id) ON DELETE CASCADE,
  action VARCHAR(20) NOT NULL,
  performed_by VARCHAR(255) NOT NULL,
  old_value TEXT,
  new_value TEXT,
  note TEXT,
  timestamp TIMESTAMP NOT NULL DEFAULT NOW()
);
-- No UPDATE or DELETE triggers; table is append-only
CREATE INDEX idx_audit_record ON audit_log(record_id);
```

---

## Decision 10: CO2 Total Calculation — Include Pending/Flagged or Approved Only?

### The Ambiguity
When computing total CO2 for a dashboard or report, should pending or flagged rows be included?

### Decision: Approved Only

**Why:**
- Regulatory compliance: CO2 totals sent to auditors cannot include unreviewed data
- Including pending rows: counts data the analyst hasn't verified
- Including flagged rows: counts data the system itself identified as suspicious
- Either would produce a figure indefensible to auditors

**Implementation:**
```python
def get_co2_summary():
    approved = EmissionRecord.objects.filter(status="approved")
    return {
        "total_kg": approved.aggregate(Sum("co2_kg"))["co2_kg__sum"] or 0,
        "scope_1_kg": approved.filter(scope="scope_1").aggregate(Sum("co2_kg"))["co2_kg__sum"] or 0,
        "scope_2_kg": approved.filter(scope="scope_2").aggregate(Sum("co2_kg"))["co2_kg__sum"] or 0,
        "scope_3_kg": approved.filter(scope="scope_3").aggregate(Sum("co2_kg"))["co2_kg__sum"] or 0,
    }
```

---

## Summary Table: All Decisions

| Decision | Choice | Rationale | Production Change |
|----------|--------|-----------|---|
| SAP Format | CSV Flat File | Realistic, no live credentials | Add scheduled exports |
| Electricity | Portal CSV | Available, structured | Add PDF fallback |
| Travel | Concur CSV | No API friction | Support multiple platforms |
| Unit Storage | Dual (raw + normalised) | Audit trail + immutability | No change |
| Scope Assignment | Automatic | Remove human error | No change |
| Flagging | Row-level, 7 checks | Analyst efficiency | Extend check list |
| Multi-Tenancy | Single-tenant | Scope constraint | 1-line migration |
| Emission Factors | Hardcoded | Simplicity | Versioned table |
| Audit Trail | Insert-only | Legal defensibility | Database constraint |
| CO2 Totals | Approved only | Regulatory compliance | No change |

---

**End of DECISIONS.md**
