import pytest
from app.services.neural.trainer import NeuralTrainer


def test_trainer_initializes():
    t = NeuralTrainer()
    assert t.MODEL_DIR == "models"


def test_train_insufficient_data():
    t = NeuralTrainer()
    result = t.train_cashflow_predictor([])
    assert result["status"] == "insufficient_data"


def test_train_and_predict():
    t = NeuralTrainer()
    historical = [
        {"date": "2025-01-01", "net_amount": 1000},
        {"date": "2025-02-01", "net_amount": 1200},
        {"date": "2025-03-01", "net_amount": 1100},
        {"date": "2025-04-01", "net_amount": 1300},
        {"date": "2025-05-01", "net_amount": 1250}
    ]
    result = t.train_cashflow_predictor(historical)
    assert result["status"] == "trained"
    assert result["data_points"] == 5

    predictions = t.predict_cashflow(3)
    assert len(predictions) == 3
    assert all(p >= 0 for p in predictions)


@pytest.mark.asyncio
async def test_train_endpoint(client):
    r = client.post("/api/v1/intelligence/neural/train/cashflow")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] in ["trained", "insufficient_data"]


@pytest.mark.asyncio
async def test_predict_endpoint(client):
    client.post("/api/v1/intelligence/neural/train/cashflow")
    r = client.get("/api/v1/intelligence/neural/predict/cashflow?periods=3")
    assert r.status_code == 200
    data = r.json()
    assert "forecast" in data
    assert len(data["forecast"]) == 3
