"""Tests for the text engine module."""

from __future__ import annotations

from unittest.mock import MagicMock

from clipforge.text_engine import TextEngine, SubtitleRenderer


def test_text_engine_importable():
    """TextEngine and SubtitleRenderer must be importable."""
    assert TextEngine is not None
    assert SubtitleRenderer is not None


def test_text_engine_instantiates():
    """TextEngine instantiates without arguments."""
    engine = TextEngine()
    assert engine is not None


def test_subtitle_renderer_instantiates_with_mode():
    """SubtitleRenderer instantiates with mode and style."""
    renderer = SubtitleRenderer(mode="static", style="clean")
    assert renderer.mode == "static"
    assert renderer.style == "clean"


def test_subtitle_renderer_default_mode():
    """SubtitleRenderer default mode is 'none'."""
    renderer = SubtitleRenderer()
    assert renderer.mode == "none"


def test_text_engine_has_add_text_overlay():
    """TextEngine must expose add_text_overlay method."""
    assert callable(getattr(TextEngine, "add_text_overlay", None))


def test_text_mode_none_returns_clip_unchanged():
    """text_mode='none' should return the clip as-is (no overlay)."""
    engine = TextEngine()
    mock_clip = MagicMock()
    scene = {"text": "Hello world", "estimated_duration": 3.0}
    config = {"text_mode": "none", "subtitle_mode": "static", "style": "clean"}
    result = engine.add_text_overlay(mock_clip, scene, config)
    # In none mode the original clip must be returned unchanged
    assert result is mock_clip


def test_text_mode_empty_text_returns_clip_unchanged():
    """Empty scene text should return the clip unchanged regardless of mode."""
    engine = TextEngine()
    mock_clip = MagicMock()
    scene = {"text": "", "estimated_duration": 3.0}
    config = {"text_mode": "subtitle", "subtitle_mode": "static", "style": "clean"}
    result = engine.add_text_overlay(mock_clip, scene, config)
    assert result is mock_clip


def test_subtitle_modes_are_distinct():
    """static, typewriter, and word-by-word modes must produce different mode values."""
    static = SubtitleRenderer(mode="static")
    typewriter = SubtitleRenderer(mode="typewriter")
    wbw = SubtitleRenderer(mode="word-by-word")
    assert static.mode != typewriter.mode
    assert static.mode != wbw.mode
    assert typewriter.mode != wbw.mode


def test_subtitle_renderer_has_render_method():
    """SubtitleRenderer must expose a render method."""
    renderer = SubtitleRenderer(mode="static")
    assert callable(getattr(renderer, "render", None))


def test_subtitle_renderer_render_returns_list():
    """render() returns a list."""
    renderer = SubtitleRenderer(mode="static")
    result = renderer.render(["Hello world", "Second scene"])
    assert isinstance(result, list)


def test_text_engine_default_mode():
    """TextEngine default mode is subtitle."""
    from clipforge.constants import TEXT_SUBTITLE
    engine = TextEngine()
    assert engine.mode == TEXT_SUBTITLE
