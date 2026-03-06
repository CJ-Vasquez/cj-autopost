"""Clase base abstracta para publishers — CJ_Dev4.20 AutoPost."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod

import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from core.models import PublishContent, PublishResult

logger = structlog.get_logger(__name__)


class PublishError(Exception):
    """Error durante la publicación."""


class BasePublisher(ABC):
    """Clase base para todos los publishers con retry automático."""

    platform_name: str = "base"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def publish(self, content: PublishContent) -> PublishResult:
        """Publica contenido con retry automático."""
        logger.info("Publicando", platform=self.platform_name, topic=content.topic.titulo)
        self._rate_limit_check()
        try:
            result = self._do_publish(content)
            logger.info("Publicación exitosa", platform=self.platform_name, url=result.url)
            return result
        except Exception as e:
            logger.error("Error al publicar", platform=self.platform_name, error=str(e))
            raise PublishError(f"[{self.platform_name}] {e}") from e

    @abstractmethod
    def _do_publish(self, content: PublishContent) -> PublishResult:
        """Implementación específica de la publicación."""

    @abstractmethod
    def validate_credentials(self) -> bool:
        """Verifica que las credenciales sean válidas."""

    def _rate_limit_check(self) -> None:
        """Pausa breve para respetar rate limits."""
        time.sleep(1)
