"""Brand profile system for ClipForge.

Allows users to define persistent channel/brand settings that are
automatically applied to configs, saving repetitive CLI arguments.
"""

from __future__ import annotations

import json
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
    PLATFORM_REELS,
    PLATFORM_TIKTOK,
    PLATFORM_YOUTUBE_SHORTS,
    PLATFORM_YOUTUBE,
)

# Platform-aware defaults that differ from global defaults
_PLATFORM_DEFAULTS: dict[str, dict[str, Any]] = {
    PLATFORM_REELS: {
        "text_mode": "subtitle",
        "subtitle_mode": "word-by-word",
        "fps": 30,
    },
    PLATFORM_TIKTOK: {
        "text_mode": "subtitle",
        "subtitle_mode": "word-by-word",
        "fps": 30,
    },
    PLATFORM_YOUTUBE_SHORTS: {
        "text_mode": "subtitle",
        "subtitle_mode": "static",
        "fps": 60,
    },
    PLATFORM_YOUTUBE: {
        "text_mode": "subtitle",
        "subtitle_mode": "static",
        "fps": 30,
    },
}


class BrandProfile:
    """Persistent brand/channel settings.

    Example JSON profile::

        {
          "brand_name": "TechBrief",
          "platform": "reels",
          "style": "bold",
          "audio_mode": "voiceover+music",
          "music_file": "assets/music/background.mp3",
          "music_volume": 0.12,
          "intro_text": "TechBrief",
          "outro_text": "Follow for more",
          "watermark_text": "TechBrief",
          "watermark_position": "bottom-right",
          "watermark_opacity": 0.7,
          "watermark_size": 24,
          "ai_mode": "off",
          "ai_provider": "openai"
        }
    """

    def __init__(
        self,
        brand_name: str = "",
        platform: str = DEFAULT_PLATFORM,
        style: str = DEFAULT_STYLE,
        audio_mode: str = DEFAULT_AUDIO_MODE,
        text_mode: str = DEFAULT_TEXT_MODE,
        subtitle_mode: str = DEFAULT_SUBTITLE_MODE,
        music_file: str = "",
        music_volume: float = DEFAULT_MUSIC_VOLUME,
        intro_text: str = "",
        outro_text: str = "",
        watermark_text: str = "",
        watermark_position: str = "bottom-right",
        watermark_opacity: float = 0.7,
        watermark_size: int = 24,
        ai_mode: str = DEFAULT_AI_MODE,
        ai_provider: str = "",
        ai_model: str = "",
        logo_file: str = "",
        extra: dict[str, Any] | None = None,
    ) -> None:
        self.brand_name = brand_name
        self.platform = platform
        self.style = style
        self.audio_mode = audio_mode
        self.text_mode = text_mode
        self.subtitle_mode = subtitle_mode
        self.music_file = music_file
        self.music_volume = music_volume
        self.intro_text = intro_text
        self.outro_text = outro_text
        self.watermark_text = watermark_text
        self.watermark_position = watermark_position
        self.watermark_opacity = watermark_opacity
        self.watermark_size = watermark_size
        self.ai_mode = ai_mode
        self.ai_provider = ai_provider
        self.ai_model = ai_model
        self.logo_file = logo_file
        self.extra: dict[str, Any] = extra or {}

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """Return a plain dict representation."""
        d: dict[str, Any] = {
            "brand_name": self.brand_name,
            "platform": self.platform,
            "style": self.style,
            "audio_mode": self.audio_mode,
            "text_mode": self.text_mode,
            "subtitle_mode": self.subtitle_mode,
            "music_file": self.music_file,
            "music_volume": self.music_volume,
            "intro_text": self.intro_text,
            "outro_text": self.outro_text,
            "watermark_text": self.watermark_text,
            "watermark_position": self.watermark_position,
            "watermark_opacity": self.watermark_opacity,
            "watermark_size": self.watermark_size,
            "ai_mode": self.ai_mode,
            "ai_provider": self.ai_provider,
            "ai_model": self.ai_model,
            "logo_file": self.logo_file,
        }
        d.update(self.extra)
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BrandProfile":
        """Create a BrandProfile from a plain dict."""
        known_keys = {
            "brand_name", "platform", "style", "audio_mode", "text_mode",
            "subtitle_mode", "music_file", "music_volume", "intro_text",
            "outro_text", "watermark_text", "watermark_position",
            "watermark_opacity", "watermark_size", "ai_mode", "ai_provider",
            "ai_model", "logo_file",
        }
        extra = {k: v for k, v in data.items() if k not in known_keys}
        kwargs = {k: v for k, v in data.items() if k in known_keys}
        return cls(extra=extra, **kwargs)

    @classmethod
    def load(cls, path: str | Path) -> "BrandProfile":
        """Load a BrandProfile from a JSON file."""
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Profile file not found: {path}")
        with p.open(encoding="utf-8") as fh:
            data = json.load(fh)
        return cls.from_dict(data)

    def save(self, path: str | Path) -> None:
        """Save this profile to a JSON file."""
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("w", encoding="utf-8") as fh:
            json.dump(self.to_dict(), fh, indent=2)

    # ------------------------------------------------------------------
    # Config integration
    # ------------------------------------------------------------------

    def apply_to_config(self, config: dict[str, Any]) -> dict[str, Any]:
        """Return a new config dict with profile values applied.

        Profile values fill in any keys that are missing or empty in config,
        but do NOT override values the user explicitly set.
        """
        result = dict(config)
        profile_dict = self.to_dict()

        # Apply platform-aware defaults first
        platform = result.get("platform") or self.platform
        platform_defaults = _PLATFORM_DEFAULTS.get(platform, {})
        for key, value in platform_defaults.items():
            if key not in result or not result[key]:
                result[key] = value

        # Apply profile fields — only fill in missing / empty values
        for key, value in profile_dict.items():
            if key not in result or result[key] in (None, "", 0, 0.0):
                result[key] = value

        return result

    # ------------------------------------------------------------------
    # Dunder
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"BrandProfile(brand_name={self.brand_name!r}, "
            f"platform={self.platform!r}, style={self.style!r})"
        )
