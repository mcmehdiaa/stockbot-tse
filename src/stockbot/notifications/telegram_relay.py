from __future__ import annotations

from typing import Any

import httpx


class TelegramRelayError(RuntimeError):
    pass


class TelegramRelay:
    """The server knows only the relay URL and shared secret, never the Telegram token."""

    def __init__(self, url: str, secret: str) -> None:
        self._url = url
        self._secret = secret

    async def invoke(self, method: str, params: dict[str, Any]) -> Any:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                self._url,
                headers={"authorization": f"Bearer {self._secret}"},
                json={"method": method, "params": params},
            )
        try:
            body = response.json()
        except ValueError as error:
            raise TelegramRelayError("relay returned invalid JSON") from error
        if not response.is_success or not body.get("ok"):
            raise TelegramRelayError(str(body.get("error", f"relay HTTP {response.status_code}")))
        return body.get("result")

    async def send_message(self, chat_id: str, text: str) -> Any:
        return await self.invoke("sendMessage", {"chat_id": chat_id, "text": text})

    async def get_updates(self, offset: int, timeout: int) -> list[dict[str, Any]]:
        result = await self.invoke("getUpdates", {"offset": offset, "timeout": timeout})
        return result if isinstance(result, list) else []
