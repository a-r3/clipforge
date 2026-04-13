"""
Preset utilities.

This module loads preset definitions from JSON files located in the `data`
directory. Presets include platform definitions (resolution, aspect ratio)
and visual styles (font sizes, colours). The functions return native Python
structures for easy consumption by CLI commands and builders.
"""

import json
from pathlib import Path
from typing import Dict, Any, List


DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def load_presets() -> Dict[str, Any]:
    """
    Load the presets JSON file. The file combines both platform and style
    definitions.

    :return: A dictionary with keys `platforms` and `styles`.
    """
    with open(DATA_DIR / "presets.json", "r", encoding="utf-8") as f:
        return json.load(f)


def list_platforms() -> List[str]:
    """
    Return a list of supported platform names.
    """
    data = load_presets()
    return [p["name"] for p in data.get("platforms", [])]


def list_styles() -> List[str]:
    """
    Return a list of supported style names.
    """
    data = load_presets()
    return [s["name"] for s in data.get("styles", [])]
