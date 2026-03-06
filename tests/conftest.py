"""Fixtures compartidas para tests."""

import pytest

from core.models import TopicData


@pytest.fixture
def sample_topic() -> TopicData:
    return TopicData(
        id="TEST001",
        titulo="Variables en Python",
        descripcion="Aprende a declarar y usar variables en Python",
        codigo='nombre = "CJ"\nedad = 25\nprint(f"Hola {nombre}, tienes {edad} años")',
        lenguaje="python",
        color_hex="#6C63FF",
        icono="📦",
        hashtags_extra=["#variables", "#basics"],
    )
