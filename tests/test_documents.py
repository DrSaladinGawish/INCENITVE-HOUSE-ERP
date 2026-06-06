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


def test_document_upload(client):
    resp = client.post("/api/v1/documents/upload", files={"file": ("test.txt", b"Hello World")})
    assert resp.status_code == 200
    data = resp.json()
    assert data["uploaded"] == True
    assert data["file_name"] == "test.txt"


def test_document_upload_and_download(client):
    resp = client.post("/api/v1/documents/upload", files={"file": ("hello.txt", b"Download me")})
    assert resp.status_code == 200
    doc_id = resp.json()["document_id"]
    resp2 = client.get(f"/api/v1/documents/{doc_id}/download")
    assert resp2.status_code == 200
    assert resp2.content == b"Download me"


def test_document_upload_and_delete(client):
    resp = client.post("/api/v1/documents/upload", files={"file": ("delete_me.txt", b"Delete me")})
    assert resp.status_code == 200
    doc_id = resp.json()["document_id"]
    resp2 = client.delete(f"/api/v1/documents/{doc_id}")
    assert resp2.status_code == 200
    assert resp2.json()["deleted"] == True
    resp3 = client.get(f"/api/v1/documents/{doc_id}")
    assert resp3.status_code == 404


def test_document_download_not_found(client):
    resp = client.get("/api/v1/documents/99999/download")
    assert resp.status_code == 404


def test_document_delete_not_found(client):
    resp = client.delete("/api/v1/documents/99999")
    assert resp.status_code == 404
