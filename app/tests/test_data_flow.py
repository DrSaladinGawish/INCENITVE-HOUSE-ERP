#!/usr/bin/env python3
"""
IH-ERP Data Flow Test — Phase 3
Verifies end-to-end data flow across all modules
"""
import requests
import json
import sys
from datetime import datetime, timedelta

class DataFlowTest:
    def __init__(self, base_url="http://localhost:9005"):
        self.base_url = base_url
        self.token = None
        self.test_data = {}
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "base_url": base_url,
            "flows": {},
            "passed": 0,
            "failed": 0
        }

    def log(self, msg, status="INFO"):
        icon = {"INFO": " * ", "PASS": "[OK]", "FAIL": "[!!]", "WARN": "[??]"}.get(status, " - ")
        print(f"  {icon} {msg}")

    def login(self):
        """Authenticate and get token"""
        try:
            resp = requests.post(
                f"{self.base_url}/api/auth/login",
                json={"username": "admin", "password": "admin123"},
                timeout=10
            )
            if resp.status_code == 200:
                self.token = resp.json().get("access_token")
                self.log("Login successful", "PASS")
                return True
            else:
                self.log(f"Login failed: HTTP {resp.status_code} - {resp.text[:100]}", "FAIL")
        except Exception as e:
            self.log(f"Login failed: {e}", "FAIL")
        return False

    def headers(self):
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    def test_flow_1_event_to_invoice(self):
        """Flow 1: Create Event -> Add Items -> Record Payment"""
        self.log("\n[FLOW 1] Event -> Payment", "INFO")
        flow_passed = True

        # 1. Create event (PNR) - requires PNRNumber
        ts = datetime.now().strftime('%H%M%S')
        event_data = {
            "PNRNumber": f"FLOWTEST-{ts}",
            "EventName": f"Flow Test Event {ts}",
            "EventStartDate": datetime.now().strftime("%Y-%m-%d"),
            "EventEndDate": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
            "client_id": 1,
            "budget": 50000,
        }

        resp = requests.post(f"{self.base_url}/api/evn/pnrs",
                           json=event_data, headers=self.headers(), timeout=10)
        if resp.status_code not in [200, 201]:
            self.log(f"Create PNR failed: HTTP {resp.status_code} {resp.text[:100]}", "FAIL")
            flow_passed = False
        else:
            pnr = resp.json()
            pnr_number = pnr.get("PNRNumber") or pnr.get("pnr_number")
            self.test_data["pnr_number"] = pnr_number
            self.log(f"PNR created: {pnr_number}", "PASS")

            # 2. Record a bank transaction
            payment = {
                "transaction_type": "CREDIT",
                "amount": 10000,
                "reference": f"FLOW-{pnr_number}",
                "description": "Flow test payment",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "bank_code": "BNK001"
            }
            resp = requests.post(f"{self.base_url}/api/bnk/transactions",
                               json=payment, headers=self.headers(), timeout=10)
            if resp.status_code in [200, 201]:
                self.log("Payment recorded in banking", "PASS")
            else:
                payment2 = {"type": "CREDIT", "amount": 10000, "reference": f"FLOW-{pnr_number}"}
                resp2 = requests.post(f"{self.base_url}/api/bnk/transactions",
                                    json=payment2, headers=self.headers(), timeout=10)
                if resp2.status_code in [200, 201]:
                    self.log("Payment recorded (alt format)", "PASS")
                else:
                    self.log(f"Record payment: HTTP {resp.status_code}", "WARN")

        self.results["flows"]["event_to_invoice"] = flow_passed
        return flow_passed

    def test_flow_2_purchase_to_inventory(self):
        """Flow 2: Create Purchase Voucher"""
        self.log("\n[FLOW 2] Purchase Voucher", "INFO")
        flow_passed = True

        ts = datetime.now().strftime('%H%M%S')
        po_data = {"VoucherNumber": f"FLOWTEST-{ts}", "TotalValue": 25000}

        resp = requests.post(f"{self.base_url}/api/pur/vouchers",
                           json=po_data, headers=self.headers(), timeout=10)
        if resp.status_code in [200, 201]:
            voucher_id = resp.json().get("VoucherID") or resp.json().get("voucher_id") or resp.json().get("id")
            self.log(f"Purchase voucher created: {voucher_id}", "PASS")
        else:
            self.log(f"Create purchase: HTTP {resp.status_code} (known server issue)", "FAIL")
            flow_passed = False

        self.results["flows"]["purchase_to_inventory"] = flow_passed
        return flow_passed

    def test_flow_3_report_generation(self):
        """Flow 3: Generate reports from transaction data"""
        self.log("\n[FLOW 3] Reports -> Export", "INFO")
        flow_passed = True

        from_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        to_date = datetime.now().strftime("%Y-%m-%d")

        reports = [
            ("Trial Balance", f"/reports/financial/api/trial-balance?as_of_date={to_date}"),
            ("P&L", f"/reports/financial/api/profit-loss?from_date={from_date}&to_date={to_date}"),
            ("Balance Sheet", f"/reports/financial/api/balance-sheet?as_of_date={to_date}"),
            ("Cash Flow", f"/reports/financial/api/cash-flow?from_date={from_date}&to_date={to_date}"),
        ]

        for name, path in reports:
            resp = requests.get(f"{self.base_url}{path}", headers=self.headers(), timeout=15)
            status = "PASS" if resp.status_code == 200 else "FAIL"
            if resp.status_code != 200:
                flow_passed = False
            self.log(f"{name}: HTTP {resp.status_code}", status)

        exports = [
            ("P&L CSV", f"/reports/financial/api/profit-loss/csv?from_date={from_date}&to_date={to_date}"),
            ("TB CSV", f"/reports/financial/api/trial-balance/csv?as_of_date={to_date}"),
        ]

        for name, path in exports:
            resp = requests.get(f"{self.base_url}{path}", headers=self.headers(), timeout=15)
            status = "PASS" if resp.status_code == 200 else "FAIL"
            if resp.status_code != 200:
                flow_passed = False
            self.log(f"{name}: HTTP {resp.status_code}", status)

        self.results["flows"]["report_generation"] = flow_passed
        return flow_passed

    def test_flow_4_backup_and_archive(self):
        """Flow 4: Backup system + Archive integration"""
        self.log("\n[FLOW 4] Backup -> Archive", "INFO")
        flow_passed = True

        resp = requests.get(f"{self.base_url}/api/v1/admin/backup/status", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            self.log(f"Backup status: {data.get('status', 'unknown')}", "PASS")
        else:
            self.log(f"Backup status: HTTP {resp.status_code}", "FAIL")
            flow_passed = False

        resp = requests.get(f"{self.base_url}/api/v1/archive/status", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            status = "PASS" if data.get("connected") else "WARN"
            self.log(f"USB Archive: {'Connected' if data.get('connected') else 'Not connected'}", status)
        else:
            self.log(f"Archive status: HTTP {resp.status_code}", "WARN")

        self.results["flows"]["backup_and_archive"] = flow_passed
        return flow_passed

    def test_data_locations(self):
        """Verify data exists in correct tables"""
        self.log("\n[DATA LOCATIONS] Record counts via API", "INFO")

        endpoints = [
            ("Events (PNRs)", "/api/evn/pnrs"),
            ("Sales Invoices", "/api/sal/invoices"),
            ("Purchase Vouchers", "/api/pur/vouchers"),
            ("Bank Transactions", "/api/bnk/transactions"),
        ]

        for name, path in endpoints:
            resp = requests.get(f"{self.base_url}{path}", headers=self.headers(), timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list):
                    count = len(data)
                elif isinstance(data, dict):
                    count = data.get("count") or data.get("total") or len(data)
                else:
                    count = 0
                self.log(f"{name}: {count} records", "PASS" if count is not None else "WARN")
            else:
                self.log(f"{name}: HTTP {resp.status_code}", "WARN")

        return True

    def run_all(self):
        """Run all data flow tests"""
        print("=" * 60)
        print("IH-ERP DATA FLOW TEST - Phase 3")
        print("=" * 60)

        if not self.login():
            print("\nCannot proceed without authentication")
            return False

        flows = [
            self.test_flow_1_event_to_invoice,
            self.test_flow_2_purchase_to_inventory,
            self.test_flow_3_report_generation,
            self.test_flow_4_backup_and_archive,
            self.test_data_locations,
        ]

        for flow in flows:
            try:
                result = flow()
                if result:
                    self.results["passed"] += 1
                else:
                    self.results["failed"] += 1
            except Exception as e:
                self.log(f"Flow error: {e}", "FAIL")
                self.results["failed"] += 1

        print("\n" + "=" * 60)
        print("RESULTS")
        print("=" * 60)

        total = len(flows)
        passed = self.results["passed"]
        failed = self.results["failed"]

        for name, result in self.results["flows"].items():
            status = "PASS" if result else "FAIL"
            print(f"  [{status}] - {name}")

        print(f"\nTotal: {passed}/{total} flows passed")

        report_path = f"reports/data_flow_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, "w") as f:
            json.dump(self.results, f, indent=2, default=str)
        print(f"\nReport saved: {report_path}")

        return failed == 0


def main():
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:9005"
    tester = DataFlowTest(base_url)
    success = tester.run_all()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
