"""Phase 3: List Enhancements — sort, paginate, search"""


def test_pnr_list_pagination(client, auth_headers):
    resp = client.get("/api/evn/pnrs?page=1&per_page=5", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    assert "items" in data
    assert "total" in data
    assert "page" in data


def test_sales_list_pagination(client, auth_headers):
    resp = client.get("/api/sal/invoices?page=1&per_page=5", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    assert "items" in data or "invoices" in data


def test_search_pnr(client, auth_headers):
    resp = client.get("/api/search?q=PNR", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "pnrs" in data


def test_search_empty(client, auth_headers):
    resp = client.get("/api/search?q=", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data == {"pnrs": 0, "clients": 0, "vendors": 0}


def test_search_client(client, auth_headers):
    resp = client.get("/api/search?q=test", headers=auth_headers)
    assert resp.status_code == 200


def test_data_headers_on_pnrs(client, auth_headers):
    resp = client.get("/api/evn/pnrs", headers=auth_headers)
    assert resp.status_code == 200
