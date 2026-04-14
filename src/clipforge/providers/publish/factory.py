"""Publish provider factory — select the right provider for a platform/config.

Usage::

    from clipforge.providers.publish.factory import PublishProviderFactory
    from clipforge.publish_config import PublishConfig

    config = PublishConfig.load("publish_config.json")
    provider = PublishProviderFactory.for_platform("youtube", config)
    result = provider.dry_run_publish(target)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from clipforge.providers.publish.base import PublishProvider
    from clipforge.publish_config import PublishConfig


# Default platform → provider name mapping
_DEFAULT_PLATFORM_PROVIDERS: dict[str, str] = {
    "youtube": "youtube",
    "youtube-shorts": "youtube",
    "reels": "manual",
    "tiktok": "manual",
    "landscape": "manual",
}


class PublishProviderFactory:
    """Select and instantiate the appropriate publish provider."""

    @classmethod
    def for_platform(
        cls,
        platform: str,
        config: "PublishConfig | None" = None,
    ) -> "PublishProvider":
        """Return a provider instance for *platform*.

        Provider selection order:
        1. ``config.platform_providers[platform]`` if set
        2. ``_DEFAULT_PLATFORM_PROVIDERS[platform]``
        3. ``ManualPublishProvider`` (always available)
        """
        provider_name = _DEFAULT_PLATFORM_PROVIDERS.get(platform, "manual")

        if config is not None:
            provider_name = config.platform_providers.get(platform, provider_name)
            # Global override
            if config.default_provider and platform not in (config.platform_providers or {}):
                provider_name = config.default_provider

        return cls._build(provider_name, config)

    @classmethod
    def for_manifest(
        cls,
        manifest: Any,
        config: "PublishConfig | None" = None,
    ) -> "PublishProvider":
        """Return a provider for the platform named in *manifest*."""
        return cls.for_platform(manifest.platform, config)

    @classmethod
    def _build(
        cls,
        provider_name: str,
        config: "PublishConfig | None",
    ) -> "PublishProvider":
        from clipforge.providers.publish.manual_provider import ManualPublishProvider

        name = provider_name.lower().strip()

        if name == "manual":
            return ManualPublishProvider()

        if name == "youtube":
            from clipforge.providers.publish.youtube_provider import YouTubePublishProvider
            creds = ""
            if config is not None:
                creds = config.youtube_credentials_path
            return YouTubePublishProvider(credentials_path=creds)

        # Unknown provider — fall back to manual with a note
        return ManualPublishProvider()

    @classmethod
    def available_providers(cls) -> list[str]:
        """Return the list of known provider names."""
        return ["manual", "youtube"]

    @classmethod
    def is_real_provider(cls, provider_name: str) -> bool:
        """Return True if *provider_name* does a real platform upload."""
        return provider_name.lower() in {"youtube"}
