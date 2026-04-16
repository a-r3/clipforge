"""Configuration loading for ClipForge.

Loads JSON config files, applies CLI overrides, validates required fields,
and returns a complete config dict with sensible defaults.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from clipforge.constants import (
    DEFAULT_AI_MODE,
    DEFAULT_AUDIO_MODE,
    DEFAULT_MAX_SCENES,
    DEFAULT_MUSIC_VOLUME,
    DEFAULT_PLATFORM,
    DEFAULT_STYLE,
    DEFAULT_SUBTITLE_MODE,
    DEFAULT_TEXT_MODE,
)
from clipforge.utils import load_env_file, load_json, merge_dicts

# Default configuration values — baseline before smart-defaults are applied
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
    "watermark_position": "bottom-right",
    "ai_mode": DEFAULT_AI_MODE,
    "ai_provider": "",
    "ai_model": "",
    "max_scenes": DEFAULT_MAX_SCENES,
    "brand_name": "",
}

# Platform-specific smart defaults applied on top of _DEFAULTS when a field
# has not been explicitly set by the user.
_PLATFORM_SMART_DEFAULTS: dict[str, dict[str, Any]] = {
    "reels": {
        "text_mode": "subtitle",
        "subtitle_mode": "word-by-word",
        "style": "bold",
    },
    "tiktok": {
        "text_mode": "subtitle",
        "subtitle_mode": "word-by-word",
        "style": "bold",
    },
    "youtube-shorts": {
        "text_mode": "subtitle",
        "subtitle_mode": "static",
        "style": "clean",
    },
    "youtube": {
        "text_mode": "subtitle",
        "subtitle_mode": "static",
        "style": "clean",
    },
    "landscape": {
        "text_mode": "subtitle",
        "subtitle_mode": "static",
        "style": "cinematic",
    },
}


def _apply_smart_defaults(config: dict[str, Any], explicit_keys: set[str]) -> dict[str, Any]:
    """Apply platform-aware smart defaults for any keys the user did NOT explicitly set.

    Only fills in keys that are still equal to the baseline _DEFAULTS value AND
    were not passed explicitly, so the user always wins.
    """
    platform = config.get("platform", DEFAULT_PLATFORM)
    platform_defaults = _PLATFORM_SMART_DEFAULTS.get(platform, {})
    result = dict(config)
    for key, smart_value in platform_defaults.items():
        if key not in explicit_keys and result.get(key) == _DEFAULTS.get(key):
            result[key] = smart_value
    return result


class ConfigLoader:
    """Load, merge, and validate ClipForge configurations."""

    def __init__(self, defaults: dict[str, Any] | None = None) -> None:
        self._defaults = merge_dicts(_DEFAULTS, defaults or {})

    def load(self, path: str | Path | None = None, overrides: dict[str, Any] | None = None) -> dict[str, Any]:
        """Load config from *path* (optional), apply *overrides*, and return merged config.

        Smart defaults are applied for any field the user did not explicitly set:
        - Vertical platforms (reels, tiktok) default to bold style + word-by-word subtitles
        - Landscape/YouTube platforms default to clean style + static subtitles

        Args:
            path: Path to a JSON config file.  If None, only defaults are used.
            overrides: Dict of values to override after file loading.

        Returns:
            Complete config dict with all defaults filled in.
        """
        config = dict(self._defaults)

        # Track which keys were set explicitly (file or CLI), so smart defaults
        # only fill in genuinely missing ones.
        explicit_keys: set[str] = set()

        if path is not None:
            file_data = load_json(path)
            if file_data:
                explicit_keys.update(file_data.keys())
                config = merge_dicts(config, file_data)

        if overrides:
            # Strip None values so missing CLI flags don't override file values
            clean_overrides = {k: v for k, v in overrides.items() if v is not None}
            explicit_keys.update(clean_overrides.keys())
            config = merge_dicts(config, clean_overrides)

        # Apply smart platform-aware defaults for anything not set explicitly
        config = _apply_smart_defaults(config, explicit_keys)

        return config

    def validate(self, config: dict[str, Any]) -> list[str]:
        """Validate *config* and return a list of human-readable error messages.

        An empty list means the config is valid.
        """
        errors: list[str] = []

        from clipforge.constants import ALL_PLATFORMS, AUDIO_MODES, SUBTITLE_MODES, TEXT_MODES

        # Platform
        platform = config.get("platform", "")
        if platform and platform not in ALL_PLATFORMS:
            errors.append(
                f"Invalid platform '{platform}'. "
                f"Supported: {', '.join(sorted(ALL_PLATFORMS))}."
            )

        # Audio mode
        audio_mode = config.get("audio_mode", "")
        if audio_mode and audio_mode not in AUDIO_MODES:
            errors.append(
                f"Invalid audio_mode '{audio_mode}'. "
                f"Supported: {', '.join(sorted(AUDIO_MODES))}."
            )

        # Text mode
        text_mode = config.get("text_mode", "")
        if text_mode and text_mode not in TEXT_MODES:
            errors.append(
                f"Invalid text_mode '{text_mode}'. "
                f"Supported: {', '.join(sorted(TEXT_MODES))}."
            )

        # Subtitle mode
        subtitle_mode = config.get("subtitle_mode", "")
        if subtitle_mode and subtitle_mode not in SUBTITLE_MODES:
            errors.append(
                f"Invalid subtitle_mode '{subtitle_mode}'. "
                f"Supported: {', '.join(sorted(SUBTITLE_MODES))}."
            )

        # File paths — only validate if non-empty (existence check)
        for key in ("script_file", "music_file", "logo_file"):
            val = config.get(key, "")
            if val and not os.path.exists(val):
                errors.append(
                    f"File not found for '{key}': {val}"
                )

        return errors


# Module-level convenience function
def load_config(path: str | Path | None = None, overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    """Load and return a config dict (module-level convenience wrapper)."""
    load_env_file()
    return ConfigLoader().load(path, overrides)
