"""Publish queue — local file-backed queue for publish manifests.

A queue is a folder containing:

    queue.json         — metadata + ordered list of manifest IDs
    manifests/         — one .json per manifest entry

Usage::

    from clipforge.publish_queue import PublishQueue

    q = PublishQueue.init("./publish_queue")
    q.append(manifest)

    for entry in q.filter_by_status("ready"):
        print(entry.job_name, entry.publish_at)

    q.update_status(manifest_id, "scheduled")
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from clipforge.publish_manifest import PublishManifest, VALID_STATUSES


_QUEUE_FILE = "queue.json"
_MANIFESTS_DIR = "manifests"


class PublishQueue:
    """Local file-backed queue of :class:`PublishManifest` entries.

    Each queue lives in its own folder.  The top-level ``queue.json``
    stores metadata and an ordered list of manifest IDs; each manifest
    is stored as an individual JSON file in ``manifests/``.

    Statuses (in rough lifecycle order):

    * **draft** — created but not ready to go
    * **pending** — waiting for approval / review
    * **ready** — approved, waiting to be scheduled
    * **scheduled** — has a ``publish_at`` time set
    * **manual_action_required** — needs human intervention
    * **published** — successfully published (terminal)
    * **failed** — publish attempt failed (terminal)
    * **archived** — removed from active queue (terminal)
    """

    def __init__(
        self,
        path: str | Path,
        name: str = "",
        created_at: str = "",
        updated_at: str = "",
        entry_ids: list[str] | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        self.path = Path(path).resolve()
        self.name = name or self.path.name
        now = datetime.now(timezone.utc).isoformat()
        self.created_at = created_at or now
        self.updated_at = updated_at or now
        self._entry_ids: list[str] = entry_ids or []
        self.extra: dict[str, Any] = extra or {}

    # ── Factory ───────────────────────────────────────────────────────────────

    @classmethod
    def init(cls, path: str | Path, name: str = "") -> "PublishQueue":
        """Create a new queue at *path*.

        Creates the folder structure and saves an empty queue.json.
        Returns the new queue.
        """
        p = Path(path)
        p.mkdir(parents=True, exist_ok=True)
        (p / _MANIFESTS_DIR).mkdir(exist_ok=True)
        q = cls(path=p, name=name or p.name)
        q.save()
        return q

    @classmethod
    def load(cls, path: str | Path) -> "PublishQueue":
        """Load an existing queue from *path*.

        Raises FileNotFoundError if the queue folder or queue.json is missing.
        """
        p = Path(path)
        qfile = p / _QUEUE_FILE
        if not p.is_dir():
            raise FileNotFoundError(f"Queue directory not found: {path}")
        if not qfile.exists():
            raise FileNotFoundError(
                f"Not a ClipForge queue (missing {_QUEUE_FILE}): {path}"
            )
        data = json.loads(qfile.read_text(encoding="utf-8"))
        return cls(
            path=p,
            name=data.get("name", p.name),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            entry_ids=data.get("entry_ids", []),
            extra={k: v for k, v in data.items()
                   if k not in {"name", "created_at", "updated_at", "entry_ids"}},
        )

    # ── Persistence ───────────────────────────────────────────────────────────

    def save(self) -> None:
        """Persist queue metadata to queue.json."""
        self.updated_at = datetime.now(timezone.utc).isoformat()
        data: dict[str, Any] = {
            "name": self.name,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "entry_ids": self._entry_ids,
        }
        data.update(self.extra)
        (self.path / _QUEUE_FILE).write_text(
            json.dumps(data, indent=2), encoding="utf-8"
        )

    def _manifest_path(self, manifest_id: str) -> Path:
        return self.path / _MANIFESTS_DIR / f"{manifest_id}.json"

    # ── Queue operations ──────────────────────────────────────────────────────

    def append(self, manifest: PublishManifest) -> None:
        """Add a manifest to the end of the queue.

        Saves the manifest file and updates queue.json.
        Raises ValueError if a manifest with the same ID already exists.
        """
        if manifest.manifest_id in self._entry_ids:
            raise ValueError(
                f"Manifest '{manifest.manifest_id}' is already in the queue."
            )
        manifest.save(self._manifest_path(manifest.manifest_id))
        self._entry_ids.append(manifest.manifest_id)
        self.save()

    def get(self, manifest_id: str) -> PublishManifest:
        """Load and return a manifest by ID.

        Raises KeyError if the ID is not in the queue.
        Raises FileNotFoundError if the manifest file is missing.
        """
        if manifest_id not in self._entry_ids:
            raise KeyError(f"Manifest '{manifest_id}' not found in queue.")
        return PublishManifest.load(self._manifest_path(manifest_id))

    def update_status(self, manifest_id: str, status: str) -> None:
        """Update the status of a manifest in the queue.

        Raises ValueError for invalid status strings.
        Raises KeyError if the manifest is not in the queue.
        """
        if status not in VALID_STATUSES:
            raise ValueError(
                f"Invalid status '{status}'. "
                f"Valid values: {', '.join(sorted(VALID_STATUSES))}"
            )
        m = self.get(manifest_id)
        m.status = status
        m.touch()
        m.save(self._manifest_path(manifest_id))

    def remove(self, manifest_id: str) -> None:
        """Remove a manifest from the queue (does not delete the file)."""
        if manifest_id not in self._entry_ids:
            raise KeyError(f"Manifest '{manifest_id}' not found in queue.")
        self._entry_ids.remove(manifest_id)
        self.save()

    # ── Listing and filtering ─────────────────────────────────────────────────

    def list(self) -> list[PublishManifest]:
        """Return all manifests in queue order."""
        result = []
        for mid in self._entry_ids:
            mpath = self._manifest_path(mid)
            if mpath.exists():
                result.append(PublishManifest.load(mpath))
        return result

    def filter_by_status(self, status: str) -> list[PublishManifest]:
        """Return manifests whose status matches *status*."""
        return [m for m in self.list() if m.status == status]

    def filter_by_platform(self, platform: str) -> list[PublishManifest]:
        """Return manifests whose platform matches *platform*."""
        return [m for m in self.list() if m.platform == platform]

    def filter_by_campaign(self, campaign_name: str) -> list[PublishManifest]:
        """Return manifests belonging to *campaign_name*."""
        return [m for m in self.list() if m.campaign_name == campaign_name]

    # ── Summary ───────────────────────────────────────────────────────────────

    def summary(self) -> dict[str, Any]:
        """Return a summary dict with counts by status."""
        counts: dict[str, int] = {s: 0 for s in sorted(VALID_STATUSES)}
        total = 0
        for m in self.list():
            counts[m.status] = counts.get(m.status, 0) + 1
            total += 1
        return {
            "name": self.name,
            "path": str(self.path),
            "total": total,
            "by_status": counts,
            "updated_at": self.updated_at,
        }

    def __len__(self) -> int:
        return len(self._entry_ids)

    def __repr__(self) -> str:
        return f"PublishQueue(name={self.name!r}, entries={len(self)})"
