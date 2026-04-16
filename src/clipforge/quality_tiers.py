"""Quality tier management for video outputs.

Provides platform-specific quality presets:
- High: 4K, 80 Mbps (archive, professional)
- Medium: 1080p, 25 Mbps (social media default)
- Low: 720p, 8 Mbps (mobile, low bandwidth)
- Mobile: Auto-bitrate adaptive streaming
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from clipforge.ffmpeg_renderer import CodecProfile, Codec


class QualityTier(Enum):
    """Quality tier options."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    MOBILE = "mobile"


class Platform(Enum):
    """Video platform."""

    YOUTUBE = "youtube"
    YOUTUBE_SHORTS = "youtube-shorts"
    TIKTOK = "tiktok"
    INSTAGRAM_REELS = "instagram-reels"
    TWITTER = "twitter"
    SNAPCHAT = "snapchat"


@dataclass
class QualityProfile:
    """Video quality profile."""

    tier: QualityTier
    resolution: tuple[int, int]  # (width, height)
    bitrate: str
    fps: int
    codec: Codec
    preset: str  # ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow
    crf: int  # Constant Rate Factor (0-51, lower=better)
    platform: Platform | None = None


class QualityTierManager:
    """Manage quality tiers and platform-specific settings."""

    # High quality (4K, archive)
    HIGH_PROFILES = {
        "4k": QualityProfile(
            tier=QualityTier.HIGH,
            resolution=(3840, 2160),
            bitrate="80000k",
            fps=60,
            codec=Codec.H265,
            preset="slow",
            crf=18,
        ),
        "1080p-high": QualityProfile(
            tier=QualityTier.HIGH,
            resolution=(1920, 1080),
            bitrate="25000k",
            fps=60,
            codec=Codec.H265,
            preset="slow",
            crf=18,
        ),
    }

    # Medium quality (social media default)
    MEDIUM_PROFILES = {
        "1080p": QualityProfile(
            tier=QualityTier.MEDIUM,
            resolution=(1920, 1080),
            bitrate="8000k",
            fps=30,
            codec=Codec.H264,
            preset="medium",
            crf=23,
        ),
        "720p-short": QualityProfile(
            tier=QualityTier.MEDIUM,
            resolution=(1080, 1920),
            bitrate="5000k",
            fps=30,
            codec=Codec.H265,
            preset="medium",
            crf=23,
        ),
    }

    # Low quality (mobile, bandwidth-conscious)
    LOW_PROFILES = {
        "720p": QualityProfile(
            tier=QualityTier.LOW,
            resolution=(1280, 720),
            bitrate="3500k",
            fps=24,
            codec=Codec.H265,
            preset="fast",
            crf=28,
        ),
        "480p-mobile": QualityProfile(
            tier=QualityTier.LOW,
            resolution=(854, 480),
            bitrate="2000k",
            fps=24,
            codec=Codec.H265,
            preset="fast",
            crf=28,
        ),
    }

    # Mobile adaptive (auto-adjusts based on bandwidth)
    MOBILE_PROFILES = {
        "adaptive": QualityProfile(
            tier=QualityTier.MOBILE,
            resolution=(1080, 1920),
            bitrate="4000k",  # Will adjust
            fps=30,
            codec=Codec.H265,
            preset="veryfast",
            crf=25,
        ),
    }

    @staticmethod
    def get_profile_for_platform(
        platform: Platform, tier: QualityTier = QualityTier.MEDIUM
    ) -> QualityProfile:
        """Get recommended quality profile for platform.

        Args:
            platform: Target platform
            tier: Quality tier preference

        Returns:
            Recommended QualityProfile
        """
        # Platform-specific defaults
        if platform in [Platform.YOUTUBE_SHORTS, Platform.TIKTOK, Platform.INSTAGRAM_REELS]:
            # Short-form vertical video
            if tier == QualityTier.HIGH:
                return QualityTierManager.HIGH_PROFILES["1080p-high"]
            elif tier == QualityTier.LOW:
                return QualityTierManager.LOW_PROFILES["720p"]
            else:  # MEDIUM
                return QualityTierManager.MEDIUM_PROFILES["720p-short"]

        elif platform == Platform.YOUTUBE:
            # Long-form horizontal video
            if tier == QualityTier.HIGH:
                return QualityTierManager.HIGH_PROFILES["4k"]
            elif tier == QualityTier.LOW:
                return QualityTierManager.LOW_PROFILES["720p"]
            else:  # MEDIUM
                return QualityTierManager.MEDIUM_PROFILES["1080p"]

        elif platform in [Platform.TWITTER, Platform.SNAPCHAT]:
            # Mobile-first platforms
            return QualityTierManager.MOBILE_PROFILES["adaptive"]

        # Default
        return QualityTierManager.MEDIUM_PROFILES["1080p"]

    @staticmethod
    def get_codec_profile(quality_profile: QualityProfile) -> CodecProfile:
        """Convert QualityProfile to FFmpeg CodecProfile.

        Args:
            quality_profile: Quality tier profile

        Returns:
            FFmpeg codec configuration
        """
        return CodecProfile(
            codec=quality_profile.codec,
            bitrate=quality_profile.bitrate,
            preset=quality_profile.preset,
            crf=quality_profile.crf,
            resolution=quality_profile.resolution,
            fps=quality_profile.fps,
        )

    @staticmethod
    def estimate_file_size(quality_profile: QualityProfile, duration_sec: float) -> float:
        """Estimate output file size in MB.

        Args:
            quality_profile: Quality tier profile
            duration_sec: Video duration in seconds

        Returns:
            Estimated file size in MB
        """
        # Parse bitrate (e.g., "5000k" → 5000)
        bitrate_str = quality_profile.bitrate.rstrip("k")
        bitrate_kbps = int(bitrate_str)

        # Calculate: (bitrate * duration) / 8000 (to convert to MB)
        # 1 MB = 1024 * 1024 bytes, but we'll use 8000 for simplicity
        file_size_mb = (bitrate_kbps * duration_sec) / 8000

        return file_size_mb

    @staticmethod
    def get_all_tiers() -> dict[str, QualityProfile]:
        """Get all available quality profiles."""
        all_profiles = {}
        all_profiles.update(QualityTierManager.HIGH_PROFILES)
        all_profiles.update(QualityTierManager.MEDIUM_PROFILES)
        all_profiles.update(QualityTierManager.LOW_PROFILES)
        all_profiles.update(QualityTierManager.MOBILE_PROFILES)
        return all_profiles

    @staticmethod
    def compare_profiles(profile1: QualityProfile, profile2: QualityProfile) -> dict[str, Any]:
        """Compare two quality profiles.

        Args:
            profile1: First profile
            profile2: Second profile

        Returns:
            Comparison metrics
        """
        return {
            "profile1_name": f"{profile1.resolution[0]}p",
            "profile2_name": f"{profile2.resolution[0]}p",
            "resolution_ratio": (
                (profile1.resolution[0] * profile1.resolution[1])
                / (profile2.resolution[0] * profile2.resolution[1])
            ),
            "bitrate_ratio": (
                int(profile1.bitrate.rstrip("k")) / int(profile2.bitrate.rstrip("k"))
            ),
            "quality_tier_1": profile1.tier.value,
            "quality_tier_2": profile2.tier.value,
            "codec_1": profile1.codec.value,
            "codec_2": profile2.codec.value,
        }
