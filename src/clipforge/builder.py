"""Video builder for ClipForge.

Assembles scenes into a final MP4 video using MoviePy + FFmpeg.
All MoviePy calls are isolated in small methods to allow mocking in tests.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from clipforge.constants import DEFAULT_PLATFORM
from clipforge.utils import ensure_dir, get_platform_spec
from clipforge.text_engine import TextEngine
from clipforge.audio_engine import AudioEngine

logger = logging.getLogger(__name__)

# Fallback solid-colour background colours per visual type
_BG_COLORS: dict[str, tuple[int, int, int]] = {
    "technology": (10, 10, 30),
    "business": (20, 20, 40),
    "people": (30, 15, 15),
    "city": (15, 15, 25),
    "nature": (10, 30, 10),
    "abstract": (20, 20, 20),
}


@dataclass
class BuildSummary:
    """Statistics returned after a successful build."""

    scene_count: int = 0
    stock_hits: int = 0
    fallbacks: int = 0
    total_duration: float = 0.0
    output_path: str = ""
    audio_mode: str = ""
    text_mode: str = ""
    subtitle_mode: str = ""
    stock_sources: list[str] = field(default_factory=list)

    def print(self) -> None:
        """Print a human-readable summary to stdout."""
        line = "-" * 48
        print(line)
        print("  Build complete")
        print(line)
        print(f"  Scenes          : {self.scene_count}")
        print(f"  Stock hits      : {self.stock_hits}")
        print(f"  Fallbacks       : {self.fallbacks}")
        print(f"  Total duration  : {self.total_duration:.1f}s")
        print(f"  Audio mode      : {self.audio_mode}")
        print(f"  Text mode       : {self.text_mode}")
        print(f"  Subtitle mode   : {self.subtitle_mode}")
        print(f"  Output          : {self.output_path}")
        print(line)


class VideoBuilder:
    """Assemble video clips into a final MP4."""

    def __init__(self) -> None:
        self._text_engine = TextEngine()
        self._audio_engine = AudioEngine()

    def build(
        self,
        scenes: list[dict[str, Any]],
        config: dict[str, Any],
        output_path: str | Path,
    ) -> BuildSummary:
        """Build the video from *scenes* using *config* and write to *output_path*.

        Args:
            scenes: List of planned scene dicts (from ScenePlanner).
            config: Full config dict.
            output_path: Where to write the MP4.

        Returns:
            BuildSummary with render statistics.
        """
        output_path = Path(output_path)
        ensure_dir(output_path.parent)

        platform = config.get("platform", DEFAULT_PLATFORM)
        spec = get_platform_spec(platform)
        width, height = spec["width"], spec["height"]
        fps = spec["fps"]

        # Optionally fetch stock media
        scenes = self._attach_stock_media(scenes, config, width, height)

        # Build individual scene clips
        if not scenes:
            raise ValueError("No scenes to build video from.")

        stock_hits = 0
        fallbacks = 0
        sources: list[str] = []
        total_duration = 0.0
        video_clips = []

        for scene in scenes:
            clip = self._build_scene_clip(scene, width, height, config)
            video_clips.append(clip)
            total_duration += scene.get("duration", 3.0)
            src = scene.get("_media_source", "fallback")
            sources.append(src)
            if src == "fallback":
                fallbacks += 1
            else:
                stock_hits += 1

        # Concatenate all scene clips
        final_clip = self._concatenate_clips(video_clips)

        # Build and attach audio
        audio = self._audio_engine.build_audio(scenes, config)
        if audio is not None:
            final_clip = final_clip.set_audio(audio)

        # Add intro/outro text overlays if configured
        intro_text = config.get("intro_text", "")
        outro_text = config.get("outro_text", "")
        if intro_text or outro_text:
            final_clip = self._add_intro_outro(final_clip, intro_text, outro_text, config)

        # Write final video
        self._write_videofile(final_clip, str(output_path), fps)

        logger.info("Video written to %s", output_path)

        return BuildSummary(
            scene_count=len(scenes),
            stock_hits=stock_hits,
            fallbacks=fallbacks,
            total_duration=total_duration,
            output_path=str(output_path),
            audio_mode=config.get("audio_mode", "silent"),
            text_mode=config.get("text_mode", "none"),
            subtitle_mode=config.get("subtitle_mode", "static"),
            stock_sources=sources,
        )

    # ------------------------------------------------------------------
    # Stock media attachment
    # ------------------------------------------------------------------

    def _attach_stock_media(
        self,
        scenes: list[dict[str, Any]],
        config: dict[str, Any],
        width: int,
        height: int,
    ) -> list[dict[str, Any]]:
        """Attempt to attach stock media paths to each scene dict.

        Emits warnings if API keys are missing. Scenes with no media
        found get ``asset_path = ""`` and ``_media_source = "fallback"``.
        """
        from clipforge.media_fetcher import MediaFetcher

        fetcher = MediaFetcher(
            pexels_key=config.get("pexels_api_key", ""),
            pixabay_key=config.get("pixabay_api_key", ""),
        )

        # Warn once per missing key
        for warning in fetcher.warn_if_no_keys():
            logger.warning(warning)

        updated: list[dict[str, Any]] = []
        for scene in scenes:
            scene = dict(scene)
            if not scene.get("asset_path"):
                path, source = fetcher.fetch_for_scene(scene, width, height)
                scene["asset_path"] = path or ""
                scene["_media_source"] = source
            else:
                scene.setdefault("_media_source", "pre_loaded")
            updated.append(scene)

        return updated

    # ------------------------------------------------------------------
    # Private helpers — isolated for easy mocking in tests
    # ------------------------------------------------------------------

    def _build_scene_clip(
        self,
        scene: dict[str, Any],
        width: int,
        height: int,
        config: dict[str, Any],
    ) -> Any:
        """Build a single scene clip from a scene dict."""
        duration = scene.get("duration", 3.0)

        # Try to load a video/image asset; fall back to solid colour
        clip = self._load_or_create_clip(scene, width, height, duration)

        # Add text overlay
        clip = self._text_engine.add_text_overlay(clip, scene, config)

        return clip

    def _load_or_create_clip(
        self,
        scene: dict[str, Any],
        width: int,
        height: int,
        duration: float,
    ) -> Any:
        """Load a media asset for the scene, or create a solid-colour fallback."""
        asset_path = scene.get("asset_path", "")
        visual_type = scene.get("visual_type", "abstract")
        color = _BG_COLORS.get(visual_type, (20, 20, 20))

        if asset_path and os.path.exists(asset_path):
            try:
                return self._load_video_clip(asset_path, duration, width, height)
            except Exception as exc:
                logger.warning("Failed to load asset %s: %s — using fallback", asset_path, exc)

        # Fallback to solid colour background
        return self._create_color_clip(color, duration, width, height)

    def _load_video_clip(self, path: str, duration: float, width: int, height: int) -> Any:
        """Load a VideoFileClip and crop/resize to fill the frame."""
        from moviepy.editor import VideoFileClip  # type: ignore[import]

        clip = VideoFileClip(path)
        clip = self._resize_and_crop(clip, width, height)
        if clip.duration > duration:
            clip = clip.subclip(0, duration)
        elif clip.duration < duration:
            from moviepy.video.fx.all import loop  # type: ignore[import]
            clip = loop(clip, duration=duration)
        return clip

    def _create_color_clip(
        self,
        color: tuple[int, int, int],
        duration: float,
        width: int,
        height: int,
    ) -> Any:
        """Create a solid-colour video clip."""
        from moviepy.editor import ColorClip  # type: ignore[import]

        return ColorClip(size=(width, height), color=color, duration=duration)

    def _resize_and_crop(self, clip: Any, width: int, height: int) -> Any:
        """Resize and centre-crop a clip to fill (width, height)."""
        cw, ch = clip.w, clip.h
        target_ratio = width / height
        clip_ratio = cw / ch

        if clip_ratio > target_ratio:
            new_height = height
            new_width = int(cw * height / ch)
        else:
            new_width = width
            new_height = int(ch * width / cw)

        clip = clip.resize((new_width, new_height))
        x1 = (new_width - width) // 2
        y1 = (new_height - height) // 2
        return clip.crop(x1=x1, y1=y1, x2=x1 + width, y2=y1 + height)

    def _concatenate_clips(self, clips: list[Any]) -> Any:
        """Concatenate a list of video clips."""
        from moviepy.editor import concatenate_videoclips  # type: ignore[import]

        return concatenate_videoclips(clips, method="compose")

    def _add_intro_outro(
        self,
        clip: Any,
        intro_text: str,
        outro_text: str,
        config: dict[str, Any],
    ) -> Any:
        """Add intro and/or outro text overlays (future: prepend/append clips)."""
        return clip

    def _write_videofile(self, clip: Any, output_path: str, fps: int) -> None:
        """Write the clip to an MP4 file using H.264/AAC."""
        clip.write_videofile(
            output_path,
            fps=fps,
            codec="libx264",
            audio_codec="aac",
            logger=None,
        )


# Module-level convenience function
def make_video(
    script: str,
    out_name: str = "final.mp4",
    voiceover_path: str | None = None,
) -> BuildSummary:
    """Build a video from a script (convenience function).

    Returns a BuildSummary with render statistics.
    """
    from clipforge.script_parser import ScriptParser
    from clipforge.scene_planner import ScenePlanner
    from clipforge.config_loader import load_config

    config = load_config()
    config["output"] = out_name
    if voiceover_path:
        config["voiceover_path"] = voiceover_path

    parser = ScriptParser()
    scenes = [s.to_dict() for s in parser.parse(script)]

    planner = ScenePlanner()
    planned_scenes = planner.plan(scenes)

    builder = VideoBuilder()
    return builder.build(planned_scenes, config, out_name)
