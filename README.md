# IncentiveHouse ERP v2.2.2

## System Overview
A production-ready ERP system with real-time data extraction, validation, staging, and reconciliation pipelines.

## Quick Start

### Terminal 1 - Start Server
```powershell
cd "D:\ERP System\BIO_ERP\app\organs\incentivehouse_organ"
python incentivehouse_server.py
```

### Terminal 2 - Run Tests
```powershell
cd "D:\ERP System\BIO_ERP\app\organs\incentivehouse_organ"
python test_api.py
```

## API Endpoints

### Authentication
- **POST** `/v2/auth/login` - Login with username/password
  - Users: `admin`, `accountant`, `event_mgr`, `viewer`

### Extraction
- **POST** `/v2/extract` - Extract module data (BNK, SAL, PUR, EVN, ENV)
- **POST** `/v2/extract/master` - Extract master tables

### Processing Pipeline
- **POST** `/v2/validate` - Validate extracted data
- **POST** `/v2/stage` - Stage validated data
- **POST** `/v2/reconcile` - Reconcile staged records
- **POST** `/v2/approve` - Approve reconciled data
- **POST** `/v2/promote` - Promote to production
- **POST** `/v2/observe` - Monitor production data

### Status & Health
- **GET** `/v2/status` - System status and table counts
- **GET** `/health` - Health check (no auth required)

## Database
- **SQLite**: `protocell_staging.db`
- **Tables**: 17 (extraction logs, staging tables, master data)

## Test Results
✅ Authentication working
✅ BNK extraction: 2,501 records
✅ Master data: 4 tables, 242 records
✅ All 8 pipeline stages operational
✅ Health check: HEALTHY

## Source Files
- `extraction_engine.py` - Data extraction logic
- `incentivehouse_server.py` - FastAPI server
- `test_api.py` - Integration tests
- `protocell_staging.db` - SQLite database
- `templates/` - HTML templates (optional)

## Configuration
Edit `extraction_engine.py` for:
- Database file path
- Source file paths
- Module configurations
- Master table mappings
