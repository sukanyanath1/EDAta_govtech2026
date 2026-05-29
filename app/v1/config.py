"""Application configuration loaded from environment / .env file."""

from __future__ import annotations

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── OpenAI ────────────────────────────────────────────────────────────────
    openai_api_key: SecretStr
    openai_model: str

    # ── Azure Data Lake Storage Gen2 ──────────────────────────────────────────
    # e.g. https://<account>.dfs.core.windows.net
    storage_account_url: str
    adls_filesystem: str

    # Provide ONE of the three auth options below (SAS token takes priority).
    adls_sas_token: str | None = None
    adls_account_key: str | None = None
    adls_connection_string: str | None = None

    # ── WTO Timeseries API ────────────────────────────────────────────────────
    wto_subscription_key: SecretStr | None = None


settings = Settings()
