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
