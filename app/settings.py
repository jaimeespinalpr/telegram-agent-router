from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_secret_key: str = Field(default="change-me")
    admin_username: str = Field(default="admin")
    admin_password: str = Field(default="change-me")

    telegram_api_id: int | None = None
    telegram_api_hash: str | None = None
    telegram_session_path: str = ".sessions/router"

    agents_config_path: str = "config/agents.yaml"
    router_agent_id: str = "router"


@lru_cache
def get_settings() -> Settings:
    return Settings()

