"""Publish provider package.

V5 ships:
  - ManualPublishProvider — first-class manual handoff (always available)
  - YouTubePublishProvider — real YouTube Data API v3 upload
  - PublishProviderFactory — select provider by platform/config

The abstract base (PublishProvider) and data classes (PublishTarget,
PublishResult) are importable directly from this package for convenience.
"""
from clipforge.providers.publish.base import (
    PublishNotAvailableError,
    PublishProvider,
    PublishResult,
    PublishTarget,
)

__all__ = [
    "PublishProvider",
    "PublishResult",
    "PublishTarget",
    "PublishNotAvailableError",
]
