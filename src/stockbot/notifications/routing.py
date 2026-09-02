from stockbot.domain import Channel, UserAccess


def delivery_order(access: UserAccess) -> tuple[Channel, ...]:
    """Telegram is tried first; Bale is a fallback only for identities the user linked."""
    return tuple(channel for channel in (Channel.TELEGRAM, Channel.BALE) if channel in access.channels)
