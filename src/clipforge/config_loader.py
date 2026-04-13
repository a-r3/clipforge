"""Configuration loading for ClipForge.

Loads JSON config files, applies CLI overrides, validates required fields,
and returns a complete config dict with sensible defaults.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from clipforge.constants import (
    DEFAULT_PLATFORM,
    DEFAULT_STYLE,
    DEFAULT_AUDIO_MODE,
    DEFAULT_TEXT_MODE,
    DEFAULT_SUBTITLE_MODE,
    DEFAULT_AI_MODE,
    DEFAULT_MUSIC_VOLUME,
    DEFAULT_MAX_SCENES,
)
from clipforge.utils import merge_dicts, load_json


# Default configuration values
_DEFAULTS: dict[str, Any] = {
    "script_file": "",
    "output": "output/video.mp4",
    "platform": DEFAULT_PLATFORM,
    "style": DEFAULT_STYLE,
    "audio_mode": DEFAULT_AUDIO_MODE,
    "text_mode": DEFAULT_TEXT_MODE,
    "subtitle_mode": DEFAULT_SUBTITLE_MODE,
    "music_file": "",
    "music_volume": DEFAULT_MUSIC_VOLUME,
    "auto_voice": False,
    "voice_language": "en",
    "intro_text": "",
    "outro_text": "",
    "logo_file": "",
    "watermark_position": "top-right",
    "ai_mode": DEFAULT_AI_MODE,
    "ai_provider": "",
    "ai_model": "",
    "max_scenes": DEFAULT_MAX_SCENES,
    "brand_name": "",
}


class ConfigLoader:
    """Load, merge, and validate ClipForge configurations."""

    def __init__(self, defaults: dict[str, Any] | None = None) -> None:
        self._defaults = merge_dicts(_DEFAULTS, defaults or {})

    def load(self, path: str | Path | None = None, overrides: dict[str, Any] | None = None) -> dict[str, Any]:
        """Load config from *path* (optional), apply *overrides*, and return merged config.

        Args:
            path: Path to a JSON config file.  If None, only defaults are used.
            overrides: Dict of values to override after file loading.

        Returns:
            Complete config dict with all defaults filled in.
        """
        config = dict(self._defaults)

        if path is not None:
            file_data = load_json(path)
            if file_data:
                config = merge_dicts(config, file_data)

        if overrides:
            # Strip None values so missing CLI flags don't override file values
            clean_overrides = {k: v for k, v in overrides.items() if v is not None}
            config = merge_dicts(config, clean_overrides)

        return config

    def validate(self, config: dict[str, Any]) -> list[str]:
        """Validate *config* and return a list of error messages (empty = valid)."""
        errors: list[str] = []

        script_file = config.get("script_file", "")
        if not script_file and not config.get("script_text", ""):
            # Not an error at load time — the CLI will check this
            pass

        platform = config.get("platform", "")
        from clipforge.constants import ALL_PLATFORMS
        if platform and platform not in ALL_PLATFORMS:
            errors.append(f"Unknown platform '{platform}'. Valid: {sorted(ALL_PLATFORMS)}")

        audio_mode = config.get("audio_mode", "")
        from clipforge.constants import AUDIO_MODES
        if audio_mode and audio_mode not in AUDIO_MODES:
            errors.append(f"Unknown audio_mode '{audio_mode}'. Valid: {sorted(AUDIO_MODES)}")

        text_mode = config.get("text_mode", "")
        from clipforge.constants import TEXT_MODES
        if text_mode and text_mode not in TEXT_MODES:
            errors.append(f"Unknown text_mode '{text_mode}'. Valid: {sorted(TEXT_MODES)}")

        return errors


# Module-level convenience function
def load_config(path: str | Path | None = None, overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    """Load and return a config dict (module-level convenience wrapper)."""
    return ConfigLoader().load(path, overrides)
