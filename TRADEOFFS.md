# TRADEOFFS.md — What Was Deliberately Not Built and Why

**Author:** Mahendra Limanpure  
**Date:** May 25, 2026  
**Project:** Breathe ESG Tech Intern Assignment

---

## Overview

This document explains three features that would be valuable in production but were deliberately excluded from the 4-day prototype. For each, the rationale is: given the time constraint and the assignment's emphasis on data model quality and defensible decisions, these features were deferred to preserve development focus on the core ingestion → review → approval pipeline.

---

## Tradeoff 1: PDF Electricity Bill Parsing

### What We Didn't Build
Automated extraction of consumption data from PDF utility bills (MSEDCL, TATA Power, BESCOM, BSES, etc.).

### Why It Would Be Valuable
- **Reality:** Many Indian facilities teams receive bills only as email PDFs, not portal exports
- **Coverage:** Enables ingestion from utilities that don't offer online portals
- **One-Stop Onboarding:** Client uploads bill PDFs directly instead of manually logging into utility portals

### Why We Didn't Build It

| Reason | Cost | Impact |
|--------|------|--------|
| **Utility-specific formats** | Each utility has different bill layout → needs regex/template per utility | High friction: 2–3 days for 4 major utilities |
| **Regex fragility** | Layout changes mid-year → regex breaks → manual fix required | Ongoing maintenance burden |
| **OCR for handwritten fields** | Meter readings sometimes handwritten → requires vision model | Significant infrastructure |
| **Conflicting data** | Bill has amount paid ≠ consumption billed; which is authoritative? | Ambiguity requires analyst review anyway |
| **Portal Alternative** | Portal CSVs are structured, reliable, and already integrated | Portal path is 80% as effective with 10% the code |

### What We Built Instead
CSV portal export parsing — covers 70% of real client scenarios with 90% less complexity.

### Production Path
If we later need PDF support:
1. Start with one utility (e.g., TATA Power) — extract bill format rules
2. Use rule-based parsing (regex) for structured fields (meter ID, period, units)
3. Use vision model (e.g., OpenAI Vision API) for handwritten/image fields only
4. Store extracted data in same EmissionRecord schema — no schema changes needed
5. Estimate: 1–2 weeks per major utility

### Question for PM
"How many of your target clients rely solely on PDF bills (no portal access)? Is this worth 2+ weeks of development?"

---

## Tradeoff 2: Live SAP OData / API Integration

### What We Didn't Build
Real-time data sync from a live SAP system via OData/RFC/BAPI.

### Why It Would Be Valuable
- **No Manual Upload:** Data pulled automatically; no analyst waits for file upload
- **Continuous Sync:** Daily/hourly deltas instead of periodic batch imports
- **Fresher Data:** Latest transactions reflected in dashboard hours after SAP entry

### Why We Didn't Build It

| Reason | Cost | Impact |
|--------|------|--------|
| **SAP Access Unavailable** | Prototype has no live SAP credentials; would need test client system | Out of scope for demo |
| **OAuth Setup Complexity** | SAP OData requires RFC credentials, VPN, firewall rules | 2–3 days of IT coordination |
| **Rate Limiting** | OData services have strict call limits → backoff/retry logic needed | Additional error handling |
| **Schema Brittleness** | SAP field changes between versions → parser breaks | Maintenance risk |
| **Realistic Onboarding** | Real clients DO upload CSVs; API access is aspirational | CSV upload is how it happens in week 1 |
| **Infrastructure Cost** | Polling service, scheduler, secrets management, monitoring | Beyond prototype scope |

### What We Built Instead
CSV flat-file upload simulating realistic onboarding: Finance officer exports MB51, uploads file.

### Production Path
If we need live OData later:
1. Client grants RFC credentials to Breathe ESG service account
2. Build Django Celery task: `sync_sap_data(client_id, werks_filter, date_range)`
3. Task calls SAP OData Gateway → fetches MB51 records → triggers same parser
4. Store records in same EmissionRecord table — no schema changes
5. Run daily at off-peak hours to respect rate limits
6. Estimate: 1 week for stable, production-ready integration

### Question for PM
"At what scale do clients demand real-time sync vs. accepting weekly uploads? Should we build this in phase 2?"

---

## Tradeoff 3: Automated Emissions Reporting / PDF Export

### What We Didn't Build
Dashboard button → PDF report generator that produces a formatted audit report with CO2 totals, breakdowns by scope, and approval signatures.

### Why It Would Be Valuable
- **Compliance Ready:** Auditors receive formatted report, not raw dashboard screenshots
- **Executive Summary:** C-suite gets one-page overview (total tonnes, trend, scope breakdown)
- **Attestation:** Analyst digital signature on report (requires PKI setup)
- **Versioning:** Dated reports stored for regulatory record-keeping

### Why We Didn't Build It

| Reason | Cost | Impact |
|--------|------|--------|
| **Frontend Complexity** | Report UI, download button, template selection, preview | 1–2 days frontend work |
| **PDF Generation** | Library choice (ReportLab, weasyprint, puppeteer) and styling | 1 day backend + frontend sync |
| **Regulatory Format Unknown** | BRSR format? CSRD template? Client-specific? | Ambiguity requires PM input |
| **Digital Signature** | Analyst approval signature requires PKI / certificate infra | Out of scope |
| **Multi-Scenario Support** | Full-year report, mid-year, by-scope, by-site → combinatorial explosion | Scope creep |
| **Core Value is Ingestion** | Assignment emphasizes data model + ingestion. Reporting is secondary. | Time better spent elsewhere |

### What We Built Instead
Dashboard displays all EmissionRecords with filters (source, scope, status, date range). Analysts screenshot or export CSV manually.

### Production Path
If we need formal reporting:
1. Pick reporting framework: BRSR (if India), CSRD (if EU), or client-specific template
2. Build `Report` model: `Report(client_id, report_date, format, generated_by, approved_by)`
3. Add API endpoint: `GET /api/reports/<report_id>/download/` → PDF bytes
4. Use ReportLab or weasyprint to render approved EmissionRecords into templated PDF
5. Store signed PDFs in S3 for audit archival
6. Estimate: 3–4 days for basic version, 1–2 weeks for full regulatory compliance

### Question for PM
"Which regulatory framework applies (BRSR/CSRD/both)? Should we prioritize report generation in phase 2?"

---

## Why These Three Were Chosen

The three tradeoffs represent the intersection of:

1. **Would require >1 day of focused development** (expensive for 4-day sprint)
2. **Have acceptable interim solutions** (PDF → portal CSV, OData → flat file upload, reporting → manual export)
3. **Require external dependencies or ambiguities** (PDF parsing needs vision model, OData needs SAP access, reporting needs regulatory spec)

---

## What Gets Built Instead: The Core Pipeline

By deferring these three, we focus the 4 days on:

✓ Data model that supports all three sources  
✓ Robust parsers with proper error handling  
✓ Automatic flagging logic that catches real-world data issues  
✓ Analyst review dashboard with approve/reject workflows  
✓ Audit trail (every decision is logged)  
✓ Deployed, working app (both backend and frontend)  
✓ Comprehensive documentation (DECISIONS.md, TRADEOFFS.md, SOURCES.md)

This is the correct prioritization: **a sharp, well-understood core beats a feature-rich mess.**

---

## Summary

| Tradeoff | Effort | Value | Alternative | Production Timeline |
|----------|--------|-------|---|---|
| **PDF Parsing** | 2–3 days | High (covers ~20% extra clients) | Portal CSV (current) | 1–2 weeks when ready |
| **Live OData** | 1 week | High (real-time sync) | File upload (current) | Phase 2 after MVP |
| **PDF Reporting** | 3–4 days | Medium (nice-to-have) | Manual export (current) | 3–4 days once spec is clear |

---

**End of TRADEOFFS.md**
