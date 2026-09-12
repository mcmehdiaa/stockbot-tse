from __future__ import annotations

from typing import Any


class TelegramRelayNotifier:
    """Small notifier that sends messages through the Vercel Telegram relay."""

    def __init__(self, http: Any, relay_url: str, relay_secret: str, chat_id: str) -> None:
        self.http = http
        self.relay_url = relay_url
        self.relay_secret = relay_secret
        self.chat_id = chat_id

    async def send_text(self, text: str, *, chat_id: str | None = None) -> bool:
        response = await self.http.request(
            "POST",
            self.relay_url,
            headers={"Authorization": f"Bearer {self.relay_secret}"},
            json={
                "method": "sendMessage",
                "params": {"chat_id": chat_id or self.chat_id, "text": text[:4096]},
            },
        )
        return bool(response.json().get("ok"))
