def test_document_search(client):
    resp = client.get("/api/v1/documents")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data


def test_document_modules(client):
    resp = client.get("/api/v1/documents/modules")
    assert resp.status_code == 200


def test_document_stats(client):
    resp = client.get("/api/v1/documents/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_documents" in data


def test_document_orphans(client):
    resp = client.get("/api/v1/documents/orphans")
    assert resp.status_code == 200


def test_document_seed_modules(client):
    resp = client.post("/api/v1/documents/seed-modules")
    assert resp.status_code == 200


def test_document_seeded_modules(client):
    """Seed modules returns count (may be 0 if no DB)."""
    resp = client.post("/api/v1/documents/seed-modules")
    assert resp.status_code == 200


def test_document_not_found(client):
    resp = client.get("/api/v1/documents/99999")
    assert resp.status_code == 404


def test_document_auto_link(client):
    resp = client.post("/api/v1/documents/auto-link")
    assert resp.status_code == 200


def test_document_verify_all(client):
    resp = client.post("/api/v1/documents/verify-all")
    assert resp.status_code == 200


def test_document_ingest_nonexistent(client):
    resp = client.post("/api/v1/documents/ingest?path=nonexistent.pdf")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ingested"] == False
