"""Publisher de Facebook — CJ_Dev4.20 AutoPost."""

from __future__ import annotations

import httpx
import structlog

from config.settings import get_settings
from core.models import PublishContent, PublishResult
from publishers.base_publisher import BasePublisher, PublishError

logger = structlog.get_logger(__name__)

GRAPH_API_BASE = "https://graph.facebook.com/v19.0"


class FacebookPublisher(BasePublisher):
    """Publica contenido en una Facebook Page usando Graph API."""

    platform_name = "facebook"

    def __init__(self) -> None:
        self._settings = get_settings()
        self._token = self._settings.facebook_access_token
        self._page_id = self._settings.facebook_page_id

    def validate_credentials(self) -> bool:
        """Verifica el token de la página de Facebook."""
        if not self._token or not self._page_id:
            return False
        try:
            resp = httpx.get(
                f"{GRAPH_API_BASE}/{self._page_id}",
                params={"access_token": self._token, "fields": "id,name"},
                timeout=10,
            )
            return resp.status_code == 200
        except httpx.HTTPError:
            return False

    def _do_publish(self, content: PublishContent) -> PublishResult:
        """Publica video o imagen en la Facebook Page."""
        if content.video_path and content.video_path.exists():
            return self._publish_video(content)
        elif content.image_path and content.image_path.exists():
            return self._publish_image(content)
        else:
            raise PublishError("No se encontró contenido para Facebook")

    def _publish_video(self, content: PublishContent) -> PublishResult:
        """Sube video a la página."""
        caption = self._build_caption(content)

        with open(content.video_path, "rb") as video_file:
            resp = httpx.post(
                f"{GRAPH_API_BASE}/{self._page_id}/videos",
                data={
                    "description": caption,
                    "access_token": self._token,
                },
                files={"source": ("video.mp4", video_file, "video/mp4")},
                timeout=120,
            )

        if resp.status_code != 200:
            raise PublishError(f"Facebook video error: {resp.text}")

        video_id = resp.json().get("id", "")
        url = f"https://www.facebook.com/{self._page_id}/videos/{video_id}"

        return PublishResult(platform="facebook", success=True, url=url)

    def _publish_image(self, content: PublishContent) -> PublishResult:
        """Sube imagen a la página."""
        caption = self._build_caption(content)

        with open(content.image_path, "rb") as img_file:
            resp = httpx.post(
                f"{GRAPH_API_BASE}/{self._page_id}/photos",
                data={
                    "message": caption,
                    "published": "true",
                    "access_token": self._token,
                },
                files={"source": ("image.png", img_file, "image/png")},
                timeout=60,
            )

        if resp.status_code != 200:
            raise PublishError(f"Facebook image error: {resp.text}")

        post_id = resp.json().get("id", "")
        url = f"https://www.facebook.com/{self._page_id}/posts/{post_id}"

        return PublishResult(platform="facebook", success=True, url=url)

    @staticmethod
    def _build_caption(content: PublishContent) -> str:
        """Construye caption con hashtags."""
        parts = [content.topic.titulo, "", content.topic.descripcion]
        hashtags = " ".join(content.hashtags[:20])
        return "\n".join(parts) + "\n\n" + hashtags
