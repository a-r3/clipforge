"""Simple file-based cache for AI responses in ClipForge."""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_DEFAULT_CACHE_DIR = Path(".clipforge_cache")


class AICache:
    """Cache AI responses to avoid redundant API calls."""

    def __init__(self, cache_dir: str | Path = _DEFAULT_CACHE_DIR) -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _key(self, prompt: str) -> str:
        """Generate a cache key from the prompt."""
        return hashlib.sha256(prompt.encode("utf-8")).hexdigest()

    def _path(self, key: str) -> Path:
        return self.cache_dir / f"{key}.json"

    def get(self, prompt: str) -> dict[str, Any] | None:
        """Return cached response for *prompt*, or None if not cached."""
        path = self._path(self._key(prompt))
        if path.exists():
            try:
                with path.open("r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning("Cache read error: %s", exc)
        return None

    def set(self, prompt: str, response: dict[str, Any]) -> None:
        """Cache *response* for *prompt*."""
        path = self._path(self._key(prompt))
        try:
            with path.open("w", encoding="utf-8") as f:
                json.dump(response, f, indent=2, ensure_ascii=False)
        except OSError as exc:
            logger.warning("Cache write error: %s", exc)

    def clear(self) -> int:
        """Clear all cached responses. Returns the number of files deleted."""
        count = 0
        for f in self.cache_dir.glob("*.json"):
            try:
                f.unlink()
                count += 1
            except OSError:
                pass
        return count
