"""Notificador por Telegram — CJ_Dev4.20 AutoPost."""

from __future__ import annotations

from datetime import datetime

import httpx
import structlog

from config.settings import get_settings
from core.models import TopicData

logger = structlog.get_logger(__name__)

TELEGRAM_API = "https://api.telegram.org"


class TelegramNotifier:
    """Envía notificaciones formateadas por Telegram."""

    def __init__(self) -> None:
        settings = get_settings()
        self._token = settings.telegram_bot_token
        self._chat_id = settings.telegram_chat_id
        self._enabled = bool(self._token and self._chat_id)

    def notify_success(
        self, topic: TopicData, urls: dict[str, str], duration_s: float
    ) -> None:
        """Envía notificación de publicación exitosa."""
        if not self._enabled:
            logger.info("Telegram no configurado, omitiendo notificación")
            return

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        url_lines = []
        platform_icons = {
            "tiktok": "🎵 TikTok",
            "instagram": "📸 Instagram",
            "youtube": "▶️ YouTube",
            "facebook": "👤 Facebook",
        }
        for platform, url in urls.items():
            icon = platform_icons.get(platform, platform)
            url_lines.append(f"{icon}: {url}")

        message = (
            f"✅ *Publicación completada — CJ_Dev4.20*\n"
            f"📅 {now}\n"
            f"📚 Tema: {topic.titulo}\n"
            f"⏱️ Tiempo total: {duration_s:.1f}s\n\n"
            + "\n".join(url_lines)
        )

        self._send(message)

    def notify_error(self, topic: TopicData, error: Exception, stage: str) -> None:
        """Envía notificación de error."""
        if not self._enabled:
            return

        message = (
            f"❌ *ERROR en {stage} — CJ_Dev4.20*\n"
            f"📚 Tema: {topic.titulo}\n"
            f"💬 Error: {str(error)[:300]}\n"
            f"🔧 Acción: Revisar columna Error\\_Log en Google Sheets"
        )

        self._send(message)

    def notify_low_content(self, days_remaining: int) -> None:
        """Envía alerta de contenido bajo."""
        if not self._enabled:
            return

        message = (
            f"⚠️ *Alerta de contenido bajo — CJ_Dev4.20*\n\n"
            f"Solo quedan *{days_remaining}* días de contenido\\.\n"
            f"Agrega más temas al Google Sheets\\."
        )

        self._send(message)

    def _send(self, text: str) -> None:
        """Envía mensaje por Telegram Bot API."""
        try:
            resp = httpx.post(
                f"{TELEGRAM_API}/bot{self._token}/sendMessage",
                json={
                    "chat_id": self._chat_id,
                    "text": text,
                    "parse_mode": "Markdown",
                },
                timeout=10,
            )
            if resp.status_code != 200:
                logger.warning("Telegram send error", status=resp.status_code, body=resp.text)
            else:
                logger.info("Notificación Telegram enviada")
        except httpx.HTTPError as e:
            logger.error("Error enviando notificación Telegram", error=str(e))
