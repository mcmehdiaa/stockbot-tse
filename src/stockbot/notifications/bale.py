from __future__ import annotations

from typing import Any

import httpx


class BaleApiError(RuntimeError):
    pass


class BaleBot:
    """Direct Bale adapter; it deliberately shares no state or token with Telegram."""

    def __init__(self, base_url: str, token: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._token = token

    async def invoke(self, method: str, params: dict[str, Any]) -> Any:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{self._base_url}/bot{self._token}/{method}", json=params)
        body = response.json()
        if not response.is_success or not body.get("ok"):
            raise BaleApiError(str(body.get("description", f"Bale HTTP {response.status_code}")))
        return body.get("result")

    async def send_message(self, chat_id: str, text: str) -> Any:
        return await self.invoke("sendMessage", {"chat_id": chat_id, "text": text})

    async def get_updates(self, offset: int, timeout: int) -> list[dict[str, Any]]:
        result = await self.invoke("getUpdates", {"offset": offset, "timeout": timeout})
        return result if isinstance(result, list) else []
