"""Small, single-process scheduler. Each market pipeline keeps its own worker later."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, time
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

from stockbot.config import Settings, get_settings
from stockbot.services.tse_ingestion import run_once

if TYPE_CHECKING:
    import asyncpg

LOGGER = logging.getLogger(__name__)


def is_tse_window(now: datetime, settings: Settings) -> bool:
    """Only the configured Tehran time window is eligible; days remain provider-configurable."""
    start = time.fromisoformat(settings.tse_start_time)
    end = time.fromisoformat(settings.tse_end_time)
    return now.weekday() in settings.tse_weekdays and start <= now.timetz().replace(tzinfo=None) <= end


async def serve() -> None:
    import asyncpg

    settings = get_settings()
    if not settings.tse_schedule_enabled:
        LOGGER.warning("TSE scheduler is disabled by configuration")
        return

    timezone = ZoneInfo(settings.tse_timezone)
    pool = await asyncpg.create_pool(str(settings.database_url), min_size=1, max_size=2)
    try:
        last_slot: datetime | None = None
        while True:
            now = datetime.now(timezone)
            slot = now.replace(second=0, microsecond=0)
            if is_tse_window(now, settings) and slot != last_slot:
                last_slot = slot
                try:
                    count = await run_once(pool, settings)
                    LOGGER.info("TSE ingestion completed: %s snapshots", count)
                except Exception:
                    LOGGER.exception("TSE ingestion failed; the worker will retry next interval")
            await asyncio.sleep(settings.tse_poll_seconds)
    finally:
        await pool.close()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    asyncio.run(serve())


if __name__ == "__main__":
    main()
