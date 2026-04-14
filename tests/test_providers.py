"""Tests for clipforge.providers — abstract provider layer."""

from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# Stock provider
# ---------------------------------------------------------------------------

def test_stock_provider_importable():
    from clipforge.providers.stock import StockProvider, StockResult
    assert StockProvider is not None
    assert StockResult is not None


def test_stock_result_success_true_with_path():
    from clipforge.providers.stock import StockResult
    r = StockResult(local_path="/tmp/video.mp4", source="pexels_video")
    assert r.success is True


def test_stock_result_success_false_without_path():
    from clipforge.providers.stock import StockResult
    r = StockResult(local_path=None, source="fallback")
    assert r.success is False


def test_stock_provider_is_abstract():
    from clipforge.providers.stock import StockProvider
    with pytest.raises(TypeError):
        StockProvider()  # type: ignore[abstract]


def test_stock_provider_concrete_subclass_works():
    from clipforge.providers.stock import StockProvider, StockResult

    class DummyStock(StockProvider):
        def fetch(self, query, width, height, used_ids=None):
            return StockResult(local_path="/fake/path.mp4", source="dummy", query_used=query)

    p = DummyStock(api_key="testkey")
    assert p.is_available()
    result = p.fetch("AI technology", 1080, 1920)
    assert result.success
    assert result.query_used == "AI technology"


def test_stock_provider_no_key_not_available():
    from clipforge.providers.stock import StockProvider, StockResult

    class DummyStock(StockProvider):
        def fetch(self, query, width, height, used_ids=None):
            return StockResult()

    p = DummyStock(api_key="")
    assert not p.is_available()


# ---------------------------------------------------------------------------
# TTS provider
# ---------------------------------------------------------------------------

def test_tts_provider_importable():
    from clipforge.providers.tts import TTSProvider, TTSResult
    assert TTSProvider is not None
    assert TTSResult is not None


def test_tts_result_success_true():
    from clipforge.providers.tts import TTSResult
    r = TTSResult(audio_path="/tmp/audio.mp3")
    assert r.success is True


def test_tts_result_success_false():
    from clipforge.providers.tts import TTSResult
    r = TTSResult(audio_path=None)
    assert r.success is False


def test_tts_provider_is_abstract():
    from clipforge.providers.tts import TTSProvider
    with pytest.raises(TypeError):
        TTSProvider()  # type: ignore[abstract]


def test_tts_provider_concrete_subclass_works():
    from clipforge.providers.tts import TTSProvider, TTSResult

    class DummyTTS(TTSProvider):
        def synthesize(self, text, output_path, language=None, voice=None):
            return TTSResult(audio_path=output_path, provider="dummy", language=language or self.language)

    p = DummyTTS(language="en")
    assert p.is_available()
    result = p.synthesize("Hello world", "/tmp/out.mp3")
    assert result.success
    assert result.audio_path == "/tmp/out.mp3"
    assert result.language == "en"


# ---------------------------------------------------------------------------
# Publish provider
# ---------------------------------------------------------------------------

def test_publish_provider_importable():
    from clipforge.providers.publish import PublishProvider, PublishResult, PublishTarget
    assert PublishProvider is not None
    assert PublishResult is not None
    assert PublishTarget is not None


def test_publish_result_defaults():
    from clipforge.providers.publish import PublishResult
    r = PublishResult()
    assert r.success is False
    assert r.post_url == ""
    assert r.error == ""


def test_publish_target_dataclass():
    from clipforge.providers.publish import PublishTarget
    t = PublishTarget(
        video_path="output/video.mp4",
        caption="Hello world",
        hashtags="#test",
        platform="reels",
    )
    assert t.video_path == "output/video.mp4"
    assert t.platform == "reels"


def test_publish_provider_is_abstract():
    from clipforge.providers.publish import PublishProvider
    with pytest.raises(TypeError):
        PublishProvider()  # type: ignore[abstract]


def test_publish_provider_concrete_subclass_works():
    from clipforge.providers.publish import PublishProvider, PublishResult, PublishTarget

    class DummyPublisher(PublishProvider):
        def publish(self, target):
            return PublishResult(
                success=True,
                post_url=f"https://example.com/{target.platform}/123",
                platform=target.platform,
            )

    p = DummyPublisher(api_key="key123")
    assert p.is_available()
    result = p.publish(PublishTarget(video_path="v.mp4", platform="reels"))
    assert result.success
    assert "reels" in result.post_url


def test_publish_provider_no_key_not_available():
    from clipforge.providers.publish import PublishProvider, PublishResult, PublishTarget

    class DummyPublisher(PublishProvider):
        def publish(self, target):
            return PublishResult()

    p = DummyPublisher()
    assert not p.is_available()
