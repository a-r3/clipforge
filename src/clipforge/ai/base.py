"""Abstract base class for AI providers in ClipForge."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class AIProvider(ABC):
    """Abstract base class for AI providers.

    All providers must implement ``generate()``.
    """

    def __init__(self, api_key: str = "", model: str = "") -> None:
        self.api_key = api_key
        self.model = model

    @abstractmethod
    def generate(self, prompt: str, schema: dict[str, Any] | None = None) -> dict[str, Any]:
        """Send *prompt* to the AI and return a structured dict.

        Args:
            prompt: The prompt text.
            schema: Optional JSON schema hint describing the expected output.

        Returns:
            A dict with the AI response (structured according to schema if provided).

        Raises:
            RuntimeError: If the AI call fails and cannot be handled.
        """

    def is_available(self) -> bool:
        """Return True if the provider is configured and ready."""
        return bool(self.api_key)

    def __repr__(self) -> str:
        cls = type(self).__name__
        model = self.model or "default"
        return f"{cls}(model={model!r})"
