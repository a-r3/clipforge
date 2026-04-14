"""Publish configuration — provider credentials and defaults.

Keeps all publish-provider configuration in one place.
Never stores secrets in the config file; credentials are always file paths.

Config is loaded from a JSON file and can be supplemented by environment
variables.

Usage::

    from clipforge.publish_config import PublishConfig

    config = PublishConfig.from_env()          # env vars only
    config = PublishConfig.load("publish.json")  # file + env vars

    provider = config.get_provider_for("youtube")

Environment variables:
    CLIPFORGE_PUBLISH_DRY_RUN       Set to "1" to default all publishes to dry-run.
    CLIPFORGE_DEFAULT_PROVIDER      Override default provider name.
    YOUTUBE_CREDENTIALS_PATH        Path to YouTube credentials JSON.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class PublishConfig:
    """Publish provider configuration.

    Fields
    ------
    default_provider:
        Provider name used when no platform-specific override exists.
        Defaults to ``"manual"`` (safe).
    dry_run_default:
        If True, all publish calls default to dry-run unless the caller
        explicitly opts in to real publishing.
    youtube_credentials_path:
        Path to a Google credentials JSON (OAuth2 token or service account).
    platform_providers:
        Override which provider handles each platform, e.g.
        ``{"youtube": "youtube", "reels": "manual"}``.
    extra:
        Arbitrary additional fields for future providers.
    """

    default_provider: str = "manual"
    dry_run_default: bool = False
    youtube_credentials_path: str = ""
    platform_providers: dict[str, str] = field(default_factory=dict)
    extra: dict[str, Any] = field(default_factory=dict)

    # ── Factories ─────────────────────────────────────────────────────────────

    @classmethod
    def from_env(cls) -> "PublishConfig":
        """Build a PublishConfig populated from environment variables only."""
        dry_run = os.environ.get("CLIPFORGE_PUBLISH_DRY_RUN", "").strip() in ("1", "true", "yes")
        return cls(
            default_provider=os.environ.get("CLIPFORGE_DEFAULT_PROVIDER", "manual"),
            dry_run_default=dry_run,
            youtube_credentials_path=os.environ.get("YOUTUBE_CREDENTIALS_PATH", ""),
        )

    @classmethod
    def load(cls, path: str | Path) -> "PublishConfig":
        """Load from a JSON file, then apply env var overrides.

        Raises FileNotFoundError if the file does not exist.
        """
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Publish config not found: {path}")
        data = json.loads(p.read_text(encoding="utf-8"))

        base = cls(
            default_provider=data.get("default_provider", "manual"),
            dry_run_default=data.get("dry_run_default", False),
            youtube_credentials_path=data.get("youtube_credentials_path", ""),
            platform_providers=data.get("platform_providers", {}),
            extra={k: v for k, v in data.items() if k not in {
                "default_provider", "dry_run_default",
                "youtube_credentials_path", "platform_providers",
            }},
        )

        # Env var overrides win over file values
        env = cls.from_env()
        if env.youtube_credentials_path:
            base.youtube_credentials_path = env.youtube_credentials_path
        if os.environ.get("CLIPFORGE_DEFAULT_PROVIDER"):
            base.default_provider = env.default_provider
        if os.environ.get("CLIPFORGE_PUBLISH_DRY_RUN"):
            base.dry_run_default = env.dry_run_default

        return base

    @classmethod
    def load_or_default(cls, path: str | Path | None) -> "PublishConfig":
        """Load from *path* if given and exists, otherwise use env/defaults."""
        if path:
            p = Path(path)
            if p.exists():
                return cls.load(p)
        return cls.from_env()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def save(self, path: str | Path) -> None:
        """Save to a JSON file (does NOT write credentials — only paths)."""
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        data: dict[str, Any] = {
            "default_provider": self.default_provider,
            "dry_run_default": self.dry_run_default,
            "youtube_credentials_path": self.youtube_credentials_path,
            "platform_providers": self.platform_providers,
        }
        data.update(self.extra)
        p.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "default_provider": self.default_provider,
            "dry_run_default": self.dry_run_default,
            "youtube_credentials_path": self.youtube_credentials_path,
            "platform_providers": dict(self.platform_providers),
        }
        d.update(self.extra)
        return d

    def is_provider_enabled(self, name: str) -> bool:
        """Return True if *name* is usable (always True for manual)."""
        if name == "manual":
            return True
        if name == "youtube":
            return bool(self.youtube_credentials_path)
        return False

    def __repr__(self) -> str:
        enabled = [k for k, v in {
            "manual": True,
            "youtube": bool(self.youtube_credentials_path),
        }.items() if v]
        return (
            f"PublishConfig(default={self.default_provider!r}, "
            f"dry_run={self.dry_run_default}, "
            f"enabled_providers={enabled})"
        )
