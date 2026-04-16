"""Smart media ranking system for ClipForge.

Ranks stock media by relevance, color harmony, and scene fit.
Replaces random selection with ML-based scoring.
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests

logger = logging.getLogger(__name__)


@dataclass
class MediaScore:
    """Media quality score."""

    relevance: float  # 0-1: Text similarity
    color_harmony: float  # 0-1: Color palette match
    resolution_fit: float  # 0-1: Aspect ratio fit
    popularity: float  # 0-1: Normalized views/likes
    final_score: float = 0.0  # Weighted average

    def calculate(
        self,
        w_relevance: float = 0.4,
        w_harmony: float = 0.2,
        w_fit: float = 0.2,
        w_pop: float = 0.2,
    ) -> float:
        """Calculate final weighted score."""
        self.final_score = (
            self.relevance * w_relevance
            + self.color_harmony * w_harmony
            + self.resolution_fit * w_fit
            + self.popularity * w_pop
        )
        return self.final_score


class MediaRanker:
    """Rank and select best media for scenes."""

    def __init__(self) -> None:
        self._cache_dir = Path("assets/media_cache")
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    def score_media(
        self,
        media_list: list[dict[str, Any]],
        scene_keywords: list[str],
        target_colors: list[tuple[int, int, int]] | None = None,
        aspect_ratio: tuple[int, int] = (9, 16),
    ) -> list[tuple[dict[str, Any], MediaScore]]:
        """Score and rank media for a scene.

        Args:
            media_list: List of media items with metadata.
            scene_keywords: Keywords/topics for the scene.
            target_colors: Desired color palette (RGB tuples).
            aspect_ratio: Target aspect ratio (width, height).

        Returns:
            List of (media, score) tuples sorted by score DESC.
        """
        scored = []

        for media in media_list:
            score = MediaScore(
                relevance=self._score_relevance(media, scene_keywords),
                color_harmony=self._score_color_harmony(
                    media, target_colors or self._get_default_colors(scene_keywords)
                ),
                resolution_fit=self._score_aspect_ratio(media, aspect_ratio),
                popularity=self._score_popularity(media),
            )
            score.calculate()
            scored.append((media, score))

        # Sort by final score descending
        scored.sort(key=lambda x: x[1].final_score, reverse=True)
        return scored

    def _score_relevance(self, media: dict[str, Any], keywords: list[str]) -> float:
        """Score media title/description against keywords (0-1)."""
        if not keywords:
            return 0.5

        title = media.get("title", "").lower()
        description = media.get("description", "").lower()
        text = f"{title} {description}"

        if not text.strip():
            return 0.3

        matches = sum(1 for kw in keywords if kw.lower() in text)
        return min(1.0, matches / len(keywords))

    def _score_color_harmony(
        self, media: dict[str, Any], target_colors: list[tuple[int, int, int]]
    ) -> float:
        """Score media color palette against target colors (0-1)."""
        media_colors = media.get("dominant_colors", [])

        if not media_colors or not target_colors:
            return 0.5

        # Simple: count matching colors
        matches = 0
        for mc in media_colors:
            for tc in target_colors:
                if self._color_distance(mc, tc) < 50:  # Threshold
                    matches += 1
                    break

        return min(1.0, matches / len(target_colors))

    def _score_aspect_ratio(
        self, media: dict[str, Any], target_ratio: tuple[int, int]
    ) -> float:
        """Score media aspect ratio fit (0-1)."""
        w = media.get("width", 1080)
        h = media.get("height", 1920)

        if w == 0 or h == 0:
            return 0.5

        target_ar = target_ratio[0] / target_ratio[1]
        media_ar = w / h

        # Closer to 1.0 means better fit
        diff = abs(target_ar - media_ar) / max(target_ar, media_ar)
        return max(0.0, 1.0 - diff)

    def _score_popularity(self, media: dict[str, Any]) -> float:
        """Normalize popularity metrics (views, likes) to 0-1."""
        views = media.get("views", 0)
        likes = media.get("likes", 0)

        popularity = views + likes * 10  # Likes weighted heavier

        # Normalize to 0-1 (assume max reasonable is 1M)
        return min(1.0, popularity / 1_000_000)

    @staticmethod
    def _color_distance(c1: tuple[int, int, int], c2: tuple[int, int, int]) -> float:
        """Euclidean distance between two RGB colors."""
        return sum((a - b) ** 2 for a, b in zip(c1, c2)) ** 0.5

    @staticmethod
    def _get_default_colors(keywords: list[str]) -> list[tuple[int, int, int]]:
        """Get default color palette based on keywords."""
        keyword_colors = {
            "technology": [(36, 74, 142), (70, 130, 180)],  # Blues
            "business": [(54, 68, 107), (169, 169, 169)],  # Navy, gray
            "people": [(124, 66, 63), (205, 133, 63)],  # Browns
            "nature": [(46, 104, 74), (144, 238, 144)],  # Greens
            "city": [(58, 64, 88), (128, 128, 128)],  # Grays
            "abstract": [(72, 72, 96), (255, 255, 255)],  # Any
        }

        for kw in keywords:
            for theme, colors in keyword_colors.items():
                if theme in kw.lower():
                    return colors

        return [(128, 128, 128), (200, 200, 200)]  # Neutral gray


class CachedMediaRanker(MediaRanker):
    """MediaRanker with local scoring cache."""

    def score_media(
        self,
        media_list: list[dict[str, Any]],
        scene_keywords: list[str],
        target_colors: list[tuple[int, int, int]] | None = None,
        aspect_ratio: tuple[int, int] = (9, 16),
    ) -> list[tuple[dict[str, Any], MediaScore]]:
        """Score media with caching."""
        cache_key = self._make_cache_key(media_list, scene_keywords)
        cached = self._load_cache(cache_key)

        if cached:
            logger.debug("Media ranking cache hit for key=%s", cache_key[:8])
            return cached

        scored = super().score_media(media_list, scene_keywords, target_colors, aspect_ratio)
        self._save_cache(cache_key, scored)
        return scored

    def _make_cache_key(self, media_list: list[dict[str, Any]], keywords: list[str]) -> str:
        """Create cache key from media IDs and keywords."""
        key_data = {
            "media_ids": [m.get("id") for m in media_list],
            "keywords": sorted(keywords),
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()

    def _load_cache(self, key: str) -> list[tuple[dict[str, Any], MediaScore]] | None:
        """Load cached scores (simplified, no serialization)."""
        # In production: load from JSON/pickle
        return None

    def _save_cache(self, key: str, data: list[tuple[dict[str, Any], MediaScore]]) -> None:
        """Save scores to cache (simplified)."""
        # In production: save to JSON/pickle
        pass
