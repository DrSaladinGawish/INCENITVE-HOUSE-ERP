def test_bnk_banks(client, auth_headers):
    resp = client.get("/api/bnk/banks", headers=auth_headers)
    assert resp.status_code == 200


def test_bnk_transactions(client, auth_headers):
    resp = client.get("/api/bnk/transactions", headers=auth_headers)
    assert resp.status_code == 200


def test_sal_clients(client, auth_headers):
    resp = client.get("/api/sal/clients", headers=auth_headers)
    assert resp.status_code == 200


def test_sal_invoices(client, auth_headers):
    resp = client.get("/api/sal/invoices", headers=auth_headers)
    assert resp.status_code == 200


def test_pur_vendors(client, auth_headers):
    resp = client.get("/api/pur/vendors", headers=auth_headers)
    assert resp.status_code == 200


def test_pur_vouchers(client, auth_headers):
    resp = client.get("/api/pur/vouchers", headers=auth_headers)
    assert resp.status_code == 200


def test_evn_pnrs(client, auth_headers):
    resp = client.get("/api/evn/pnrs", headers=auth_headers)
    assert resp.status_code == 200


def test_evn_categories(client, auth_headers):
    resp = client.get("/api/evn/categories", headers=auth_headers)
    assert resp.status_code == 200


def test_evn_sub_categories(client, auth_headers):
    resp = client.get("/api/evn/sub-categories", headers=auth_headers)
    assert resp.status_code == 200


def test_evn_service_types(client, auth_headers):
    resp = client.get("/api/evn/service-types", headers=auth_headers)
    assert resp.status_code == 200


def test_evn_budget_lines(client, auth_headers):
    resp = client.get("/api/evn/budget-lines", headers=auth_headers)
    assert resp.status_code == 200


def test_gl_accounts(client, auth_headers):
    resp = client.get("/api/gl/accounts", headers=auth_headers)
    assert resp.status_code == 200


def test_gl_vouchers(client, auth_headers):
    resp = client.get("/api/gl/vouchers", headers=auth_headers)
    assert resp.status_code == 200


def test_gl_employees(client, auth_headers):
    resp = client.get("/api/gl/employees", headers=auth_headers)
    assert resp.status_code == 200


def test_dashboard_summary(client, auth_headers):
    resp = client.get("/api/dashboard/summary", headers=auth_headers)
    assert resp.status_code == 200


def test_dashboard_export_pdf(client, auth_headers):
    resp = client.get("/api/dashboard/export?format=pdf", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"


def test_dashboard_export_csv(client, auth_headers):
    resp = client.get("/api/dashboard/export?format=csv", headers=auth_headers)
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]


def test_dashboard_export_xlsx(client, auth_headers):
    resp = client.get("/api/dashboard/export?format=xlsx", headers=auth_headers)
    assert resp.status_code == 200
    assert "spreadsheetml" in resp.headers["content-type"]


def test_dashboard_monthly(client, auth_headers):
    resp = client.get("/api/dashboard/monthly", headers=auth_headers)
    assert resp.status_code == 200


def test_export_pnrs_pdf(client, auth_headers):
    resp = client.get("/api/export/pnrs?format=pdf", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"


def test_export_sales_csv(client, auth_headers):
    resp = client.get("/api/export/sales?format=csv", headers=auth_headers)
    assert resp.status_code == 200


def test_export_unknown_entity(client, auth_headers):
    resp = client.get("/api/export/unknown?format=pdf", headers=auth_headers)
    assert resp.status_code == 404
