"""Tests for clipforge.config_loader module."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from clipforge.config_loader import ConfigLoader, load_config


class TestConfigLoader:
    def test_module_has_function(self):
        import importlib
        module = importlib.import_module("clipforge.config_loader")
        assert hasattr(module, "load_config")

    def test_load_returns_dict(self):
        loader = ConfigLoader()
        config = loader.load()
        assert isinstance(config, dict)

    def test_defaults_present(self):
        loader = ConfigLoader()
        config = loader.load()
        assert "platform" in config
        assert "audio_mode" in config
        assert "text_mode" in config
        assert "output" in config

    def test_load_from_file(self, tmp_path):
        data = {"platform": "tiktok", "style": "bold"}
        f = tmp_path / "config.json"
        f.write_text(json.dumps(data), encoding="utf-8")

        loader = ConfigLoader()
        config = loader.load(f)
        assert config["platform"] == "tiktok"
        assert config["style"] == "bold"

    def test_file_overrides_defaults(self, tmp_path):
        data = {"platform": "youtube"}
        f = tmp_path / "config.json"
        f.write_text(json.dumps(data), encoding="utf-8")

        loader = ConfigLoader()
        config = loader.load(f)
        assert config["platform"] == "youtube"

    def test_overrides_take_precedence_over_file(self, tmp_path):
        data = {"platform": "tiktok"}
        f = tmp_path / "config.json"
        f.write_text(json.dumps(data), encoding="utf-8")

        loader = ConfigLoader()
        config = loader.load(f, overrides={"platform": "youtube"})
        assert config["platform"] == "youtube"

    def test_none_overrides_ignored(self, tmp_path):
        data = {"platform": "tiktok"}
        f = tmp_path / "config.json"
        f.write_text(json.dumps(data), encoding="utf-8")

        loader = ConfigLoader()
        config = loader.load(f, overrides={"platform": None})
        assert config["platform"] == "tiktok"

    def test_missing_file_uses_defaults(self, tmp_path):
        loader = ConfigLoader()
        config = loader.load(tmp_path / "nonexistent.json")
        assert config["platform"] == "reels"  # default

    def test_custom_defaults(self):
        loader = ConfigLoader(defaults={"platform": "youtube"})
        config = loader.load()
        assert config["platform"] == "youtube"

    def test_validate_returns_empty_for_valid_config(self):
        loader = ConfigLoader()
        config = loader.load()
        errors = loader.validate(config)
        assert errors == []

    def test_validate_catches_invalid_platform(self):
        loader = ConfigLoader()
        config = {"platform": "invalid_platform"}
        errors = loader.validate(config)
        assert len(errors) > 0
        assert any("platform" in e.lower() for e in errors)

    def test_validate_catches_invalid_audio_mode(self):
        loader = ConfigLoader()
        config = {"audio_mode": "invalid_mode"}
        errors = loader.validate(config)
        assert len(errors) > 0

    def test_validate_catches_invalid_text_mode(self):
        loader = ConfigLoader()
        errors = loader.validate({"text_mode": "bad_mode"})
        assert any("text_mode" in e for e in errors)

    def test_validate_catches_invalid_subtitle_mode(self):
        loader = ConfigLoader()
        errors = loader.validate({"subtitle_mode": "spinning"})
        assert any("subtitle_mode" in e for e in errors)

    def test_validate_valid_subtitle_modes(self):
        loader = ConfigLoader()
        for mode in ("static", "typewriter", "word-by-word"):
            errors = loader.validate({"subtitle_mode": mode})
            assert errors == [], f"Unexpected error for subtitle_mode={mode!r}: {errors}"

    def test_validate_catches_missing_script_file(self, tmp_path):
        loader = ConfigLoader()
        errors = loader.validate({"script_file": str(tmp_path / "ghost.txt")})
        assert any("script_file" in e for e in errors)

    def test_validate_catches_missing_music_file(self, tmp_path):
        loader = ConfigLoader()
        errors = loader.validate({"music_file": str(tmp_path / "missing.mp3")})
        assert any("music_file" in e for e in errors)

    def test_validate_ignores_empty_optional_paths(self):
        loader = ConfigLoader()
        errors = loader.validate({"music_file": "", "logo_file": ""})
        assert errors == []

    def test_error_messages_are_human_readable(self):
        loader = ConfigLoader()
        errors = loader.validate({"platform": "snapchat"})
        assert len(errors) > 0
        # Message should contain the bad value
        assert "snapchat" in errors[0]


class TestLoadConfigFunction:
    def test_returns_dict(self):
        config = load_config()
        assert isinstance(config, dict)

    def test_loads_from_file(self, sample_config_file):
        config = load_config(sample_config_file)
        assert config["platform"] == "reels"
        assert config["brand_name"] == "TestBrand"

    def test_applies_overrides(self):
        config = load_config(overrides={"platform": "tiktok"})
        assert config["platform"] == "tiktok"
