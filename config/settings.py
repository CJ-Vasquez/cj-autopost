"""Configuración centralizada del sistema CJ_Dev4.20 AutoPost."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import field_validator
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent


class ConfigurationError(Exception):
    """Error de configuración del sistema."""


class Settings(BaseSettings):
    """Configuración principal cargada desde .env."""

    # Google
    google_service_account_json: str = "./credentials/google_service_account.json"
    google_sheet_id: str = "TU_SHEET_ID_AQUI"
    google_drive_folder_id: str = "TU_FOLDER_ID_AQUI"

    # TikTok
    tiktok_client_key: str = ""
    tiktok_client_secret: str = ""
    tiktok_access_token: str = ""

    # Instagram / Facebook
    instagram_access_token: str = ""
    instagram_business_account_id: str = ""
    facebook_page_id: str = ""
    facebook_access_token: str = ""

    # YouTube
    youtube_client_id: str = ""
    youtube_client_secret: str = ""
    youtube_refresh_token: str = ""

    # Telegram
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    # App
    channel_name: str = "CJ_Dev4.20"
    output_dir: str = "./output"
    logs_dir: str = "./logs"
    log_level: str = "INFO"
    dry_run: bool = False

    model_config = {"env_file": str(BASE_DIR / ".env"), "env_file_encoding": "utf-8"}

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in allowed:
            raise ValueError(f"LOG_LEVEL debe ser uno de {allowed}")
        return v.upper()

    @property
    def output_path(self) -> Path:
        return BASE_DIR / self.output_dir

    @property
    def logs_path(self) -> Path:
        return BASE_DIR / self.logs_dir

    @property
    def service_account_path(self) -> Path:
        return BASE_DIR / self.google_service_account_json

    def validate_required_for_platform(self, platform: str) -> list[str]:
        """Retorna lista de variables faltantes para una plataforma."""
        checks: dict[str, list[str]] = {
            "tiktok": ["tiktok_client_key", "tiktok_client_secret", "tiktok_access_token"],
            "instagram": ["instagram_access_token", "instagram_business_account_id"],
            "youtube": ["youtube_client_id", "youtube_client_secret", "youtube_refresh_token"],
            "facebook": ["facebook_page_id", "facebook_access_token"],
            "google": ["google_sheet_id", "google_drive_folder_id"],
            "telegram": ["telegram_bot_token", "telegram_chat_id"],
        }
        fields = checks.get(platform, [])
        missing = []
        for field in fields:
            value = getattr(self, field, "")
            if not value or value.startswith("TU_"):
                missing.append(field.upper())
        return missing

    def validate_all_tokens(self) -> dict[str, list[str]]:
        """Valida credenciales de todas las plataformas. Retorna dict de errores."""
        errors: dict[str, list[str]] = {}
        for platform in ["google", "tiktok", "instagram", "youtube", "facebook", "telegram"]:
            missing = self.validate_required_for_platform(platform)
            if missing:
                errors[platform] = missing
        return errors


def load_platform_config() -> dict[str, Any]:
    """Carga la configuración de plataformas desde platforms.yaml."""
    config_path = BASE_DIR / "config" / "platforms.yaml"
    if not config_path.exists():
        raise ConfigurationError(f"No se encontró {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@lru_cache
def get_settings() -> Settings:
    """Retorna singleton de Settings."""
    return Settings()


def get_enabled_platforms() -> list[str]:
    """Retorna lista de plataformas habilitadas en platforms.yaml."""
    config = load_platform_config()
    platforms = config.get("platforms", {})
    return [name for name, cfg in platforms.items() if cfg.get("enabled", False)]
