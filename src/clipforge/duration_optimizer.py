"""Intelligent scene duration optimizer for ClipForge.

Dynamically calculates optimal scene duration based on:
- Reading speed (NLP-based)
- Scene complexity
- Music tempo
- Pause detection
- Content type
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class DurationMetrics:
    """Duration analysis for a scene."""

    text: str
    word_count: int = 0
    sentence_count: int = 0
    reading_speed: float = 0.0  # words per second
    pause_count: int = 0
    complexity_score: float = 0.0  # 0-1: complex sentence structure
    recommended_duration: float = 0.0


class SceneDurationOptimizer:
    """Optimize scene durations for better pacing and engagement."""

    # Reading speeds (words per second) for different contexts
    _READING_SPEEDS = {
        "default": 2.5,  # Normal reading: ~150 wpm
        "fast": 3.5,  # ~210 wpm
        "slow": 1.8,  # ~108 wpm (emphasis, emotional)
        "technical": 2.0,  # Complex terms, slower
        "conversational": 2.8,  # Natural speech pace
    }

    # Pause multipliers based on punctuation
    _PAUSE_DURATION = {
        ".": 0.5,  # Period: 0.5s
        "!": 0.4,  # Exclamation: 0.4s
        "?": 0.6,  # Question: 0.6s
        ",": 0.2,  # Comma: 0.2s
        ":": 0.3,  # Colon: 0.3s
        ";": 0.4,  # Semicolon: 0.4s
    }

    # Content type adjustments
    _CONTENT_MULTIPLIERS = {
        "intro": 1.2,  # Intros: slightly longer for impact
        "hook": 1.1,  # Hooks: slightly longer for emphasis
        "call_to_action": 1.3,  # CTAs: much longer for readability
        "educational": 1.0,  # Educational: standard
        "motivational": 1.15,  # Motivational: moderate increase
        "humorous": 0.9,  # Humorous: faster pacing
    }

    def __init__(self) -> None:
        pass

    def analyze_scene(self, scene: dict[str, Any]) -> DurationMetrics:
        """Analyze scene text and return duration metrics."""
        text = scene.get("text", "")
        keywords = scene.get("keywords", [])

        word_count = len(text.split())
        sentence_count = self._count_sentences(text)
        pause_count = self._count_pauses(text)
        complexity = self._calculate_complexity(text)

        # Determine reading speed context
        reading_context = self._determine_reading_context(text, keywords)
        reading_speed = self._READING_SPEEDS.get(reading_context, 2.5)

        # Calculate base duration
        base_duration = self._calculate_base_duration(
            word_count, reading_speed, pause_count, sentence_count
        )

        # Apply content type multiplier
        content_type = scene.get("content_type", "educational")
        multiplier = self._CONTENT_MULTIPLIERS.get(content_type, 1.0)
        recommended_duration = base_duration * multiplier

        # Enforce minimum/maximum
        recommended_duration = max(2.0, min(15.0, recommended_duration))

        return DurationMetrics(
            text=text,
            word_count=word_count,
            sentence_count=sentence_count,
            reading_speed=reading_speed,
            pause_count=pause_count,
            complexity_score=complexity,
            recommended_duration=recommended_duration,
        )

    def optimize_batch_pacing(
        self, scenes: list[dict[str, Any]], target_total: float | None = None
    ) -> list[dict[str, Any]]:
        """Optimize pacing across multiple scenes for consistent flow.

        Args:
            scenes: List of scene dicts.
            target_total: Target total duration (optional). If set, normalize all scenes.

        Returns:
            Scenes with optimized durations.
        """
        metrics = [self.analyze_scene(scene) for scene in scenes]
        optimized_scenes = [dict(s) for s in scenes]

        if target_total is None:
            # Just apply individual optimizations
            for i, (opt_scene, metric) in enumerate(zip(optimized_scenes, metrics)):
                opt_scene["estimated_duration"] = metric.recommended_duration
            return optimized_scenes

        # Normalize to target total
        current_total = sum(m.recommended_duration for m in metrics)
        scale_factor = target_total / max(current_total, 0.1)

        for i, (opt_scene, metric) in enumerate(zip(optimized_scenes, metrics)):
            normalized = metric.recommended_duration * scale_factor
            # Keep within min/max bounds
            opt_scene["estimated_duration"] = max(2.0, min(15.0, normalized))

        return optimized_scenes

    def sync_with_music_tempo(
        self,
        scene_duration: float,
        music_bpm: float,
        music_beats_per_measure: int = 4,
    ) -> float:
        """Adjust scene duration to align with music tempo.

        Args:
            scene_duration: Current duration.
            music_bpm: Music tempo (beats per minute).
            music_beats_per_measure: Beats per measure (usually 4).

        Returns:
            Adjusted duration that aligns with musical phrases.
        """
        if music_bpm <= 0:
            return scene_duration

        # Calculate beat duration
        beat_duration = 60.0 / music_bpm

        # Snap to nearest musical phrase (usually 8 or 16 beats)
        phrase_duration = beat_duration * music_beats_per_measure * 2  # 8 beats default

        # Find closest multiple of phrase_duration
        closest_multiple = round(scene_duration / phrase_duration) * phrase_duration

        # Avoid extremely short or long durations
        return max(2.0, min(15.0, closest_multiple))

    # =====================================================================
    # Private helpers
    # =====================================================================

    @staticmethod
    def _count_sentences(text: str) -> int:
        """Count sentences by splitting on sentence boundaries."""
        sentences = re.split(r"[.!?]+", text)
        return max(1, len([s for s in sentences if s.strip()]))

    @staticmethod
    def _count_pauses(text: str) -> int:
        """Count pause points (punctuation)."""
        return sum(text.count(p) for p in ".!?,;:")

    @staticmethod
    def _calculate_complexity(text: str) -> float:
        """Calculate sentence complexity (0-1).

        Heuristic based on average word length and sentence length.
        """
        words = text.split()
        if not words:
            return 0.0

        avg_word_length = sum(len(w) for w in words) / len(words)
        avg_sentence_length = len(words) / max(1, len(text.split(".")))

        # Normalize to 0-1
        # Long words + long sentences = complex
        complexity = min(1.0, (avg_word_length + avg_sentence_length) / 20.0)
        return complexity

    def _determine_reading_context(self, text: str, keywords: list[str]) -> str:
        """Determine reading speed context based on content."""
        keyword_str = " ".join(keywords).lower()

        if any(kw in keyword_str for kw in ["tech", "api", "code", "algorithm"]):
            return "technical"

        if any(kw in keyword_str for kw in ["motivat", "inspire", "quote", "philos"]):
            return "slow"

        if any(kw in keyword_str for kw in ["joke", "funny", "humor", "laugh"]):
            return "fast"

        if any(kw in keyword_str for kw in ["question", "tutorial", "explain", "how"]):
            return "conversational"

        return "default"

    @staticmethod
    def _calculate_base_duration(
        word_count: int, reading_speed: float, pause_count: int, sentence_count: int
    ) -> float:
        """Calculate base duration from reading metrics."""
        # Reading time in seconds
        reading_time = word_count / reading_speed

        # Add pause time
        pause_time = pause_count * 0.3  # Average pause

        # Add inter-sentence gaps (natural speech rhythm)
        gap_time = sentence_count * 0.2

        total = reading_time + pause_time + gap_time

        # Ensure minimum display time (even for very short text)
        return max(2.0, total)

    @staticmethod
    def _get_music_metadata(
        music_file: str | None,
    ) -> dict[str, Any]:
        """Extract BPM and beat info from music file.

        Placeholder: in production, use librosa or audio analysis.
        """
        if not music_file:
            return {"bpm": 120, "beats_per_measure": 4}

        # Simplified: return default values
        # In production: use ffprobe + librosa for actual tempo detection
        return {"bpm": 120, "beats_per_measure": 4}
