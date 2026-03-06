"""Publisher de Instagram — CJ_Dev4.20 AutoPost."""

from __future__ import annotations

import time

import httpx
import structlog

from config.settings import get_settings
from core.models import PublishContent, PublishResult
from publishers.base_publisher import BasePublisher, PublishError

logger = structlog.get_logger(__name__)

GRAPH_API_BASE = "https://graph.facebook.com/v19.0"


class InstagramPublisher(BasePublisher):
    """Publica imágenes en Instagram usando Graph API."""

    platform_name = "instagram"

    def __init__(self) -> None:
        self._settings = get_settings()
        self._token = self._settings.instagram_access_token
        self._account_id = self._settings.instagram_business_account_id

    def validate_credentials(self) -> bool:
        """Verifica el access token de Instagram."""
        if not self._token or not self._account_id:
            return False
        try:
            resp = httpx.get(
                f"{GRAPH_API_BASE}/{self._account_id}",
                params={"access_token": self._token, "fields": "id,username"},
                timeout=10,
            )
            return resp.status_code == 200
        except httpx.HTTPError:
            return False

    def _do_publish(self, content: PublishContent) -> PublishResult:
        """Publica imagen en Instagram."""
        if not content.image_path or not content.image_path.exists():
            raise PublishError("No se encontró la imagen para Instagram")

        caption = self._build_caption(content)

        # 1. Crear media container
        # Instagram requiere URL pública — usar la URL de Drive
        if not content.image_url:
            raise PublishError(
                "Instagram requiere una URL publica para la imagen. "
                "Asegurate de que el upload a Google Drive se complete antes de publicar."
            )
        image_url = content.image_url

        create_resp = httpx.post(
            f"{GRAPH_API_BASE}/{self._account_id}/media",
            data={
                "image_url": image_url,
                "caption": caption,
                "access_token": self._token,
            },
            timeout=30,
        )

        if create_resp.status_code != 200:
            raise PublishError(f"Instagram create error: {create_resp.text}")

        creation_id = create_resp.json().get("id")
        if not creation_id:
            raise PublishError("Instagram: no se recibió creation_id")

        # 2. Esperar procesamiento
        time.sleep(5)

        # 3. Publicar
        publish_resp = httpx.post(
            f"{GRAPH_API_BASE}/{self._account_id}/media_publish",
            data={
                "creation_id": creation_id,
                "access_token": self._token,
            },
            timeout=30,
        )

        if publish_resp.status_code != 200:
            raise PublishError(f"Instagram publish error: {publish_resp.text}")

        media_id = publish_resp.json().get("id", "")
        url = f"https://www.instagram.com/p/{media_id}/"

        return PublishResult(platform="instagram", success=True, url=url)

    @staticmethod
    def _build_caption(content: PublishContent) -> str:
        """Construye caption con hashtags (máx. 30 hashtags)."""
        parts = [content.topic.titulo, "", content.topic.descripcion]
        hashtags = content.hashtags[:30]
        caption = "\n".join(parts) + "\n\n" + " ".join(hashtags)
        return caption[:2200]
