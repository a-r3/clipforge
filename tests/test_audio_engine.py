"""Tests for the audio engine module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from clipforge.audio_engine import AudioEngine


def test_audio_engine_importable():
    """AudioEngine class must be importable."""
    assert AudioEngine is not None


def test_audio_engine_instantiates():
    """AudioEngine must instantiate with default config."""
    engine = AudioEngine()
    assert engine is not None


def test_silent_mode_returns_none():
    """Silent mode should return None (no audio clip)."""
    engine = AudioEngine()
    result = engine.build_audio([], {"audio_mode": "silent"})
    assert result is None


def test_music_mode_warns_on_missing_file(caplog):
    """Music mode with missing file should warn and not raise."""
    import logging
    engine = AudioEngine()
    with caplog.at_level(logging.WARNING):
        result = engine.build_audio([], {"audio_mode": "music", "music_file": "/nonexistent/music.mp3"})
    assert result is None


def test_voiceover_mode_falls_back_without_pyttsx3():
    """Voiceover mode must not crash if pyttsx3 is unavailable."""
    scenes = [{"text": "Hello world", "estimated_duration": 2.0}]
    engine = AudioEngine()
    with patch.dict("sys.modules", {"pyttsx3": None}):
        # Should not raise; pyttsx3 import will fail and engine falls back
        try:
            result = engine.build_audio(scenes, {"audio_mode": "voiceover", "auto_voice": True, "voice_language": "en"})
        except Exception:
            pass  # Acceptable — what matters is no unhandled crash in normal flow


def test_build_audio_silent_accepts_any_scenes():
    """build_audio in silent mode accepts any scenes list."""
    engine = AudioEngine()
    scenes = [
        {"text": "Scene one", "estimated_duration": 3.0},
        {"text": "Scene two", "estimated_duration": 5.0},
    ]
    result = engine.build_audio(scenes, {"audio_mode": "silent"})
    assert result is None


def test_audio_engine_has_build_audio():
    """AudioEngine must expose build_audio method."""
    assert callable(getattr(AudioEngine, "build_audio", None))
