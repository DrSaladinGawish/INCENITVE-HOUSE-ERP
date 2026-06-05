def test_ai_ask(client):
    resp = client.post("/api/ai/ask", json={"query": "test query"})
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data


def test_ai_analyze(client):
    resp = client.post("/api/ai/analyze", json={"entity_type": "bnk", "entity_id": "1"})
    assert resp.status_code == 200


def test_ai_predict(client):
    resp = client.post("/api/ai/predict", json={"entity_type": "bnk", "entity_id": "1"})
    assert resp.status_code == 200


def test_ai_trends(client):
    resp = client.post("/api/ai/trends", json={"entity_type": "bnk", "entity_id": "1"})
    assert resp.status_code == 200


def test_neural_nodes_list(client):
    resp = client.get("/api/v1/ai/nodes")
    assert resp.status_code == 200


def test_neural_insights(client):
    resp = client.get("/api/v1/ai/insights")
    assert resp.status_code == 200


def test_neural_dashboard(client):
    resp = client.get("/api/v1/ai/dashboard")
    assert resp.status_code == 200


def test_neural_predict_fallback(client):
    resp = client.post("/api/v1/ai/predict/finance/cashflow", json={"forecast_days": 30})
    assert resp.status_code == 200


def test_neural_feedback(client):
    resp = client.post("/api/v1/ai/feedback", json={
        "prediction_id": "test-1", "organ": "finance", "cell": "cashflow",
        "actual_outcome": 100.0, "feedback_text": "test feedback"
    })
    assert resp.status_code == 200


def test_neural_refresh_features(client):
    resp = client.post("/api/v1/ai/refresh-features")
    assert resp.status_code == 200
