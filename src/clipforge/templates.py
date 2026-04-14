"""Template pack manager for ClipForge.

Templates are reusable starting points for common content types:
business, AI, motivation, educational. Each template provides
platform, style, audio mode, and sample script defaults.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _templates_dir() -> Path:
    """Return the path to the data/templates directory."""
    here = Path(__file__).resolve()
    # Walk up from src/clipforge/ to find data/templates/
    for parent in here.parents:
        candidate = parent / "data" / "templates"
        if candidate.is_dir():
            return candidate
    return Path(__file__).resolve().parents[2] / "data" / "templates"


class TemplateManager:
    """Load and apply ClipForge template packs."""

    def __init__(self, templates_dir: str | Path | None = None) -> None:
        self._dir = Path(templates_dir) if templates_dir else _templates_dir()
        self._cache: dict[str, dict[str, Any]] | None = None

    def _load_all(self) -> dict[str, dict[str, Any]]:
        if self._cache is not None:
            return self._cache
        result: dict[str, dict[str, Any]] = {}
        if self._dir.is_dir():
            for fp in sorted(self._dir.glob("*.json")):
                try:
                    data = json.loads(fp.read_text(encoding="utf-8"))
                    name = data.get("name") or fp.stem
                    result[name] = data
                except Exception:
                    pass
        self._cache = result
        return result

    def list_templates(self) -> list[dict[str, Any]]:
        """Return a list of all available templates (each as a dict)."""
        return list(self._load_all().values())

    def get(self, name: str) -> dict[str, Any]:
        """Return the template dict for *name*.

        Raises KeyError if not found.
        """
        templates = self._load_all()
        if name not in templates:
            raise KeyError(
                f"Template '{name}' not found. "
                f"Available: {', '.join(sorted(templates.keys()))}"
            )
        return dict(templates[name])

    def apply_to_config(self, config: dict[str, Any], template_name: str) -> dict[str, Any]:
        """Apply template *template_name* to *config*.

        Template values fill in empty/default config fields.
        User-set config values always win.
        """
        template = self.get(template_name)
        # Keys that are config-relevant (exclude metadata-only keys)
        config_keys = {
            "platform", "style", "audio_mode", "text_mode", "subtitle_mode",
            "music_volume", "max_scenes", "intro_text", "outro_text",
        }
        result = dict(config)
        for key in config_keys:
            if key in template and (key not in result or not result[key]):
                result[key] = template[key]
        return result

    def get_sample_script(self, template_name: str) -> str:
        """Return the sample script for *template_name*, or empty string."""
        return self.get(template_name).get("sample_script", "")
