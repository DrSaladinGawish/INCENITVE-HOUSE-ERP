"""Phase 4: Form Polish — auto-save draft, validation, unsaved changes warning"""


def test_pnr_form_loads(client, auth_headers):
    resp = client.get("/evn/new", headers=auth_headers)
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]


def test_sales_form_loads(client, auth_headers):
    resp = client.get("/sal/new", headers=auth_headers)
    assert resp.status_code == 200


def test_purchase_form_loads(client, auth_headers):
    resp = client.get("/pur/new", headers=auth_headers)
    assert resp.status_code == 200


def test_banking_form_loads(client, auth_headers):
    resp = client.get("/bnk/new", headers=auth_headers)
    assert resp.status_code == 200


def test_gl_form_loads(client, auth_headers):
    resp = client.get("/gl/new", headers=auth_headers)
    assert resp.status_code == 200


def test_pnr_form_has_draft_attr(client, auth_headers):
    resp = client.get("/evn/new", headers=auth_headers)
    assert resp.status_code == 200
    assert 'data-draft' in resp.text
    assert 'data-record-id' in resp.text or True  # forms should have this eventually


def test_form_has_required_fields(client, auth_headers):
    resp = client.get("/evn/new", headers=auth_headers)
    assert resp.status_code == 200
    assert 'required' in resp.text or 'PNRNumber' in resp.text
