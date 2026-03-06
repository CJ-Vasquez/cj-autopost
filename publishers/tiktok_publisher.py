"""Publisher de TikTok — CJ_Dev4.20 AutoPost."""

from __future__ import annotations

import time

import httpx
import structlog

from config.settings import get_settings
from core.models import PublishContent, PublishResult
from publishers.base_publisher import BasePublisher, PublishError

logger = structlog.get_logger(__name__)

TIKTOK_API_BASE = "https://open.tiktokapis.com/v2"


class TikTokPublisher(BasePublisher):
    """Publica videos en TikTok usando Content Posting API v2."""

    platform_name = "tiktok"

    def __init__(self) -> None:
        self._settings = get_settings()
        self._token = self._settings.tiktok_access_token

    def validate_credentials(self) -> bool:
        """Verifica el access token de TikTok."""
        if not self._token:
            return False
        try:
            resp = httpx.get(
                f"{TIKTOK_API_BASE}/user/info/",
                headers=self._headers(),
                params={"fields": "display_name"},
                timeout=10,
            )
            return resp.status_code == 200
        except httpx.HTTPError:
            return False

    def _do_publish(self, content: PublishContent) -> PublishResult:
        """Publica video en TikTok."""
        if not content.video_path or not content.video_path.exists():
            raise PublishError("No se encontró el video para TikTok")

        # 1. Inicializar upload
        caption = self._build_caption(content)
        file_size = content.video_path.stat().st_size

        init_data = {
            "post_info": {
                "title": caption[:2200],
                "privacy_level": "PUBLIC_TO_EVERYONE",
            },
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": file_size,
                "chunk_size": file_size,
                "total_chunk_count": 1,
            },
        }

        init_resp = httpx.post(
            f"{TIKTOK_API_BASE}/post/publish/video/init/",
            headers=self._headers(),
            json=init_data,
            timeout=30,
        )

        if init_resp.status_code != 200:
            error_data = init_resp.json()
            error_code = error_data.get("error", {}).get("code", "")
            if error_code == "spam_risk_too_many_posts":
                logger.warning("TikTok spam risk, esperando 1 hora")
                time.sleep(3600)
                raise PublishError("spam_risk_too_many_posts — reintentar")
            raise PublishError(f"TikTok init error: {init_resp.text}")

        resp_data = init_resp.json().get("data", {})
        publish_id = resp_data.get("publish_id", "")
        upload_url = resp_data.get("upload_url", "")

        # 2. Subir video
        with open(content.video_path, "rb") as f:
            upload_resp = httpx.put(
                upload_url,
                content=f.read(),
                headers={
                    "Content-Type": "video/mp4",
                    "Content-Range": f"bytes 0-{file_size - 1}/{file_size}",
                },
                timeout=120,
            )

        if upload_resp.status_code not in (200, 201):
            raise PublishError(f"TikTok upload error: {upload_resp.text}")

        return PublishResult(
            platform="tiktok",
            success=True,
            url=f"https://www.tiktok.com/@{self._settings.channel_name}",
        )

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }

    @staticmethod
    def _build_caption(content: PublishContent) -> str:
        """Construye caption con hashtags (máx. 2200 chars)."""
        parts = [content.topic.titulo, content.topic.descripcion]
        hashtags = " ".join(content.hashtags[:10])
        caption = " | ".join(parts) + "\n\n" + hashtags
        return caption[:2200]
