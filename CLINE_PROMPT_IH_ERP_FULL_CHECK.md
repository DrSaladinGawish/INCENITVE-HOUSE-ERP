# IH-ERP Full System Check — Cline Prompt
## Objective: Verify IH-ERP is 100% operational with launcher-integrated testing, data location tracking, and data flow validation

---

## CONTEXT

IH-ERP is at `D:\IncentiveHouse_ERP` (port 9001/9003). It uses:
- FastAPI + SQLAlchemy + PostgreSQL
- IHF Pattern v1.0 architecture
- Launcher: `D:\IncentiveHouse_ERP\launcher\Start-IH-ERP.bat` and `.ps1`
- Tests: `app/tests/test_smoke.py` (60/60 pass)
- Dashboard: `app/templates/launcher_dashboard_v2.html`

---

## PHASE 1: LAUNCHER INTEGRATION CHECK

### 1.1 Verify Launcher Files Exist
```
D:\IncentiveHouse_ERP\launcher\
├── Start-IH-ERP.bat      (cmd.exe version)
├── Start-IH-ERP.ps1      (PowerShell 5.1 version)
└── (optional) README.txt
```

### 1.2 Verify Launcher Functionality
- [ ] Double-click `Start-IH-ERP.bat` → imports check → server starts
- [ ] Run `.\Start-IH-ERP.ps1` from PowerShell → imports check → server starts
- [ ] Verify `cd /d D:\IncentiveHouse_ERP` is present (avoids path issues)
- [ ] Verify port is 9001 (or 9003 if 9001 is ghosted)
- [ ] Verify `--reload` flag is present for development

### 1.3 Verify Dashboard Endpoint
- [ ] `GET /api/v1/launcher/dashboard-v2` returns HTML
- [ ] Dashboard shows 15 modules with status badges
- [ ] Dashboard shows system assessment scores
- [ ] Dashboard shows gap analysis (14 features)
- [ ] Chat bot responds to health/test/backup/gap queries
- [ ] Auto-refresh works (60-second interval)

### 1.4 Verify Launcher Router Endpoints
| Endpoint | Method | Expected |
|----------|--------|----------|
| `/api/v1/launcher/status` | GET | `{launcher_version, ihf_pattern, server_pid, status}` |
| `/api/v1/launcher/run-test` | POST | `{status: "started", message, report_path}` |
| `/api/v1/launcher/test-report/latest` | GET | Full test report JSON |
| `/api/v1/launcher/restart` | POST | `{status: "restarting", message}` (requires confirm=true) |
| `/api/v1/launcher/dashboard` | GET | Old dashboard HTML (fallback) |
| `/api/v1/launcher/dashboard-v2` | GET | **New dashboard HTML** |

---

## PHASE 2: DATA LOCATION TRACKING

### 2.1 Verify Data Directory Structure
```
D:\IncentiveHouse_ERP\
├── data/                    # Application data
│   ├── exports/             # CSV, Excel exports
│   ├── reports/             # Generated PDFs
│   └── uploads/             # User uploads
├── backups/                 # Database backups
│   ├── backup_manifest.json
│   └── *.sql.gz
├── logs/                    # Application logs
│   └── server.log
├── reports/                 # Test reports
│   └── smoke_report_*.json
└── STAGING_BRIDGE/          # Archived/orphaned files
    └── archive/
        └── bio_erp_organ_orphans/
```

### 2.2 Verify Database Data Locations
Run SQL queries to confirm data lives in correct tables:

```sql
-- Master Data Tables
SELECT 'COA' as table_name, COUNT(*) as records FROM coa_accounts;
SELECT 'Items' as table_name, COUNT(*) as records FROM items;
SELECT 'Clients' as table_name, COUNT(*) as records FROM clients;
SELECT 'Suppliers' as table_name, COUNT(*) as records FROM suppliers;
SELECT 'Staff' as table_name, COUNT(*) as records FROM staff;

-- Transaction Tables
SELECT 'Events' as table_name, COUNT(*) as records FROM events;
SELECT 'Sales' as table_name, COUNT(*) as records FROM sales_invoices;
SELECT 'Purchases' as table_name, COUNT(*) as records FROM purchase_orders;
SELECT 'Banking' as table_name, COUNT(*) as records FROM bank_transactions;
SELECT 'HR' as table_name, COUNT(*) as records FROM payroll_records;

-- Archive & Audit
SELECT 'USB Archive' as table_name, COUNT(*) as records FROM usb_archive_index;
SELECT 'Audit Trail' as table_name, COUNT(*) as records FROM archive_audit_log;
SELECT 'Backup Log' as table_name, COUNT(*) as records FROM archive_audit_log WHERE action='BACKUP';
```

### 2.3 Verify File System Data Locations
- [ ] `D:\IncentiveHouse_ERP\backups\` contains `.sql.gz` files
- [ ] `D:\IncentiveHouse_ERP\reports\pdf\` contains generated PDFs
- [ ] `D:\IncentiveHouse_ERP\reports\` contains `smoke_report_*.json`
- [ ] `D:\IncentiveHouse_ERP\USB Drive\` (if connected) shows archive structure
- [ ] `D:\IncentiveHouse_ERP\logs\server.log` exists and is writable

---

## PHASE 3: DATA FLOW TESTING

### 3.1 End-to-End Transaction Flow
Test a complete business transaction from creation to report:

```python
# Step 1: Create Event
POST /api/v1/events/
{"name": "Test Event", "client_id": 1, "start_date": "2026-06-13", "budget": 50000}

# Step 2: Add Sales Line Items
POST /api/v1/events/{id}/line-items
{"item_id": 1, "quantity": 10, "unit_price": 1000}

# Step 3: Generate Invoice
POST /api/v1/sales/invoices
{"event_id": {id}, "items": [...]}

# Step 4: Record Payment
POST /api/v1/banking/transactions
{"type": "CREDIT", "amount": 10000, "reference": "INV-{id}"}

# Step 5: Check Reports
GET /api/v1/reports/financial/profit-loss?from_date=2026-06-01&to_date=2026-06-30
GET /api/v1/reports/financial/cash-flow?from_date=2026-06-01&to_date=2026-06-30

# Step 6: Export Data
GET /api/v1/reports/financial/api/profit-loss/csv
GET /api/v1/reports/financial/api/cash-flow/pdf

# Step 7: Verify Archive
GET /api/v1/archive/usb/status
POST /api/v1/archive/upload (attach supporting document)
```

### 3.2 Cross-Module Data Flow Verification
| From Module | To Module | Data Flow | Verify |
|-------------|-----------|-----------|--------|
| Events | Sales | Event → Invoice | Invoice has event_id |
| Sales | Banking | Invoice → Payment | Payment references invoice |
| Banking | Reports | Transaction → P&L | P&L includes transaction |
| Purchase | Inventory | PO → Stock | Inventory updated on GRN |
| HR | Payroll | Employee → Salary | Payroll linked to staff_id |
| All | Audit | Action → Log | Every POST/PUT/DELETE logged |
| All | Backup | Data → .sql.gz | Backup contains all tables |

### 3.3 Data Integrity Checks
```sql
-- Verify referential integrity
SELECT COUNT(*) as orphaned_invoices 
FROM sales_invoices si 
LEFT JOIN events e ON si.event_id = e.id 
WHERE e.id IS NULL;

-- Verify totals match
SELECT 
    'Sales' as category,
    SUM(total_amount) as total
FROM sales_invoices
WHERE date >= '2026-06-01';

-- Verify audit trail completeness
SELECT 
    table_name,
    COUNT(*) as changes,
    MAX(changed_at) as last_change
FROM audit_trail
GROUP BY table_name;
```

---

## PHASE 4: FULL TEST SUITE EXECUTION

### 4.1 Run Smoke Test
```bash
cd D:\IncentiveHouse_ERP
python -m app.tests.test_smoke http://localhost:9001
```

**Expected:** 60/60 pass, JSON report saved to `reports/smoke_report_*.json`

### 4.2 Run Launcher Test
```bash
cd D:\IncentiveHouse_ERP
python -m app.tests.test_launcher http://localhost:9001
```

**Expected:** 6 cycles, ~50 endpoints, all pass, JSON report saved

### 4.3 Run Import Verification
```bash
cd D:\IncentiveHouse_ERP
python -c "import app.main; import app.models; import app.routers; import app.services; import app.reports; print('ALL OK')"
```

**Expected:** No errors, prints `ALL OK`

### 4.4 Database Health Check
```bash
cd D:\IncentiveHouse_ERP
python -c "from app.database import engine; from sqlalchemy import inspect; insp = inspect(engine); print('Tables:', len(insp.get_table_names()))"
```

**Expected:** Lists all tables, no connection errors

---

## PHASE 5: REPORTING & DOCUMENTATION

### 5.1 Generate System Health Report
```bash
curl http://localhost:9001/api/v1/launcher/status
curl http://localhost:9001/api/v1/health
curl http://localhost:9001/api/v1/admin/backup/status
```

### 5.2 Generate Gap Analysis Report
```bash
curl http://localhost:9001/api/v1/launcher/dashboard-v2
# Or manually check: 14 features, which are complete/partial/missing
```

### 5.3 Update Documentation
- [ ] `README.md` — update with launcher instructions
- [ ] `DIRECTORY_CONTRACT.md` — verify all paths correct
- [ ] `CHANGELOG.md` — add v2.5.0 entry with launcher + dashboard

---

## SUCCESS CRITERIA

| Check | Pass Criteria |
|-------|---------------|
| Launcher starts | `.bat` and `.ps1` both work, imports verify, server starts |
| Dashboard loads | `/dashboard-v2` shows 15 modules, assessments, chat bot |
| All tests pass | Smoke test 60/60, launcher test 6 cycles, no failures |
| Data locations | All tables have data, backups exist, exports work |
| Data flows | End-to-end transaction creates → reports → exports correctly |
| No errors | Zero 500 errors in logs, zero import failures |

---

## DELIVERABLES

After completing this check, you should have:
1. ✅ `launcher_dashboard_v2.html` in `app/templates/`
2. ✅ `launcher_router.py` in `app/routers/` (mounted in `main.py`)
3. ✅ `Start-IH-ERP.bat` and `Start-IH-ERP.ps1` in `launcher/`
4. ✅ Test reports in `reports/`
5. ✅ Updated `README.md` with launcher instructions
6. ✅ Git commit with all changes

---

## COMMANDS SUMMARY

```bash
# Start server
D:\IncentiveHouse_ERP\launcher\Start-IH-ERP.bat

# Run tests
cd D:\IncentiveHouse_ERP
python -m app.tests.test_smoke http://localhost:9001
python -m app.tests.test_launcher http://localhost:9001

# Check health
curl http://localhost:9001/api/v1/health
curl http://localhost:9001/api/v1/launcher/status

# Open dashboard
start http://localhost:9001/api/v1/launcher/dashboard-v2

# Commit
git add -A
git commit -m "IH-ERP v2.5.0: Full system check, launcher integration, data flow validation"
```
