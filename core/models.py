"""Modelos de datos del sistema CJ_Dev4.20 AutoPost."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Optional

from pydantic import BaseModel


class TopicData(BaseModel):
    """Datos de un tema a publicar."""

    id: str
    titulo: str
    descripcion: str
    codigo: str
    lenguaje: str = "python"
    color_hex: str = "#6C63FF"
    icono: str = "💻"
    hashtags_extra: list[str] = []
    fecha_programada: Optional[date] = None


class PlatformConfig(BaseModel):
    """Configuración de una plataforma."""

    name: str
    enabled: bool = True
    format: str = "9:16"
    resolution: list[int] = [1080, 1920]
    max_duration_seconds: int = 60
    hashtags_limit: int = 10


class PublishContent(BaseModel):
    """Contenido listo para publicar."""

    topic: TopicData
    image_path: Optional[Path] = None
    video_path: Optional[Path] = None
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    caption: str = ""
    hashtags: list[str] = []


class PublishResult(BaseModel):
    """Resultado de una publicación."""

    platform: str
    success: bool
    url: str = ""
    error: str = ""
