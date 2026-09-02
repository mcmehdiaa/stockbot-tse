from __future__ import annotations

import json
from typing import TYPE_CHECKING

from stockbot.config import Settings
from stockbot.ingestion.http import JsonTransport
from stockbot.ingestion.tse import MarketSnapshot, TsetmcJsonSource

if TYPE_CHECKING:
    import asyncpg


async def run_once(pool: asyncpg.Pool, settings: Settings) -> int:
    """Run only the TSE ingestion path; crypto and forex are never touched here."""
    if settings.tse_market_watch_url is None:
        raise RuntimeError("TSE_MARKET_WATCH_URL is not configured")

    async with pool.acquire() as connection:
        run_id = await connection.fetchval(
            "INSERT INTO pipeline_runs (pipeline, status) VALUES ('tse', 'started') RETURNING id"
        )

    try:
        transport = JsonTransport(requests_per_minute=settings.tse_requests_per_minute)
        snapshots = await TsetmcJsonSource(transport, str(settings.tse_market_watch_url)).fetch()
        await _store_success(pool, run_id, snapshots)
        return len(snapshots)
    except Exception as error:
        await _store_failure(pool, run_id, error)
        raise


async def _store_success(pool: asyncpg.Pool, run_id: object, snapshots: list[MarketSnapshot]) -> None:
    async with pool.acquire() as connection, connection.transaction():
        if snapshots:
            await connection.executemany(
                """
                INSERT INTO market_snapshots (provider, symbol, observed_at, payload)
                VALUES ($1, $2, $3, $4::jsonb)
                ON CONFLICT (provider, symbol, observed_at) DO NOTHING
                """,
                [(item.provider, item.symbol, item.observed_at, json.dumps(item.raw, ensure_ascii=False)) for item in snapshots],
            )
        await connection.execute(
            """
            UPDATE pipeline_runs
            SET status = 'succeeded', finished_at = now(), item_count = $2
            WHERE id = $1
            """,
            run_id,
            len(snapshots),
        )


async def _store_failure(pool: asyncpg.Pool, run_id: object, error: Exception) -> None:
    async with pool.acquire() as connection:
        await connection.execute(
            """
            UPDATE pipeline_runs
            SET status = 'failed', finished_at = now(), error_code = $2, error_detail = $3
            WHERE id = $1
            """,
            run_id,
            type(error).__name__,
            str(error)[:1000],
        )
