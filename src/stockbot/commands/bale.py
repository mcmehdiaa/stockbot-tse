from __future__ import annotations

from datetime import datetime, time
from uuid import UUID
from zoneinfo import ZoneInfo

from stockbot.access import AccessRepository
from stockbot.commands.parser import Command, parse_command
from stockbot.config import Settings
from stockbot.domain import Channel


async def handle_bale_command(repository: AccessRepository, settings: Settings, chat_id: str, display_name: str | None, text: str | None) -> dict[str, str]:
    command = parse_command(text)
    if command is None:
        return {chat_id: "دستور نامعتبر است. از /start یا /status استفاده کنید."}
    if command.name == "start":
        user_id = await repository.request_access(Channel.BALE, chat_id, display_name)
        replies = {chat_id: "درخواست شما ثبت شد و پس از تأیید مدیر فعال می‌شود."}
        for admin_id in settings.bale_admin_ids:
            replies[str(admin_id)] = f"درخواست جدید Bale: {display_name or '-'}\nشناسه کاربر: {user_id}\nتأیید: /approve {user_id} YYYY-MM-DD\nلغو: /revoke {user_id}"
        return replies
    if command.name == "status":
        access = await repository.access_for(Channel.BALE, chat_id)
        if access is None:
            return {chat_id: "درخواستی ثبت نشده است. /start را بزنید."}
        expiry = access.expires_at.isoformat() if access.expires_at else "بدون تاریخ انقضا"
        return {chat_id: f"وضعیت: {access.status.value}\nانقضا: {expiry}"}
    if command.name == "approve":
        return await _approve(repository, settings, chat_id, command)
    if command.name == "revoke":
        return await _revoke(repository, settings, chat_id, command)
    return {chat_id: "دستور شناخته نشد. /start یا /status"}


async def _approve(repository: AccessRepository, settings: Settings, chat_id: str, command: Command) -> dict[str, str]:
    if not _admin(settings, chat_id):
        return {chat_id: "اجازه این دستور را ندارید."}
    try:
        user_id = UUID(command.arguments[0])
        expiry = _expiry(command.arguments[1], settings.tse_timezone) if len(command.arguments) > 1 else None
    except (IndexError, ValueError):
        return {chat_id: "فرمت: /approve USER_UUID [YYYY-MM-DD]"}
    return {chat_id: "دسترسی فعال شد." if await repository.approve(user_id, f"bale:{chat_id}", expiry) else "کاربر قابل تأیید نیست یا وجود ندارد."}


async def _revoke(repository: AccessRepository, settings: Settings, chat_id: str, command: Command) -> dict[str, str]:
    if not _admin(settings, chat_id):
        return {chat_id: "اجازه این دستور را ندارید."}
    try:
        user_id = UUID(command.arguments[0])
    except (IndexError, ValueError):
        return {chat_id: "فرمت: /revoke USER_UUID"}
    return {chat_id: "دسترسی فوراً لغو شد." if await repository.revoke(user_id, "admin_revoked") else "کاربر قابل لغو نیست یا وجود ندارد."}


def _admin(settings: Settings, chat_id: str) -> bool:
    return chat_id.isdigit() and int(chat_id) in settings.bale_admin_ids


def _expiry(value: str, timezone: str) -> datetime:
    return datetime.combine(datetime.fromisoformat(value).date(), time.max, ZoneInfo(timezone))
