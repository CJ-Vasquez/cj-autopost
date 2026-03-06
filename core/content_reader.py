"""Lector de contenido desde Google Sheets — CJ_Dev4.20 AutoPost."""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

import gspread
import structlog
from google.oauth2.service_account import Credentials

from config.settings import get_settings
from core.models import TopicData

logger = structlog.get_logger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# Mapeo de columnas (0-indexed)
COL = {
    "id": 0,
    "fecha_programada": 1,
    "titulo": 2,
    "descripcion": 3,
    "codigo": 4,
    "lenguaje": 5,
    "color_hex": 6,
    "icono": 7,
    "hashtags_extra": 8,
    "estado": 9,
    "url_tiktok": 10,
    "url_instagram": 11,
    "url_youtube": 12,
    "url_facebook": 13,
    "error_log": 14,
    "fecha_publicacion": 15,
}


class ContentReader:
    """Lee y actualiza temas desde Google Sheets."""

    def __init__(self) -> None:
        settings = get_settings()
        creds = Credentials.from_service_account_file(
            str(settings.service_account_path), scopes=SCOPES
        )
        self._client = gspread.authorize(creds)
        self._sheet = self._client.open_by_key(settings.google_sheet_id).sheet1
        logger.info("Google Sheets conectado", sheet_id=settings.google_sheet_id)

    def get_today_topic(self) -> Optional[TopicData]:
        """Busca el primer tema pendiente con fecha <= hoy o sin fecha."""
        logger.info("Buscando tema del día")
        rows = self._sheet.get_all_values()

        if len(rows) <= 1:
            logger.info("Sheet vacía o solo tiene encabezados")
            return None

        today = date.today()

        for row in rows[1:]:  # Skip header
            if len(row) <= COL["estado"]:
                continue

            estado = row[COL["estado"]].strip().lower()
            if estado != "pendiente":
                continue

            fecha_str = row[COL["fecha_programada"]].strip()
            if fecha_str:
                try:
                    fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
                    if fecha > today:
                        continue
                except ValueError:
                    logger.warning("Fecha inválida", fecha=fecha_str, id=row[COL["id"]])

            topic = self._row_to_topic(row)
            logger.info("Tema encontrado", id=topic.id, titulo=topic.titulo)
            return topic

        logger.info("No hay temas pendientes")
        return None

    def mark_as_published(self, topic_id: str, urls: dict[str, str]) -> None:
        """Marca un tema como publicado y registra las URLs."""
        cell = self._sheet.find(topic_id, in_column=1)
        if not cell:
            logger.error("No se encontró el tema", id=topic_id)
            return

        row = cell.row
        updates = {
            COL["estado"] + 1: "publicado",
            COL["url_tiktok"] + 1: urls.get("tiktok", ""),
            COL["url_instagram"] + 1: urls.get("instagram", ""),
            COL["url_youtube"] + 1: urls.get("youtube", ""),
            COL["url_facebook"] + 1: urls.get("facebook", ""),
            COL["fecha_publicacion"] + 1: datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        for col, value in updates.items():
            self._sheet.update_cell(row, col, value)

        logger.info("Tema marcado como publicado", id=topic_id)

    def mark_as_error(self, topic_id: str, error: str) -> None:
        """Marca un tema como error y registra el mensaje."""
        cell = self._sheet.find(topic_id, in_column=1)
        if not cell:
            logger.error("No se encontró el tema para marcar error", id=topic_id)
            return

        row = cell.row
        self._sheet.update_cell(row, COL["estado"] + 1, "error")
        self._sheet.update_cell(row, COL["error_log"] + 1, error[:500])
        logger.info("Tema marcado como error", id=topic_id)

    def get_pending_count(self) -> int:
        """Retorna cuántos temas quedan pendientes."""
        rows = self._sheet.get_all_values()
        count = sum(
            1 for row in rows[1:]
            if len(row) > COL["estado"] and row[COL["estado"]].strip().lower() == "pendiente"
        )
        logger.info("Temas pendientes", count=count)
        return count

    @staticmethod
    def _row_to_topic(row: list[str]) -> TopicData:
        """Convierte una fila del Sheet a TopicData."""
        hashtags_raw = row[COL["hashtags_extra"]].strip() if len(row) > COL["hashtags_extra"] else ""
        hashtags = [h.strip() for h in hashtags_raw.split(",") if h.strip()] if hashtags_raw else []

        fecha_str = row[COL["fecha_programada"]].strip()
        fecha = None
        if fecha_str:
            try:
                fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
            except ValueError:
                pass

        return TopicData(
            id=row[COL["id"]].strip(),
            titulo=row[COL["titulo"]].strip(),
            descripcion=row[COL["descripcion"]].strip(),
            codigo=row[COL["codigo"]].strip(),
            lenguaje=row[COL["lenguaje"]].strip() or "python",
            color_hex=row[COL["color_hex"]].strip() or "#6C63FF",
            icono=row[COL["icono"]].strip() or "💻",
            hashtags_extra=hashtags,
            fecha_programada=fecha,
        )
