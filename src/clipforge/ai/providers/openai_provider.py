"""OpenAI provider for ClipForge AI integration."""

from __future__ import annotations

import json
import logging
from typing import Any

from clipforge.ai.base import AIProvider

logger = logging.getLogger(__name__)


class OpenAIProvider(AIProvider):
    """AI provider using the OpenAI API."""

    def __init__(self, api_key: str = "", model: str = "gpt-4o-mini") -> None:
        super().__init__(api_key=api_key, model=model)

    def generate(self, prompt: str, schema: dict[str, Any] | None = None) -> dict[str, Any]:
        """Send *prompt* to OpenAI and return a structured dict.

        Raises RuntimeError if the call fails.
        """
        try:
            import openai  # lazy import
        except ImportError as exc:
            raise RuntimeError("openai package is not installed. Run: pip install openai") from exc

        client = openai.OpenAI(api_key=self.api_key)

        messages = [
            {"role": "system", "content": "You are a helpful assistant. Always respond with valid JSON."},
            {"role": "user", "content": prompt},
        ]

        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                response_format={"type": "json_object"},
                max_tokens=512,
                temperature=0.7,
            )
            content = response.choices[0].message.content or "{}"
            return json.loads(content)
        except Exception as exc:
            logger.error("OpenAI API error: %s", exc)
            raise RuntimeError(f"OpenAI generation failed: {exc}") from exc
