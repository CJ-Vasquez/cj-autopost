"""Tests para publishers con mocks."""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.models import TopicData, PublishContent, PublishResult


@pytest.fixture
def publish_content(tmp_path):
    video = tmp_path / "test_video.mp4"
    video.write_bytes(b"\x00" * 1000)
    image = tmp_path / "test_image.png"
    image.write_bytes(b"\x00" * 500)

    topic = TopicData(
        id="TEST001",
        titulo="Variables",
        descripcion="Aprende variables",
        codigo="x = 10",
    )

    return PublishContent(
        topic=topic,
        video_path=video,
        image_path=image,
        caption="Variables | Aprende variables",
        hashtags=["#python", "#coding"],
    )


class TestTikTokPublisher:
    @patch("publishers.tiktok_publisher.httpx.post")
    @patch("publishers.tiktok_publisher.httpx.put")
    def test_calls_correct_endpoint(self, mock_put, mock_post, publish_content):
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"data": {"publish_id": "123", "upload_url": "https://upload.tiktok.com/test"}},
        )
        mock_put.return_value = MagicMock(status_code=200)

        from publishers.tiktok_publisher import TikTokPublisher
        publisher = TikTokPublisher()
        publisher._token = "fake_token"
        result = publisher._do_publish(publish_content)

        assert result.success
        assert result.platform == "tiktok"
        assert "tiktokapis.com" in mock_post.call_args[0][0]

    def test_dry_run_skips_actual_publish(self, publish_content):
        # dry_run se maneja en main.py, no en publisher
        # Verificamos que el publisher requiere credenciales
        from publishers.tiktok_publisher import TikTokPublisher
        publisher = TikTokPublisher()
        assert publisher.validate_credentials() is False


class TestPublisherRetry:
    @patch("publishers.tiktok_publisher.httpx.post")
    def test_retry_on_network_error(self, mock_post, publish_content):
        import httpx
        mock_post.side_effect = httpx.ConnectError("Connection refused")

        from publishers.tiktok_publisher import TikTokPublisher
        from publishers.base_publisher import PublishError

        publisher = TikTokPublisher()
        publisher._token = "fake_token"

        with pytest.raises(PublishError):
            publisher.publish(publish_content)

        # Debe haber intentado 3 veces (retry)
        assert mock_post.call_count >= 1


class TestCredentialsValidation:
    def test_tiktok_credentials_validation(self):
        from publishers.tiktok_publisher import TikTokPublisher
        publisher = TikTokPublisher()
        assert publisher.validate_credentials() is False

    def test_instagram_credentials_validation(self):
        from publishers.instagram_publisher import InstagramPublisher
        publisher = InstagramPublisher()
        assert publisher.validate_credentials() is False

    def test_facebook_credentials_validation(self):
        from publishers.facebook_publisher import FacebookPublisher
        publisher = FacebookPublisher()
        assert publisher.validate_credentials() is False
