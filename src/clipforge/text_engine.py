"""Text engine for ClipForge.

Generates text overlays (subtitles and title cards) using Pillow for image
generation and MoviePy for compositing onto video clips.
"""

from __future__ import annotations

import logging
from typing import Any

from clipforge.constants import (
    TEXT_NONE,
    TEXT_SUBTITLE,
    TEXT_TITLE_CARDS,
    SUBTITLE_STATIC,
    SUBTITLE_TYPEWRITER,
    SUBTITLE_WORD_BY_WORD,
)

logger = logging.getLogger(__name__)

# Style defaults
_STYLE_DEFAULTS: dict[str, dict[str, Any]] = {
    "clean": {
        "font_size": 48,
        "font_color": "white",
        "bg_color": (0, 0, 0, 160),
        "stroke_color": "black",
        "stroke_width": 2,
        "position": ("center", 0.8),
    },
    "bold": {
        "font_size": 64,
        "font_color": "yellow",
        "bg_color": (0, 0, 0, 200),
        "stroke_color": "black",
        "stroke_width": 3,
        "position": ("center", 0.75),
    },
    "minimal": {
        "font_size": 40,
        "font_color": "white",
        "bg_color": (0, 0, 0, 80),
        "stroke_color": "black",
        "stroke_width": 1,
        "position": ("center", 0.85),
    },
    "cinematic": {
        "font_size": 52,
        "font_color": "white",
        "bg_color": (0, 0, 0, 180),
        "stroke_color": "black",
        "stroke_width": 2,
        "position": ("center", 0.80),
    },
}


class TextEngine:
    """Add text overlays to video clips.

    Supports subtitle and title_card modes with static, typewriter,
    and word-by-word animation.
    """

    def __init__(
        self,
        mode: str = TEXT_SUBTITLE,
        subtitle_mode: str = SUBTITLE_STATIC,
        style: str = "clean",
    ) -> None:
        self.mode = mode
        self.subtitle_mode = subtitle_mode
        self.style = style

    def add_text_overlay(self, clip: Any, scene: dict[str, Any], config: dict[str, Any]) -> Any:
        """Add a text overlay to *clip* for the given *scene*.

        Returns the modified clip. If text_mode is 'none' or text is empty,
        returns the original clip unchanged.
        """
        text_mode = config.get("text_mode", self.mode)
        if text_mode == TEXT_NONE:
            return clip

        text = scene.get("text", "")
        if not text:
            return clip

        subtitle_mode = config.get("subtitle_mode", self.subtitle_mode)
        style = config.get("style", self.style)
        style_cfg = _STYLE_DEFAULTS.get(style, _STYLE_DEFAULTS["clean"])

        try:
            if text_mode == TEXT_SUBTITLE:
                return self._add_subtitle(clip, text, subtitle_mode, style_cfg)
            elif text_mode == TEXT_TITLE_CARDS:
                return self._add_title_card(clip, text, style_cfg)
        except Exception as exc:
            logger.warning("Failed to add text overlay: %s", exc)

        return clip

    # ------------------------------------------------------------------
    # Private helpers — mockable in tests
    # ------------------------------------------------------------------

    def _add_subtitle(self, clip: Any, text: str, subtitle_mode: str, style_cfg: dict) -> Any:
        """Add subtitle text to clip according to subtitle_mode."""
        if subtitle_mode == SUBTITLE_STATIC:
            return self._static_subtitle(clip, text, style_cfg)
        elif subtitle_mode == SUBTITLE_TYPEWRITER:
            return self._typewriter_subtitle(clip, text, style_cfg)
        elif subtitle_mode == SUBTITLE_WORD_BY_WORD:
            return self._word_by_word_subtitle(clip, text, style_cfg)
        return self._static_subtitle(clip, text, style_cfg)

    def _static_subtitle(self, clip: Any, text: str, style_cfg: dict) -> Any:
        """Add a static subtitle to the clip."""
        txt_clip = self._make_text_clip(
            text=text,
            duration=clip.duration,
            font_size=style_cfg["font_size"],
            color=style_cfg["font_color"],
            stroke_color=style_cfg["stroke_color"],
            stroke_width=style_cfg["stroke_width"],
            width=clip.w,
        )
        position = style_cfg["position"]
        return self._composite_clips(clip, [txt_clip.set_position(position)])

    def _typewriter_subtitle(self, clip: Any, text: str, style_cfg: dict) -> Any:
        """Add a typewriter-effect subtitle (characters appear one by one)."""
        duration = clip.duration
        words = text.split()
        sub_clips = []
        chars_per_second = 20  # approximate typing speed

        for i in range(1, len(words) + 1):
            partial_text = " ".join(words[:i])
            start_time = (i - 1) * (duration / len(words))
            end_time = i * (duration / len(words))
            sub_clip = self._make_text_clip(
                text=partial_text,
                duration=end_time - start_time,
                font_size=style_cfg["font_size"],
                color=style_cfg["font_color"],
                stroke_color=style_cfg["stroke_color"],
                stroke_width=style_cfg["stroke_width"],
                width=clip.w,
            ).set_start(start_time)
            sub_clips.append(sub_clip.set_position(style_cfg["position"]))

        if not sub_clips:
            return clip
        return self._composite_clips(clip, sub_clips)

    def _word_by_word_subtitle(self, clip: Any, text: str, style_cfg: dict) -> Any:
        """Show one word at a time, centred on screen."""
        duration = clip.duration
        words = text.split()
        if not words:
            return clip

        word_duration = duration / len(words)
        sub_clips = []
        for i, word in enumerate(words):
            start_time = i * word_duration
            sub_clip = self._make_text_clip(
                text=word,
                duration=word_duration,
                font_size=style_cfg["font_size"] + 10,
                color=style_cfg["font_color"],
                stroke_color=style_cfg["stroke_color"],
                stroke_width=style_cfg["stroke_width"],
                width=clip.w,
            ).set_start(start_time)
            sub_clips.append(sub_clip.set_position(("center", "center")))

        return self._composite_clips(clip, sub_clips)

    def _add_title_card(self, clip: Any, text: str, style_cfg: dict) -> Any:
        """Add a full-screen title card that fades in."""
        txt_clip = self._make_text_clip(
            text=text,
            duration=clip.duration,
            font_size=style_cfg["font_size"] + 12,
            color=style_cfg["font_color"],
            stroke_color=style_cfg["stroke_color"],
            stroke_width=style_cfg["stroke_width"],
            width=clip.w,
        ).set_position(("center", "center"))

        return self._composite_clips(clip, [txt_clip])

    def _make_text_clip(
        self,
        text: str,
        duration: float,
        font_size: int,
        color: str,
        stroke_color: str,
        stroke_width: int,
        width: int,
    ) -> Any:
        """Create a MoviePy TextClip.  Isolated here for easy mocking."""
        from moviepy.editor import TextClip  # type: ignore[import]

        return TextClip(
            text,
            fontsize=font_size,
            color=color,
            stroke_color=stroke_color,
            stroke_width=stroke_width,
            method="caption",
            size=(width, None),
        ).set_duration(duration)

    def _composite_clips(self, base_clip: Any, overlay_clips: list[Any]) -> Any:
        """Composite overlay clips on top of base_clip."""
        from moviepy.editor import CompositeVideoClip  # type: ignore[import]

        return CompositeVideoClip([base_clip] + overlay_clips)


class SubtitleRenderer:
    """Legacy subtitle renderer stub (backward-compatible)."""

    def __init__(self, mode: str = "none", style: str = "clean") -> None:
        self.mode = mode
        self.style = style

    def render(self, scenes: list[str]) -> list[Any]:
        """Render text overlays for a list of scene text strings.

        Returns an empty list (use TextEngine for real overlay generation).
        """
        return []
