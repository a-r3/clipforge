"""Preset management for ClipForge.

Loads style presets from data/presets.json and provides functions to list,
retrieve, and apply them to a configuration dict.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from clipforge.utils import load_json, merge_dicts


def _data_dir() -> Path:
    """Return the path to the data directory (relative to project root)."""
    # Walk up from this file to find the data/ directory
    here = Path(__file__).resolve()
    for parent in [here.parent.parent.parent, here.parent.parent.parent.parent]:
        candidate = parent / "data"
        if candidate.is_dir():
            return candidate
    # Fallback: assume data/ is alongside src/
    return Path(__file__).resolve().parents[3] / "data"


_BUILTIN_PRESETS: dict[str, dict[str, Any]] = {
    "clean": {
        "style": "clean",
        "text_mode": "subtitle",
        "subtitle_mode": "static",
        "audio_mode": "silent",
        "music_volume": 0.10,
    },
    "bold": {
        "style": "bold",
        "text_mode": "title_cards",
        "subtitle_mode": "static",
        "audio_mode": "music",
        "music_volume": 0.15,
    },
    "minimal": {
        "style": "minimal",
        "text_mode": "none",
        "subtitle_mode": "static",
        "audio_mode": "silent",
        "music_volume": 0.08,
    },
    "cinematic": {
        "style": "cinematic",
        "text_mode": "subtitle",
        "subtitle_mode": "word-by-word",
        "audio_mode": "voiceover+music",
        "music_volume": 0.12,
    },
}


class Presets:
    """Load and apply ClipForge presets."""

    def __init__(self, presets_file: str | Path | None = None) -> None:
        self._presets: dict[str, dict[str, Any]] = dict(_BUILTIN_PRESETS)

        # Try loading from file
        if presets_file is None:
            presets_file = _data_dir() / "presets.json"

        file_data = load_json(presets_file)
        if isinstance(file_data, dict):
            self._presets.update(file_data)

    def list_presets(self) -> list[str]:
        """Return a sorted list of available preset names."""
        return sorted(self._presets.keys())

    def get_preset(self, name: str) -> dict[str, Any]:
        """Return the preset dict for *name*.

        Raises KeyError if the preset does not exist.
        """
        if name not in self._presets:
            raise KeyError(f"Preset '{name}' not found. Available: {self.list_presets()}")
        return dict(self._presets[name])

    def apply_preset(self, config: dict[str, Any], preset_name: str) -> dict[str, Any]:
        """Apply preset *preset_name* to *config* and return merged config.

        Config values take precedence over preset values for non-default keys.
        """
        preset = self.get_preset(preset_name)
        return merge_dicts(preset, config)
