"""Google Gemini provider for ClipForge AI integration."""

from __future__ import annotations

import json
import logging
from typing import Any

from clipforge.ai.base import AIProvider

logger = logging.getLogger(__name__)


class GeminiProvider(AIProvider):
    """AI provider using the Google Gemini API."""

    def __init__(self, api_key: str = "", model: str = "gemini-pro") -> None:
        super().__init__(api_key=api_key, model=model)

    def generate(self, prompt: str, schema: dict[str, Any] | None = None) -> dict[str, Any]:
        """Send *prompt* to Gemini and return a structured dict.

        Raises RuntimeError if the call fails.
        """
        try:
            import google.generativeai as genai  # lazy import
        except ImportError as exc:
            raise RuntimeError(
                "google-generativeai package is not installed. "
                "Run: pip install google-generativeai"
            ) from exc

        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel(self.model)

        full_prompt = prompt + "\n\nRespond with valid JSON only."

        try:
            response = model.generate_content(full_prompt)
            content = response.text or "{}"
            # Extract JSON from response
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                content = content[start:end]
            return json.loads(content)
        except Exception as exc:
            logger.error("Gemini API error: %s", exc)
            raise RuntimeError(f"Gemini generation failed: {exc}") from exc
