"""Manual publish provider — first-class safe path for human-handled publishing.

When direct platform publishing is unavailable or not desired, the manual
provider validates the content, produces a human-readable handoff checklist,
and marks the queue item as ``manual_action_required``.

This is NOT a fallback hack.  It is a valid, first-class publish path.

Usage::

    from clipforge.providers.publish.manual_provider import ManualPublishProvider

    provider = ManualPublishProvider()
    result = provider.dry_run_publish(target)   # just validate
    result = provider.publish(target)            # produce checklist, set status
    print(result.response_summary)

The checklist is also written to a ``<job_name>_checklist.txt`` file if
``checklist_dir`` is provided in ``target.extra``.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

from clipforge.providers.publish.base import (
    PublishProvider,
    PublishResult,
    PublishTarget,
)


class ManualPublishProvider(PublishProvider):
    """First-class manual publishing provider.

    Validates content readiness and produces a publish checklist.
    Marks the result as ``manual_action_required=True`` — it is the caller's
    responsibility to update the manifest/queue status accordingly.

    Never marks success=True.  The human must confirm publication.
    """

    PROVIDER_NAME = "manual"

    def __init__(self) -> None:
        # No API key needed — always available
        super().__init__(api_key="", access_token="")

    def is_available(self) -> bool:
        """Manual provider is always available."""
        return True

    def provider_name(self) -> str:
        return "manual"

    # ── Validation ────────────────────────────────────────────────────────────

    def validate_target(self, target: PublishTarget) -> list[str]:
        """Check that the target is ready for manual handoff."""
        errors: list[str] = []

        if not target.video_path:
            errors.append("video_path is required")
        elif not os.path.exists(target.video_path):
            errors.append(f"video_path does not exist: {target.video_path}")

        if target.thumbnail_path and not os.path.exists(target.thumbnail_path):
            errors.append(f"thumbnail_path does not exist: {target.thumbnail_path}")

        if not target.title and not target.caption:
            errors.append("at least one of title or caption is required")

        if not target.platform:
            errors.append("platform is required")

        return errors

    # ── Dry-run ───────────────────────────────────────────────────────────────

    def dry_run_publish(self, target: PublishTarget) -> PublishResult:
        """Validate and describe what the manual checklist would contain."""
        errors = self.validate_target(target)
        checklist_lines = self._build_checklist(target)

        summary_lines = ["Manual publish dry-run:"]
        summary_lines.append(f"  Platform : {target.platform or '(not set)'}")
        summary_lines.append(f"  Video    : {target.video_path or '(not set)'}")
        summary_lines.append(f"  Title    : {target.title or '(not set)'}")
        if errors:
            summary_lines.append(f"  Errors   : {len(errors)}")
            for e in errors:
                summary_lines.append(f"    ! {e}")
        else:
            summary_lines.append(f"  Checklist: {len(checklist_lines)} step(s) ready")
            summary_lines.append("  Status would be: manual_action_required")

        return PublishResult(
            success=not bool(errors),
            dry_run=True,
            provider=self.PROVIDER_NAME,
            platform=target.platform,
            manual_action_required=True,
            error="; ".join(errors),
            response_summary="\n".join(summary_lines),
            metadata={"checklist_preview": checklist_lines[:5]},
        )

    # ── Publish ───────────────────────────────────────────────────────────────

    def publish(self, target: PublishTarget) -> PublishResult:
        """Produce a manual publish checklist and mark as manual_action_required.

        Never marks success=True — a human must complete the upload.
        Optionally writes a checklist file if ``target.extra['checklist_dir']``
        is provided.
        """
        errors = self.validate_target(target)
        if errors:
            return PublishResult(
                success=False,
                provider=self.PROVIDER_NAME,
                platform=target.platform,
                manual_action_required=True,
                error="; ".join(errors),
                response_summary=f"Validation failed ({len(errors)} error(s)); cannot prepare checklist.",
            )

        checklist_lines = self._build_checklist(target)
        checklist_text = "\n".join(checklist_lines)

        # Write checklist file if a dir was given
        checklist_path = ""
        checklist_dir = target.extra.get("checklist_dir", "")
        if checklist_dir:
            d = Path(checklist_dir)
            d.mkdir(parents=True, exist_ok=True)
            job = target.extra.get("job_name", Path(target.video_path).stem)
            checklist_path = str(d / f"{job}_checklist.txt")
            Path(checklist_path).write_text(checklist_text, encoding="utf-8")

        summary = (
            f"Manual publish checklist prepared for '{target.platform}'.\n"
            f"  {len(checklist_lines)} step(s). "
            + (f"Saved to: {checklist_path}" if checklist_path else "No file saved.")
            + "\n  Status: manual_action_required — a human must complete the upload."
        )

        return PublishResult(
            success=False,          # never True for manual provider
            provider=self.PROVIDER_NAME,
            platform=target.platform,
            manual_action_required=True,
            response_summary=summary,
            metadata={
                "checklist": checklist_lines,
                "checklist_path": checklist_path,
            },
        )

    # ── Checklist builder ─────────────────────────────────────────────────────

    def _build_checklist(self, target: PublishTarget) -> list[str]:
        """Build a human-readable publish checklist for the given target."""
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        lines: list[str] = [
            f"ClipForge Manual Publish Checklist — {target.platform.upper()}",
            f"Generated: {now}",
            "=" * 60,
            "",
            "FILES",
            f"  [ ] Upload video   : {target.video_path}",
        ]

        if target.thumbnail_path:
            lines.append(f"  [ ] Upload thumbnail: {target.thumbnail_path}")
        else:
            lines.append("  [ ] Thumbnail      : (none provided — consider adding one)")

        lines += ["", "METADATA"]
        if target.title:
            lines.append(f"  [ ] Set title      : {target.title}")
        if target.caption:
            short_cap = (target.caption[:80] + "…") if len(target.caption) > 80 else target.caption
            lines.append(f"  [ ] Set caption    : {short_cap}")
        if target.hashtags:
            lines.append(f"  [ ] Set hashtags   : {target.hashtags}")
        if target.tags:
            lines.append(f"  [ ] Set tags       : {', '.join(target.tags[:10])}")
        if target.privacy:
            lines.append(f"  [ ] Privacy        : {target.privacy}")

        if target.schedule_at:
            lines += ["", "SCHEDULING"]
            lines.append(f"  [ ] Schedule for   : {target.schedule_at}")

        lines += [
            "",
            "PUBLISHING",
            f"  [ ] Log in to {target.platform} account",
            "  [ ] Upload and configure the video",
            "  [ ] Confirm publish / scheduling",
            "  [ ] Record the post URL below:",
            "      Post URL: _________________________________",
            "",
            "  [ ] Update ClipForge queue status to 'published'",
            "      clipforge queue status <queue_dir> <manifest_id> published",
        ]

        return lines
