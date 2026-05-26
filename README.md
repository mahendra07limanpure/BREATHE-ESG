# Breathe ESG — Emissions Data Management System

**Author:** Mahendra Limanpure | **Date:** May 26, 2026

## Overview
Full-stack ESG emissions data platform with multi-source ingestion, automatic anomaly detection, analyst review dashboard, and complete audit trail for regulatory compliance.

**Features:**
✓ Multi-source data ingestion (SAP, Electricity, Travel)  
✓ 7 automatic flag checks for data quality  
✓ Analyst review & approval dashboard  
✓ CO2 calculations with regulatory emission factors  
✓ Immutable audit trail for compliance  
✓ Scope 1/2/3 categorization  

## Quick Start

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```
API: http://localhost:8000/api

### Frontend
```bash
cd frontend/vite-project
npm install
npm run dev
```
Dashboard: http://localhost:5173

## Documentation
- **DECISIONS.md** — 10 design decisions with rationale
- **TRADEOFFS.md** — Features deliberately not built
- **SOURCES.md** — Data source research & format analysis
- **MODEL.md** — Complete data model documentation

## Sample Data
Pre-generated CSV files in `sample_data/`:
- `sap_fuel_data.csv` (408 rows) — SAP fuel & procurement
- `electricity_data.csv` (125 rows) — Utility consumption
- `travel_data.csv` (188 rows) — Business travel expenses

## API Endpoints
- `POST /api/upload/` — Upload CSV file
- `GET /api/records/review/` — Get pending records
- `PATCH /api/records/<id>/approve/` — Approve record
- `PATCH /api/records/<id>/reject/` — Reject record
- `GET /api/summary/co2/` — CO2 totals
- `GET /api/dashboard/stats/` — Dashboard statistics

## Deployment
- **Backend:** Render (PostgreSQL + Gunicorn)
- **Frontend:** Vercel (React + Vite)

See README sections above for detailed setup & deployment instructions.