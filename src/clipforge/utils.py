"""Utility functions for ClipForge."""

from __future__ import annotations

import json
import math
import os
import re
from pathlib import Path
from typing import Any

from clipforge.constants import PLATFORM_SPECS, DEFAULT_WPM


def slugify(text: str) -> str:
    """Convert text to a filename-safe slug.

    Example: "How AI Changes Business!" -> "how-ai-changes-business"
    """
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def ensure_dir(path: str | Path) -> Path:
    """Create a directory and all parents if it does not exist.

    Returns the Path object.
    """
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def merge_dicts(base: dict, override: dict) -> dict:
    """Deep-merge two dicts. Values in *override* take precedence.

    Nested dicts are merged recursively; other values are overwritten.
    """
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value
    return result


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp *value* to the range [min_val, max_val]."""
    return max(min_val, min(max_val, value))


def format_duration(seconds: float) -> str:
    """Format a duration in seconds as MM:SS.

    Example: 75.3 -> "1:15"
    """
    total = int(seconds)
    minutes = total // 60
    secs = total % 60
    return f"{minutes}:{secs:02d}"


def estimate_read_time(text: str, wpm: int = DEFAULT_WPM) -> float:
    """Estimate how many seconds it takes to read *text* aloud at *wpm* words per minute.

    Minimum 1.0 seconds.
    """
    words = len(text.split())
    minutes = words / wpm
    seconds = minutes * 60
    return max(1.0, round(seconds, 2))


def load_json(path: str | Path) -> Any:
    """Load and return JSON data from *path*.

    Returns an empty dict if the file does not exist or cannot be parsed.
    """
    p = Path(path)
    if not p.exists():
        return {}
    try:
        with p.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_json(data: Any, path: str | Path, indent: int = 2) -> None:
    """Save *data* as JSON to *path*, creating parent directories as needed."""
    p = Path(path)
    ensure_dir(p.parent)
    with p.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


def get_platform_spec(platform: str) -> dict:
    """Return the platform specification dict for *platform*.

    Falls back to reels spec if platform is unknown.
    """
    from clipforge.constants import DEFAULT_PLATFORM
    return PLATFORM_SPECS.get(platform, PLATFORM_SPECS[DEFAULT_PLATFORM])


def extract_keywords(text: str, max_keywords: int = 8) -> list[str]:
    """Extract simple keywords from text by removing stop words.

    Returns a list of lowercase words.
    """
    stop_words = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to",
        "for", "of", "with", "by", "from", "is", "are", "was", "were",
        "be", "been", "being", "have", "has", "had", "do", "does", "did",
        "will", "would", "could", "should", "may", "might", "shall", "can",
        "it", "its", "this", "that", "these", "those", "i", "we", "you",
        "he", "she", "they", "me", "us", "him", "her", "them", "my", "our",
        "your", "his", "their", "what", "which", "who", "when", "where",
        "how", "why", "as", "if", "so", "not", "no", "more", "also",
        "over", "under", "into", "out", "up", "down", "about", "after",
        "before", "between", "through", "during", "without", "within",
        "just", "than", "then", "than", "each", "every", "all", "both",
    }
    words = re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())
    keywords = [w for w in words if w not in stop_words]
    # Deduplicate while preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for w in keywords:
        if w not in seen:
            seen.add(w)
            unique.append(w)
    return unique[:max_keywords]
