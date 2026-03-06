"""Uploader a Google Drive — CJ_Dev4.20 AutoPost."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import structlog
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from config.settings import get_settings
from core.models import TopicData

logger = structlog.get_logger(__name__)

SCOPES = ["https://www.googleapis.com/auth/drive"]

MIME_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".mp4": "video/mp4",
    ".mp3": "audio/mpeg",
}


class DriveUploader:
    """Sube archivos a Google Drive con estructura organizada."""

    def __init__(self) -> None:
        settings = get_settings()
        creds = Credentials.from_service_account_file(
            str(settings.service_account_path), scopes=SCOPES
        )
        self._service = build("drive", "v3", credentials=creds)
        self._root_folder_id = settings.google_drive_folder_id
        self._folder_cache: dict[str, str] = {}

    def upload_batch(self, topic: TopicData, files: dict[str, Path]) -> dict[str, str]:
        """Sube todos los archivos a una carpeta organizada en Drive."""
        now = datetime.now()
        folder_path = (
            f"CJ_Dev4.20/{now.year}/"
            f"{now.strftime('%B')}/{now.strftime('%d')}-{topic.titulo.upper()}"
        )

        folder_id = self._get_or_create_folder(folder_path)
        results: dict[str, str] = {}

        for filename, file_path in files.items():
            if not file_path.exists():
                logger.warning("Archivo no encontrado, omitiendo", file=str(file_path))
                continue

            logger.info("Subiendo a Drive", file=filename)
            url = self._upload_file(folder_id, file_path, filename)
            results[filename] = url
            logger.info("Archivo subido", file=filename, url=url)

        return results

    def _upload_file(self, folder_id: str, file_path: Path, filename: str) -> str:
        """Sube un archivo individual a la carpeta indicada."""
        mime_type = MIME_TYPES.get(file_path.suffix.lower(), "application/octet-stream")

        file_metadata = {
            "name": filename,
            "parents": [folder_id],
        }

        media = MediaFileUpload(str(file_path), mimetype=mime_type, resumable=True)

        file = (
            self._service.files()
            .create(body=file_metadata, media_body=media, fields="id,webViewLink")
            .execute()
        )

        return file.get("webViewLink", f"https://drive.google.com/file/d/{file.get('id')}")

    def _get_or_create_folder(self, path: str) -> str:
        """Crea la jerarquía de carpetas si no existe. Usa caché."""
        if path in self._folder_cache:
            return self._folder_cache[path]

        parts = path.strip("/").split("/")
        parent_id = self._root_folder_id

        current_path = ""
        for part in parts:
            current_path = f"{current_path}/{part}" if current_path else part

            if current_path in self._folder_cache:
                parent_id = self._folder_cache[current_path]
                continue

            folder_id = self._find_folder(parent_id, part)
            if not folder_id:
                folder_id = self._create_folder(parent_id, part)

            self._folder_cache[current_path] = folder_id
            parent_id = folder_id

        return parent_id

    def _find_folder(self, parent_id: str, name: str) -> str | None:
        """Busca una carpeta por nombre dentro de un parent."""
        query = (
            f"name='{name}' and '{parent_id}' in parents "
            f"and mimeType='application/vnd.google-apps.folder' and trashed=false"
        )
        results = self._service.files().list(q=query, fields="files(id)").execute()
        files = results.get("files", [])
        return files[0]["id"] if files else None

    def _create_folder(self, parent_id: str, name: str) -> str:
        """Crea una carpeta en Drive."""
        metadata = {
            "name": name,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [parent_id],
        }
        folder = self._service.files().create(body=metadata, fields="id").execute()
        logger.info("Carpeta creada en Drive", name=name)
        return folder["id"]
