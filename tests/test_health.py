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
