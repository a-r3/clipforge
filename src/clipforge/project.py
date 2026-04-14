"""Project/session support for ClipForge.

A ClipForge project is a folder that keeps everything for a channel or campaign
together: scripts, configs, profiles, output, and assets.

Project structure::

    my-project/
        project.json          # metadata and defaults
        scripts/              # .txt script files
        output/               # rendered videos
        assets/
            music/            # background tracks
            logo/             # brand images
            downloads/        # cached stock media
        config.json           # default config (optional)
        profile.json          # default brand profile (optional)

Usage::

    # Create a new project
    project = ClipForgeProject.init("./my-project", name="TechBrief")
    project.save()

    # Load an existing project
    project = ClipForgeProject.load("./my-project")
    config = project.build_config(overrides={"platform": "reels"})
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


_PROJECT_FILE = "project.json"
_PROJECT_SUBDIRS = ["scripts", "output", "assets/music", "assets/logo", "assets/downloads"]


class ClipForgeProject:
    """A reusable ClipForge project folder.

    Stores project metadata and default settings. Apply to any build
    with ``build_config()`` which merges project defaults with overrides.
    """

    def __init__(
        self,
        path: str | Path,
        name: str = "",
        platform: str = "reels",
        style: str = "clean",
        brand_name: str = "",
        profile_file: str = "",
        config_file: str = "",
        # Publish / queue defaults
        default_queue: str = "",
        default_campaign: str = "",
        default_publish_target: str = "",
        manual_review_required: bool = False,
        created_at: str = "",
        updated_at: str = "",
        extra: dict[str, Any] | None = None,
    ) -> None:
        self.path = Path(path).resolve()
        self.name = name or self.path.name
        self.platform = platform
        self.style = style
        self.brand_name = brand_name
        self.profile_file = profile_file
        self.config_file = config_file
        self.default_queue = default_queue
        self.default_campaign = default_campaign
        self.default_publish_target = default_publish_target
        self.manual_review_required = manual_review_required
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()
        self.updated_at = updated_at or self.created_at
        self.extra: dict[str, Any] = extra or {}

    # ------------------------------------------------------------------
    # Factory methods
    # ------------------------------------------------------------------

    @classmethod
    def init(
        cls,
        path: str | Path,
        name: str = "",
        platform: str = "reels",
        style: str = "",
        brand_name: str = "",
    ) -> "ClipForgeProject":
        """Create a new project at *path*.

        Creates the folder structure but does NOT save yet — call
        ``project.save()`` when ready.
        """
        p = Path(path)
        p.mkdir(parents=True, exist_ok=True)
        for subdir in _PROJECT_SUBDIRS:
            (p / subdir).mkdir(parents=True, exist_ok=True)

        # Auto-pick smart style if not given
        if not style:
            style = "bold" if platform in ("reels", "tiktok") else "clean"

        return cls(path=p, name=name or p.name, platform=platform,
                   style=style, brand_name=brand_name)

    @classmethod
    def load(cls, path: str | Path) -> "ClipForgeProject":
        """Load a project from an existing project folder.

        Raises FileNotFoundError if the folder or project.json is missing.
        """
        p = Path(path)
        meta_file = p / _PROJECT_FILE
        if not p.is_dir():
            raise FileNotFoundError(f"Project directory not found: {path}")
        if not meta_file.exists():
            raise FileNotFoundError(
                f"Not a ClipForge project (missing {_PROJECT_FILE}): {path}"
            )
        data = json.loads(meta_file.read_text(encoding="utf-8"))
        extra = {k: v for k, v in data.items() if k not in {
            "name", "platform", "style", "brand_name",
            "profile_file", "config_file",
            "default_queue", "default_campaign", "default_publish_target",
            "manual_review_required",
            "created_at", "updated_at",
        }}
        return cls(
            path=p,
            name=data.get("name", p.name),
            platform=data.get("platform", "reels"),
            style=data.get("style", "clean"),
            brand_name=data.get("brand_name", ""),
            profile_file=data.get("profile_file", ""),
            config_file=data.get("config_file", ""),
            default_queue=data.get("default_queue", ""),
            default_campaign=data.get("default_campaign", ""),
            default_publish_target=data.get("default_publish_target", ""),
            manual_review_required=data.get("manual_review_required", False),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            extra=extra,
        )

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self) -> None:
        """Save project metadata to project.json."""
        self.updated_at = datetime.now(timezone.utc).isoformat()
        data: dict[str, Any] = {
            "name": self.name,
            "platform": self.platform,
            "style": self.style,
            "brand_name": self.brand_name,
            "profile_file": self.profile_file,
            "config_file": self.config_file,
            "default_queue": self.default_queue,
            "default_campaign": self.default_campaign,
            "default_publish_target": self.default_publish_target,
            "manual_review_required": self.manual_review_required,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        data.update(self.extra)
        meta_file = self.path / _PROJECT_FILE
        meta_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "name": self.name,
            "path": str(self.path),
            "platform": self.platform,
            "style": self.style,
            "brand_name": self.brand_name,
            "profile_file": self.profile_file,
            "config_file": self.config_file,
            "default_queue": self.default_queue,
            "default_campaign": self.default_campaign,
            "default_publish_target": self.default_publish_target,
            "manual_review_required": self.manual_review_required,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        d.update(self.extra)
        return d

    # ------------------------------------------------------------------
    # Config integration
    # ------------------------------------------------------------------

    def build_config(self, overrides: dict[str, Any] | None = None) -> dict[str, Any]:
        """Return a config dict combining project defaults and *overrides*.

        Load order (later wins):
        1. Project defaults (platform, style, brand_name, output dir)
        2. Project-level config.json (if present)
        3. Project-level profile.json (if present)
        4. *overrides* passed in by the caller
        """
        from clipforge.config_loader import load_config
        from clipforge.utils import merge_dicts

        # Resolve config and profile paths relative to project folder
        config_path = self._resolve(self.config_file) if self.config_file else None
        profile_path = self._resolve(self.profile_file) if self.profile_file else None

        project_defaults: dict[str, Any] = {
            "platform": self.platform,
            "style": self.style,
            "brand_name": self.brand_name,
            "output": str(self.path / "output" / "video.mp4"),
        }

        config = load_config(config_path, overrides=project_defaults)

        if profile_path and profile_path.exists():
            from clipforge.profile import BrandProfile
            profile = BrandProfile.load(profile_path)
            config = profile.apply_to_config(config)

        if overrides:
            config = merge_dicts(config, {k: v for k, v in overrides.items() if v is not None})

        return config

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _resolve(self, rel_path: str) -> Path:
        """Resolve a path relative to the project folder."""
        p = Path(rel_path)
        if p.is_absolute():
            return p
        return self.path / p

    def scripts_dir(self) -> Path:
        return self.path / "scripts"

    def output_dir(self) -> Path:
        return self.path / "output"

    def list_scripts(self) -> list[Path]:
        """Return all .txt files in the scripts directory."""
        d = self.scripts_dir()
        if not d.is_dir():
            return []
        return sorted(d.glob("*.txt"))

    def make_manifest(
        self,
        job_name: str = "",
        video_path: str = "",
        overrides: "dict[str, Any] | None" = None,
    ) -> "Any":
        """Create a :class:`PublishManifest` pre-populated with project defaults.

        The manifest is returned but NOT saved — call ``manifest.save(path)``
        when ready.  To add to the project queue, use::

            m = project.make_manifest(...)
            q = PublishQueue.load(project.queue_dir())
            q.append(m)
        """
        from clipforge.publish_manifest import PublishManifest

        kw: dict[str, Any] = {
            "job_name": job_name,
            "project_name": self.name,
            "platform": self.platform,
            "video_path": video_path,
            "brand_name": self.brand_name,
            "profile_ref": self.profile_file,
            "queue_name": self.default_queue or "default",
            "campaign_name": self.default_campaign,
            "publish_target": self.default_publish_target,
            "manual_review_required": self.manual_review_required,
            "status": "draft",
        }
        if overrides:
            kw.update({k: v for k, v in overrides.items() if v is not None})
        return PublishManifest(**kw)

    def queue_dir(self) -> "Path":
        """Return the path to this project's default publish queue folder."""
        return self.path / "publish_queue"

    def __repr__(self) -> str:
        return f"ClipForgeProject(name={self.name!r}, path={str(self.path)!r})"
