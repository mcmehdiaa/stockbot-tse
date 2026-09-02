from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from stockbot.domain import Channel, SubscriptionStatus, UserAccess

if TYPE_CHECKING:
    import asyncpg


class AccessRepository:
    """PostgreSQL-backed access decisions; chat platforms are never authoritative."""

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def request_access(self, channel: Channel, chat_id: str, display_name: str | None = None) -> UUID:
        """Create a pending request, without reactivating a revoked subscription."""
        async with self._pool.acquire() as connection, connection.transaction():
            user_id = await connection.fetchval(
                "SELECT user_id FROM user_channels WHERE channel = $1 AND chat_id = $2",
                channel.value,
                chat_id,
            )
            if user_id is None:
                user_id = await connection.fetchval(
                    "INSERT INTO users (display_name) VALUES ($1) RETURNING id", display_name
                )
                await connection.execute(
                    "INSERT INTO user_channels (user_id, channel, chat_id) VALUES ($1, $2, $3)",
                    user_id,
                    channel.value,
                    chat_id,
                )
            await connection.execute(
                "INSERT INTO subscriptions (user_id) VALUES ($1) ON CONFLICT (user_id) DO NOTHING", user_id
            )
            return user_id

    async def approve(self, user_id: UUID, admin_identity: str, expires_at: datetime | None) -> bool:
        result = await self._pool.execute(
            """
            UPDATE subscriptions
            SET status = 'active', approved_by = $2, approved_at = now(),
                expires_at = $3, revoked_at = NULL, revoke_reason = NULL, updated_at = now()
            WHERE user_id = $1 AND status IN ('pending', 'expired', 'revoked')
            """,
            user_id,
            admin_identity,
            expires_at,
        )
        return result == "UPDATE 1"

    async def revoke(self, user_id: UUID, reason: str | None = None) -> bool:
        result = await self._pool.execute(
            """
            UPDATE subscriptions
            SET status = 'revoked', revoked_at = now(), revoke_reason = $2, updated_at = now()
            WHERE user_id = $1 AND status <> 'revoked'
            """,
            user_id,
            reason,
        )
        return result == "UPDATE 1"

    async def access_for(self, channel: Channel, chat_id: str) -> UserAccess | None:
        row = await self._pool.fetchrow(
            """
            SELECT s.user_id, s.status, s.expires_at,
                   array_agg(uc.channel::text) AS channels
            FROM user_channels requested
            JOIN subscriptions s ON s.user_id = requested.user_id
            JOIN user_channels uc ON uc.user_id = requested.user_id
            WHERE requested.channel = $1 AND requested.chat_id = $2
            GROUP BY s.user_id, s.status, s.expires_at
            """,
            channel.value,
            chat_id,
        )
        if row is None:
            return None
        return UserAccess(
            user_id=row["user_id"],
            status=SubscriptionStatus(row["status"]),
            expires_at=row["expires_at"],
            channels=frozenset(Channel(name) for name in row["channels"]),
        )
