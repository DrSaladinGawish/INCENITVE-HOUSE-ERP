import pytest
from app.services.ai.llm_service import LLMService


def test_llm_service_initializes():
    service = LLMService()
    assert service.provider in ["ollama", "openai"]
    assert service.model is not None


def test_llm_fallback_revenue():
    service = LLMService()
    context = {"page": "dashboard", "user": "Admin"}
    erp_context = "Revenue YTD: EGP 4,769,491.00\nExpenses YTD: EGP 2,500,000.00\nActive PNRs: 42"

    result = service._rich_fallback("What is my revenue?", context, erp_context)
    assert "4,769,491" in result["reply"]
    assert result["confidence"] >= 0.9


def test_llm_fallback_profit():
    service = LLMService()
    context = {"page": "dashboard", "user": "Admin"}
    erp_context = "Revenue YTD: EGP 4,769,491.00\nExpenses YTD: EGP 2,500,000.00\nActive PNRs: 42"

    result = service._rich_fallback("What is my profit?", context, erp_context)
    assert "2,269,491" in result["reply"]
    assert result["confidence"] >= 0.9


@pytest.mark.asyncio
async def test_llm_ask_endpoint(client):
    r = client.post("/api/v1/intelligence/ai/assist", json={
        "message": "What is revenue?",
        "page_context": "/dashboard",
        "user": "Admin"
    })
    assert r.status_code == 200
    data = r.json()
    assert "reply" in data
    assert "confidence" in data
