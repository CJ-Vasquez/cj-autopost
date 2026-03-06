"""Generador de video con MoviePy — CJ_Dev4.20 AutoPost."""

from __future__ import annotations

from pathlib import Path

import structlog
from moviepy.editor import (
    AudioFileClip,
    CompositeVideoClip,
    ImageClip,
    TextClip,
    ColorClip,
    concatenate_videoclips,
)

from config.settings import BASE_DIR, get_settings, load_platform_config
from core.models import TopicData

logger = structlog.get_logger(__name__)

OUTPUT_DIR = BASE_DIR / "output" / "videos"


class VideoGenerator:
    """Ensambla video final combinando imágenes, audio y transiciones."""

    def generate(
        self,
        images: list[Path],
        audio: Path,
        topic: TopicData,
        platform: str,
    ) -> Path:
        """Genera video final optimizado para la plataforma indicada."""
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        output_path = OUTPUT_DIR / f"video_{platform}_{topic.id}.mp4"

        logger.info("Generando video", platform=platform, topic=topic.titulo)

        config = load_platform_config()
        p_cfg = config.get("platforms", {}).get(platform, {})
        resolution = tuple(p_cfg.get("resolution", [1080, 1920]))
        max_duration = p_cfg.get("max_duration_seconds", 60)

        audio_clip = AudioFileClip(str(audio))
        audio_duration = audio_clip.duration

        clips = self._build_clip_sequence(images, audio_duration, resolution)
        final = concatenate_videoclips(clips, method="compose")

        # Limitar duración
        if final.duration > max_duration:
            final = final.subclip(0, max_duration)

        # Overlay de título
        final = self._add_title_overlay(final, topic.titulo, resolution)

        # Barra de progreso
        final = self._add_progress_bar(final, resolution)

        # Watermark
        final = self._add_watermark(final, resolution)

        # Audio
        final = final.set_audio(audio_clip)
        if final.duration > audio_clip.duration + 2:
            final = final.subclip(0, audio_clip.duration + 2)

        final.write_videofile(
            str(output_path),
            fps=30,
            codec="libx264",
            audio_codec="aac",
            preset="medium",
            threads=4,
            logger=None,
        )

        audio_clip.close()
        final.close()
        for c in clips:
            c.close()

        logger.info("Video generado", path=str(output_path))
        return output_path

    def _build_clip_sequence(
        self, images: list[Path], audio_duration: float, resolution: tuple[int, int]
    ) -> list[ImageClip]:
        """Construye la secuencia de clips de imagen."""
        clips = []
        w, h = resolution

        if not images:
            logger.warning("No hay imágenes, creando placeholder")
            placeholder = ColorClip(size=(w, h), color=(15, 15, 25))
            return [placeholder.set_duration(audio_duration + 2)]

        # Distribuir tiempo entre las imágenes disponibles
        total_time = audio_duration + 2
        time_per_image = total_time / len(images)

        for img_path in images:
            clip = (
                ImageClip(str(img_path))
                .set_duration(time_per_image)
                .resize(resolution)
                .crossfadein(0.3)
            )
            clips.append(clip)

        return clips

    def _add_title_overlay(
        self, clip: CompositeVideoClip, title: str, resolution: tuple[int, int]
    ) -> CompositeVideoClip:
        """Agrega título en la parte superior con fade."""
        w, h = resolution
        try:
            txt = (
                TextClip(
                    title,
                    fontsize=int(36 * (min(w, h) / 1080)),
                    color="white",
                    font="Arial",
                    stroke_color="black",
                    stroke_width=2,
                )
                .set_position(("center", int(30 * (h / 1920))))
                .set_duration(clip.duration)
                .crossfadein(0.5)
                .crossfadeout(0.5)
            )
            return CompositeVideoClip([clip, txt])
        except Exception as e:
            logger.warning("No se pudo agregar título overlay", error=str(e))
            return clip

    def _add_progress_bar(
        self, clip: CompositeVideoClip, resolution: tuple[int, int]
    ) -> CompositeVideoClip:
        """Agrega barra de progreso animada en la parte inferior."""
        w, h = resolution
        bar_height = int(4 * (h / 1920))

        def make_frame(t: float):
            """Genera frame de la barra de progreso."""
            import numpy as np
            progress = t / clip.duration if clip.duration > 0 else 0
            bar = np.zeros((bar_height, w, 3), dtype=np.uint8)
            fill_width = int(w * progress)
            bar[:, :fill_width] = [108, 99, 255]  # Violeta
            return bar

        try:
            bar_clip = (
                ColorClip(size=(w, bar_height), color=(108, 99, 255))
                .set_duration(clip.duration)
                .set_position(("left", h - bar_height))
            )
            # Usar lambda para animar el ancho
            from moviepy.video.VideoClip import VideoClip
            progress_bar = (
                VideoClip(make_frame, duration=clip.duration)
                .set_position(("left", h - bar_height))
            )
            return CompositeVideoClip([clip, progress_bar])
        except Exception as e:
            logger.warning("No se pudo agregar barra de progreso", error=str(e))
            return clip

    def _add_watermark(
        self, clip: CompositeVideoClip, resolution: tuple[int, int]
    ) -> CompositeVideoClip:
        """Agrega @CJ_Dev4.20 semi-transparente en esquina superior."""
        w, h = resolution
        settings = get_settings()
        try:
            wm = (
                TextClip(
                    f"@{settings.channel_name}",
                    fontsize=int(20 * (min(w, h) / 1080)),
                    color="white",
                    font="Arial",
                )
                .set_opacity(0.4)
                .set_position((w - int(200 * (w / 1080)), int(20 * (h / 1920))))
                .set_duration(clip.duration)
            )
            return CompositeVideoClip([clip, wm])
        except Exception as e:
            logger.warning("No se pudo agregar watermark", error=str(e))
            return clip
