"""Generador de imágenes para todas las plataformas — CJ_Dev4.20 AutoPost."""

from __future__ import annotations

import math
import textwrap
from io import BytesIO
from pathlib import Path
from typing import Any

import requests
import structlog
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from pygments import highlight
from pygments.formatters import ImageFormatter
from pygments.lexers import get_lexer_by_name, PythonLexer
from pygments.token import Token

from config.settings import get_settings, load_platform_config, BASE_DIR
from core.models import TopicData, PlatformConfig

logger = structlog.get_logger(__name__)

FONTS_DIR = BASE_DIR / "assets" / "fonts"
OUTPUT_DIR = BASE_DIR / "output" / "images"

FONT_URLS = {
    "Montserrat-Black.ttf": "https://raw.githubusercontent.com/JulietaUla/Montserrat/master/fonts/ttf/Montserrat-Black.ttf",
    "FiraCode-Regular.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/firacode/FiraCode%5Bwght%5D.ttf",
    "Inter-Regular.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/inter/Inter%5Bopsz%2Cwght%5D.ttf",
}

# Colores del tema Dracula para syntax highlighting
DRACULA_COLORS = {
    Token.Keyword: "#ff79c6",
    Token.Keyword.Namespace: "#ff79c6",
    Token.Name.Function: "#50fa7b",
    Token.Name.Class: "#8be9fd",
    Token.Name.Builtin: "#8be9fd",
    Token.Literal.String: "#f1fa8c",
    Token.Literal.String.Doc: "#6272a4",
    Token.Literal.Number: "#bd93f9",
    Token.Comment: "#6272a4",
    Token.Operator: "#ff79c6",
    Token.Punctuation: "#f8f8f2",
    Token.Name: "#f8f8f2",
    Token.Text: "#f8f8f2",
}

MAC_DOTS = [("#FF5F56", ), ("#FFBD2E", ), ("#27C93F", )]


class ImageGenerator:
    """Genera imágenes estilizadas para cada plataforma."""

    def __init__(self) -> None:
        self._download_fonts()
        self._title_font: ImageFont.FreeTypeFont | None = None
        self._code_font: ImageFont.FreeTypeFont | None = None
        self._text_font: ImageFont.FreeTypeFont | None = None

    def _download_fonts(self) -> None:
        """Descarga fuentes si no existen localmente."""
        FONTS_DIR.mkdir(parents=True, exist_ok=True)
        for filename, url in FONT_URLS.items():
            font_path = FONTS_DIR / filename
            if not font_path.exists():
                logger.info("Descargando fuente", font=filename)
                try:
                    resp = requests.get(url, timeout=30)
                    resp.raise_for_status()
                    font_path.write_bytes(resp.content)
                    logger.info("Fuente descargada", font=filename)
                except Exception as e:
                    logger.warning("No se pudo descargar fuente", font=filename, error=str(e))

    def _get_font(self, name: str, size: int) -> ImageFont.FreeTypeFont:
        """Carga una fuente por nombre y tamaño."""
        font_path = FONTS_DIR / name
        try:
            return ImageFont.truetype(str(font_path), size)
        except OSError:
            logger.warning("Fuente no encontrada, usando default", font=name)
            return ImageFont.load_default()

    def generate_all_formats(self, topic: TopicData) -> dict[str, Path]:
        """Genera imágenes para todas las plataformas habilitadas."""
        config = load_platform_config()
        platforms = config.get("platforms", {})
        results: dict[str, Path] = {}

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        for platform_name, platform_cfg in platforms.items():
            if not platform_cfg.get("enabled", False):
                continue
            p_config = PlatformConfig(
                name=platform_name,
                resolution=platform_cfg["resolution"],
                format=platform_cfg.get("format", "9:16"),
            )
            logger.info("Generando imagen", platform=platform_name)
            img = self._generate_card(topic, p_config)
            output_path = OUTPUT_DIR / f"{platform_name}_{topic.id}.png"
            img.save(str(output_path), "PNG", quality=95)
            results[platform_name] = output_path
            logger.info("Imagen guardada", path=str(output_path))

        return results

    def _generate_card(self, topic: TopicData, config: PlatformConfig) -> Image.Image:
        """Genera una tarjeta visual completa para una plataforma."""
        w, h = config.resolution
        img = Image.new("RGBA", (w, h), (0, 0, 0, 255))

        # Fondo con gradiente radial
        img = self._draw_radial_gradient(img, topic.color_hex)

        draw = ImageDraw.Draw(img)

        # Escalar tamaños de fuente según resolución
        scale = min(w, h) / 1080
        title_size = int(48 * scale)
        desc_size = int(24 * scale)
        code_size = int(20 * scale)
        footer_size = int(18 * scale)
        padding = int(40 * scale)

        title_font = self._get_font("Montserrat-Black.ttf", title_size)
        text_font = self._get_font("Inter-Regular.ttf", desc_size)
        code_font = self._get_font("FiraCode-Regular.ttf", code_size)
        footer_font = self._get_font("Inter-Regular.ttf", footer_size)

        y_cursor = padding

        # Línea neon superior
        neon_color = self._hex_to_rgb(topic.color_hex)
        draw.rectangle([0, 0, w, int(4 * scale)], fill=neon_color)

        y_cursor += int(20 * scale)

        # Icono + Título
        title_text = f"{topic.icono}  {topic.titulo}"
        wrapped_title = textwrap.fill(title_text, width=int(30 * (w / 1080)))
        # Text shadow
        draw.multiline_text(
            (padding + 2, y_cursor + 2), wrapped_title,
            font=title_font, fill=(0, 0, 0, 180)
        )
        draw.multiline_text(
            (padding, y_cursor), wrapped_title,
            font=title_font, fill=(255, 255, 255, 255)
        )
        title_bbox = draw.multiline_textbbox((padding, y_cursor), wrapped_title, font=title_font)
        y_cursor = title_bbox[3] + int(20 * scale)

        # Descripción
        wrapped_desc = textwrap.fill(topic.descripcion, width=int(45 * (w / 1080)))
        draw.multiline_text(
            (padding, y_cursor), wrapped_desc,
            font=text_font, fill=(200, 200, 200, 255)
        )
        desc_bbox = draw.multiline_textbbox((padding, y_cursor), wrapped_desc, font=text_font)
        y_cursor = desc_bbox[3] + int(30 * scale)

        # Panel de código (glassmorphism)
        code_block = self._render_code_block(topic.codigo, topic.lenguaje, w, code_font, scale)
        code_panel_x = padding
        code_panel_y = y_cursor

        # Fondo glassmorphism del panel de código
        panel_w = w - 2 * padding
        panel_h = code_block.height + int(60 * scale)

        # Limitar el panel para que no se salga de la imagen
        max_panel_h = h - y_cursor - int(80 * scale)
        if panel_h > max_panel_h:
            panel_h = max_panel_h

        glass_panel = Image.new("RGBA", (panel_w, panel_h), (30, 30, 46, 200))
        glass_draw = ImageDraw.Draw(glass_panel)

        # Borde neon
        border_color = (*neon_color, 150)
        glass_draw.rectangle(
            [0, 0, panel_w - 1, panel_h - 1],
            outline=border_color, width=2
        )

        # Dots de macOS
        dot_y = int(15 * scale)
        dot_radius = int(6 * scale)
        dot_spacing = int(22 * scale)
        dot_colors = ["#FF5F56", "#FFBD2E", "#27C93F"]
        for i, color in enumerate(dot_colors):
            cx = int(20 * scale) + i * dot_spacing
            glass_draw.ellipse(
                [cx - dot_radius, dot_y - dot_radius, cx + dot_radius, dot_y + dot_radius],
                fill=self._hex_to_rgb(color)
            )

        # Pegar code block dentro del panel
        code_y_in_panel = int(40 * scale)
        if code_block.height <= panel_h - code_y_in_panel:
            glass_panel.paste(code_block, (int(15 * scale), code_y_in_panel), code_block)
        else:
            cropped = code_block.crop((0, 0, code_block.width, panel_h - code_y_in_panel))
            glass_panel.paste(cropped, (int(15 * scale), code_y_in_panel), cropped)

        img.paste(glass_panel, (code_panel_x, code_panel_y), glass_panel)
        y_cursor = code_panel_y + panel_h + int(20 * scale)

        # Footer — hashtags + handle
        content_config = load_platform_config().get("content", {})
        hashtags = content_config.get("hashtags_base", [])[:5]
        hashtags_text = " ".join(hashtags)
        draw.text(
            (padding, h - int(60 * scale)),
            hashtags_text, font=footer_font,
            fill=(150, 150, 150, 255)
        )

        # Handle @CJ_Dev4.20
        handle = f"@{get_settings().channel_name}"
        handle_bbox = draw.textbbox((0, 0), handle, font=footer_font)
        handle_w = handle_bbox[2] - handle_bbox[0]
        draw.text(
            (w - padding - handle_w, h - int(60 * scale)),
            handle, font=footer_font,
            fill=(*neon_color, 200)
        )

        # Watermark sutil
        wm_font = self._get_font("Inter-Regular.ttf", int(12 * scale))
        draw.text(
            (w - padding - int(80 * scale), h - int(30 * scale)),
            "CJ_Dev4.20", font=wm_font,
            fill=(100, 100, 100, 100)
        )

        # Aplicar glow al borde superior
        img = self._apply_glow_effect(img, topic.color_hex, 0.3)

        return img.convert("RGB")

    def _render_code_block(
        self, code: str, language: str, width: int,
        font: ImageFont.FreeTypeFont, scale: float
    ) -> Image.Image:
        """Renderiza código con syntax highlighting usando Pygments y Pillow."""
        try:
            lexer = get_lexer_by_name(language)
        except Exception:
            lexer = PythonLexer()

        tokens = list(lexer.get_tokens(code))
        line_height = int(26 * scale)
        char_width = int(12 * scale)
        line_num_width = int(40 * scale)

        lines = code.split("\n")
        img_height = max(len(lines) * line_height + int(20 * scale), int(100 * scale))
        img_width = width - int(110 * scale)

        img = Image.new("RGBA", (img_width, img_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Dibujar números de línea
        for i, _line in enumerate(lines):
            y = i * line_height
            draw.text(
                (0, y), str(i + 1).rjust(3),
                font=font, fill=(100, 100, 100, 255)
            )

        # Dibujar tokens con colores
        x = line_num_width
        y = 0
        for token_type, token_value in tokens:
            color = self._get_token_color(token_type)
            for char in token_value:
                if char == "\n":
                    x = line_num_width
                    y += line_height
                    continue
                if x < img_width - char_width:
                    draw.text((x, y), char, font=font, fill=self._hex_to_rgb(color))
                x += char_width

        return img

    def _get_token_color(self, token_type: Any) -> str:
        """Obtiene el color para un tipo de token."""
        while token_type:
            if token_type in DRACULA_COLORS:
                return DRACULA_COLORS[token_type]
            token_type = token_type.parent
        return "#f8f8f2"

    def _draw_radial_gradient(self, img: Image.Image, color_hex: str) -> Image.Image:
        """Dibuja un gradiente radial oscuro con tinte del color del tema."""
        w, h = img.size
        gradient = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(gradient)

        r, g, b = self._hex_to_rgb(color_hex)
        cx, cy = w // 2, h // 3
        max_radius = int(math.sqrt(w ** 2 + h ** 2) / 2)

        steps = 50
        for i in range(steps, 0, -1):
            ratio = i / steps
            radius = int(max_radius * ratio)
            alpha = int(40 * ratio)
            cr = int(r * ratio * 0.3)
            cg = int(g * ratio * 0.3)
            cb = int(b * ratio * 0.3)
            draw.ellipse(
                [cx - radius, cy - radius, cx + radius, cy + radius],
                fill=(cr, cg, cb, alpha)
            )

        # Fondo base oscuro
        base = Image.new("RGBA", (w, h), (15, 15, 25, 255))
        base = Image.alpha_composite(base, gradient)
        return base

    def _apply_glow_effect(self, img: Image.Image, color: str, intensity: float) -> Image.Image:
        """Aplica efecto glow/bloom en la parte superior."""
        w, h = img.size
        glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(glow)

        r, g, b = self._hex_to_rgb(color)
        glow_height = int(h * 0.05)
        for y in range(glow_height):
            alpha = int(100 * intensity * (1 - y / glow_height))
            draw.line([(0, y), (w, y)], fill=(r, g, b, alpha))

        glow = glow.filter(ImageFilter.GaussianBlur(radius=10))
        return Image.alpha_composite(img, glow)

    @staticmethod
    def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
        """Convierte color hex a tupla RGB."""
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore
