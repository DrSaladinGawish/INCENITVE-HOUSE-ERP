def test_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"


def test_root_page(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "IncentiveHouse" in resp.text


def test_evn_page(client):
    resp = client.get("/evn")
    assert resp.status_code == 200


def test_bnk_page(client):
    resp = client.get("/bnk")
    assert resp.status_code == 200


def test_sal_page(client):
    resp = client.get("/sal")
    assert resp.status_code == 200


def test_pur_page(client):
    resp = client.get("/pur")
    assert resp.status_code == 200


def test_gl_page(client):
    resp = client.get("/gl")
    assert resp.status_code == 200


def test_login_page(client):
    resp = client.get("/login")
    assert resp.status_code == 200
    assert "Login" in resp.text


def test_evn_new_page(client):
    resp = client.get("/evn/new")
    assert resp.status_code == 200
    assert "New PNR" in resp.text


def test_sal_new_page(client):
    resp = client.get("/sal/new")
    assert resp.status_code == 200
    assert "New Sales Invoice" in resp.text


def test_pur_new_page(client):
    resp = client.get("/pur/new")
    assert resp.status_code == 200
    assert "New Purchase Voucher" in resp.text


def test_bnk_new_page(client):
    resp = client.get("/bnk/new")
    assert resp.status_code == 200
    assert "New Bank Transaction" in resp.text


def test_gl_new_page(client):
    resp = client.get("/gl/new")
    assert resp.status_code == 200
    assert "New Journal Voucher" in resp.text


def test_search_endpoint(client):
    resp = client.get("/api/search?q=test")
    assert resp.status_code == 200
    data = resp.json()
    assert "pnrs" in data
    assert "clients" in data
    assert "vendors" in data


def test_auth_me_endpoint(client, auth_headers):
    resp = client.get("/api/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "admin"
