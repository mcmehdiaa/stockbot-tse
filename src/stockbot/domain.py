from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class Channel(StrEnum):
    TELEGRAM = "telegram"
    BALE = "bale"


class SubscriptionStatus(StrEnum):
    PENDING = "pending"
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"


class PipelineName(StrEnum):
    TSE = "tse"
    CRYPTO = "crypto"
    FOREX = "forex"


@dataclass(frozen=True)
class UserAccess:
    user_id: UUID
    status: SubscriptionStatus
    expires_at: datetime | None
    channels: frozenset[Channel]

    def can_receive(self, now: datetime) -> bool:
        return self.status is SubscriptionStatus.ACTIVE and (self.expires_at is None or self.expires_at > now)
