"""Tests for FFmpeg renderer module."""

from __future__ import annotations

import pytest
from pathlib import Path

from clipforge.ffmpeg_renderer import (
    Codec,
    HardwareAccelerator,
    ColorSpace,
    CodecProfile,
    RenderProgress,
    FFmpegCommand,
    FFmpegDetector,
    FFmpegRenderer,
)


class TestCodecProfile:
    """Test codec profile configuration."""

    def test_default_profile(self) -> None:
        """Test default profile initialization."""
        profile = CodecProfile()
        
        assert profile.codec == Codec.H264
        assert profile.bitrate == "5000k"
        assert profile.preset == "medium"
        assert profile.crf == 23
        assert profile.resolution == (1080, 1920)
        assert profile.fps == 30

    def test_custom_profile(self) -> None:
        """Test custom profile creation."""
        profile = CodecProfile(
            codec=Codec.H265,
            bitrate="3500k",
            preset="fast",
            crf=25,
        )
        
        assert profile.codec == Codec.H265
        assert profile.bitrate == "3500k"
        assert profile.preset == "fast"
        assert profile.crf == 25

    def test_profile_with_hw_accel(self) -> None:
        """Test profile with hardware acceleration."""
        profile = CodecProfile(
            hw_accel=HardwareAccelerator.NVIDIA_CUDA,
            preset="fast",
        )
        
        assert profile.hw_accel == HardwareAccelerator.NVIDIA_CUDA
        assert profile.preset == "fast"


class TestRenderProgress:
    """Test render progress tracking."""

    def test_progress_calculation(self) -> None:
        """Test progress percentage calculation."""
        progress = RenderProgress(total_frames=100, current_frame=25)
        
        assert progress.progress_percent == 25.0

    def test_progress_full(self) -> None:
        """Test 100% progress."""
        progress = RenderProgress(total_frames=100, current_frame=100)
        
        assert progress.progress_percent == 100.0

    def test_progress_zero(self) -> None:
        """Test 0% progress."""
        progress = RenderProgress(total_frames=100, current_frame=0)
        
        assert progress.progress_percent == 0.0

    def test_eta_calculation(self) -> None:
        """Test ETA calculation."""
        progress = RenderProgress(
            total_frames=100,
            current_frame=50,
            fps=30.0,  # 30 fps
        )
        
        # 50 frames remaining at 30 fps = 1.667 seconds
        eta = progress.eta_seconds
        assert 1.6 < eta < 1.7

    def test_eta_with_zero_fps(self) -> None:
        """Test ETA with zero fps."""
        progress = RenderProgress(
            total_frames=100,
            current_frame=50,
            fps=0.0,
        )
        
        assert progress.eta_seconds == 0.0


class TestFFmpegCommand:
    """Test FFmpeg command builder."""

    def test_basic_command_build(self) -> None:
        """Test building basic FFmpeg command."""
        profile = CodecProfile()
        cmd = FFmpegCommand(profile)
        cmd.set_codec_args()
        cmd.set_resolution_fps()
        cmd.set_audio_args()
        
        cmd_list = cmd.build("/tmp/test.mp4")
        
        assert "ffmpeg" in cmd_list[0]
        assert "/tmp/test.mp4" in cmd_list
        assert "-c:v" in cmd_list
        assert "-c:a" in cmd_list

    def test_h264_codec(self) -> None:
        """Test H.264 codec configuration."""
        profile = CodecProfile(codec=Codec.H264)
        cmd = FFmpegCommand(profile)
        cmd.set_codec_args()
        
        assert "-c:v" in cmd.output_args
        assert cmd.output_args["-c:v"] == "libx264"
        assert "-crf" in cmd.output_args

    def test_h265_codec(self) -> None:
        """Test H.265 codec configuration."""
        profile = CodecProfile(codec=Codec.H265)
        cmd = FFmpegCommand(profile)
        cmd.set_codec_args()
        
        assert cmd.output_args["-c:v"] == "libx265"

    def test_vp9_codec(self) -> None:
        """Test VP9 codec configuration."""
        profile = CodecProfile(codec=Codec.VP9)
        cmd = FFmpegCommand(profile)
        cmd.set_codec_args()
        
        assert cmd.output_args["-c:v"] == "libvpx-vp9"

    def test_add_filter(self) -> None:
        """Test adding video filters."""
        cmd = FFmpegCommand()
        cmd.add_filter("scale=1080:1920")
        cmd.add_filter("fps=30")
        
        assert len(cmd.filters) == 2
        assert "scale=1080:1920" in cmd.filters
        assert "fps=30" in cmd.filters

    def test_add_input(self) -> None:
        """Test adding inputs."""
        cmd = FFmpegCommand()
        cmd.add_input("/tmp/input.mp4")
        cmd.add_input("/tmp/audio.wav", {"-ss": "1.5"})
        
        assert len(cmd.inputs) == 2

    def test_command_chaining(self) -> None:
        """Test method chaining."""
        cmd = (
            FFmpegCommand()
            .set_codec_args()
            .set_resolution_fps()
            .set_audio_args()
        )
        
        assert len(cmd.output_args) > 0


class TestFFmpegDetector:
    """Test FFmpeg detection and capability checking."""

    def test_ffmpeg_check(self) -> None:
        """Test FFmpeg availability check."""
        # This will only pass if FFmpeg is installed
        is_available = FFmpegDetector.check_ffmpeg()
        
        if is_available:
            # If available, version should also be retrievable
            version = FFmpegDetector.get_ffmpeg_version()
            assert version is not None
            assert "ffmpeg" in version.lower()

    def test_version_parsing(self) -> None:
        """Test FFmpeg version detection."""
        version = FFmpegDetector.get_ffmpeg_version()
        
        if version:
            assert isinstance(version, str)
            assert len(version) > 0

    def test_codec_detection(self) -> None:
        """Test supported codec detection."""
        codecs = FFmpegDetector.get_supported_codecs()
        
        # H.264 should always be available
        assert Codec.H264 in codecs
        assert isinstance(codecs, list)

    def test_hw_accelerator_detection(self) -> None:
        """Test hardware accelerator detection."""
        accelerators = FFmpegDetector.detect_hw_accelerators()
        
        # Should be a list (may be empty)
        assert isinstance(accelerators, list)
        
        # All items should be HardwareAccelerator enum
        for accel in accelerators:
            assert isinstance(accel, HardwareAccelerator)


class TestFFmpegRenderer:
    """Test FFmpeg renderer."""

    def test_renderer_initialization(self) -> None:
        """Test renderer initialization."""
        # This test only runs if FFmpeg is installed
        if FFmpegDetector.check_ffmpeg():
            renderer = FFmpegRenderer()
            
            assert renderer.version is not None
            assert len(renderer.supported_codecs) > 0
            assert Codec.H264 in renderer.supported_codecs

    def test_optimal_profile_h265(self) -> None:
        """Test getting optimal profile."""
        if FFmpegDetector.check_ffmpeg():
            renderer = FFmpegRenderer()
            profile = renderer.get_optimal_profile()
            
            # Profile should be optimized
            assert profile.codec in renderer.supported_codecs
            
            # If H.265 available, should use it
            if Codec.H265 in renderer.supported_codecs:
                assert profile.codec == Codec.H265
                assert profile.bitrate == "3500k"

    def test_optimal_profile_with_gpu(self) -> None:
        """Test optimal profile uses GPU if available."""
        if FFmpegDetector.check_ffmpeg():
            renderer = FFmpegRenderer()
            profile = renderer.get_optimal_profile()
            
            if renderer.hw_accelerators:
                assert profile.hw_accel in renderer.hw_accelerators
                assert profile.preset == "fast"

    def test_optimal_profile_fallback(self) -> None:
        """Test optimal profile fallback to CPU."""
        if FFmpegDetector.check_ffmpeg():
            renderer = FFmpegRenderer()
            profile = renderer.get_optimal_profile()
            
            # Should always have a codec
            assert profile.codec is not None
            assert profile.resolution == (1080, 1920)


class TestCodecEnum:
    """Test codec enumeration."""

    def test_codec_values(self) -> None:
        """Test codec enum values."""
        assert Codec.H264.value == "h264"
        assert Codec.H265.value == "hevc"
        assert Codec.VP9.value == "vp9"
        assert Codec.AV1.value == "av1"

    def test_codec_comparison(self) -> None:
        """Test codec comparison."""
        assert Codec.H264 != Codec.H265
        assert Codec.H264 == Codec.H264


class TestColorSpace:
    """Test color space configuration."""

    def test_color_space_values(self) -> None:
        """Test color space enum values."""
        assert ColorSpace.BT709.value == "bt709"
        assert ColorSpace.BT2020.value == "bt2020"
        assert ColorSpace.SRGB.value == "srgb"


class TestHardwareAccelerator:
    """Test hardware accelerator enum."""

    def test_hw_accel_values(self) -> None:
        """Test hardware accelerator enum values."""
        assert HardwareAccelerator.NONE.value == "none"
        assert HardwareAccelerator.NVIDIA_CUDA.value == "cuda"
        assert HardwareAccelerator.AMD_VCE.value == "h264_amf"
        assert HardwareAccelerator.INTEL_QSV.value == "h264_qsv"
