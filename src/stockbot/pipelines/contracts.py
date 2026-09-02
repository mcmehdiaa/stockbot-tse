from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from stockbot.domain import PipelineName


@dataclass(frozen=True)
class Signal:
    pipeline: PipelineName
    symbol: str
    score: float
    message: str
    observed_at: datetime


class Pipeline(Protocol):
    name: PipelineName

    async def run(self, observed_at: datetime) -> list[Signal]:
        """Fetch, validate, analyse, and return only deliverable signals."""
