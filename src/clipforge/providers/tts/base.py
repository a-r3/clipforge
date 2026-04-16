"""Abstract base class for TTS (text-to-speech) providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class TTSResult:
    """Result from a TTS synthesis request."""

    audio_path: str | None = None
    duration_seconds: float = 0.0
    provider: str = ""
    language: str = "en"
    voice: str = ""

    @property
    def success(self) -> bool:
        """True if audio was generated."""
        return self.audio_path is not None


class TTSProvider(ABC):
    """Abstract base class for TTS providers.

    Implementations convert text to a local audio file and return a
    ``TTSResult``.

    Current built-in implementation: ``Pyttsx3Provider`` (uses pyttsx3).
    Future implementations could add ElevenLabs, Google TTS, OpenAI TTS, etc.

    Usage::

        class ElevenLabsProvider(TTSProvider):
            def synthesize(self, text, output_path, language="en", voice=None):
                ...

        result = ElevenLabsProvider(api_key="...").synthesize(
            "Hello world", "/tmp/hello.mp3"
        )
        if result.success:
            use(result.audio_path)
    """

    def __init__(self, api_key: str = "", language: str = "en") -> None:
        self.api_key = api_key
        self.language = language

    @abstractmethod
    def synthesize(
        self,
        text: str,
        output_path: str,
        language: str | None = None,
        voice: str | None = None,
    ) -> TTSResult:
        """Synthesize *text* to audio and save it at *output_path*.

        Args:
            text:        The text to synthesize.
            output_path: Local file path to write the audio to.
            language:    BCP-47 language code (e.g. 'en', 'es').
                         Falls back to ``self.language`` if None.
            voice:       Optional provider-specific voice ID.

        Returns:
            ``TTSResult`` — check ``.success`` before using ``.audio_path``.
        """

    def is_available(self) -> bool:
        """Return True if this provider can synthesize audio."""
        return True  # local providers are always available; override for API ones

    def __repr__(self) -> str:
        cls = type(self).__name__
        return f"{cls}(language={self.language!r})"
