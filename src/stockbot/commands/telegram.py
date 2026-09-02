from __future__ import annotations

from datetime import datetime, time
from uuid import UUID
from zoneinfo import ZoneInfo

from stockbot.access import AccessRepository
from stockbot.commands.parser import Command, parse_command
from stockbot.config import Settings
from stockbot.domain import Channel


async def handle_telegram_command(
    repository: AccessRepository,
    settings: Settings,
    chat_id: str,
    display_name: str | None,
    text: str | None,
) -> dict[str, str]:
    """Returns recipient/message pairs; transport is intentionally outside this layer."""
    command = parse_command(text)
    if command is None:
        return {chat_id: "دستور نامعتبر است. از /start یا /status استفاده کنید."}
    if command.name == "start":
        return await _request_access(repository, settings, chat_id, display_name)
    if command.name == "status":
        return await _status(repository, chat_id)
    if command.name == "approve":
        return await _approve(repository, settings, chat_id, command)
    if command.name == "revoke":
        return await _revoke(repository, settings, chat_id, command)
    return {chat_id: "دستور شناخته نشد. /start یا /status"}


async def _request_access(repository: AccessRepository, settings: Settings, chat_id: str, display_name: str | None) -> dict[str, str]:
    user_id = await repository.request_access(Channel.TELEGRAM, chat_id, display_name)
    result = {chat_id: "درخواست شما ثبت شد و پس از تأیید مدیر فعال می‌شود."}
    for admin_id in settings.telegram_admin_ids:
        result[str(admin_id)] = f"درخواست جدید Telegram: {display_name or '-'}\nشناسه کاربر: {user_id}\nتأیید: /approve {user_id} YYYY-MM-DD\nلغو: /revoke {user_id}"
    return result


async def _status(repository: AccessRepository, chat_id: str) -> dict[str, str]:
    access = await repository.access_for(Channel.TELEGRAM, chat_id)
    if access is None:
        return {chat_id: "درخواستی ثبت نشده است. /start را بزنید."}
    expiry = access.expires_at.isoformat() if access.expires_at else "بدون تاریخ انقضا"
    return {chat_id: f"وضعیت: {access.status.value}\nانقضا: {expiry}"}


async def _approve(repository: AccessRepository, settings: Settings, chat_id: str, command: Command) -> dict[str, str]:
    if not _is_admin(settings, chat_id):
        return {chat_id: "اجازه این دستور را ندارید."}
    if not command.arguments:
        return {chat_id: "فرمت: /approve USER_UUID [YYYY-MM-DD]"}
    try:
        user_id = UUID(command.arguments[0])
        expires_at = _expiry(command.arguments[1], settings.tse_timezone) if len(command.arguments) > 1 else None
    except (ValueError, IndexError):
        return {chat_id: "شناسه یا تاریخ نامعتبر است."}
    approved = await repository.approve(user_id, f"telegram:{chat_id}", expires_at)
    return {chat_id: "دسترسی فعال شد." if approved else "کاربر قابل تأیید نیست یا وجود ندارد."}


async def _revoke(repository: AccessRepository, settings: Settings, chat_id: str, command: Command) -> dict[str, str]:
    if not _is_admin(settings, chat_id):
        return {chat_id: "اجازه این دستور را ندارید."}
    try:
        user_id = UUID(command.arguments[0])
    except (IndexError, ValueError):
        return {chat_id: "فرمت: /revoke USER_UUID"}
    revoked = await repository.revoke(user_id, "admin_revoked")
    return {chat_id: "دسترسی فوراً لغو شد." if revoked else "کاربر قابل لغو نیست یا وجود ندارد."}


def _is_admin(settings: Settings, chat_id: str) -> bool:
    return chat_id.isdigit() and int(chat_id) in settings.telegram_admin_ids


def _expiry(value: str, timezone: str) -> datetime:
    date = datetime.fromisoformat(value).date()
    return datetime.combine(date, time.max, ZoneInfo(timezone))
