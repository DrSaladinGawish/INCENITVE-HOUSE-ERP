import os
import httpx
from typing import Dict, Optional
from datetime import datetime


class LLMService:
    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "ollama")
        self.api_key = os.getenv("LLM_API_KEY", "")
        self.base_url = os.getenv("LLM_BASE_URL", "http://host.docker.internal:11434")
        self.model = os.getenv("LLM_MODEL", "llama3.1:8b")
        self.context_window = 4096
        self._context_cache: Dict[str, str] = {}
        self._cache_time: Optional[datetime] = None

    async def ask(self, message: str, context: dict) -> dict:
        erp_context = await self._build_erp_context(context.get("page", "unknown"))
        system_prompt = f"""You are the Incentive House ERP AI Assistant.

CURRENT PAGE: {context.get('page', 'unknown')}
USER: {context.get('user', 'User')}

LIVE ERP DATA:
{erp_context}

Answer based on the actual data above. Be specific with numbers.
If you don't know, say "I need to check the [specific report] for that."
Keep answers under 3 sentences."""

        try:
            if self.provider == "openai" and self.api_key:
                return await self._ask_openai(message, system_prompt)
            elif self.provider == "ollama":
                return await self._ask_ollama(message, system_prompt)
            else:
                return self._rich_fallback(message, context, erp_context)
        except Exception:
            return self._rich_fallback(message, context, erp_context)

    async def _build_erp_context(self, page: str) -> str:
        cache_key = f"ctx_{page}_{datetime.now().hour}"
        if cache_key in self._context_cache:
            return self._context_cache[cache_key]
        context_parts = []
        try:
            from app.services.dashboard_service import get_dashboard_data
            dash = await get_dashboard_data("YTD")
            context_parts.append(f"Revenue YTD: EGP {dash.get('total_revenue', 0):,.2f}")
            context_parts.append(f"Expenses YTD: EGP {dash.get('total_expenses', 0):,.2f}")
            context_parts.append(f"Active PNRs: {dash.get('active_pnrs', 0)}")
            context_parts.append(f"Bank Balance: EGP {dash.get('bank_balance', 0):,.2f}")
        except Exception:
            pass
        result = "\n".join(context_parts)
        self._context_cache[cache_key] = result
        return result

    async def _ask_openai(self, message: str, system_prompt: str) -> dict:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": message}
                    ],
                    "temperature": 0.2,
                    "max_tokens": 500
                }
            )
            data = r.json()
            return {
                "reply": data["choices"][0]["message"]["content"],
                "model": self.model,
                "confidence": 0.95,
                "source": "openai",
                "cached": False
            }

    async def _ask_ollama(self, message: str, system_prompt: str) -> dict:
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": message}
                    ],
                    "stream": False,
                    "options": {"temperature": 0.2}
                }
            )
            data = r.json()
            return {
                "reply": data.get("message", {}).get("content", "No response"),
                "model": self.model,
                "confidence": 0.85,
                "source": "ollama",
                "cached": False
            }

    def _rich_fallback(self, message: str, context: dict, erp_context: str) -> dict:
        msg_lower = message.lower()
        revenue = 0
        expenses = 0
        pnrs = 0
        for line in erp_context.split("\n"):
            if "Revenue" in line:
                try:
                    revenue = float(line.split("EGP")[1].replace(",", ""))
                except Exception:
                    pass
            elif "Expenses" in line:
                try:
                    expenses = float(line.split("EGP")[1].replace(",", ""))
                except Exception:
                    pass
            elif "PNRs" in line:
                try:
                    pnrs = int(line.split(":")[1].strip())
                except Exception:
                    pass

        if "revenue" in msg_lower:
            return {"reply": f"Total revenue YTD is EGP {revenue:,.2f}. Check Sales > Invoices for client breakdown.", "confidence": 0.9, "source": "erp_data"}
        elif "expense" in msg_lower or "cost" in msg_lower:
            return {"reply": f"Total expenses YTD are EGP {expenses:,.2f}. Check Purchases > Vouchers for details.", "confidence": 0.9, "source": "erp_data"}
        elif "pnr" in msg_lower or "event" in msg_lower:
            return {"reply": f"There are {pnrs} active PNRs. Go to Events to create new ones or view details.", "confidence": 0.9, "source": "erp_data"}
        elif "profit" in msg_lower or "net" in msg_lower:
            profit = revenue - expenses
            return {"reply": f"Net profit YTD is EGP {profit:,.2f} (Revenue {revenue:,.2f} - Expenses {expenses:,.2f}).", "confidence": 0.9, "source": "erp_data"}
        elif "help" in msg_lower:
            return {"reply": "I can tell you revenue, expenses, PNR count, bank balance, or help with any form. What do you need?", "confidence": 0.8, "source": "fallback"}
        else:
            return {"reply": f"I'm on the {context.get('page', 'dashboard')} with live data. Ask about revenue, expenses, PNRs, or banking.", "confidence": 0.6, "source": "fallback"}


llm_service = LLMService()
