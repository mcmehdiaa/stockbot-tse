from datetime import UTC, datetime, timedelta
from uuid import uuid4

from stockbot.domain import Channel, SubscriptionStatus, UserAccess
from stockbot.notifications.routing import delivery_order


def test_expired_user_cannot_receive() -> None:
    access = UserAccess(uuid4(), SubscriptionStatus.ACTIVE, datetime.now(UTC) - timedelta(seconds=1), frozenset({Channel.TELEGRAM}))
    assert not access.can_receive(datetime.now(UTC))


def test_telegram_is_prioritized_before_bale() -> None:
    access = UserAccess(uuid4(), SubscriptionStatus.ACTIVE, None, frozenset({Channel.TELEGRAM, Channel.BALE}))
    assert delivery_order(access) == (Channel.TELEGRAM, Channel.BALE)
