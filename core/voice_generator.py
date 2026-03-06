"""Generador de voz con gTTS — CJ_Dev4.20 AutoPost."""

from __future__ import annotations

from pathlib import Path

import structlog
from gtts import gTTS

from config.settings import BASE_DIR
from core.models import TopicData

logger = structlog.get_logger(__name__)

OUTPUT_DIR = BASE_DIR / "output" / "videos"


class VoiceGenerator:
    """Genera narración en español usando gTTS."""

    def generate(self, topic: TopicData, output_path: Path | None = None) -> Path:
        """Genera archivo de audio MP3 con la narración del tema."""
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        if output_path is None:
            output_path = OUTPUT_DIR / f"audio_{topic.id}.mp3"

        script = self._build_script(topic)
        logger.info("Generando narración", topic=topic.titulo, chars=len(script))

        tts = gTTS(text=script, lang="es", slow=False)
        tts.save(str(output_path))

        logger.info("Audio generado", path=str(output_path))
        return output_path

    @staticmethod
    def _build_script(topic: TopicData) -> str:
        """Construye el script de narración."""
        return (
            f"Hoy aprenderemos sobre {topic.titulo}. "
            f"{topic.descripcion}. "
            f"Veamos un ejemplo en {topic.lenguaje}."
        )
