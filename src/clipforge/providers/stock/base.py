"""Abstract base class for stock media providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class StockResult:
    """A single stock media result."""

    local_path: str | None = None
    source: str = "fallback"    # e.g. "pexels_video", "pixabay_image", "fallback"
    media_type: str = "video"   # "video" or "image"
    query_used: str = ""
    provider: str = ""
    asset_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def success(self) -> bool:
        """True if a local file was downloaded."""
        return self.local_path is not None


class StockProvider(ABC):
    """Abstract base class for stock media providers.

    Implementations should query an external stock API and return a
    ``StockResult``.  They must handle their own API keys, caching,
    retries, and graceful degradation.

    Usage::

        class PexelsProvider(StockProvider):
            def fetch(self, query, width, height, used_ids=None):
                ...

        result = PexelsProvider(api_key="...").fetch("AI technology", 1080, 1920)
        if result.success:
            use(result.local_path)
    """

    def __init__(self, api_key: str = "", cache_dir: str = "assets/downloads") -> None:
        self.api_key = api_key
        self.cache_dir = cache_dir

    @abstractmethod
    def fetch(
        self,
        query: str,
        width: int,
        height: int,
        used_ids: set[str] | None = None,
    ) -> StockResult:
        """Fetch media for *query* at the given dimensions.

        Args:
            query:    Search query string.
            width:    Target video/image width in pixels.
            height:   Target video/image height in pixels.
            used_ids: Optional set of already-used asset IDs to avoid
                      returning duplicate media.

        Returns:
            ``StockResult`` — check ``.success`` before using ``.local_path``.
        """

    def is_available(self) -> bool:
        """Return True if this provider has a valid API key configured."""
        return bool(self.api_key)

    def __repr__(self) -> str:
        cls = type(self).__name__
        return f"{cls}(available={self.is_available()})"
