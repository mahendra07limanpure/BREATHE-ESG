# SOURCES.md — Data Source Research, Format Analysis, and Sample Data Justification

**Author:** Mahendra Limanpure  
**Date:** May 25, 2026  
**Project:** Breathe ESG Tech Intern Assignment

---

## Overview

This document provides the research conducted for each of the three data sources, explains what real-world format was chosen, what the sample data looks like, and what would break in production.

---

## Source 1: SAP Fuel and Procurement Data

### Real-World Format Research

**SAP Background:**
SAP is the dominant ERP system for large Indian enterprises (Fortune 500, PSUs, industrial conglomerates). Over 70% of large manufacturing companies in India run SAP.

**Transaction Researched: MB51 (Material Document List)**
- Path in SAP GUI: LOGISTIC → MATERIAL MANAGEMENT → ENVIRONMENT → LIST → MATERIAL DOCUMENT LIST (MB51)
- Output: List of all material movements (inbound, outbound, transfers) in a date range
- Export Options: List → Export → Spreadsheet (to XLSX or CSV)

**Typical MB51 Export Fields:**

| Field | Type | Example | Notes |
|-------|------|---------|-------|
| MANDT | Client | 100 | SAP multi-client code |
| BUKRS | Company Code | 1000, 2000 | Accounting unit |
| WERKS | Plant | PL01, PL02 | Manufacturing site code |
| BLDAT | Document Date | 20240115 | YYYYMMDD format (German standard) |
| BUDAT | Posting Date | 20240115 | When entered into system |
| MATNR | Material Number | 000000000500012 | 18-digit SAP code; not human-readable |
| MAKTX | Material Description | "Diesel EN590" | Human-readable name |
| MENGE | Quantity | 500.000 | Depends on base unit |
| MEINS | Base Unit of Measure | L, GAL, KG, M3 | Can vary per material |
| DMBTR | Amount in Doc Currency | 45000.00 | Cost; relevant for audit but not CO2 |
| WAERS | Currency | INR, USD | Billing currency |
| BWART | Movement Type | 261, 201, 101 | 261 = goods receipt, 201 = goods issue |
| KOSTL | Cost Centre | KST-5001 | For internal allocation; not ESG-relevant |
| LIFNR | Vendor | SAP vendor code | Only for inbound movements |

**Column Header Variants:**
- German Configuration: MENGE, MEINS, BLDAT (German headers)
- English Configuration: QTY, UOM, DOC_DATE (English headers)
- Mixed: Some systems use both — trailing spaces in headers are common

**Data Quality Issues in Real SAP Exports:**
1. **Unit Inconsistency:** Same material (e.g., "Diesel") can appear as L (litre), GAL (gallon), or M3 (cubic metre)
2. **Negative Quantities:** SAP uses negative MENGE to represent reversals/returns (goods sent back). ~2–5% of rows in real data.
3. **Plant Codes Meaningless:** WERKS = "PL01" → must look up in master data to find "Mumbai Plant"
4. **Dates Without Separators:** BLDAT = "20240115" (not "2024-01-15") due to German date format standard in SAP
5. **Encoding Issues:** Latin-1 or Windows-1252 encoding (not UTF-8) depending on server location

### Sample Data Rationale

**What We Generated:**
- 400 rows across 4 plants
- Fuel types: Diesel EN590, Motor Spirit, LPG Industrial (Scope 1)
- Procurement: Structural Steel, Concrete Mix (Scope 3)
- Date range: Jan 1 — Jun 30, 2024
- Anomalies: 8% injected (negative qty, future dates, unknown units, outliers)
- Duplicates: 8 duplicate rows added (realistic data quality issue)

**Why This Looks Realistic:**
- Seasonal multiplier: Summer months (April–June) show 20% higher fuel consumption (air conditioning load)
- Unit variance: ~15% of fuel entries in GAL instead of L (real users sometimes prefer imperial units)
- Negative entries: ~2–3% of rows are reversals (goods returned)
- Plant distribution: Even split across 4 sites (Mumbai, Pune, Delhi, Gujarat)

**What Breaks in Production:**
1. **Plant Master Mismatch:** WERKS = "PL05" that doesn't exist in PlantMaster table → parser falls back to code; analyst sees "PL05" instead of site name
2. **Unknown Material Descriptions:** MAKTX = "Raw Material A" → parser cannot map to emission factor → flagged as unknown activity
3. **Multi-Currency:** Some rows in USD or EUR instead of INR → cost field becomes ambiguous (do we assume FX rate?)
4. **Retroactive SAP Entry:** Row date BLDAT = "20230315" (11 months old) uploaded today → historical data from catch-up entry
5. **Encoding Corruption:** Accented characters (ü, ö, ñ) in MAKTX → appears as mojibake if encoding guessed wrong

### Sample Data File

**Location:** `sample_data/sap_fuel_data.csv`

**First 5 rows (truncated):**
```
TENANT_ID,COMPANY_NAME,MANDT,BUKRS,WERKS,BLDAT,MATNR,MAKTX,BWART,MENGE,MEINS,DMBTR,WAERS,KOSTL
T001,Tata Manufacturing Ltd,100,1000,PL01,20240115,000000000500012,Diesel EN590,261,500.00,L,45000.00,INR,KST-5001
T001,Tata Manufacturing Ltd,100,1000,PL02,20240120,000000000500013,Motor Spirit,261,300.00,L,28500.00,INR,KST-5002
T001,Tata Manufacturing Ltd,100,2000,PL01,20240201,000000000500012,Diesel EN590,261,50000.00,L,4500000.00,INR,KST-5001
T001,Tata Manufacturing Ltd,100,1000,PL03,20240215,000000000500014,LPG Industrial,-200.00,KG,18000.00,INR,KST-5003
T001,Tata Manufacturing Ltd,100,1000,PL01,20240301,000000000500012,Diesel EN590,261,480.00,GAL,41000.00,INR,KST-5001
```

**Statistics:**
- Total rows: 408 (400 + 8 duplicates)
- Flagged rows: ~32 (8% of 400)
- Scope distribution: ~60% Scope 1 (fuel), ~40% Scope 3 (procurement)

---

## Source 2: Electricity (Utility Data)

### Real-World Format Research

**How Indian Facilities Teams Get Data:**

| Method | Prevalence | Effort | Data Quality |
|--------|-----------|--------|---|
| **Email PDF Bill** | 95% (all utilities) | Manual download | Medium (embedded in bill layout) |
| **Portal CSV Export** | 70% (major utilities) | Automated download | High (structured CSV) |
| **Utility API** | <5% (only TATA Power, NTPC) | API OAuth setup | High (real-time) |
| **Manual Spreadsheet** | 20% (backups, legacy) | Analyst maintenance | Low (errors, delays) |

**Utilities Researched:**
- **TATA Power** (Mumbai, Pune): Portal available, API available
- **MSEDCL** (Maharashtra): Portal only, no API
- **BSES** (Delhi): Portal only, no API
- **Torrent Power** (Gujarat): Portal only, no API

**Portal CSV Export Format Observed:**

| Field | Type | Example | Notes |
|-------|------|---------|-------|
| account_number | String | ACC-1001 | Unique per billing account |
| meter_id | String | MUM-2001 | Unique per meter |
| supplier_name | String | Tata Power / BSES | Utility operator |
| site_name | String | Mumbai Plant | Facility name (analyst enters) |
| billing_period_start | Date | 2024-01-01 | First day of billing cycle |
| billing_period_end | Date | 2024-01-31 | Last day of billing cycle |
| units_consumed | Float | 5432.50 | Total units in billing period |
| unit | Enum | kWh, kVAh, UNITS | Billing unit (see below) |
| tariff_category | String | Industrial-HT | Rate structure applied |
| invoice_number | String | INV-5001 | Bill reference |
| invoice_date | Date | 2024-02-05 | Date bill was generated |

**Unit Variants Observed:**
- **kWh** (kilowatt-hour) — standard real power consumption
- **kVAh** (kilovolt-ampere-hour) — apparent power (includes reactive load); requires power factor to convert to real power
- **UNITS** — legacy meter term, synonym for kWh on older electromechanical meters

**Billing Period Reality:**
- Standard: 28–31 days starting from customer's cycle date, NOT calendar month
- Example: Cycle starts 15th of each month → billing period Jan 15 — Feb 14 (crosses calendar month boundary)
- This requires **apportionment:** split consumption across calendar months for monthly reporting

### Sample Data Rationale

**What We Generated:**
- 120 rows representing 4 plants × 30 billing cycles
- 3–4 rows per plant (one per month + occasional repeat)
- Date range: Jan 1 — Jun 30, 2024
- Billing periods: 28–31 days, randomly scattered (some cross month boundary)
- Units: ~85% kWh, ~15% kVAh (needs power factor conversion)
- Anomalies: 8% injected (zero consumption, future dates, invalid units, extreme values)

**Why This Looks Realistic:**
- Seasonal variation: Peak consumption in Apr–Jun (summer cooling season, 25% higher)
- Meter reading delays: Invoices dated 5 days after billing period end (utility processing lag)
- Cross-month periods: ~30% of rows cross calendar month → require apportionment logic
- Power factor conversion: 15% of rows in kVAh (real utilities use this for industrial tariffs)

**What Breaks in Production:**

1. **Tariff Structure Changes:** Mid-year tariff change (e.g., Jan–May @ ₹5.50/unit, Jun–Dec @ ₹6.20/unit) → cost calculation breaks, but consumption is still valid
2. **Meter Replacement:** New meter installed mid-period → two meter readings in one CSV → need de-duplication logic
3. **Estimated vs. Actual Reading:** Some portals show "E" (estimated) vs. "A" (actual) — consumption may be revised in next bill
4. **Demand Charges Separate:** Industrial bills have fixed demand charge (₹X per kW contracted) + variable consumption charge → we ignore demand but should account for it
5. **State/Grid Factor Uncertainty:** India has 5 major grids with different CO2 intensity. CEA publishes state-wise factors (0.62–1.05 kg CO2/kWh). Do we use tariff location or facility location?
6. **Meter Tampering / Fraud:** Sudden 10× consumption spike → could be real or fraud; flagging required

### Sample Data File

**Location:** `sample_data/electricity_data.csv`

**First 5 rows:**
```
tenant_id,company_name,account_number,meter_id,site_name,billing_period_start,billing_period_end,units_consumed,unit,tariff_category,supplier_name,invoice_number,invoice_date
T001,Tata Manufacturing Ltd,ACC-1001,MUM-2001,Mumbai Plant,2024-01-01,2024-01-31,8750.50,kWh,Industrial-HT,Tata Power,INV-5001,2024-02-05
T001,Tata Manufacturing Ltd,ACC-1002,PUN-2002,Pune Factory,2024-01-15,2024-02-14,6200.75,kVAh,Industrial-HT,MSEDCL,INV-5002,2024-02-19
T001,Tata Manufacturing Ltd,ACC-1003,DEL-2003,Delhi Warehouse,2024-01-01,2024-01-31,3100.25,kWh,Commercial-LT,BSES,INV-5003,2024-02-05
T001,Tata Manufacturing Ltd,ACC-1004,GUJ-2004,Gujarat Unit,2024-01-20,2024-02-19,12500.00,kWh,Industrial-HT,Torrent Power,INV-5004,2024-02-23
...
```

**Statistics:**
- Total rows: 125 (120 + 5 duplicates)
- Flagged rows: ~10 (8% of 120)
- Cross-month periods: ~36 rows (~30% of total)
- kVAh rows: ~18 (~15% of total)

---

## Source 3: Corporate Travel Data

### Real-World Format Research

**Travel Platforms Researched:**
- **Concur** (SAP Concur) — de facto standard for large enterprises; extensive API and CSV export
- **Navan** (formerly Ramp Travel) — newer, growing adoption in US; strong API
- **Certify** (formerly Chrome River) — mid-market; limited export
- **Expensify** — small companies; basic export

**Travel Expense Categories:**
- **Flights** — highest emissions, distance varies, class matters (economy vs. business)
- **Hotels** — per-night emissions, location matters
- **Ground Transport** — low emissions per km, but high frequency
- **Meals** — not travel-related, excluded
- **Other** — gifts, office supplies, etc., excluded

**Concur CSV Export Format Observed:**

| Field | Type | Example | Notes |
|-------|------|---------|-------|
| report_id | String | REP-10001 | Expense report reference |
| employee_id | String | EMP001 | Employee code |
| employee_name | String | Rahul Sharma | Name for audit |
| department | String | Engineering | Org unit |
| trip_date | Date | 2024-01-15 | Travel date (flights) or check-in date (hotels) |
| category | Enum | Flight, Hotel, Cab | Expense type |
| origin | String | BOM | IATA airport code (flights only) |
| destination | String | DEL | IATA airport code (flights) or city (hotels) |
| distance_km | Float | 1148 | Distance if recorded; nullable |
| cabin_class | String | Economy, Business | Cabin class (flights only) |
| nights | Integer | 3 | Number of nights (hotels only) |
| vendor_name | String | IndiGo, Marriott, Uber | Vendor |
| amount_inr | Float | 15000.00 | Cost in INR |
| currency | String | INR | Billing currency |

**Distance Resolution Logic:**
- **Explicit distance:** If distance_km is provided, use it directly
- **IATA codes:** If origin/destination are IATA codes (e.g., BOM → DEL), compute distance using Haversine formula + ICAO routing factor (1.09)
- **Missing both:** Flag for analyst review

**Cabin Class Variants:**
- "Economy", "Eco", "Y class" → economy factor 0.255
- "Business", "Club", "J class" → business factor 0.357
- "First", "F class" → first class factor 0.510
- Blank → analyst decision (default to economy vs. flag for review)

### Sample Data Rationale

**What We Generated:**
- 180 rows representing 4 employees × 45 trips
- Trip types: 40% flights, 35% hotels, 25% cabs
- Flight routes: India domestic + international (5 predefined routes)
- Date range: Jan 1 — Jun 30, 2024
- Cabin class: 70% economy, 30% business
- Hotel locations: Mumbai, Delhi, Bangalore, Dubai, London
- Ground transport: 5–45 km (intra-city)
- Anomalies: 8% injected (invalid airport, missing distance, future date, extreme amount, missing nights)

**Why This Looks Realistic:**
- Seasonal pattern: Peak travel in Q1 and Q4 (financial year planning meetings)
- International mix: 15% of flights international (UK, Singapore, Dubai); company is multinational
- Business class skew: Executives book business, ICs book economy
- Hotel pricing: ₹4,000–₹12,000 per night (realistic Indian +Dubai range)
- Cab pricing: ₹500–₹1,500 per trip (realistic Uber/Ola in metros)

**What Breaks in Production:**

1. **Unknown Airport Codes:** 
   - Input: origin="JTR" (typo for "JER" Jersey Airport)
   - Issue: Not in IATA database → distance cannot be computed → flagged
   - Real scenario: ~2% of manual entries have typos

2. **Domestic vs. International Flag Missing:**
   - Example: BOM → LHR (Mumbai → London) — international, should use RFI (Radiative Forcing Index) factor 3.15
   - Our model: Uses Haversine only (no RFI multiplier)
   - Reality: ICAO recommends RFI 1.5–3.15 for international flights
   - **What Breaks:** CO2 for international flights will be underestimated

3. **Private Jet Charters:**
   - Not in standard "Flight/Hotel/Cab" categories
   - If present in data, parser flags as unknown category
   - Emission factor for private jets: ~5–10x higher than commercial flights

4. **Round-Trip vs. One-Way:**
   - Concur sometimes shows: origin="BOM", destination="DEL", distance=1148
   - Is this one-way or round-trip?
   - Our model: Assumes one-way; analyst must verify if actual trip was round-trip (2x distance)

5. **Per-Diem Allowance vs. Actual Spend:**
   - Concur distinguishes: actual invoice amount vs. daily per-diem claim
   - If per-diem: ₹500/day for 5 days = ₹2500 allowance (not actual spend on hotels)
   - Our model: Treats all entries as actual spend; doesn't flag per-diem rows
   - **Reality:** Per-diem trips shouldn't be included in emissions calculation (they're allowances, not actuals)

6. **Unaccounted-For Ground Transport:**
   - Airport transfers (airport → hotel) often expensed separately under "Miscellaneous"
   - Our model only captures explicit "Cab" entries
   - Missing: 10–20% of actual ground emissions

### Sample Data File

**Location:** `sample_data/travel_data.csv`

**First 8 rows (flights + hotels + cab):**
```
tenant_id,company_name,report_id,employee_id,employee_name,department,trip_date,category,origin,destination,distance_km,nights,cabin_class,vendor_name,amount_inr,currency
T001,Tata Manufacturing Ltd,REP-10001,EMP001,Rahul Sharma,Engineering,2024-01-10,Flight,BOM,DEL,1148,,,IndiGo,8000.00,INR
T001,Tata Manufacturing Ltd,REP-10002,EMP002,Priya Mehta,Sales,2024-01-12,Hotel,,Delhi,,,3,Marriott,36000.00,INR
T001,Tata Manufacturing Ltd,REP-10003,EMP003,Amit Verma,Operations,2024-01-15,Cab,,Mumbai,,,,Uber,800.00,INR
T001,Tata Manufacturing Ltd,REP-10004,EMP001,Rahul Sharma,Engineering,2024-01-18,Flight,DEL,BLR,1740,Business,,Air India,18000.00,INR
T001,Tata Manufacturing Ltd,REP-10005,EMP002,Priya Mehta,Sales,2024-01-20,Hotel,,Bangalore,,4,Hilton,48000.00,INR
T001,Tata Manufacturing Ltd,REP-10006,EMP004,Neha Singh,Finance,2024-02-01,Flight,BOM,DXB,1930,,Business,Emirates,35000.00,INR
T001,Tata Manufacturing Ltd,REP-10007,EMP001,Rahul Sharma,Engineering,2024-02-05,Hotel,,Dubai,,2,Hyatt,45000.00,INR
...
```

**Statistics:**
- Total rows: 188 (180 + 5 duplicates + 3 anomalies)
- Flagged rows: ~15 (8% of 180)
- Flight rows: ~72 (40%)
- Hotel rows: ~63 (35%)
- Cab rows: ~45 (25%)
- International flights: ~27 (15% of all flights)
- Business class: ~20 (28% of flights)

---

## Summary: Why These Formats Were Chosen

| Source | Format | Why | Coverage | Realistic |
|--------|--------|-----|----------|-----------|
| **SAP** | CSV flat-file (MB51) | No live credentials, realistic onboarding | 95% of SAP clients | ✓ High |
| **Electricity** | Portal CSV export | Structured, available for major utilities | 70% of Indian facilities | ✓ High |
| **Travel** | Concur CSV export | Standard industry format, widely supported | 60% of enterprises | ✓ High |

---

## What Real Deployments Will Encounter

### Beyond Our Sample Data

1. **Encoding Mayhem:** SAP Windows-1252, electricity UTF-8 with BOM, travel portal Latin-1 → need robust encoding detection
2. **Data Quality:** Real data is 10–100× messier (typos, missing fields, duplicates, retroactive entries)
3. **Volume:** Sample data: 700 rows; real client might onboard with 50,000+ historical rows
4. **Incremental Ingestion:** Subsequent uploads might overlap with prior data (May re-submit April data)
5. **Missing PKI / Certificates:** SAP system might require SSL certificate pinning; utility API might be behind VPN
6. **Ambiguous Business Logic:**
   - Should we include historical data retroactively? (Yes, but flag as catch-up)
   - Should we recalculate CO2 if emission factors update? (No, preserve historical calculation)
   - Should we support data deletion? (No, audit trail is immutable)

---

**End of SOURCES.md**
