"""Premium Text-to-Speech Engine for ClipForge.

Replaces pyttsx3 (robotic) with professional TTS providers:
- Google Cloud Text-to-Speech
- Azure Speech Services
- Multiple voices and languages
- Emotion/rate control
- Professional voice quality
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class TTSProvider(Enum):
    """TTS provider options."""

    GOOGLE = "google"
    AZURE = "azure"
    PYTTSX3 = "pyttsx3"  # Fallback


class SpeechGender(Enum):
    """Speaker gender."""

    MALE = "MALE"
    FEMALE = "FEMALE"
    NEUTRAL = "NEUTRAL"


class SpeechRate(Enum):
    """Speech rate/speed."""

    SLOW = 0.75
    NORMAL = 1.0
    FAST = 1.25
    VERY_FAST = 1.5


class AudioEncoding(Enum):
    """Audio encoding format."""

    MP3 = "MP3"
    OGG = "OGG_OPUS"
    WAV = "LINEAR16"
    ALAW = "ALAW"
    ULAW = "ULAW"


@dataclass
class VoiceConfig:
    """Voice configuration."""

    provider: TTSProvider
    language_code: str  # "en-US", "es-ES", etc
    voice_name: str  # "en-US-Neural2-A", "es-ES-Neural2-A", etc
    gender: SpeechGender
    speech_rate: float  # 0.25 to 4.0
    pitch: float  # -20.0 to 20.0 (semitones)


@dataclass
class TTSRequest:
    """Text-to-speech request."""

    text: str
    voice_config: VoiceConfig
    output_path: Path
    audio_encoding: AudioEncoding = AudioEncoding.MP3


@dataclass
class TTSResult:
    """TTS synthesis result."""

    success: bool
    audio_path: Optional[Path]
    duration_sec: float
    file_size_bytes: int
    error: Optional[str] = None


class GoogleCloudTTS:
    """Google Cloud Text-to-Speech provider."""

    # Popular voices by language
    VOICES = {
        "en-US": {
            "male": "en-US-Neural2-A",
            "female": "en-US-Neural2-C",
            "neutral": "en-US-Neural2-E",
        },
        "es-ES": {
            "male": "es-ES-Neural2-A",
            "female": "es-ES-Neural2-B",
        },
        "fr-FR": {
            "male": "fr-FR-Neural2-A",
            "female": "fr-FR-Neural2-C",
        },
        "de-DE": {
            "male": "de-DE-Neural2-A",
            "female": "de-DE-Neural2-C",
        },
        "ja-JP": {
            "male": "ja-JP-Neural2-A",
            "female": "ja-JP-Neural2-B",
        },
        "pt-BR": {
            "male": "pt-BR-Neural2-A",
            "female": "pt-BR-Neural2-B",
        },
    }

    def __init__(self, api_key: str | None = None) -> None:
        """Initialize Google Cloud TTS client.

        Args:
            api_key: Google Cloud API key (or uses GOOGLE_APPLICATION_CREDENTIALS)
        """
        self.api_key = api_key
        self.client = None
        self._init_client()

    def _init_client(self) -> None:
        """Initialize Google Cloud TTS client."""
        try:
            from google.cloud import texttospeech

            self.client = texttospeech.TextToSpeechClient()
            logger.info("✓ Google Cloud TTS client initialized")
        except ImportError:
            logger.warning("⚠ google-cloud-texttospeech not installed")
            logger.warning("  Install: pip install google-cloud-texttospeech")
        except Exception as e:
            logger.error(f"Failed to initialize Google Cloud TTS: {e}")

    def synthesize(self, request: TTSRequest) -> TTSResult:
        """Synthesize speech from text.

        Args:
            request: TTS request

        Returns:
            TTS result with audio path
        """
        if not self.client:
            return TTSResult(
                success=False,
                audio_path=None,
                duration_sec=0,
                file_size_bytes=0,
                error="Google Cloud TTS client not initialized",
            )

        try:
            from google.cloud import texttospeech

            # Build synthesis input
            synthesis_input = texttospeech.SynthesisInput(text=request.text)

            # Build voice config
            voice = texttospeech.VoiceSelectionParams(
                language_code=request.voice_config.language_code,
                name=request.voice_config.voice_name,
                ssml_gender=request.voice_config.gender.value,
            )

            # Build audio config
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding[request.audio_encoding.value],
                speaking_rate=request.voice_config.speech_rate,
                pitch=request.voice_config.pitch,
            )

            # Make request
            response = self.client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config,
            )

            # Save audio
            request.output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(request.output_path, "wb") as out:
                out.write(response.audio_content)

            # Estimate duration (approximate)
            word_count = len(request.text.split())
            words_per_minute = 150 * request.voice_config.speech_rate
            duration_sec = (word_count / words_per_minute) * 60

            file_size = request.output_path.stat().st_size

            logger.info(
                f"✓ Synthesized {word_count} words ({duration_sec:.1f}s) → {request.output_path}"
            )

            return TTSResult(
                success=True,
                audio_path=request.output_path,
                duration_sec=duration_sec,
                file_size_bytes=file_size,
            )

        except Exception as e:
            logger.error(f"Synthesis error: {e}")
            return TTSResult(
                success=False,
                audio_path=None,
                duration_sec=0,
                file_size_bytes=0,
                error=str(e),
            )

    @staticmethod
    def get_available_voices(language: str = "en-US") -> dict[str, str]:
        """Get available voices for language.

        Args:
            language: Language code (e.g., "en-US")

        Returns:
            Dictionary of gender→voice_name
        """
        return GoogleCloudTTS.VOICES.get(language, {})


class AzureSpeechTTS:
    """Azure Speech Services TTS provider."""

    def __init__(self, subscription_key: str | None = None, region: str = "eastus") -> None:
        """Initialize Azure Speech TTS client.

        Args:
            subscription_key: Azure Speech subscription key
            region: Azure region
        """
        self.subscription_key = subscription_key
        self.region = region
        self.client = None
        self._init_client()

    def _init_client(self) -> None:
        """Initialize Azure Speech client."""
        try:
            import azure.cognitiveservices.speech as speechsdk

            if not self.subscription_key:
                logger.warning("⚠ Azure subscription key not provided")
                return

            speech_config = speechsdk.SpeechConfig(
                subscription=self.subscription_key,
                region=self.region,
            )
            self.client = speech_config
            logger.info("✓ Azure Speech TTS client initialized")
        except ImportError:
            logger.warning("⚠ azure-cognitiveservices-speech not installed")
            logger.warning("  Install: pip install azure-cognitiveservices-speech")
        except Exception as e:
            logger.error(f"Failed to initialize Azure Speech: {e}")

    def synthesize(self, request: TTSRequest) -> TTSResult:
        """Synthesize speech from text.

        Args:
            request: TTS request

        Returns:
            TTS result with audio path
        """
        if not self.client:
            return TTSResult(
                success=False,
                audio_path=None,
                duration_sec=0,
                file_size_bytes=0,
                error="Azure Speech client not initialized",
            )

        try:
            import azure.cognitiveservices.speech as speechsdk

            # Configure speech synthesis
            self.client.speech_synthesis_voice_name = request.voice_config.voice_name

            # Output to file
            audio_config = speechsdk.audio.AudioOutputConfig(
                filename=str(request.output_path)
            )
            self.client.set_property_by_name("SpeechSynthesizer_LogFilePath", "")

            # Create synthesizer
            synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=self.client,
                audio_config=audio_config,
            )

            # Synthesize
            result = synthesizer.speak_text(request.text)

            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                word_count = len(request.text.split())
                words_per_minute = 150 * request.voice_config.speech_rate
                duration_sec = (word_count / words_per_minute) * 60

                file_size = request.output_path.stat().st_size if request.output_path.exists() else 0

                logger.info(
                    f"✓ Synthesized {word_count} words ({duration_sec:.1f}s) → {request.output_path}"
                )

                return TTSResult(
                    success=True,
                    audio_path=request.output_path,
                    duration_sec=duration_sec,
                    file_size_bytes=file_size,
                )
            else:
                error_msg = result.error_details if hasattr(result, "error_details") else "Unknown error"
                return TTSResult(
                    success=False,
                    audio_path=None,
                    duration_sec=0,
                    file_size_bytes=0,
                    error=str(error_msg),
                )

        except Exception as e:
            logger.error(f"Synthesis error: {e}")
            return TTSResult(
                success=False,
                audio_path=None,
                duration_sec=0,
                file_size_bytes=0,
                error=str(e),
            )


class PyttSX3TTS:
    """pyttsx3 fallback TTS provider (robotic voice)."""

    def __init__(self) -> None:
        """Initialize pyttsx3 TTS engine."""
        try:
            import pyttsx3

            self.engine = pyttsx3.init()
            logger.info("✓ pyttsx3 TTS engine initialized (fallback)")
        except ImportError:
            logger.warning("⚠ pyttsx3 not installed")
            self.engine = None

    def synthesize(self, request: TTSRequest) -> TTSResult:
        """Synthesize speech using pyttsx3.

        Args:
            request: TTS request

        Returns:
            TTS result with audio path
        """
        if not self.engine:
            return TTSResult(
                success=False,
                audio_path=None,
                duration_sec=0,
                file_size_bytes=0,
                error="pyttsx3 not installed",
            )

        try:
            # Configure voice
            self.engine.setProperty(
                "rate",
                150 * request.voice_config.speech_rate,
            )

            # Save to file
            request.output_path.parent.mkdir(parents=True, exist_ok=True)
            self.engine.save_to_file(request.text, str(request.output_path))
            self.engine.runAndWait()

            # Estimate duration
            word_count = len(request.text.split())
            words_per_minute = 150 * request.voice_config.speech_rate
            duration_sec = (word_count / words_per_minute) * 60

            file_size = request.output_path.stat().st_size if request.output_path.exists() else 0

            logger.info(
                f"✓ Synthesized {word_count} words ({duration_sec:.1f}s) with pyttsx3 → {request.output_path}"
            )

            return TTSResult(
                success=True,
                audio_path=request.output_path,
                duration_sec=duration_sec,
                file_size_bytes=file_size,
            )

        except Exception as e:
            logger.error(f"pyttsx3 synthesis error: {e}")
            return TTSResult(
                success=False,
                audio_path=None,
                duration_sec=0,
                file_size_bytes=0,
                error=str(e),
            )


class TTSEngine:
    """Main TTS engine with provider selection."""

    def __init__(self, provider: TTSProvider = TTSProvider.GOOGLE, **kwargs) -> None:
        """Initialize TTS engine.

        Args:
            provider: TTS provider to use
            **kwargs: Provider-specific arguments
        """
        self.provider = provider
        self.google_client = None
        self.azure_client = None
        self.pyttsx3_client = None

        if provider == TTSProvider.GOOGLE:
            self.google_client = GoogleCloudTTS(kwargs.get("api_key"))
        elif provider == TTSProvider.AZURE:
            self.azure_client = AzureSpeechTTS(
                kwargs.get("subscription_key"),
                kwargs.get("region", "eastus"),
            )
        elif provider == TTSProvider.PYTTSX3:
            self.pyttsx3_client = PyttSX3TTS()

    def synthesize(self, request: TTSRequest) -> TTSResult:
        """Synthesize speech.

        Args:
            request: TTS request

        Returns:
            TTS result
        """
        if self.provider == TTSProvider.GOOGLE and self.google_client:
            return self.google_client.synthesize(request)
        elif self.provider == TTSProvider.AZURE and self.azure_client:
            return self.azure_client.synthesize(request)
        elif self.provider == TTSProvider.PYTTSX3:
            return self.pyttsx3_client.synthesize(request)
        else:
            # Fallback to pyttsx3
            fallback = PyttSX3TTS()
            return fallback.synthesize(request)

    @staticmethod
    def get_best_provider() -> TTSProvider:
        """Get best available TTS provider."""
        # Try Google first (best quality)
        try:
            from google.cloud import texttospeech  # noqa

            return TTSProvider.GOOGLE
        except ImportError:
            pass

        # Try Azure second
        try:
            import azure.cognitiveservices.speech  # noqa

            return TTSProvider.AZURE
        except ImportError:
            pass

        # Fall back to pyttsx3
        return TTSProvider.PYTTSX3

    @staticmethod
    def create_optimal() -> TTSEngine:
        """Create TTS engine with best available provider."""
        best_provider = TTSEngine.get_best_provider()
        logger.info(f"Using TTS provider: {best_provider.value}")
        return TTSEngine(best_provider)
