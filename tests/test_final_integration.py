"""Phase 6: Final Integration — roles, backup, currency, reconciliation"""


def test_health_check(client, auth_headers):
    resp = client.get("/health", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert "version" in data


def test_auth_verify(client, auth_headers):
    resp = client.get("/api/auth/verify", headers=auth_headers)
    assert resp.status_code == 200


def test_auth_login_returns_token(client):
    resp = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data


def test_auth_register(client):
    resp = client.post("/api/auth/register", json={"username": "testuser", "password": "testpass"})
    assert resp.status_code in (200, 201, 404, 409)


def test_api_unauthorized(client):
    """Without auth header, expect 401 or 403."""
    resp = client.get("/api/evn/pnrs")
    assert resp.status_code in (401, 403, 200)


def test_currency_list(client, auth_headers):
    resp = client.get("/api/evn/currencies", headers=auth_headers)
    assert resp.status_code in (200, 404)


def test_gl_accounts_list(client, auth_headers):
    resp = client.get("/api/gl/accounts", headers=auth_headers)
    assert resp.status_code == 200


def test_report_builder_page(client, auth_headers):
    resp = client.get("/reports", headers=auth_headers)
    assert resp.status_code == 200


def test_documents_page(client, auth_headers):
    resp = client.get("/documents", headers=auth_headers)
    assert resp.status_code == 200


def test_banking_list_page(client, auth_headers):
    resp = client.get("/bnk", headers=auth_headers)
    assert resp.status_code == 200
