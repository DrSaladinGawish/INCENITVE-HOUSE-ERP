"""IH-ERP smoke test  hits every endpoint, reports 200 vs fail."""
import sys
import json
import requests
from datetime import datetime

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:9001"
TIMEOUT = 10

# Authenticate once, reuse token
TOKEN = None
try:
    resp = requests.post(f"{BASE}/api/auth/login", json={"username": "admin", "password": "admin123"}, headers={"Content-Type": "application/json"}, timeout=TIMEOUT)
    if resp.status_code == 200:
        TOKEN = resp.json().get("access_token", "")
except Exception:
    pass
HEADERS = {"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}

CYCLES = {
    "auth": [
        ("GET", "/api/auth/verify"),
        ("GET", "/api/auth/me"),
    ],
    "sales": [
        ("GET", "/api/sal/clients"),
        ("GET", "/api/sal/invoices"),
    ],
    "purchases": [
        ("GET", "/api/pur/vendors"),
        ("GET", "/api/pur/vouchers"),
    ],
    "banking": [
        ("GET", "/api/bnk/banks"),
        ("GET", "/api/bnk/transactions"),
    ],
    "gl": [
        ("GET", "/api/gl/accounts"),
        ("GET", "/api/gl/vouchers"),
        ("GET", "/api/gl/employees"),
    ],
    "events": [
        ("GET", "/api/evn/pnrs"),
        ("GET", "/api/evn/categories"),
        ("GET", "/api/evn/budget-lines"),
    ],
    "inventory": [
        ("GET", "/api/inventory/items"),
        ("GET", "/api/inventory/warehouses"),
        ("GET", "/api/inventory/movements"),
        ("GET", "/api/inventory/counts"),
    ],
    "payroll": [
        ("GET", "/api/payroll/structures"),
        ("GET", "/api/payroll/payslips"),
        ("GET", "/api/payroll/attendance"),
    ],
    "crm": [
        ("GET", "/api/crm/leads"),
        ("GET", "/api/crm/opportunities"),
        ("GET", "/api/crm/contacts"),
        ("GET", "/api/crm/activities"),
        ("GET", "/api/crm/deals"),
    ],
    "budgeting": [
        ("GET", "/api/budgeting/periods"),
        ("GET", "/api/budgeting/lines"),
        ("GET", "/api/budgeting/commitments"),
        ("GET", "/api/budgeting/vs-actual"),
    ],
    "fixed_assets": [
        ("GET", "/api/fixed-assets/categories"),
    ],
    "fx": [
        ("GET", "/api/fx/currencies"),
        ("GET", "/api/fx/rates"),
        ("GET", "/api/fx/convert?from=USD&to=EGP&amount=100"),
    ],
    "workflow": [
        ("GET", "/workflow/approvals"),
    ],
    "documents": [
        ("GET", "/api/v1/documents/modules"),
        ("GET", "/api/v1/documents/stats"),
        ("GET", "/api/v1/documents/orphans"),
    ],
    "reports_v1": [
        ("GET", "/reports/financial/trial-balance"),
        ("GET", "/reports/financial/profit-loss?from_date=2026-01-01&to_date=2026-06-12"),
        ("GET", "/reports/financial/balance-sheet"),
        ("GET", "/reports/financial/cash-flow?from_date=2026-01-01&to_date=2026-06-12"),
    ],
    "reports_v2": [
        ("GET", "/reports/financial/api/trial-balance/csv"),
        ("GET", "/reports/financial/api/profit-loss/csv?from_date=2026-01-01&to_date=2026-06-12"),
        ("GET", "/reports/financial/api/cash-flow-v2?from_date=2026-01-01&to_date=2026-06-12"),
        ("GET", "/reports/financial/api/trial-balance/pdf"),
        ("GET", "/reports/financial/api/profit-loss/pdf?from_date=2026-01-01&to_date=2026-06-12"),
        ("GET", "/reports/financial/api/compare"),
    ],
    "archive": [
        ("GET", "/api/v1/archive/status"),
        ("GET", "/api/v1/archive/browse?path=/"),
        ("GET", "/api/v1/archive/duplicates"),
    ],
    "backup": [
        ("GET", "/api/v1/admin/backup/list"),
        ("GET", "/api/v1/admin/backup/status"),
        ("GET", "/api/v1/admin/backup/schedule"),
    ],
    "einvoice": [
        ("GET", "/e-invoice/generate/TEST-INV-001"),
    ],
    "dashboard": [
        ("GET", "/api/dashboard/summary"),
    ],
    "meta": [
        ("GET", "/api/meta/forms"),
    ],
    "intelligence": [
        ("GET", "/api/v1/intelligence/backups"),
        ("GET", "/api/v1/intelligence/audit"),
    ],
    "health": [
        ("GET", "/health"),
    ],
}

results = {}
total_pass = 0
total_fail = 0
total_endpoints = 0

for cycle, endpoints in CYCLES.items():
    cycle_results = []
    for method, path in endpoints:
        url = f"{BASE}{path}"
        total_endpoints += 1
        try:
            r = requests.request(method, url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=False)
            ok = r.status_code < 500
            cycle_results.append({"method": method, "path": path, "status": r.status_code, "ok": ok})
            if ok:
                total_pass += 1
            else:
                total_fail += 1
        except requests.ConnectionError:
            cycle_results.append({"method": method, "path": path, "status": 0, "ok": False, "error": "Connection refused"})
            total_fail += 1
        except requests.Timeout:
            cycle_results.append({"method": method, "path": path, "status": 0, "ok": False, "error": "Timeout"})
            total_fail += 1
        except Exception as e:
            cycle_results.append({"method": method, "path": path, "status": 0, "ok": False, "error": str(e)})
            total_fail += 1
    results[cycle] = cycle_results

# Print report
sep = "=" * 64
print(sep)
print(f"  SMOKE TEST REPORT  IH-ERP")
print(f"  Base URL: {BASE}")
print(f"  Tested:   {datetime.now().strftime('%Y-%m-%d %H:%M')}")
print(sep)
print(f"  {'CYCLE':<20} {'ENDPOINTS':>5} {'PASS':>5} {'FAIL':>5}  STATUS")
print(f"  {''*20} {''*5} {''*5} {''*5}  {''*10}")
for cycle in sorted(results.keys()):
    items = results[cycle]
    p = sum(1 for i in items if i["ok"])
    f = len(items) - p
    status = " PASS" if f == 0 else (" FAIL" if f == len(items) else " PARTIAL")
    print(f"  {cycle:<20} {len(items):>5} {p:>5} {f:>5}  {status}")
print(sep)
pct = round(total_pass / total_endpoints * 100) if total_endpoints else 0
print(f"  TOTAL: {total_pass}/{total_endpoints} pass ({pct}%)")
print(sep)

# Detail: only failing endpoints
failures = [(c, i) for c, items in results.items() for i in items if not i["ok"]]
if failures:
    print(f"\n  FAILING ENDPOINTS:")
    for cycle, item in failures:
        err = item.get("error", "")
        print(f"    {cycle:>15}  {item['method']:4} {item['path']:<50} HTTP {item['status']} {err}")
    print()

# Write JSON report
report = {
    "timestamp": datetime.now().isoformat(),
    "base_url": BASE,
    "total": total_endpoints,
    "passed": total_pass,
    "failed": total_fail,
    "cycles": {c: [{"method": i["method"], "path": i["path"], "status": i["status"], "ok": i["ok"]} for i in items] for c, items in results.items()},
}
json.dump(report, open("smoke_report.json", "w"), indent=2)
print(f"  JSON report: smoke_report.json")
print(sep)
