"""Integration tests for IncentiveHouse ERP v2.2.2."""

import pytest
from httpx import AsyncClient


class TestHealth:
    async def test_health_endpoint(self, client: AsyncClient):
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["version"] == "2.2.2"

    async def test_ready_endpoint(self, client: AsyncClient):
        resp = await client.get("/ready")
        data = resp.json()
        assert data["status"] in ("ready", "not ready")

    async def test_root_redirect(self, client: AsyncClient):
        resp = await client.get("/", follow_redirects=False)
        assert resp.status_code == 307


class TestClients:
    async def test_list_clients(self, client: AsyncClient):
        resp = await client.get("/api/v1/clients/")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_create_and_get_client(self, client: AsyncClient):
        payload = {"client_code": "TST001", "name": "Test Client", "email": "test@example.com"}
        resp = await client.post("/api/v1/clients/", json=payload)
        assert resp.status_code == 201
        created = resp.json()
        assert created["name"] == "Test Client"
        cid = created["client_id"]

        resp = await client.get(f"/api/v1/clients/{cid}")
        assert resp.status_code == 200
        assert resp.json()["client_id"] == cid

    async def test_update_client(self, client: AsyncClient):
        payload = {"client_code": "TST002", "name": "Update Me"}
        resp = await client.post("/api/v1/clients/", json=payload)
        cid = resp.json()["client_id"]

        resp = await client.put(f"/api/v1/clients/{cid}", json={"name": "Updated"})
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated"


class TestVendors:
    async def test_list_vendors(self, client: AsyncClient):
        resp = await client.get("/api/v1/vendors/")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_create_vendor(self, client: AsyncClient):
        payload = {"vendor_code": "V001", "name": "Test Vendor"}
        resp = await client.post("/api/v1/vendors/", json=payload)
        assert resp.status_code == 201
        assert resp.json()["name"] == "Test Vendor"


class TestPNR:
    async def test_list_pnr(self, client: AsyncClient):
        resp = await client.get("/api/v1/pnr/")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_create_pnr(self, client: AsyncClient):
        payload = {"pnr_code": "TEST99", "name": "Test PNR", "pnr_type": "JOB"}
        resp = await client.post("/api/v1/pnr/", json=payload)
        assert resp.status_code == 201
        assert resp.json()["pnr_code"] == "TEST99"

    async def test_fuzzy_search(self, client: AsyncClient):
        resp = await client.get("/api/v1/pnr/search/fuzzy", params={"query": "TEST"})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestEmployees:
    async def test_list_employees(self, client: AsyncClient):
        resp = await client.get("/api/v1/employees/")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_create_employee(self, client: AsyncClient):
        payload = {"employee_code": "E001", "name": "John Doe", "position": "technician"}
        resp = await client.post("/api/v1/employees/", json=payload)
        assert resp.status_code == 201
        assert resp.json()["name"] == "John Doe"


class TestReports:
    async def test_dashboard_kpi(self, client: AsyncClient):
        resp = await client.get("/api/v1/reports/dashboard/kpi")
        assert resp.status_code == 200
        data = resp.json()
        assert "active_events" in data
        assert "total_revenue" in data

    async def test_monthly_trend(self, client: AsyncClient):
        resp = await client.get("/api/v1/reports/monthly-trend", params={"months": 3})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_event_pnl(self, client: AsyncClient):
        resp = await client.get("/api/v1/reports/event-pnl")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_event_status_breakdown(self, client: AsyncClient):
        resp = await client.get("/api/v1/reports/event-status-breakdown")
        assert resp.status_code == 200
        assert isinstance(resp.json(), dict)


class TestFinance:
    async def test_cash_flow_projections(self, client: AsyncClient):
        resp = await client.get("/api/v1/finance/cash-flow-projections")
        assert resp.status_code == 200
        data = resp.json()
        assert "expected_inflow" in data
        assert "expected_outflow" in data

    async def test_aging_report(self, client: AsyncClient):
        resp = await client.get("/api/v1/finance/aging-report")
        assert resp.status_code == 200
        data = resp.json()
        assert "0-30" in data
        assert "91+" in data

    async def test_list_sales_invoices(self, client: AsyncClient):
        resp = await client.get("/api/v1/finance/invoices/sales")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_list_purchase_invoices(self, client: AsyncClient):
        resp = await client.get("/api/v1/finance/invoices/purchases")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_audit_trail(self, client: AsyncClient):
        resp = await client.get("/api/v1/finance/audit")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestAuth:
    async def test_me_endpoint(self, client: AsyncClient):
        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code == 200


class TestOR:
    async def test_or_health(self, client: AsyncClient):
        resp = await client.get("/api/v1/or/health")
        assert resp.status_code == 200

    async def test_or_requests(self, client: AsyncClient):
        resp = await client.get("/api/v1/or/requests")
        assert resp.status_code == 200


class TestBank:
    async def test_bank_list(self, client: AsyncClient):
        resp = await client.get("/api/v1/bnk/")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_bank_summary(self, client: AsyncClient):
        resp = await client.get("/api/v1/bnk/stats/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_transactions" in data


class TestSales:
    async def test_sales_list(self, client: AsyncClient):
        resp = await client.get("/api/v1/sales/")
        assert resp.status_code == 200

    async def test_sales_summary(self, client: AsyncClient):
        resp = await client.get("/api/v1/sales/stats/summary")
        assert resp.status_code == 200


class TestEvents:
    async def test_event_list(self, client: AsyncClient):
        resp = await client.get("/api/v1/events/")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_create_event(self, client: AsyncClient):
        payload = {"event_code": "EVT001", "name": "Test Event"}
        resp = await client.post("/api/v1/events/", json=payload)
        assert resp.status_code == 201
        assert resp.json()["name"] == "Test Event"


class TestPipeline:
    async def test_pipeline_status(self, client: AsyncClient):
        resp = await client.get("/api/v2/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "OPERATIONAL"
        assert data["version"] == "2.2.2"
        assert "stages" in data

    async def test_pipeline_validate_empty(self, client: AsyncClient):
        resp = await client.post("/api/v2/extract", json={"module": "BNK", "dry_run": True})
        assert resp.status_code == 200
        data = resp.json()
        assert data["module"] == "BNK"

    async def test_pipeline_journal_empty(self, client: AsyncClient):
        resp = await client.get("/api/v2/journal")
        assert resp.status_code == 200
        data = resp.json()
        assert "entries" in data
        assert "verification" in data

    async def test_pipeline_validate_no_extract(self, client: AsyncClient):
        resp = await client.post("/api/v2/validate", json={"extract_id": 9999})
        assert resp.status_code == 404

    async def test_pipeline_stage_no_validate(self, client: AsyncClient):
        resp = await client.post("/api/v2/stage", json={"validate_id": 9999, "target_table": "bnk_staging"})
        assert resp.status_code == 404

    async def test_pipeline_reconcile_no_stage(self, client: AsyncClient):
        resp = await client.post("/api/v2/reconcile", json={"stage_id": 9999, "module": "BNK"})
        assert resp.status_code == 404

    async def test_pipeline_approve_no_recon(self, client: AsyncClient):
        resp = await client.post("/api/v2/approve", json={"recon_id": 9999})
        assert resp.status_code == 404

    async def test_pipeline_promote_no_approve(self, client: AsyncClient):
        resp = await client.post("/api/v2/promote", json={"approve_id": 9999})
        assert resp.status_code == 404

    async def test_pipeline_observe_no_promote(self, client: AsyncClient):
        resp = await client.post("/api/v2/observe", json={"promote_id": 9999})
        assert resp.status_code == 404


class TestPettyCash:
    async def test_petty_cash_list(self, client: AsyncClient):
        resp = await client.get("/api/v1/petty-cash/")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_petty_cash_create(self, client: AsyncClient):
        payload = {"voucher_no": "PC001", "description": "Office supplies", "amount": 500}
        resp = await client.post("/api/v1/petty-cash/", json=payload)
        assert resp.status_code == 200
        assert resp.json()["voucher_no"] == "PC001"

    async def test_petty_cash_approve(self, client: AsyncClient):
        payload = {"voucher_no": "PC002", "description": "Transport", "amount": 200}
        resp = await client.post("/api/v1/petty-cash/", json=payload)
        vid = resp.json()["id"]
        resp = await client.post(f"/api/v1/petty-cash/{vid}/approve")
        assert resp.status_code == 200
        assert resp.json()["status"] == "approved"

    async def test_petty_cash_stats(self, client: AsyncClient):
        resp = await client.get("/api/v1/petty-cash/summary/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_approved" in data
        assert "total_pending" in data


class TestCOA:
    async def test_coa_list(self, client: AsyncClient):
        resp = await client.get("/api/v1/coa/")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_coa_create(self, client: AsyncClient):
        payload = {"acc_key": "1001", "acc_name": "Cash in Bank", "acc_type": "ASSET"}
        resp = await client.post("/api/v1/coa/", json=payload)
        assert resp.status_code == 200
        assert resp.json()["acc_key"] == "1001"

    async def test_coa_get(self, client: AsyncClient):
        payload = {"acc_key": "1002", "acc_name": "Accounts Receivable", "acc_type": "ASSET"}
        resp = await client.post("/api/v1/coa/", json=payload)
        cid = resp.json()["id"]
        resp = await client.get(f"/api/v1/coa/{cid}")
        assert resp.status_code == 200
        assert resp.json()["acc_key"] == "1002"

    async def test_coa_categories(self, client: AsyncClient):
        resp = await client.get("/api/v1/coa/categories/list")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_coa_types(self, client: AsyncClient):
        resp = await client.get("/api/v1/coa/types/list")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestCheques:
    async def test_cheques_list(self, client: AsyncClient):
        resp = await client.get("/api/v1/cheques/")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_cheques_create(self, client: AsyncClient):
        payload = {"cheque_no": "CHQ001", "payee": "Test Vendor", "amount": 15000}
        resp = await client.post("/api/v1/cheques/", json=payload)
        assert resp.status_code == 200
        assert resp.json()["cheque_no"] == "CHQ001"

    async def test_cheques_status_update(self, client: AsyncClient):
        payload = {"cheque_no": "CHQ002", "payee": "ABC Co", "amount": 25000}
        resp = await client.post("/api/v1/cheques/", json=payload)
        cid = resp.json()["id"]
        resp = await client.post(f"/api/v1/cheques/{cid}/status", params={"status": "cashed"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "cashed"

    async def test_cheques_stats(self, client: AsyncClient):
        resp = await client.get("/api/v1/cheques/summary/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_issued" in data


class TestWHT:
    async def test_wht_list(self, client: AsyncClient):
        resp = await client.get("/api/v1/wht/")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_wht_create(self, client: AsyncClient):
        payload = {"certificate_no": "WHT001", "vendor_id": 1, "gross_amount": 10000, "wht_rate": 1.0}
        resp = await client.post("/api/v1/wht/", json=payload)
        assert resp.status_code == 200
        assert resp.json()["certificate_no"] == "WHT001"
        assert resp.json()["wht_amount"] == 100.0

    async def test_wht_file(self, client: AsyncClient):
        payload = {"certificate_no": "WHT002", "vendor_id": 1, "gross_amount": 5000, "wht_rate": 1.0}
        resp = await client.post("/api/v1/wht/", json=payload)
        wid = resp.json()["id"]
        resp = await client.post(f"/api/v1/wht/{wid}/file")
        assert resp.status_code == 200
        assert resp.json()["status"] == "filed"

    async def test_wht_stats(self, client: AsyncClient):
        resp = await client.get("/api/v1/wht/summary/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_wht" in data
        assert "pending_wht" in data
