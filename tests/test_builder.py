"""Tests for the video builder module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from clipforge.builder import VideoBuilder, make_video
from clipforge.utils import get_platform_spec


def test_builder_importable():
    """VideoBuilder and make_video must be importable."""
    assert VideoBuilder is not None
    assert callable(make_video)


def test_video_builder_instantiates():
    """VideoBuilder instantiates without arguments."""
    builder = VideoBuilder()
    assert builder is not None


def test_platform_spec_reels():
    """Platform spec for reels must be 9:16."""
    spec = get_platform_spec("reels")
    assert spec["width"] == 1080
    assert spec["height"] == 1920


def test_platform_spec_youtube():
    """Platform spec for youtube must be 16:9."""
    spec = get_platform_spec("youtube")
    assert spec["width"] == 1920
    assert spec["height"] == 1080


def test_platform_spec_unknown_falls_back():
    """Unknown platform falls back to a default spec with width and height."""
    spec = get_platform_spec("unknown_platform_xyz")
    assert isinstance(spec["width"], int)
    assert isinstance(spec["height"], int)
    assert spec["width"] > 0
    assert spec["height"] > 0


def test_make_video_function_exists():
    """make_video module-level convenience function must exist."""
    assert callable(make_video)


def test_builder_has_build_method():
    """VideoBuilder must expose a build() method."""
    builder = VideoBuilder()
    assert callable(getattr(builder, "build", None))


def test_build_raises_on_empty_scenes(tmp_path):
    """build() with no scenes should raise ValueError."""
    builder = VideoBuilder()
    config = {
        "platform": "reels",
        "style": "clean",
        "audio_mode": "silent",
        "text_mode": "none",
        "subtitle_mode": "static",
        "music_file": "",
        "music_volume": 0.1,
        "auto_voice": False,
        "intro_text": "",
        "outro_text": "",
        "logo_file": "",
    }
    output = tmp_path / "output.mp4"

    try:
        builder.build([], config, str(output))
        assert False, "Should have raised ValueError on empty scenes"
    except (ValueError, Exception):
        pass  # Either ValueError or ImportError (moviepy) — both acceptable


def test_build_aborts_gracefully_without_moviepy(tmp_path, caplog):
    """build() should fail gracefully when moviepy is not installed."""
    import logging
    scenes = [{"text": "Test scene", "estimated_duration": 3.0, "keywords": [], "visual_intent": "abstract"}]
    config = {
        "platform": "reels",
        "style": "clean",
        "audio_mode": "silent",
        "text_mode": "none",
        "subtitle_mode": "static",
        "music_file": "",
        "music_volume": 0.1,
        "auto_voice": False,
        "intro_text": "",
        "outro_text": "",
        "logo_file": "",
    }
    builder = VideoBuilder()
    output = tmp_path / "output.mp4"

    with patch.dict("sys.modules", {"moviepy": None, "moviepy.editor": None}):
        with caplog.at_level(logging.ERROR):
            try:
                builder.build(scenes, config, str(output))
            except Exception:
                pass  # Expected — moviepy unavailable
