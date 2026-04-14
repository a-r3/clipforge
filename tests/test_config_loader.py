"""Tests for clipforge.config_loader module."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from clipforge.config_loader import ConfigLoader, load_config, _apply_smart_defaults


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


class TestSmartDefaults:
    """Tests for platform-aware smart defaults (v0.4 UX pass)."""

    def test_reels_gets_bold_style(self):
        config = _apply_smart_defaults(
            {"platform": "reels", "style": "clean"},  # style is still at baseline
            explicit_keys={"platform"},               # style was NOT set explicitly
        )
        assert config["style"] == "bold"

    def test_reels_gets_word_by_word_subtitle(self):
        config = _apply_smart_defaults(
            {"platform": "reels", "subtitle_mode": "static"},
            explicit_keys={"platform"},
        )
        assert config["subtitle_mode"] == "word-by-word"

    def test_tiktok_gets_word_by_word(self):
        config = _apply_smart_defaults(
            {"platform": "tiktok", "subtitle_mode": "static"},
            explicit_keys={"platform"},
        )
        assert config["subtitle_mode"] == "word-by-word"

    def test_youtube_keeps_static_subtitle(self):
        config = _apply_smart_defaults(
            {"platform": "youtube", "subtitle_mode": "static"},
            explicit_keys={"platform"},
        )
        assert config["subtitle_mode"] == "static"

    def test_explicit_style_not_overridden(self):
        """User-set style must not be replaced by smart default."""
        config = _apply_smart_defaults(
            {"platform": "reels", "style": "minimal"},
            explicit_keys={"platform", "style"},  # style was set explicitly
        )
        assert config["style"] == "minimal"

    def test_explicit_subtitle_mode_not_overridden(self):
        config = _apply_smart_defaults(
            {"platform": "tiktok", "subtitle_mode": "typewriter"},
            explicit_keys={"platform", "subtitle_mode"},
        )
        assert config["subtitle_mode"] == "typewriter"

    def test_load_config_applies_smart_defaults_for_reels(self):
        """load_config with platform=reels should auto-select bold+word-by-word."""
        config = load_config(overrides={"platform": "reels"})
        assert config["style"] == "bold"
        assert config["subtitle_mode"] == "word-by-word"

    def test_load_config_explicit_style_wins_over_smart(self):
        """Explicit style override must not be replaced."""
        config = load_config(overrides={"platform": "reels", "style": "minimal"})
        assert config["style"] == "minimal"

    def test_unknown_platform_no_crash(self):
        """Unknown platform should not crash — just returns config unchanged."""
        config = _apply_smart_defaults(
            {"platform": "snapchat", "style": "clean"},
            explicit_keys={"platform"},
        )
        assert isinstance(config, dict)

    def test_landscape_gets_cinematic_style(self):
        config = _apply_smart_defaults(
            {"platform": "landscape", "style": "clean"},
            explicit_keys={"platform"},
        )
        assert config["style"] == "cinematic"
