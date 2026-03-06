"""Tests para el lector de Google Sheets."""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, PropertyMock
from datetime import date

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.models import TopicData


MOCK_HEADER = [
    "ID", "Fecha_Programada", "Titulo", "Descripcion",
    "Codigo", "Lenguaje", "Color_Hex", "Icono",
    "Hashtags_Extra", "Estado", "URL_TikTok",
    "URL_Instagram", "URL_YouTube", "URL_Facebook",
    "Error_Log", "Fecha_Publicacion"
]

MOCK_ROW_PENDING = [
    "001", "2025-03-06", "Variables", "Aprende variables",
    "x = 10", "python", "#6C63FF", "📦",
    "#vars,#basics", "pendiente", "", "", "", "", "", ""
]

MOCK_ROW_PUBLISHED = [
    "002", "2025-03-05", "Ciclos", "Aprende ciclos",
    "for i in range(10): pass", "python", "#0ea5e9", "🔄",
    "", "publicado", "url1", "url2", "url3", "url4", "", "2025-03-05"
]


class TestContentReader:
    @patch("core.content_reader.gspread")
    @patch("core.content_reader.Credentials")
    def test_reads_pending_topic_correctly(self, mock_creds, mock_gspread):
        mock_sheet = MagicMock()
        mock_sheet.get_all_values.return_value = [MOCK_HEADER, MOCK_ROW_PENDING]
        mock_gspread.authorize.return_value.open_by_key.return_value.sheet1 = mock_sheet

        from core.content_reader import ContentReader
        reader = ContentReader()
        topic = reader.get_today_topic()

        assert topic is not None
        assert topic.id == "001"
        assert topic.titulo == "Variables"
        assert topic.lenguaje == "python"

    @patch("core.content_reader.gspread")
    @patch("core.content_reader.Credentials")
    def test_returns_none_when_no_pending(self, mock_creds, mock_gspread):
        mock_sheet = MagicMock()
        mock_sheet.get_all_values.return_value = [MOCK_HEADER, MOCK_ROW_PUBLISHED]
        mock_gspread.authorize.return_value.open_by_key.return_value.sheet1 = mock_sheet

        from core.content_reader import ContentReader
        reader = ContentReader()
        topic = reader.get_today_topic()

        assert topic is None

    @patch("core.content_reader.gspread")
    @patch("core.content_reader.Credentials")
    def test_handles_empty_sheet_gracefully(self, mock_creds, mock_gspread):
        mock_sheet = MagicMock()
        mock_sheet.get_all_values.return_value = [MOCK_HEADER]
        mock_gspread.authorize.return_value.open_by_key.return_value.sheet1 = mock_sheet

        from core.content_reader import ContentReader
        reader = ContentReader()
        topic = reader.get_today_topic()

        assert topic is None

    @patch("core.content_reader.gspread")
    @patch("core.content_reader.Credentials")
    def test_marks_as_published_updates_sheet(self, mock_creds, mock_gspread):
        mock_sheet = MagicMock()
        mock_cell = MagicMock()
        mock_cell.row = 2
        mock_sheet.find.return_value = mock_cell
        mock_gspread.authorize.return_value.open_by_key.return_value.sheet1 = mock_sheet

        from core.content_reader import ContentReader
        reader = ContentReader()
        reader.mark_as_published("001", {"tiktok": "http://tiktok.com/v1"})

        assert mock_sheet.update_cell.called
