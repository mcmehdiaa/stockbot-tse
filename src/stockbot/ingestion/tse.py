from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from stockbot.ingestion.http import JsonTransport


@dataclass(frozen=True)
class MarketSnapshot:
    provider: str
    symbol: str
    observed_at: datetime
    raw: dict[str, Any]


class TsetmcJsonSource:
    """Fetches the user-verified TSETMC JSON endpoint without embedding an endpoint."""

    def __init__(self, transport: JsonTransport, market_watch_url: str) -> None:
        self._transport = transport
        self._url = market_watch_url

    async def fetch(self) -> list[MarketSnapshot]:
        payload = await self._transport.get_json(self._url)
        return normalize_tsetmc_payload(payload, observed_at=datetime.now(UTC))


def normalize_tsetmc_payload(payload: Any, *, observed_at: datetime) -> list[MarketSnapshot]:
    """Normalizes common TSETMC list envelopes while retaining original provider data.

    The raw object is persisted unchanged; mappings can safely be refined once the
    exact endpoint response from the production server is supplied.
    """
    rows = _rows(payload)
    snapshots: list[MarketSnapshot] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        symbol = _first_text(row, "symbol", "lVal18AFC", "lVal30", "instrumentCode")
        if symbol:
            snapshots.append(MarketSnapshot("tsetmc", symbol, observed_at, row))
    return snapshots


def _rows(payload: Any) -> list[Any]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("data", "items", "instrumentList", "marketWatch"):
            if isinstance(payload.get(key), list):
                return payload[key]
    return []


def _first_text(row: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None
