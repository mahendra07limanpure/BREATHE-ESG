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

### Backend deployment (Render)
1. Create a Render PostgreSQL database and copy its connection details into backend environment variables.
2. Deploy the Django backend using `backend/render.yaml` / `backend/Procfile`.
3. Set these environment variables on Render:
   - `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`
   - `SECRET_KEY` (or `DJANGO_SECRET_KEY`)
   - `DEBUG` (set `False` in production)
   - `ALLOWED_HOSTS` (comma-separated, e.g. `your-render-url.com`)
   - `CORS_ALLOWED_ORIGINS` (comma-separated origins, include your Vercel domain)
4. `python manage.py migrate` runs automatically via `preDeployCommand`, including the `PlantMaster` seed migration.

After deployment, your backend base URL will be:
`<render-service-domain>/api`