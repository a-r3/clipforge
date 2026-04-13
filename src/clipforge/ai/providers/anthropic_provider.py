"""Anthropic provider for ClipForge AI integration."""

from __future__ import annotations

import json
import logging
from typing import Any

from clipforge.ai.base import AIProvider

logger = logging.getLogger(__name__)


class AnthropicProvider(AIProvider):
    """AI provider using the Anthropic Claude API."""

    def __init__(self, api_key: str = "", model: str = "claude-3-haiku-20240307") -> None:
        super().__init__(api_key=api_key, model=model)

    def generate(self, prompt: str, schema: dict[str, Any] | None = None) -> dict[str, Any]:
        """Send *prompt* to Anthropic and return a structured dict.

        Raises RuntimeError if the call fails.
        """
        try:
            import anthropic  # lazy import
        except ImportError as exc:
            raise RuntimeError("anthropic package is not installed. Run: pip install anthropic") from exc

        client = anthropic.Anthropic(api_key=self.api_key)

        system_prompt = "You are a helpful assistant. Always respond with valid JSON only, no extra text."

        try:
            message = client.messages.create(
                model=self.model,
                max_tokens=512,
                system=system_prompt,
                messages=[{"role": "user", "content": prompt}],
            )
            content = message.content[0].text if message.content else "{}"
            # Extract JSON from response
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                content = content[start:end]
            return json.loads(content)
        except Exception as exc:
            logger.error("Anthropic API error: %s", exc)
            raise RuntimeError(f"Anthropic generation failed: {exc}") from exc
