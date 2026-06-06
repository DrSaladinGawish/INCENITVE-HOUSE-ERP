"""Phase 5: Intelligence UI — OR solver, SCM analyzer, audit, neural"""


def test_ai_ask_endpoint(client, auth_headers):
    resp = client.post("/api/ai/ask", json={"query": "How many PNRs?", "context": "dashboard"}, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data


def test_ai_analyze_sales(client, auth_headers):
    resp = client.post("/api/ai/analyze", json={"query": "sales trends", "context": "sales"}, headers=auth_headers)
    assert resp.status_code == 200


def test_ai_predict(client, auth_headers):
    resp = client.post("/api/ai/predict", json={"query": "future revenue", "context": "dashboard"}, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data or "prediction" in data


def test_ai_trends(client, auth_headers):
    resp = client.post("/api/ai/trends", json={"query": "monthly trends", "context": "dashboard"}, headers=auth_headers)
    assert resp.status_code == 200


def test_neural_nodes_list(client, auth_headers):
    resp = client.get("/api/v1/ai/nodes", headers=auth_headers)
    assert resp.status_code == 200


def test_neural_dashboard(client, auth_headers):
    resp = client.get("/api/v1/ai/dashboard", headers=auth_headers)
    assert resp.status_code == 200


def test_neural_insights(client, auth_headers):
    resp = client.get("/api/v1/ai/insights", headers=auth_headers)
    assert resp.status_code == 200


def test_neural_live_cashflow(client, auth_headers):
    resp = client.post("/api/v1/neural/cashflow-predict", json={"days": 7}, headers=auth_headers)
    assert resp.status_code == 200


def test_neural_live_anomaly(client, auth_headers):
    resp = client.post("/api/v1/neural/anomaly-detect", json={"threshold": 2}, headers=auth_headers)
    assert resp.status_code == 200


def test_neural_live_churn(client, auth_headers):
    resp = client.post("/api/v1/neural/client-churn", json={"client_code": "C-001"}, headers=auth_headers)
    assert resp.status_code in (200, 404)
