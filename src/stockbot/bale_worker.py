from __future__ import annotations

import asyncio
import logging
from typing import Any

import asyncpg

from stockbot.access import AccessRepository
from stockbot.commands.bale import handle_bale_command
from stockbot.config import get_settings
from stockbot.notifications.bale import BaleBot

LOGGER = logging.getLogger(__name__)
CURSOR_NAME = "bale_update_offset"


async def serve() -> None:
    settings = get_settings()
    if not settings.bale_poll_enabled:
        LOGGER.warning("Bale polling is disabled by configuration")
        return
    pool = await asyncpg.create_pool(str(settings.database_url), min_size=1, max_size=3)
    bot = BaleBot(str(settings.bale_api_base_url), settings.bale_bot_token)
    repository = AccessRepository(pool)
    try:
        offset = await _load_cursor(pool)
        while True:
            try:
                for update in await bot.get_updates(offset, settings.bale_poll_timeout_seconds):
                    offset = await _handle_update(pool, repository, settings, bot, update, offset)
            except Exception:
                LOGGER.exception("Bale polling failed; retrying")
                await asyncio.sleep(5)
    finally:
        await pool.close()


async def _handle_update(pool: asyncpg.Pool, repository: AccessRepository, settings: Any, bot: BaleBot, update: dict[str, Any], offset: int) -> int:
    update_id, message = update.get("update_id"), update.get("message")
    if not isinstance(update_id, int) or not isinstance(message, dict):
        return offset
    chat, sender = message.get("chat"), message.get("from")
    if not isinstance(chat, dict) or not isinstance(sender, dict) or chat.get("id") is None:
        return offset
    chat_id = str(chat["id"])
    name = " ".join(filter(None, (sender.get("first_name"), sender.get("last_name")))) or None
    for recipient, text in (await handle_bale_command(repository, settings, chat_id, name, message.get("text"))).items():
        await bot.send_message(recipient, text)
    next_offset = update_id + 1
    await _save_cursor(pool, next_offset)
    return next_offset


async def _load_cursor(pool: asyncpg.Pool) -> int:
    return int(await pool.fetchval("SELECT cursor_value FROM service_cursors WHERE name = $1", CURSOR_NAME) or 0)


async def _save_cursor(pool: asyncpg.Pool, value: int) -> None:
    await pool.execute("INSERT INTO service_cursors (name, cursor_value) VALUES ($1, $2) ON CONFLICT (name) DO UPDATE SET cursor_value = EXCLUDED.cursor_value, updated_at = now()", CURSOR_NAME, value)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    asyncio.run(serve())


if __name__ == "__main__":
    main()
