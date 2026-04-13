"""AI provider factory for ClipForge."""

from __future__ import annotations

import logging
from typing import Any

from clipforge.ai.base import AIProvider

logger = logging.getLogger(__name__)


class AIFactory:
    """Create AI provider instances by name."""

    @staticmethod
    def get_provider(provider_name: str, api_key: str = "", model: str = "") -> AIProvider | None:
        """Return an AIProvider instance for *provider_name*.

        Returns None if the provider is unknown, the key is missing, or the
        required library is not installed.

        Args:
            provider_name: One of 'openai', 'anthropic', 'gemini'.
            api_key: API key for the provider.
            model: Optional model name override.

        Returns:
            An AIProvider instance, or None.
        """
        if not provider_name:
            return None

        provider_name = provider_name.lower().strip()

        if not api_key:
            logger.warning("No API key provided for AI provider '%s'.", provider_name)
            return None

        try:
            if provider_name == "openai":
                from clipforge.ai.providers.openai_provider import OpenAIProvider
                return OpenAIProvider(api_key=api_key, model=model or "gpt-4o-mini")

            if provider_name in ("anthropic", "claude"):
                from clipforge.ai.providers.anthropic_provider import AnthropicProvider
                return AnthropicProvider(api_key=api_key, model=model or "claude-3-haiku-20240307")

            if provider_name in ("gemini", "google"):
                from clipforge.ai.providers.gemini_provider import GeminiProvider
                return GeminiProvider(api_key=api_key, model=model or "gemini-pro")

            logger.warning("Unknown AI provider: '%s'.", provider_name)
            return None

        except ImportError as exc:
            logger.warning(
                "AI provider '%s' is not available (missing dependency: %s).",
                provider_name,
                exc,
            )
            return None
        except Exception as exc:
            logger.warning("Failed to initialise AI provider '%s': %s", provider_name, exc)
            return None
