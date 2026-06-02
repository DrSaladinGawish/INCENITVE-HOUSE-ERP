# IncentiveHouse ERP v2.2.2

Production ERP system with FastAPI + SQLAlchemy async + Pydantic v2.
- 43 database tables, 111 API routes
- 8-stage ERP Builder Protocol pipeline with protocell validation engine
- 17 business modules (auth, clients, vendors, PNR, events, employees, finance, bank, sales, reports, OR, pipeline, petty cash, COA, cheques, WHT, vendor rating, currency, PDF)
- Docker support, 57 passing tests

## Quick Start

```powershell
# Local
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 9001

# Docker
docker compose up -d
```

Open http://localhost:9001/docs

## Default Credentials
| Username      | Password     | Role           |
|---------------|-------------|----------------|
| admin         | admin       | admin          |
| accountant    | accountant  | accountant     |
| event_manager | events      | event_manager  |
| viewer        | viewer      | viewer         |

## API Overview

### Auth `POST /api/v1/auth/login`
### Business Modules (`/api/v1/`)
- **clients** – CRUD
- **vendors** – CRUD
- **pnr** – CRUD + fuzzy search
- **employees** – list + create
- **events** – CRUD
- **finance** – cash flow, aging, AR/AP, sales/purchase invoices, audit trail
- **bnk** – bank list + summary
- **sales** – sales list + summary
- **reports** – dashboard KPI, monthly trend, event P&L, event status
- **coa** – chart of accounts CRUD + categories/types
- **petty-cash** – list, create, approve, stats
- **cheques** – list, create, status update, stats
- **wht** – list, create, file, stats
- **vendor-performance** – get, rate, summary
- **currency** – rates list, convert, set rate
- **pdf** – download sales/purchase invoice as PDF
- **or** – OR module sub-app

### Pipeline (`/api/v2/`)
- **extract** – data extraction (Excel files)
- **validate** – 7-rule protocell validation
- **stage** – staging table insertion
- **reconcile** – staging reconciliation
- **approve** – approval workflow
- **promote** – promote to production
- **observe** – monitoring
- **status** – system status & table counts
- **journal** – dual-entry journal entries

## Configuration
Set via environment variables or `.env.example`:
- `DB_FILE` – database path (default: `protocell_staging.db`)
- `SECRET_KEY` – JWT signing key
- `AUTH_USERS_JSON` – JSON user definitions
- `JWT_EXPIRE_HOURS` – token expiry (default: 8)

## Tests
```powershell
pytest tests/ -v
```
