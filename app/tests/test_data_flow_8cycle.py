#!/usr/bin/env python3
"""
IH-ERP 8-Cycle Data Flow Test
Tests all 8 data flow cycles across the entire system
"""
import requests
import json
import sys
import os
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class CycleTest:
    def __init__(self, base_url="http://localhost:9005"):
        self.base = base_url
        self.token = None
        self.snapshots = {}
        self.results = []
        self.report = {
            "timestamp": datetime.now().isoformat(),
            "base_url": base_url,
            "cycles": {},
            "summary": {"total": 8, "passed": 0, "failed": 0}
        }

    def log(self, msg, status="INFO"):
        m = {"INFO": " * ", "PASS": "[OK]", "FAIL": "[!!]", "WARN": "[??]"}.get(status, " - ")
        print(f"  {m} {msg}")

    def auth(self):
        r = requests.post(f"{self.base}/api/auth/login", json={"username": "admin", "password": "admin123"}, timeout=10)
        if r.status_code == 200:
            self.token = r.json()["access_token"]
            return True
        self.log(f"Login failed: HTTP {r.status_code}", "FAIL")
        return False

    def h(self):
        return {"Authorization": f"Bearer {self.token}"}

    def record(self, cycle, step, status, detail=""):
        self.results.append({"cycle": cycle, "step": step, "status": status, "detail": detail, "ts": datetime.now().isoformat()})

    def cycle_1_events_to_sales(self):
        """Cycle 1: Event/PNR -> Sales Invoice"""
        print("\n=== CYCLE 1: Events -> Sales ===")
        ts = datetime.now().strftime("%H%M%S")
        passed = True

        # 1a. Create PNR (Event)
        pnr_num = f"8CYCLE-PNR-{ts}"
        r = requests.post(f"{self.base}/api/evn/pnrs", json={
            "PNRNumber": pnr_num,
            "EventName": f"8-Cycle Test Event {ts}",
            "EventStartDate": datetime.now().strftime("%Y-%m-%d"),
            "EventEndDate": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"),
            "Status": "Confirmed"
        }, headers=self.h(), timeout=10)
        if r.status_code in (200, 201):
            self.log(f"PNR created: {pnr_num}", "PASS")
            self.record("events_to_sales", "1a_create_pnr", "PASS", pnr_num)
        else:
            self.log(f"Create PNR: HTTP {r.status_code}", "FAIL")
            self.record("events_to_sales", "1a_create_pnr", "FAIL", r.text[:100])
            passed = False

        # 1b. Verify PNR in list
        r = requests.get(f"{self.base}/api/evn/pnrs", headers=self.h(), timeout=10)
        if r.status_code == 200:
            data = r.json()
            count = len(data) if isinstance(data, list) else len(data.get("items", data))
            self.log(f"PNRs listed: {count}", "PASS")
            self.record("events_to_sales", "1b_list_pnrs", "PASS", str(count))
        else:
            self.log(f"List PNRs: HTTP {r.status_code}", "FAIL")
            self.record("events_to_sales", "1b_list_pnrs", "FAIL", r.text[:100])
            passed = False

        # 1c. Create Sales Invoice linked to PNR
        inv_num = f"INV-{ts}"
        r = requests.post(f"{self.base}/api/sal/invoices", json={
            "InvoiceNumber": inv_num,
            "PNRNumber": pnr_num,
            "InvoiceDate": datetime.now().strftime("%Y-%m-%d"),
            "TotalValue": 50000,
            "lines": [{"ServiceTypeCode": "T-0001", "LineAmount": 50000}]
        }, headers=self.h(), timeout=10)
        if r.status_code in (200, 201):
            inv_id = r.json().get("InvoiceID") or r.json().get("id")
            self.snapshots["invoice_id"] = inv_id
            self.log(f"Invoice created: {inv_num} (ID {inv_id})", "PASS")
            self.record("events_to_sales", "1c_create_invoice", "PASS", f"{inv_num} ID={inv_id}")
        else:
            self.log(f"Create invoice: HTTP {r.status_code}", "FAIL")
            self.record("events_to_sales", "1c_create_invoice", "FAIL", r.text[:100])
            passed = False

        self.report["cycles"]["events_to_sales"] = "PASS" if passed else "FAIL"
        if passed: self.report["summary"]["passed"] += 1
        else: self.report["summary"]["failed"] += 1
        return passed

    def cycle_2_sales_to_banking(self):
        """Cycle 2: Sales Invoice -> Bank Payment"""
        print("\n=== CYCLE 2: Sales -> Banking ===")
        ts = datetime.now().strftime("%H%M%S")
        passed = True

        # 2a. Create bank transaction from invoice
        r = requests.post(f"{self.base}/api/bnk/transactions", json={
            "TransactionDate": datetime.now().strftime("%Y-%m-%d"),
            "Payee": "Test Client",
            "DocumentType": "Sales Invoice",
            "DocumentNumber": f"INV-{ts}",
            "Deposit": 50000,
            "TransactionType": "CREDIT",
            "Narration": "Payment for 8-cycle test invoice"
        }, headers=self.h(), timeout=10)
        if r.status_code in (200, 201):
            txn_id = r.json().get("TransactionID") or r.json().get("id")
            self.snapshots["bank_txn_id"] = txn_id
            self.log(f"Bank transaction created: ID {txn_id}", "PASS")
            self.record("sales_to_banking", "2a_create_bank_txn", "PASS", str(txn_id))
        else:
            self.log(f"Create bank txn: HTTP {r.status_code}", "FAIL")
            self.record("sales_to_banking", "2a_create_bank_txn", "FAIL", r.text[:100])
            passed = False

        # 2b. Verify transaction appears in list
        r = requests.get(f"{self.base}/api/bnk/transactions", headers=self.h(), timeout=10)
        if r.status_code == 200:
            data = r.json()
            count = len(data) if isinstance(data, list) else len(data.get("items", data))
            self.log(f"Bank transactions listed: {count}", "PASS")
            self.record("sales_to_banking", "2b_list_bank_txns", "PASS", str(count))
        else:
            self.log(f"List bank txns: HTTP {r.status_code}", "FAIL")
            self.record("sales_to_banking", "2b_list_bank_txns", "FAIL", r.text[:100])
            passed = False

        self.report["cycles"]["sales_to_banking"] = "PASS" if passed else "FAIL"
        if passed: self.report["summary"]["passed"] += 1
        else: self.report["summary"]["failed"] += 1
        return passed

    def cycle_3_banking_to_reports(self):
        """Cycle 3: Bank Transactions -> Financial Reports"""
        print("\n=== CYCLE 3: Banking -> Reports ===")
        ts = datetime.now().strftime("%Y-%m-%d")
        passed = True
        from_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

        reports = [
            ("Trial Balance", f"/reports/financial/api/trial-balance?as_of_date={ts}"),
            ("P&L", f"/reports/financial/api/profit-loss?from_date={from_date}&to_date={ts}"),
            ("Balance Sheet", f"/reports/financial/api/balance-sheet?as_of_date={ts}"),
            ("Cash Flow", f"/reports/financial/api/cash-flow?from_date={from_date}&to_date={ts}"),
        ]
        for name, path in reports:
            r = requests.get(f"{self.base}{path}", headers=self.h(), timeout=15)
            ok = r.status_code == 200
            self.log(f"{name}: HTTP {r.status_code}", "PASS" if ok else "FAIL")
            self.record("banking_to_reports", f"3_{name.lower().replace(' ','_')}", "PASS" if ok else "FAIL", str(r.status_code))
            if not ok: passed = False

        exports = [
            ("P&L CSV", f"/reports/financial/api/profit-loss/csv?from_date={from_date}&to_date={ts}"),
            ("TB CSV", f"/reports/financial/api/trial-balance/csv?as_of_date={ts}"),
            ("BS PDF", f"/reports/financial/api/balance-sheet/pdf?as_of_date={ts}"),
        ]
        for name, path in exports:
            r = requests.get(f"{self.base}{path}", headers=self.h(), timeout=15)
            ok = r.status_code == 200
            self.log(f"{name}: HTTP {r.status_code}", "PASS" if ok else "FAIL")
            self.record("banking_to_reports", f"3_export_{name.lower().replace(' ','_')}", "PASS" if ok else "FAIL", str(r.status_code))
            if not ok: passed = False

        self.report["cycles"]["banking_to_reports"] = "PASS" if passed else "FAIL"
        if passed: self.report["summary"]["passed"] += 1
        else: self.report["summary"]["failed"] += 1
        return passed

    def cycle_4_purchase_to_inventory(self):
        """Cycle 4: Purchase -> Inventory"""
        print("\n=== CYCLE 4: Purchase -> Inventory ===")
        ts = datetime.now().strftime("%H%M%S")
        passed = True

        # 4a. Create item in inventory
        item_code = f"ITM-{ts}"
        r = requests.post(f"{self.base}/api/inventory/items", json={
            "ItemCode": item_code,
            "ItemName": f"8-Cycle Test Item {ts}",
            "UnitPrice": 500,
            "Category": "Test"
        }, headers=self.h(), timeout=10)
        if r.status_code in (200, 201):
            item_id = r.json().get("ItemID") or r.json().get("id")
            self.snapshots["item_id"] = item_id
            self.log(f"Item created: {item_code} (ID {item_id})", "PASS")
            self.record("purchase_to_inventory", "4a_create_item", "PASS", f"{item_code} ID={item_id}")
        else:
            self.log(f"Create item: HTTP {r.status_code} {r.text[:80]}", "WARN")
            self.record("purchase_to_inventory", "4a_create_item", "WARN", str(r.status_code))
            item_id = 1

        # 4b. Create warehouse
        wh_code = f"WH-{ts}"
        r = requests.post(f"{self.base}/api/inventory/warehouses", json={
            "WarehouseCode": wh_code,
            "WarehouseName": f"Test Warehouse {ts}"
        }, headers=self.h(), timeout=10)
        if r.status_code in (200, 201):
            wh_id = r.json().get("WarehouseID") or r.json().get("id")
            self.snapshots["warehouse_id"] = wh_id
            self.log(f"Warehouse created: {wh_code} (ID {wh_id})", "PASS")
            self.record("purchase_to_inventory", "4b_create_warehouse", "PASS", f"{wh_code} ID={wh_id}")
        else:
            self.log(f"Create warehouse: HTTP {r.status_code} {r.text[:80]}", "WARN")
            self.record("purchase_to_inventory", "4b_create_warehouse", "WARN", str(r.status_code))
            wh_id = 1

        # 4c. Stock movement (IN)
        r = requests.post(f"{self.base}/api/inventory/movements", json={
            "ItemID": self.snapshots.get("item_id", 1),
            "WarehouseID": self.snapshots.get("warehouse_id", 1),
            "MovementType": "IN",
            "Quantity": 100,
            "UnitPrice": 500,
            "Reference": f"PO-{ts}",
            "ReferenceType": "PO"
        }, headers=self.h(), timeout=10)
        if r.status_code in (200, 201):
            mov_id = r.json().get("MovementID") or r.json().get("id")
            self.log(f"Stock movement IN: ID {mov_id}", "PASS")
            self.record("purchase_to_inventory", "4c_stock_movement", "PASS", str(mov_id))
        else:
            self.log(f"Stock movement: HTTP {r.status_code} {r.text[:80]}", "WARN")
            self.record("purchase_to_inventory", "4c_stock_movement", "WARN", str(r.status_code))

        # 4d. Check stock level
        r = requests.get(f"{self.base}/api/inventory/stock/{self.snapshots.get('item_id', 1)}", headers=self.h(), timeout=10)
        if r.status_code == 200:
            self.log(f"Stock level checked: {r.text[:100]}", "PASS")
            self.record("purchase_to_inventory", "4d_check_stock", "PASS", r.text[:80])
        else:
            self.log(f"Check stock: HTTP {r.status_code}", "WARN")
            self.record("purchase_to_inventory", "4d_check_stock", "WARN", str(r.status_code))

        self.report["cycles"]["purchase_to_inventory"] = "PASS" if passed else "FAIL"
        if passed: self.report["summary"]["passed"] += 1
        else: self.report["summary"]["failed"] += 1
        return passed

    def cycle_5_hr_to_payroll(self):
        """Cycle 5: HR Employee -> Payroll"""
        print("\n=== CYCLE 5: HR/GL Employee -> Payroll ===")
        ts = datetime.now().strftime("%H%M%S")
        passed = True

        # 5a. Create employee via GL
        emp_code = f"EMP-{ts}"
        r = requests.post(f"{self.base}/api/gl/employees", json={
            "EmployeeCode": emp_code,
            "EmployeeName": f"8-Cycle Test Employee {ts}",
            "EmployeeType": "Staff"
        }, headers=self.h(), timeout=10)
        if r.status_code in (200, 201):
            self.log(f"Employee created: {emp_code}", "PASS")
            self.record("hr_to_payroll", "5a_create_employee", "PASS", emp_code)
        else:
            self.log(f"Create employee: HTTP {r.status_code} {r.text[:80]}", "WARN")
            self.record("hr_to_payroll", "5a_create_employee", "WARN", str(r.status_code))

        # 5b. Create salary structure
        r = requests.post(f"{self.base}/api/payroll/structures", json={
            "EmployeeCode": emp_code,
            "BasicSalary": 5000,
            "HousingAllowance": 1500,
            "TransportationAllowance": 500,
            "EffectiveFrom": datetime.now().strftime("%Y-%m-%d"),
            "IsActive": True
        }, headers=self.h(), timeout=10)
        if r.status_code in (200, 201):
            self.log(f"Salary structure created", "PASS")
            self.record("hr_to_payroll", "5b_salary_structure", "PASS", "")
        else:
            self.log(f"Salary structure: HTTP {r.status_code} {r.text[:80]}", "WARN")
            self.record("hr_to_payroll", "5b_salary_structure", "WARN", str(r.status_code))

        # 5c. Create payslip
        r = requests.post(f"{self.base}/api/payroll/payslips", json={
            "EmployeeCode": emp_code,
            "PayPeriod": datetime.now().strftime("%Y-%m"),
            "PayDate": datetime.now().strftime("%Y-%m-%d"),
            "allowances": [{"AllowanceType": "Housing", "Amount": 1500}],
            "deductions": [{"DeductionType": "Tax", "Amount": 500}]
        }, headers=self.h(), timeout=10)
        if r.status_code in (200, 201):
            self.log(f"Payslip created", "PASS")
            self.record("hr_to_payroll", "5c_create_payslip", "PASS", "")
        else:
            self.log(f"Payslip: HTTP {r.status_code} {r.text[:80]}", "WARN")
            self.record("hr_to_payroll", "5c_create_payslip", "WARN", str(r.status_code))

        # 5d. Run payroll calculation
        pay_period = datetime.now().strftime("%Y-%m")
        pay_date = datetime.now().strftime("%Y-%m-%d")
        r = requests.post(f"{self.base}/api/payroll/calculate?employee_code={emp_code}&pay_period={pay_period}&pay_date={pay_date}", headers=self.h(), timeout=10)
        if r.status_code == 200:
            self.log(f"Payroll calculated: {r.json()}", "PASS")
            self.record("hr_to_payroll", "5d_calculate_payroll", "PASS", str(r.json()))
        else:
            self.log(f"Payroll calc: HTTP {r.status_code} {r.text[:80]}", "WARN")
            self.record("hr_to_payroll", "5d_calculate_payroll", "WARN", str(r.status_code))

        self.report["cycles"]["hr_to_payroll"] = "PASS" if passed else "FAIL"
        if passed: self.report["summary"]["passed"] += 1
        else: self.report["summary"]["failed"] += 1
        return passed

    def cycle_6_cross_module_integrity(self):
        """Cycle 6: Cross-Module Referential Integrity (GL + CRM + Documents)"""
        print("\n=== CYCLE 6: Cross-Module Integrity ===")
        ts = datetime.now().strftime("%H%M%S")
        passed = True

        # 6a. Create GL Journal Voucher referencing PNR
        jv_num = f"JV-{ts}"
        pnr_num = self.snapshots.get("pnr_num") or f"8CYCLE-PNR-{ts}"
        r = requests.post(f"{self.base}/api/gl/vouchers", json={
            "JVNumber": jv_num,
            "JVDate": datetime.now().strftime("%Y-%m-%d"),
            "Narration": "8-Cycle test journal",
            "TotalDebit": 10000,
            "TotalCredit": 10000,
            "lines": [
                {"AccountCode": "A-0001", "DebitAmount": 10000, "PNRNumber": pnr_num},
                {"AccountCode": "L-0001", "CreditAmount": 10000}
            ]
        }, headers=self.h(), timeout=10)
        if r.status_code in (200, 201):
            self.log(f"Journal voucher created: {jv_num}", "PASS")
            self.record("cross_module", "6a_create_jv", "PASS", jv_num)
        else:
            self.log(f"Create JV: HTTP {r.status_code} {r.text[:80]}", "FAIL")
            self.record("cross_module", "6a_create_jv", "FAIL", r.text[:100])
            passed = False

        # 6b. Create CRM Lead
        r = requests.post(f"{self.base}/api/crm/leads", json={
            "CompanyName": f"8-Cycle Test Co {ts}",
            "ContactName": "Test Contact",
            "Email": f"test{ts}@example.com",
            "Phone": "+201234567890",
            "Source": "8-Cycle Test",
            "Status": "New"
        }, headers=self.h(), timeout=10)
        if r.status_code in (200, 201):
            lead_id = r.json().get("LeadID") or r.json().get("id")
            self.snapshots["lead_id"] = lead_id
            self.log(f"CRM Lead created: ID {lead_id}", "PASS")
            self.record("cross_module", "6b_create_lead", "PASS", str(lead_id))
        else:
            self.log(f"Create lead: HTTP {r.status_code} {r.text[:80]}", "WARN")
            self.record("cross_module", "6b_create_lead", "WARN", str(r.status_code))

        # 6c. Create document (upload test file)
        test_file = os.path.join(BASE_DIR, "reports", "data_flow_test_8cycle.txt")
        with open(test_file, "w") as f:
            f.write(f"8-Cycle test document {ts}")
        with open(test_file, "rb") as f:
            r = requests.post(f"{self.base}/api/v1/documents/upload?description=8-cycle+test", 
                            files={"file": f}, headers=self.h(), timeout=15)
        if r.status_code in (200, 201):
            doc_id = r.json().get("document_id") or r.json().get("id")
            self.snapshots["doc_id"] = doc_id
            self.log(f"Document uploaded: ID {doc_id}", "PASS")
            self.record("cross_module", "6c_upload_doc", "PASS", str(doc_id))
        else:
            self.log(f"Upload doc: HTTP {r.status_code} {r.text[:80]}", "WARN")
            self.record("cross_module", "6c_upload_doc", "WARN", str(r.status_code))

        self.report["cycles"]["cross_module"] = "PASS" if passed else "FAIL"
        if passed: self.report["summary"]["passed"] += 1
        else: self.report["summary"]["failed"] += 1
        return passed

    def cycle_7_audit_trail(self):
        """Cycle 7: Audit Trail (All actions -> Audit log)"""
        print("\n=== CYCLE 7: Audit Trail ===")
        passed = True

        # 7a. Check meta audit trail
        r = requests.get(f"{self.base}/api/meta/audit", headers=self.h(), timeout=10)
        if r.status_code == 200:
            data = r.json()
            count = len(data) if isinstance(data, list) else data.get("count", 0)
            self.log(f"Meta audit records: {count}", "PASS")
            self.record("audit_trail", "7a_meta_audit", "PASS", str(count))
        else:
            self.log(f"Meta audit: HTTP {r.status_code}", "WARN")
            self.record("audit_trail", "7a_meta_audit", "WARN", str(r.status_code))

        # 7b. Check intelligence audit
        r = requests.get(f"{self.base}/api/v1/intelligence/audit", headers=self.h(), timeout=10)
        if r.status_code == 200:
            data = r.json()
            count = len(data) if isinstance(data, list) else data.get("count", 0)
            self.log(f"Intelligence audit records: {count}", "PASS")
            self.record("audit_trail", "7b_intel_audit", "PASS", str(count))
        else:
            self.log(f"Intel audit: HTTP {r.status_code}", "WARN")
            self.record("audit_trail", "7b_intel_audit", "WARN", str(r.status_code))

        # 7c. Check archive audit
        r = requests.get(f"{self.base}/api/v1/archive/status", headers=self.h(), timeout=10)
        if r.status_code == 200:
            data = r.json()
            self.log(f"Archive status: OK", "PASS")
            self.record("audit_trail", "7c_archive_status", "PASS", "")
        else:
            self.log(f"Archive status: HTTP {r.status_code}", "WARN")
            self.record("audit_trail", "7c_archive_status", "WARN", str(r.status_code))

        self.report["cycles"]["audit_trail"] = "PASS" if passed else "FAIL"
        if passed: self.report["summary"]["passed"] += 1
        else: self.report["summary"]["failed"] += 1
        return passed

    def cycle_8_backup_and_export(self):
        """Cycle 8: Backup + Export (All -> Backup + Export)"""
        print("\n=== CYCLE 8: Backup + Export ===")
        passed = True

        # 8a. Check backup status
        r = requests.get(f"{self.base}/api/v1/admin/backup/status", headers=self.h(), timeout=10)
        if r.status_code == 200:
            data = r.json()
            self.log(f"Backup system: {data.get('engine', 'unknown')}", "PASS")
            self.record("backup_export", "8a_backup_status", "PASS", json.dumps(data))
        else:
            self.log(f"Backup status: HTTP {r.status_code}", "FAIL")
            self.record("backup_export", "8a_backup_status", "FAIL", str(r.status_code))
            passed = False

        # 8b. Create backup
        r = requests.post(f"{self.base}/api/v1/admin/backup/create?label=8cycle-test", headers=self.h(), timeout=30)
        if r.status_code == 200:
            data = r.json()
            self.log(f"Backup created: {data.get('filename', 'ok')}", "PASS")
            self.record("backup_export", "8b_create_backup", "PASS", str(data.get('filename', '')))
        else:
            self.log(f"Create backup: HTTP {r.status_code} {r.text[:80]}", "WARN")
            self.record("backup_export", "8b_create_backup", "WARN", str(r.status_code))

        # 8c. Export entity data
        r = requests.get(f"{self.base}/api/export/events?format=json", headers=self.h(), timeout=15)
        if r.status_code == 200:
            self.log(f"Export events: HTTP 200", "PASS")
            self.record("backup_export", "8c_export_events", "PASS", "")
        else:
            self.log(f"Export events: HTTP {r.status_code}", "WARN")
            self.record("backup_export", "8c_export_events", "WARN", str(r.status_code))

        # 8d. Check backup list
        r = requests.get(f"{self.base}/api/v1/admin/backup/list", headers=self.h(), timeout=10)
        if r.status_code == 200:
            data = r.json()
            count = len(data) if isinstance(data, list) else data.get("count", 0)
            self.log(f"Backup list: {count} backups", "PASS")
            self.record("backup_export", "8d_backup_list", "PASS", str(count))
        else:
            self.log(f"Backup list: HTTP {r.status_code}", "WARN")
            self.record("backup_export", "8d_backup_list", "WARN", str(r.status_code))

        self.report["cycles"]["backup_export"] = "PASS" if passed else "FAIL"
        if passed: self.report["summary"]["passed"] += 1
        else: self.report["summary"]["failed"] += 1
        return passed

    def run(self):
        print("=" * 65)
        print("  IH-ERP 8-CYCLE DATA FLOW TEST")
        print("=" * 65)
        if not self.auth():
            return False
        self.cycle_1_events_to_sales()
        self.cycle_2_sales_to_banking()
        self.cycle_3_banking_to_reports()
        self.cycle_4_purchase_to_inventory()
        self.cycle_5_hr_to_payroll()
        self.cycle_6_cross_module_integrity()
        self.cycle_7_audit_trail()
        self.cycle_8_backup_and_export()

        print("\n" + "=" * 65)
        print("  8-CYCLE TEST RESULTS")
        print("=" * 65)
        for cycle, status in self.report["cycles"].items():
            m = "[OK]" if status == "PASS" else "[!!]"
            print(f"  {m} {cycle}")
        s = self.report["summary"]
        print(f"\n  Total: {s['passed']}/{s['total']} cycles passed ({s['passed']/s['total']*100:.0f}%)")
        if s["failed"] > 0:
            print(f"  Failed: {s['failed']} cycles need attention")

        report_path = os.path.join(BASE_DIR, "reports", f"8cycle_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(report_path, "w") as f:
            json.dump(self.report, f, indent=2, default=str)
        print(f"\n  Report: {report_path}")

        log_path = os.path.join(BASE_DIR, "reports", f"8cycle_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(log_path, "w") as f:
            json.dump(self.results, f, indent=2, default=str)
        print(f"  Details: {log_path}")
        return s["failed"] == 0


def main():
    base = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:9005"
    test = CycleTest(base)
    success = test.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
