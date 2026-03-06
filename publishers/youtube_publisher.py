"""Publisher de YouTube — CJ_Dev4.20 AutoPost."""

from __future__ import annotations

from pathlib import Path

import structlog
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from config.settings import get_settings, load_platform_config
from core.models import PublishContent, PublishResult
from publishers.base_publisher import BasePublisher, PublishError

logger = structlog.get_logger(__name__)


class YouTubePublisher(BasePublisher):
    """Publica videos en YouTube usando Data API v3."""

    platform_name = "youtube"

    def __init__(self) -> None:
        self._settings = get_settings()

    def validate_credentials(self) -> bool:
        """Verifica las credenciales de YouTube."""
        try:
            service = self._get_service()
            resp = service.channels().list(part="snippet", mine=True).execute()
            return len(resp.get("items", [])) > 0
        except Exception:
            return False

    def _do_publish(self, content: PublishContent) -> PublishResult:
        """Publica video en YouTube."""
        if not content.video_path or not content.video_path.exists():
            raise PublishError("No se encontró el video para YouTube")

        service = self._get_service()
        config = load_platform_config()
        yt_cfg = config.get("platforms", {}).get("youtube", {})

        body = {
            "snippet": {
                "title": content.topic.titulo[:100],
                "description": self._build_description(content),
                "tags": [h.lstrip("#") for h in content.hashtags[:30]],
                "categoryId": yt_cfg.get("category_id", "28"),
            },
            "status": {
                "privacyStatus": yt_cfg.get("privacy", "public"),
                "selfDeclaredMadeForKids": False,
            },
        }

        media = MediaFileUpload(
            str(content.video_path),
            mimetype="video/mp4",
            resumable=True,
            chunksize=1024 * 1024 * 5,
        )

        request = service.videos().insert(part="snippet,status", body=body, media_body=media)

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                logger.info("YouTube upload progress", progress=f"{int(status.progress() * 100)}%")

        video_id = response.get("id", "")
        url = f"https://www.youtube.com/watch?v={video_id}"

        # Subir thumbnail si hay imagen disponible
        if content.image_path and content.image_path.exists():
            self._set_thumbnail(service, video_id, content.image_path)

        logger.info("Video publicado en YouTube", url=url)
        return PublishResult(platform="youtube", success=True, url=url)

    def _set_thumbnail(self, service: object, video_id: str, image_path: Path) -> None:
        """Sube thumbnail personalizado."""
        try:
            media = MediaFileUpload(str(image_path), mimetype="image/png")
            service.thumbnails().set(videoId=video_id, media_body=media).execute()  # type: ignore
            logger.info("Thumbnail establecido", video_id=video_id)
        except Exception as e:
            logger.warning("No se pudo establecer thumbnail", error=str(e))

    def _get_service(self) -> object:
        """Construye el servicio de YouTube API."""
        creds = Credentials(
            token=None,
            refresh_token=self._settings.youtube_refresh_token,
            client_id=self._settings.youtube_client_id,
            client_secret=self._settings.youtube_client_secret,
            token_uri="https://oauth2.googleapis.com/token",
        )
        return build("youtube", "v3", credentials=creds)

    @staticmethod
    def _build_description(content: PublishContent) -> str:
        """Construye descripción para YouTube."""
        lines = [
            content.topic.titulo,
            "",
            content.topic.descripcion,
            "",
            "---",
            f"Canal: @CJ_Dev4.20",
            "",
            " ".join(f"#{h.lstrip('#')}" for h in content.hashtags[:15]),
        ]
        return "\n".join(lines)[:5000]
