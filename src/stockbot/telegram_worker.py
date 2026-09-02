from __future__ import annotations

import asyncio
import logging
from typing import Any

import asyncpg

from stockbot.access import AccessRepository
from stockbot.commands.telegram import handle_telegram_command
from stockbot.config import get_settings
from stockbot.notifications.telegram_relay import TelegramRelay

LOGGER = logging.getLogger(__name__)
CURSOR_NAME = "telegram_update_offset"


async def serve() -> None:
    settings = get_settings()
    if not settings.telegram_poll_enabled:
        LOGGER.warning("Telegram polling is disabled by configuration")
        return
    pool = await asyncpg.create_pool(str(settings.database_url), min_size=1, max_size=3)
    relay = TelegramRelay(str(settings.telegram_relay_url), settings.telegram_relay_secret)
    repository = AccessRepository(pool)
    try:
        offset = await _load_cursor(pool)
        while True:
            try:
                updates = await relay.get_updates(offset, settings.telegram_poll_timeout_seconds)
                for update in updates:
                    offset = await _handle_update(pool, repository, settings, relay, update, offset)
            except Exception:
                LOGGER.exception("Telegram polling failed; retrying")
                await asyncio.sleep(5)
    finally:
        await pool.close()


async def _handle_update(pool: asyncpg.Pool, repository: AccessRepository, settings: Any, relay: TelegramRelay, update: dict[str, Any], offset: int) -> int:
    update_id = update.get("update_id")
    message = update.get("message")
    if not isinstance(update_id, int) or not isinstance(message, dict):
        return offset
    chat = message.get("chat")
    sender = message.get("from")
    if not isinstance(chat, dict) or not isinstance(sender, dict):
        return offset
    chat_id = str(chat.get("id", ""))
    if not chat_id:
        return offset
    display_name = " ".join(filter(None, (sender.get("first_name"), sender.get("last_name")))) or None
    replies = await handle_telegram_command(repository, settings, chat_id, display_name, message.get("text"))
    for recipient, text in replies.items():
        await relay.send_message(recipient, text)
    next_offset = update_id + 1
    await _save_cursor(pool, next_offset)
    return next_offset


async def _load_cursor(pool: asyncpg.Pool) -> int:
    value = await pool.fetchval("SELECT cursor_value FROM service_cursors WHERE name = $1", CURSOR_NAME)
    return int(value or 0)


async def _save_cursor(pool: asyncpg.Pool, value: int) -> None:
    await pool.execute(
        """
        INSERT INTO service_cursors (name, cursor_value) VALUES ($1, $2)
        ON CONFLICT (name) DO UPDATE SET cursor_value = EXCLUDED.cursor_value, updated_at = now()
        """,
        CURSOR_NAME,
        value,
    )


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    asyncio.run(serve())


if __name__ == "__main__":
    main()
