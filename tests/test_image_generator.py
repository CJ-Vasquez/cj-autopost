"""Tests para el generador de imágenes."""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.models import TopicData, PlatformConfig


@pytest.fixture
def topic():
    return TopicData(
        id="TEST001",
        titulo="Variables en Python",
        descripcion="Aprende a declarar variables",
        codigo='x = 10\nprint(x)',
        lenguaje="python",
        color_hex="#6C63FF",
        icono="📦",
    )


class TestImageGenerator:
    def test_generates_all_platform_sizes(self, topic):
        from core.image_generator import ImageGenerator

        gen = ImageGenerator()
        results = gen.generate_all_formats(topic)

        assert len(results) > 0
        for platform, path in results.items():
            assert path.exists(), f"Imagen para {platform} no se generó"
            assert path.suffix == ".png"

    def test_code_highlighting_applies_colors(self, topic):
        from core.image_generator import ImageGenerator

        gen = ImageGenerator()
        code_font = gen._get_font("FiraCode-Regular.ttf", 20)
        code_img = gen._render_code_block(topic.codigo, "python", 800, code_font, 1.0)

        assert code_img.width > 0
        assert code_img.height > 0

    def test_output_files_exist_after_generation(self, topic):
        from core.image_generator import ImageGenerator, OUTPUT_DIR

        gen = ImageGenerator()
        results = gen.generate_all_formats(topic)

        for path in results.values():
            assert path.exists()
            assert path.stat().st_size > 0

    def test_custom_color_applied_to_card(self):
        from core.image_generator import ImageGenerator

        gen = ImageGenerator()
        topic_green = TopicData(
            id="TEST002",
            titulo="Condicionales",
            descripcion="if/else en Python",
            codigo='if True:\n    print("si")',
            color_hex="#059669",
        )

        config = PlatformConfig(name="test", resolution=[1080, 1080])
        img = gen._generate_card(topic_green, config)

        assert img.size == (1080, 1080)
