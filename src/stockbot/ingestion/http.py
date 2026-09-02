import asyncio
import random
from collections.abc import Mapping
from dataclasses import dataclass
from time import monotonic
from typing import Any

import httpx


class UpstreamUnavailable(RuntimeError):
    """Raised after transient provider failures have exhausted their retry budget."""


@dataclass
class JsonTransport:
    """Small, bounded JSON client for all providers.

    It retries only network errors and 429/5xx responses. Any other 4xx response
    is a configuration or request error and is deliberately not retried.
    """

    requests_per_minute: int
    timeout_seconds: float = 12.0
    attempts: int = 3

    def __post_init__(self) -> None:
        self._lock = asyncio.Lock()
        self._next_request_at = 0.0

    async def get_json(self, url: str, *, params: Mapping[str, str] | None = None) -> Any:
        last_error: Exception | None = None
        async with httpx.AsyncClient(timeout=self.timeout_seconds, follow_redirects=False) as client:
            for attempt in range(self.attempts):
                await self._wait_turn()
                try:
                    response = await client.get(url, params=params, headers={"accept": "application/json"})
                    if response.status_code == 429 or response.status_code >= 500:
                        raise httpx.HTTPStatusError("retryable provider response", request=response.request, response=response)
                    response.raise_for_status()
                    return response.json()
                except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError) as error:
                    last_error = error
                    if attempt + 1 < self.attempts:
                        await asyncio.sleep((2**attempt) + random.uniform(0, 0.25))
        raise UpstreamUnavailable(f"provider unavailable after {self.attempts} attempts") from last_error

    async def _wait_turn(self) -> None:
        interval = 60.0 / self.requests_per_minute
        async with self._lock:
            now = monotonic()
            wait = max(0.0, self._next_request_at - now)
            self._next_request_at = max(now, self._next_request_at) + interval
        if wait:
            await asyncio.sleep(wait)
