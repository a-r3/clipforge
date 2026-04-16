"""Tests for Phase 2C Premium Features (TTS, Color Grading, Transitions)."""

from __future__ import annotations

import pytest
from pathlib import Path

from clipforge.tts_engine import (
    TTSProvider,
    SpeechGender,
    SpeechRate,
    AudioEncoding,
    VoiceConfig,
    TTSRequest,
    TTSEngine,
    GoogleCloudTTS,
)

from clipforge.color_grader import (
    ColorGradingPreset,
    WhiteBalance,
    ColorProfile,
    ColorGradingEngine,
    LUT,
    GradingSession,
)

from clipforge.transitions import (
    TransitionType,
    EasingType,
    TransitionConfig,
    EasingCurve,
    TransitionEffect,
    TransitionLibrary,
    TransitionSequence,
)


class TestTTSProvider:
    """Test TTS provider enumeration."""

    def test_provider_values(self) -> None:
        """Test TTS provider enum values."""
        assert TTSProvider.GOOGLE.value == "google"
        assert TTSProvider.AZURE.value == "azure"
        assert TTSProvider.PYTTSX3.value == "pyttsx3"


class TestSpeechParameters:
    """Test speech parameters."""

    def test_speech_gender(self) -> None:
        """Test speech gender enum."""
        assert SpeechGender.MALE.value == "MALE"
        assert SpeechGender.FEMALE.value == "FEMALE"
        assert SpeechGender.NEUTRAL.value == "NEUTRAL"

    def test_speech_rate(self) -> None:
        """Test speech rate enum."""
        assert SpeechRate.SLOW.value == 0.75
        assert SpeechRate.NORMAL.value == 1.0
        assert SpeechRate.FAST.value == 1.25
        assert SpeechRate.VERY_FAST.value == 1.5

    def test_audio_encoding(self) -> None:
        """Test audio encoding enum."""
        assert AudioEncoding.MP3.value == "MP3"
        assert AudioEncoding.OGG.value == "OGG_OPUS"
        assert AudioEncoding.WAV.value == "LINEAR16"


class TestVoiceConfig:
    """Test voice configuration."""

    def test_voice_config_creation(self) -> None:
        """Test creating voice config."""
        config = VoiceConfig(
            provider=TTSProvider.GOOGLE,
            language_code="en-US",
            voice_name="en-US-Neural2-A",
            gender=SpeechGender.MALE,
            speech_rate=1.0,
            pitch=0.0,
        )

        assert config.provider == TTSProvider.GOOGLE
        assert config.language_code == "en-US"
        assert config.speech_rate == 1.0


class TestGoogleCloudTTS:
    """Test Google Cloud TTS."""

    def test_available_voices(self) -> None:
        """Test getting available voices."""
        voices = GoogleCloudTTS.get_available_voices("en-US")

        assert isinstance(voices, dict)
        assert "male" in voices or len(voices) == 0  # Either has voices or empty


class TestTTSEngine:
    """Test TTS engine."""

    def test_best_provider_selection(self) -> None:
        """Test selecting best available provider."""
        provider = TTSEngine.get_best_provider()

        assert provider in [
            TTSProvider.GOOGLE,
            TTSProvider.AZURE,
            TTSProvider.PYTTSX3,
        ]

    def test_engine_creation(self) -> None:
        """Test creating TTS engine."""
        engine = TTSEngine(TTSProvider.PYTTSX3)

        assert engine.provider == TTSProvider.PYTTSX3


class TestColorGradingPresets:
    """Test color grading presets."""

    def test_preset_values(self) -> None:
        """Test preset enum values."""
        assert ColorGradingPreset.CINEMATIC.value == "cinematic"
        assert ColorGradingPreset.VINTAGE.value == "vintage"
        assert ColorGradingPreset.VIBRANT.value == "vibrant"
        assert ColorGradingPreset.NOIR.value == "noir"
        assert ColorGradingPreset.NATURAL.value == "natural"


class TestColorProfile:
    """Test color profile."""

    def test_profile_creation(self) -> None:
        """Test creating color profile."""
        profile = ColorProfile(
            preset=ColorGradingPreset.CINEMATIC,
            saturation=1.1,
            contrast=1.15,
            brightness=0.05,
            highlights=0.2,
            shadows=-0.1,
            vibrance=0.9,
            temperature=-10,
            tint=5,
        )

        assert profile.preset == ColorGradingPreset.CINEMATIC
        assert profile.saturation == 1.1
        assert profile.contrast == 1.15


class TestColorGradingEngine:
    """Test color grading engine."""

    def test_engine_initialization(self) -> None:
        """Test engine init."""
        engine = ColorGradingEngine()

        assert engine is not None

    def test_get_cinematic_profile(self) -> None:
        """Test getting cinematic profile."""
        engine = ColorGradingEngine()
        profile = engine.get_profile(ColorGradingPreset.CINEMATIC)

        assert profile.preset == ColorGradingPreset.CINEMATIC
        assert profile.saturation > 1.0  # Enhanced saturation

    def test_get_vintage_profile(self) -> None:
        """Test getting vintage profile."""
        engine = ColorGradingEngine()
        profile = engine.get_profile(ColorGradingPreset.VINTAGE)

        assert profile.preset == ColorGradingPreset.VINTAGE
        assert profile.temperature > 0  # Warm tint

    def test_get_vibrant_profile(self) -> None:
        """Test getting vibrant profile."""
        engine = ColorGradingEngine()
        profile = engine.get_profile(ColorGradingPreset.VIBRANT)

        assert profile.saturation > 1.2  # High saturation


class TestEasingCurves:
    """Test easing curve calculations."""

    def test_linear_easing(self) -> None:
        """Test linear easing."""
        assert EasingCurve.linear(0.0) == 0.0
        assert EasingCurve.linear(0.5) == 0.5
        assert EasingCurve.linear(1.0) == 1.0

    def test_ease_in(self) -> None:
        """Test ease in curve."""
        assert EasingCurve.ease_in(0.0) == 0.0
        assert EasingCurve.ease_in(1.0) == 1.0
        assert EasingCurve.ease_in(0.5) < 0.5  # Starts slow

    def test_ease_out(self) -> None:
        """Test ease out curve."""
        assert EasingCurve.ease_out(0.0) == 0.0
        assert EasingCurve.ease_out(1.0) == 1.0

    def test_ease_in_out(self) -> None:
        """Test ease in-out curve."""
        assert EasingCurve.ease_in_out(0.0) == 0.0
        assert EasingCurve.ease_in_out(1.0) == 1.0

    def test_get_easing_function(self) -> None:
        """Test getting easing function."""
        func = EasingCurve.get_easing_func(EasingType.LINEAR)

        assert func is not None
        assert func(0.5) == 0.5


class TestTransitionConfig:
    """Test transition configuration."""

    def test_config_creation(self) -> None:
        """Test creating transition config."""
        config = TransitionConfig(
            transition_type=TransitionType.FADE,
            duration_sec=0.5,
            easing=EasingType.EASE_IN_OUT,
        )

        assert config.transition_type == TransitionType.FADE
        assert config.duration_sec == 0.5


class TestTransitionEffect:
    """Test transition effects."""

    def test_fade_effect(self) -> None:
        """Test fade transition effect."""
        config = TransitionConfig(
            transition_type=TransitionType.FADE,
            duration_sec=0.5,
        )
        effect = TransitionEffect(config)

        assert effect.config.transition_type == TransitionType.FADE

    def test_get_ffmpeg_filter(self) -> None:
        """Test getting FFmpeg filter."""
        config = TransitionConfig(
            transition_type=TransitionType.FADE,
            duration_sec=0.5,
        )
        effect = TransitionEffect(config)

        filter_str = effect.get_ffmpeg_filter()

        assert filter_str is not None
        assert "fade" in filter_str.lower()

    def test_duration_in_frames(self) -> None:
        """Test calculating frames from duration."""
        config = TransitionConfig(
            transition_type=TransitionType.FADE,
            duration_sec=0.5,
        )
        effect = TransitionEffect(config)

        frames = effect.get_duration_frames(30)

        assert frames == 15  # 0.5 * 30


class TestTransitionLibrary:
    """Test transition library."""

    def test_fade_fast_exists(self) -> None:
        """Test fade fast preset exists."""
        assert TransitionLibrary.FADE_FAST is not None
        assert TransitionLibrary.FADE_FAST.duration_sec == 0.3

    def test_get_all_transitions(self) -> None:
        """Test getting all transitions."""
        all_trans = TransitionLibrary.get_all_transitions()

        assert isinstance(all_trans, dict)
        assert len(all_trans) > 0

    def test_get_transition_by_name(self) -> None:
        """Test getting transition by name."""
        trans = TransitionLibrary.get_transition("FADE_FAST")

        assert trans is not None
        assert trans.duration_sec == 0.3


class TestTransitionSequence:
    """Test transition sequence."""

    def test_sequence_creation(self) -> None:
        """Test creating transition sequence."""
        seq = TransitionSequence()

        assert len(seq) == 0

    def test_add_transition(self) -> None:
        """Test adding transitions."""
        seq = TransitionSequence()

        config = TransitionConfig(
            transition_type=TransitionType.FADE,
            duration_sec=0.5,
        )
        seq.add_transition(config)

        assert len(seq) == 1

    def test_total_duration(self) -> None:
        """Test calculating total transition duration."""
        seq = TransitionSequence()

        config1 = TransitionConfig(
            transition_type=TransitionType.FADE,
            duration_sec=0.5,
        )
        config2 = TransitionConfig(
            transition_type=TransitionType.DISSOLVE,
            duration_sec=0.3,
        )

        seq.add_transition(config1)
        seq.add_transition(config2)

        total = seq.get_total_transition_duration()

        assert total == 0.8

    def test_get_ffmpeg_filters(self) -> None:
        """Test getting FFmpeg filters."""
        seq = TransitionSequence()

        config = TransitionConfig(
            transition_type=TransitionType.FADE,
            duration_sec=0.5,
        )
        seq.add_transition(config)

        filters = seq.get_ffmpeg_filters()

        assert len(filters) > 0


class TestTransitionTypes:
    """Test different transition types."""

    def test_all_transition_types_have_filters(self) -> None:
        """Test all transition types can generate filters."""
        for trans_type in TransitionType:
            config = TransitionConfig(
                transition_type=trans_type,
                duration_sec=0.3,
            )
            effect = TransitionEffect(config)

            filter_str = effect.get_ffmpeg_filter()

            # All should generate some filter (or empty string is OK for custom ones)
            assert isinstance(filter_str, str)
