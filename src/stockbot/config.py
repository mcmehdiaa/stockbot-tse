from functools import lru_cache

from pydantic import AnyHttpUrl, Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Only configuration; secrets are read from the host environment."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: str = "production"
    database_url: PostgresDsn
    admin_telegram_ids: str = ""
    admin_bale_ids: str = ""
    telegram_relay_url: AnyHttpUrl
    telegram_relay_secret: str = Field(min_length=24)
    bale_bot_token: str = Field(min_length=20)
    bale_api_base_url: AnyHttpUrl = "https://tapi.bale.ai"
    bale_poll_enabled: bool = False
    bale_poll_timeout_seconds: int = Field(default=20, ge=0, le=50)
    tse_timezone: str = "Asia/Tehran"
    max_active_users: int = Field(default=100, ge=1, le=100)
    tse_market_watch_url: AnyHttpUrl | None = None
    codal_disclosures_url: AnyHttpUrl | None = None
    tse_requests_per_minute: int = Field(default=30, ge=1, le=120)
    tse_schedule_enabled: bool = False
    tse_start_time: str = "09:00"
    tse_end_time: str = "12:30"
    tse_poll_seconds: int = Field(default=300, ge=60, le=3600)
    tse_active_weekdays: str = "0,1,2,5,6"
    telegram_poll_enabled: bool = False
    telegram_poll_timeout_seconds: int = Field(default=10, ge=0, le=10)

    @property
    def telegram_admin_ids(self) -> frozenset[int]:
        return _ids(self.admin_telegram_ids)

    @property
    def bale_admin_ids(self) -> frozenset[int]:
        return _ids(self.admin_bale_ids)

    @property
    def tse_weekdays(self) -> frozenset[int]:
        values = frozenset(int(item.strip()) for item in self.tse_active_weekdays.split(",") if item.strip())
        if not values or any(value not in range(7) for value in values):
            raise ValueError("TSE_ACTIVE_WEEKDAYS must contain Python weekdays 0 through 6")
        return values


def _ids(value: str) -> frozenset[int]:
    return frozenset(int(item.strip()) for item in value.split(",") if item.strip())


@lru_cache
def get_settings() -> Settings:
    return Settings()
