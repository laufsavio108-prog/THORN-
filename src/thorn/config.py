"""Configuração do THORN. Tudo resolve de env vars (prefixo THORN_) ou defaults."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="THORN_", env_file=".env", extra="ignore")

    home: Path = Field(default_factory=lambda: Path.home() / ".thorn")
    model: str = "claude-opus-5"
    embedder: str = "hashing"

    # A key é lida do ambiente padrão da Anthropic, SEM prefixo THORN_.
    # Deixamos aqui só para o gateway checar presença sem importar a SDK.
    anthropic_api_key: str | None = Field(default=None, alias="ANTHROPIC_API_KEY")

    @property
    def db_path(self) -> Path:
        return self.home.expanduser() / "thorn.db"

    @property
    def ai_enabled(self) -> bool:
        return bool(self.anthropic_api_key)


def load_settings() -> Settings:
    s = Settings()
    s.home.expanduser().mkdir(parents=True, exist_ok=True)
    return s
