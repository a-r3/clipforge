"""Tests for quality tier management."""

from __future__ import annotations

import pytest

from clipforge.quality_tiers import (
    QualityTier,
    Platform,
    QualityProfile,
    QualityTierManager,
)
from clipforge.ffmpeg_renderer import Codec


class TestQualityTier:
    """Test quality tier enumeration."""

    def test_tier_values(self) -> None:
        """Test quality tier enum values."""
        assert QualityTier.HIGH.value == "high"
        assert QualityTier.MEDIUM.value == "medium"
        assert QualityTier.LOW.value == "low"
        assert QualityTier.MOBILE.value == "mobile"


class TestPlatform:
    """Test platform enumeration."""

    def test_platform_values(self) -> None:
        """Test platform enum values."""
        assert Platform.YOUTUBE.value == "youtube"
        assert Platform.YOUTUBE_SHORTS.value == "youtube-shorts"
        assert Platform.TIKTOK.value == "tiktok"
        assert Platform.INSTAGRAM_REELS.value == "instagram-reels"


class TestQualityProfile:
    """Test quality profile dataclass."""

    def test_profile_creation(self) -> None:
        """Test creating a quality profile."""
        profile = QualityProfile(
            tier=QualityTier.MEDIUM,
            resolution=(1920, 1080),
            bitrate="8000k",
            fps=30,
            codec=Codec.H264,
            preset="medium",
            crf=23,
        )

        assert profile.tier == QualityTier.MEDIUM
        assert profile.resolution == (1920, 1080)
        assert profile.bitrate == "8000k"
        assert profile.fps == 30
        assert profile.codec == Codec.H264
        assert profile.preset == "medium"
        assert profile.crf == 23

    def test_profile_with_platform(self) -> None:
        """Test profile with platform specification."""
        profile = QualityProfile(
            tier=QualityTier.HIGH,
            resolution=(3840, 2160),
            bitrate="80000k",
            fps=60,
            codec=Codec.H265,
            preset="slow",
            crf=18,
            platform=Platform.YOUTUBE,
        )

        assert profile.platform == Platform.YOUTUBE


class TestQualityTierManager:
    """Test quality tier manager."""

    def test_high_profiles_exist(self) -> None:
        """Test high quality profiles are defined."""
        assert "4k" in QualityTierManager.HIGH_PROFILES
        assert "1080p-high" in QualityTierManager.HIGH_PROFILES

    def test_medium_profiles_exist(self) -> None:
        """Test medium quality profiles are defined."""
        assert "1080p" in QualityTierManager.MEDIUM_PROFILES
        assert "720p-short" in QualityTierManager.MEDIUM_PROFILES

    def test_low_profiles_exist(self) -> None:
        """Test low quality profiles are defined."""
        assert "720p" in QualityTierManager.LOW_PROFILES
        assert "480p-mobile" in QualityTierManager.LOW_PROFILES

    def test_get_profile_for_youtube_shorts(self) -> None:
        """Test getting profile for YouTube Shorts."""
        profile = QualityTierManager.get_profile_for_platform(
            Platform.YOUTUBE_SHORTS, QualityTier.MEDIUM
        )

        # Should be vertical (1080x1920)
        assert profile.resolution == (1080, 1920)
        assert profile.tier == QualityTier.MEDIUM

    def test_get_profile_for_youtube(self) -> None:
        """Test getting profile for YouTube."""
        profile = QualityTierManager.get_profile_for_platform(
            Platform.YOUTUBE, QualityTier.MEDIUM
        )

        # Should be horizontal
        assert profile.resolution == (1920, 1080)

    def test_get_profile_for_tiktok(self) -> None:
        """Test getting profile for TikTok."""
        profile = QualityTierManager.get_profile_for_platform(
            Platform.TIKTOK, QualityTier.MEDIUM
        )

        # Should be vertical
        assert profile.resolution == (1080, 1920)

    def test_get_profile_high_tier(self) -> None:
        """Test getting high quality profile."""
        profile = QualityTierManager.get_profile_for_platform(
            Platform.YOUTUBE, QualityTier.HIGH
        )

        assert profile.tier == QualityTier.HIGH
        # Should be 4K for YouTube high
        assert profile.resolution == (3840, 2160)

    def test_get_profile_low_tier(self) -> None:
        """Test getting low quality profile."""
        profile = QualityTierManager.get_profile_for_platform(
            Platform.TIKTOK, QualityTier.LOW
        )

        assert profile.tier == QualityTier.LOW
        # Should be 720p for low tier
        assert profile.resolution == (1280, 720)

    def test_get_codec_profile(self) -> None:
        """Test converting quality profile to codec profile."""
        quality_profile = QualityTierManager.MEDIUM_PROFILES["1080p"]
        codec_profile = QualityTierManager.get_codec_profile(quality_profile)

        assert codec_profile.codec == quality_profile.codec
        assert codec_profile.bitrate == quality_profile.bitrate
        assert codec_profile.preset == quality_profile.preset
        assert codec_profile.crf == quality_profile.crf
        assert codec_profile.resolution == quality_profile.resolution
        assert codec_profile.fps == quality_profile.fps

    def test_estimate_file_size(self) -> None:
        """Test file size estimation."""
        profile = QualityTierManager.MEDIUM_PROFILES["1080p"]
        
        # 30 seconds at 8000 kbps
        size_mb = QualityTierManager.estimate_file_size(profile, 30.0)

        # (8000 * 30) / 8000 = 30 MB (approx)
        assert 25 < size_mb < 35

    def test_estimate_file_size_high_quality(self) -> None:
        """Test file size estimation for high quality."""
        profile = QualityTierManager.HIGH_PROFILES["4k"]
        
        # 30 seconds at 80000 kbps
        size_mb = QualityTierManager.estimate_file_size(profile, 30.0)

        # Should be much larger
        assert size_mb > 200

    def test_estimate_file_size_low_quality(self) -> None:
        """Test file size estimation for low quality."""
        profile = QualityTierManager.LOW_PROFILES["720p"]
        
        # 30 seconds at 3500 kbps
        size_mb = QualityTierManager.estimate_file_size(profile, 30.0)

        # Should be smaller
        assert size_mb < 20

    def test_get_all_tiers(self) -> None:
        """Test getting all available profiles."""
        all_profiles = QualityTierManager.get_all_tiers()

        assert isinstance(all_profiles, dict)
        assert len(all_profiles) > 0
        
        # Check that all tiers are represented
        assert any(p.tier == QualityTier.HIGH for p in all_profiles.values())
        assert any(p.tier == QualityTier.MEDIUM for p in all_profiles.values())
        assert any(p.tier == QualityTier.LOW for p in all_profiles.values())

    def test_compare_profiles(self) -> None:
        """Test comparing two profiles."""
        profile1 = QualityTierManager.HIGH_PROFILES["4k"]
        profile2 = QualityTierManager.MEDIUM_PROFILES["1080p"]

        comparison = QualityTierManager.compare_profiles(profile1, profile2)

        assert "resolution_ratio" in comparison
        assert "bitrate_ratio" in comparison
        assert comparison["quality_tier_1"] == "high"
        assert comparison["quality_tier_2"] == "medium"
        
        # 4K should have higher resolution ratio than 1080p
        assert comparison["resolution_ratio"] > 1.0

    def test_bitrate_extraction_from_profiles(self) -> None:
        """Test bitrate extraction from profiles."""
        high_profile = QualityTierManager.HIGH_PROFILES["4k"]
        medium_profile = QualityTierManager.MEDIUM_PROFILES["1080p"]
        low_profile = QualityTierManager.LOW_PROFILES["720p"]

        # High should have higher bitrate
        assert int(high_profile.bitrate.rstrip("k")) > int(
            medium_profile.bitrate.rstrip("k")
        )
        
        # Medium should have higher bitrate than low
        assert int(medium_profile.bitrate.rstrip("k")) > int(
            low_profile.bitrate.rstrip("k")
        )

    def test_codec_selection_by_tier(self) -> None:
        """Test codec selection is appropriate for tier."""
        high = QualityTierManager.HIGH_PROFILES["4k"]
        medium = QualityTierManager.MEDIUM_PROFILES["1080p"]
        low = QualityTierManager.LOW_PROFILES["720p"]

        # High should prefer H.265 (better compression)
        assert high.codec == Codec.H265
        
        # Medium might use H.264 (compatibility)
        assert medium.codec == Codec.H264
        
        # Low should use H.265 (better compression for smaller size)
        assert low.codec == Codec.H265

    def test_preset_for_rendering_speed(self) -> None:
        """Test preset is appropriate for rendering speed."""
        high = QualityTierManager.HIGH_PROFILES["4k"]
        medium = QualityTierManager.MEDIUM_PROFILES["1080p"]
        low = QualityTierManager.LOW_PROFILES["720p"]

        # High quality should use slower preset for better quality
        assert high.preset in ["slow", "slower"]
        
        # Low should use faster preset to save time
        assert low.preset in ["fast", "veryfast"]
        
        # Medium should be balanced
        assert medium.preset == "medium"
