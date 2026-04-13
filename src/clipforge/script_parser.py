"""Script parser for ClipForge.

Splits a text script into scenes with metadata including estimated duration,
keywords, and visual intent heuristics.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from clipforge.constants import DEFAULT_MAX_SCENES
from clipforge.utils import estimate_read_time, extract_keywords


@dataclass
class Scene:
    """A single parsed scene."""

    text: str
    index: int = 0
    estimated_duration: float = 0.0
    keywords: list[str] = field(default_factory=list)
    visual_intent: str = "abstract"

    def to_dict(self) -> dict[str, Any]:
        """Convert scene to a plain dict."""
        return {
            "index": self.index,
            "text": self.text,
            "estimated_duration": self.estimated_duration,
            "keywords": self.keywords,
            "visual_intent": self.visual_intent,
        }


# Keyword heuristics for visual_intent
_VISUAL_KEYWORDS: dict[str, list[str]] = {
    "technology": [
        "tech", "technology", "ai", "artificial", "intelligence", "digital",
        "software", "computer", "data", "algorithm", "automation", "robot",
        "machine", "learning", "neural", "internet", "online", "cyber",
        "cloud", "app", "code", "coding", "programming", "developer",
    ],
    "business": [
        "business", "company", "market", "revenue", "profit", "sales",
        "customer", "client", "brand", "strategy", "growth", "startup",
        "entrepreneur", "investment", "finance", "economy", "industry",
        "corporate", "organization", "management", "leadership",
    ],
    "people": [
        "people", "team", "community", "family", "friends", "social",
        "human", "person", "individual", "group", "society", "culture",
        "collaboration", "diversity", "inclusion", "relationship",
    ],
    "city": [
        "city", "urban", "street", "building", "architecture", "downtown",
        "metro", "skyline", "traffic", "infrastructure", "neighborhood",
    ],
    "nature": [
        "nature", "outdoor", "green", "forest", "mountain", "ocean",
        "water", "sky", "plant", "animal", "environment", "sustainable",
        "earth", "tree", "river", "landscape",
    ],
}


def _detect_visual_intent(text: str) -> str:
    """Detect visual intent from text using keyword heuristics."""
    text_lower = text.lower()
    words = re.findall(r"\b\w+\b", text_lower)
    word_set = set(words)

    scores: dict[str, int] = {vtype: 0 for vtype in _VISUAL_KEYWORDS}
    for vtype, keywords in _VISUAL_KEYWORDS.items():
        for kw in keywords:
            if kw in word_set:
                scores[vtype] += 1

    best = max(scores, key=lambda k: scores[k])
    if scores[best] == 0:
        return "abstract"
    return best


def _split_into_sentences(text: str) -> list[str]:
    """Split text into sentences using regex."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if s.strip()]


def _word_count(text: str) -> int:
    """Return the number of words in *text*."""
    return len(text.split())


class ScriptParser:
    """Parse a text script into a list of Scene objects."""

    def __init__(self, max_scenes: int = DEFAULT_MAX_SCENES, min_words: int = 10) -> None:
        self.max_scenes = max_scenes
        self.min_words = min_words

    def parse(self, text: str) -> list[Scene]:
        """Parse *text* into scenes.

        Algorithm:
        1. Split on blank lines (paragraph boundaries).
        2. Within each paragraph, split further by sentence boundaries if the
           paragraph is long.
        3. Merge tiny fragments (< min_words) into the adjacent scene.
        4. Enforce max_scenes limit.
        5. Add metadata to each scene.

        Returns a list of Scene objects.
        """
        if not text or not text.strip():
            return []

        raw_paragraphs = re.split(r"\n\s*\n", text.strip())
        raw_paragraphs = [p.strip() for p in raw_paragraphs if p.strip()]

        chunks: list[str] = []
        for paragraph in raw_paragraphs:
            sentences = _split_into_sentences(paragraph)
            current_chunk = ""
            for sentence in sentences:
                candidate = (current_chunk + " " + sentence).strip()
                # Keep sentences together if combined word count < 50
                if _word_count(candidate) < 50 or not current_chunk:
                    current_chunk = candidate
                else:
                    if current_chunk:
                        chunks.append(current_chunk)
                    current_chunk = sentence
            if current_chunk:
                chunks.append(current_chunk)

        # Merge tiny fragments into adjacent chunks
        merged: list[str] = []
        for chunk in chunks:
            if _word_count(chunk) < self.min_words and merged:
                # Append to previous chunk
                merged[-1] = merged[-1] + " " + chunk
            else:
                merged.append(chunk)

        # Final pass: if last chunk is still tiny, merge it back
        if len(merged) >= 2 and _word_count(merged[-1]) < self.min_words:
            merged[-2] = merged[-2] + " " + merged[-1]
            merged = merged[:-1]

        # First pass: if first chunk is tiny, merge it forward
        if len(merged) >= 2 and _word_count(merged[0]) < self.min_words:
            merged[1] = merged[0] + " " + merged[1]
            merged = merged[1:]

        # Enforce max scenes
        if len(merged) > self.max_scenes:
            # Merge excess scenes into the last allowed scene
            tail = " ".join(merged[self.max_scenes - 1:])
            merged = merged[: self.max_scenes - 1] + [tail]

        # Build Scene objects with metadata
        scenes: list[Scene] = []
        for i, chunk in enumerate(merged):
            keywords = extract_keywords(chunk)
            visual_intent = _detect_visual_intent(chunk)
            duration = estimate_read_time(chunk)
            scenes.append(
                Scene(
                    text=chunk,
                    index=i,
                    estimated_duration=duration,
                    keywords=keywords,
                    visual_intent=visual_intent,
                )
            )

        return scenes


# Module-level convenience function
def split_script_into_scenes(script: str, max_scenes: int = DEFAULT_MAX_SCENES) -> list[dict[str, Any]]:
    """Parse *script* and return a list of scene dicts.

    This is a convenience wrapper around ScriptParser for backward compatibility.
    """
    parser = ScriptParser(max_scenes=max_scenes)
    return [s.to_dict() for s in parser.parse(script)]
