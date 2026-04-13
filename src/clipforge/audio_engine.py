"""Audio engine for ClipForge.

Handles all audio generation: silent, music-only, voiceover-only,
and voiceover+music with ducking. Uses pyttsx3 for local TTS.
"""

from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path
from typing import Any

from clipforge.constants import (
    AUDIO_SILENT,
    AUDIO_MUSIC,
    AUDIO_VOICEOVER,
    AUDIO_VOICEOVER_MUSIC,
)

logger = logging.getLogger(__name__)


class AudioEngine:
    """Build audio tracks for ClipForge videos.

    Supports four modes:
    - ``silent``: no audio
    - ``music``: background music only
    - ``voiceover``: TTS voiceover only
    - ``voiceover+music``: TTS + music with ducking
    """

    def __init__(
        self,
        mode: str = AUDIO_SILENT,
        music_file: str = "",
        music_volume: float = 0.12,
        voice_language: str = "en",
        voice_rate: int = 150,
    ) -> None:
        self.mode = mode
        self.music_file = music_file
        self.music_volume = music_volume
        self.voice_language = voice_language
        self.voice_rate = voice_rate

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build_audio(self, scenes: list[dict[str, Any]], config: dict[str, Any]) -> Any:
        """Build and return an audio clip (or None for silent mode).

        This method orchestrates TTS generation and music loading.
        Actual MoviePy calls are delegated to _create_moviepy_audio so they
        can be mocked in tests.

        Args:
            scenes: List of scene dicts (must have 'text' and 'estimated_duration').
            config: Full config dict.

        Returns:
            A MoviePy audio clip, or None for silent mode.
        """
        mode = config.get("audio_mode", self.mode)

        if mode == AUDIO_SILENT:
            return None

        voiceover_clip = None
        music_clip = None

        if mode in (AUDIO_VOICEOVER, AUDIO_VOICEOVER_MUSIC):
            voiceover_clip = self._build_voiceover(scenes, config)

        if mode in (AUDIO_MUSIC, AUDIO_VOICEOVER_MUSIC):
            music_file = config.get("music_file", self.music_file)
            music_clip = self._load_music(music_file, config)

        return self._mix_audio(voiceover_clip, music_clip, mode, config)

    def render(self, duration: float = 0.0) -> None:
        """Legacy stub: render audio according to mode. Returns None."""
        return None

    # ------------------------------------------------------------------
    # Private helpers — designed to be mockable in tests
    # ------------------------------------------------------------------

    def _build_voiceover(self, scenes: list[dict[str, Any]], config: dict[str, Any]) -> Any:
        """Generate TTS voiceover for all scenes. Returns an audio clip or None."""
        try:
            return self._generate_tts(scenes, config)
        except Exception as exc:
            logger.warning("TTS failed, falling back to no voiceover: %s", exc)
            return None

    def _generate_tts(self, scenes: list[dict[str, Any]], config: dict[str, Any]) -> Any:
        """Use pyttsx3 to generate TTS and return a path to the audio file."""
        import pyttsx3  # lazy import

        engine = pyttsx3.init()
        rate = config.get("voice_rate", self.voice_rate)
        engine.setProperty("rate", rate)

        texts = [s.get("text", "") for s in scenes if s.get("text")]
        full_text = " ".join(texts)

        if not full_text.strip():
            return None

        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp_path = tmp.name
        tmp.close()

        engine.save_to_file(full_text, tmp_path)
        engine.runAndWait()

        return self._load_audio_file(tmp_path)

    def _load_music(self, music_file: str, config: dict[str, Any]) -> Any:
        """Load a music file and return an audio clip or None."""
        if not music_file:
            logger.warning("No music_file specified in config.")
            return None
        if not os.path.exists(music_file):
            logger.warning("Music file not found: %s", music_file)
            return None
        try:
            return self._load_audio_file(music_file)
        except Exception as exc:
            logger.warning("Failed to load music file %s: %s", music_file, exc)
            return None

    def _load_audio_file(self, path: str) -> Any:
        """Load an audio file using MoviePy and return an AudioFileClip."""
        from moviepy.editor import AudioFileClip  # type: ignore[import]
        return AudioFileClip(path)

    def _mix_audio(
        self,
        voiceover: Any,
        music: Any,
        mode: str,
        config: dict[str, Any],
    ) -> Any:
        """Mix voiceover and music clips according to mode."""
        volume = config.get("music_volume", self.music_volume)

        if mode == AUDIO_MUSIC:
            if music is None:
                return None
            return music.volumex(volume)

        if mode == AUDIO_VOICEOVER:
            return voiceover

        if mode == AUDIO_VOICEOVER_MUSIC:
            if voiceover is None and music is None:
                return None
            if voiceover is None:
                return music.volumex(volume) if music else None
            if music is None:
                return voiceover
            # Duck music under voiceover
            ducked_music = music.volumex(volume * 0.4)
            return self._composite_audio([voiceover, ducked_music])

        return None

    def _composite_audio(self, clips: list[Any]) -> Any:
        """Composite multiple audio clips using MoviePy."""
        from moviepy.editor import CompositeAudioClip  # type: ignore[import]
        return CompositeAudioClip(clips)
