"""
Tests for utility functions.
"""

from autovideo.utils import load_env, is_ffmpeg_available


def test_load_env_returns_dict(monkeypatch):
    # Set an environment variable and ensure load_env reflects it
    monkeypatch.setenv("PEXELS_API_KEY", "testkey")
    env = load_env()
    assert isinstance(env, dict)
    assert env.get("PEXELS_API_KEY") == "testkey"


def test_is_ffmpeg_available_returns_bool():
    available = is_ffmpeg_available()
    assert isinstance(available, bool)
