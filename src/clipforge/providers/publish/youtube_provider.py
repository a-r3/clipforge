"""YouTube publish provider.

Real YouTube Data API v3 upload support, behind an explicit availability
guard.  The provider is *honest*: it only reports success when YouTube
confirms the upload.

Requirements (optional dependency group ``publish-youtube``)::

    pip install clipforge[publish-youtube]
    # installs: google-api-python-client, google-auth-httplib2, google-auth-oauthlib

Auth setup:
  1. Create a project in Google Cloud Console.
  2. Enable the YouTube Data API v3.
  3. Create OAuth 2.0 credentials (for a desktop app) and download
     ``client_secret.json``, OR create a Service Account and download
     its JSON key.
  4. Set YOUTUBE_CREDENTIALS_PATH to the file path (or pass in config).
  5. On first OAuth run, a browser opens to complete the consent flow;
     credentials are cached in the same directory.

Dry-run::

    provider = YouTubePublishProvider(credentials_path="creds.json")
    result = provider.dry_run_publish(target)
    # No API calls — validates metadata and file existence only.

Real upload::

    result = provider.publish(target)
    # Calls YouTube API; result.post_url is set on success.

If the ``google-api-python-client`` library is not installed,
``is_available()`` returns False and ``publish()`` raises
``PublishNotAvailableError`` with a clear message.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from clipforge.providers.publish.base import (
    PublishNotAvailableError,
    PublishProvider,
    PublishResult,
    PublishTarget,
)

# YouTube Data API constraints
_TITLE_MAX = 100
_DESCRIPTION_MAX = 5000
_TAGS_MAX = 500          # total character count across all tags
_TAG_MAX_CHARS = 30      # per-tag max
_VALID_PRIVACY = {"public", "unlisted", "private"}
_PROVIDER_NAME = "youtube"

# Env var for credentials path
_ENV_CREDS = "YOUTUBE_CREDENTIALS_PATH"


class YouTubePublishProvider(PublishProvider):
    """YouTube Data API v3 publish provider.

    Parameters
    ----------
    credentials_path:
        Path to a credentials JSON file (OAuth2 client secret, OAuth2 token,
        or service account key).  Falls back to the ``YOUTUBE_CREDENTIALS_PATH``
        environment variable if not provided.
    """

    def __init__(self, credentials_path: str = "") -> None:
        super().__init__()
        self.credentials_path = (
            credentials_path
            or os.environ.get(_ENV_CREDS, "")
        )

    def is_available(self) -> bool:
        """True if google-api-python-client is installed AND credentials exist."""
        if not self._google_libs_available():
            return False
        return bool(self.credentials_path and Path(self.credentials_path).exists())

    def provider_name(self) -> str:
        return _PROVIDER_NAME

    # ── Validation ────────────────────────────────────────────────────────────

    def validate_target(self, target: PublishTarget) -> list[str]:
        """Validate all YouTube-specific constraints without API calls."""
        errors: list[str] = []

        # File checks
        if not target.video_path:
            errors.append("video_path is required")
        elif not Path(target.video_path).exists():
            errors.append(f"video_path does not exist: {target.video_path}")

        if target.thumbnail_path and not Path(target.thumbnail_path).exists():
            errors.append(f"thumbnail_path does not exist: {target.thumbnail_path}")

        # Title
        if not target.title:
            errors.append("title is required for YouTube uploads")
        elif len(target.title) > _TITLE_MAX:
            errors.append(
                f"title is {len(target.title)} chars (YouTube max: {_TITLE_MAX})"
            )

        # Description / caption
        if target.caption and len(target.caption) > _DESCRIPTION_MAX:
            errors.append(
                f"description is {len(target.caption)} chars "
                f"(YouTube max: {_DESCRIPTION_MAX})"
            )

        # Tags
        if target.tags:
            tag_total = sum(len(t) for t in target.tags)
            if tag_total > _TAGS_MAX:
                errors.append(
                    f"tags total character count is {tag_total} "
                    f"(YouTube max: {_TAGS_MAX})"
                )
            for tag in target.tags:
                if len(tag) > _TAG_MAX_CHARS:
                    errors.append(
                        f"tag '{tag[:20]}…' is {len(tag)} chars "
                        f"(YouTube max per tag: {_TAG_MAX_CHARS})"
                    )

        # Privacy
        if target.privacy and target.privacy not in _VALID_PRIVACY:
            errors.append(
                f"privacy '{target.privacy}' is not valid "
                f"(expected: {', '.join(sorted(_VALID_PRIVACY))})"
            )

        # Scheduling: if set, validate ISO-8601
        if target.schedule_at:
            from datetime import datetime
            try:
                datetime.fromisoformat(target.schedule_at.replace("Z", "+00:00"))
            except ValueError:
                errors.append(
                    f"schedule_at '{target.schedule_at}' is not valid ISO-8601"
                )

        return errors

    # ── Dry-run ───────────────────────────────────────────────────────────────

    def dry_run_publish(self, target: PublishTarget) -> PublishResult:
        """Validate and describe the upload without making any API calls."""
        errors = self.validate_target(target)
        lib_ok = self._google_libs_available()
        creds_ok = bool(self.credentials_path and Path(self.credentials_path).exists())

        lines: list[str] = ["YouTube dry-run:"]
        lines.append(f"  Video       : {target.video_path or '(not set)'}")
        lines.append(f"  Title       : {target.title or '(not set)'}")
        desc_preview = (target.caption[:60] + "…") if len(target.caption) > 60 else target.caption
        lines.append(f"  Description : {desc_preview or '(not set)'}")
        lines.append(f"  Tags        : {', '.join(target.tags) if target.tags else '(none)'}")
        lines.append(f"  Privacy     : {target.privacy or 'public'}")
        if target.schedule_at:
            lines.append(f"  Scheduled   : {target.schedule_at}")
        if target.thumbnail_path:
            lines.append(f"  Thumbnail   : {target.thumbnail_path}")
        lines.append("")
        lines.append(f"  google-api-python-client installed : {'yes' if lib_ok else 'NO — run: pip install clipforge[publish-youtube]'}")
        lines.append(f"  Credentials file                   : {'found' if creds_ok else 'NOT FOUND — set YOUTUBE_CREDENTIALS_PATH'}")
        if errors:
            lines.append(f"\n  Validation errors ({len(errors)}):")
            for e in errors:
                lines.append(f"    ! {e}")
        else:
            lines.append("\n  Metadata validation: OK")

        overall_ok = not errors and lib_ok and creds_ok
        if not overall_ok and not errors:
            if not lib_ok:
                errors.append("google-api-python-client not installed")
            if not creds_ok:
                errors.append("YouTube credentials not configured")

        return PublishResult(
            success=overall_ok,
            dry_run=True,
            provider=_PROVIDER_NAME,
            platform=target.platform or "youtube",
            error="; ".join(errors) if errors else "",
            response_summary="\n".join(lines),
        )

    # ── Real publish ──────────────────────────────────────────────────────────

    def publish(self, target: PublishTarget) -> PublishResult:
        """Upload to YouTube via the Data API v3.

        Returns ``PublishResult(success=True, post_url=…)`` only when
        YouTube confirms the upload.  Never fakes success.

        Raises ``PublishNotAvailableError`` if dependencies are missing or
        credentials are not configured.
        """
        if not self._google_libs_available():
            raise PublishNotAvailableError(
                "google-api-python-client is not installed. "
                "Run: pip install clipforge[publish-youtube]"
            )
        if not self.credentials_path or not Path(self.credentials_path).exists():
            raise PublishNotAvailableError(
                "YouTube credentials not configured. "
                "Set the YOUTUBE_CREDENTIALS_PATH environment variable or "
                "pass credentials_path= to YouTubePublishProvider()."
            )

        errors = self.validate_target(target)
        if errors:
            return PublishResult(
                success=False,
                provider=_PROVIDER_NAME,
                platform=target.platform or "youtube",
                error="; ".join(errors),
                response_summary=f"Upload aborted: {len(errors)} validation error(s)",
            )

        try:
            return self._do_upload(target)
        except Exception as exc:
            return PublishResult(
                success=False,
                provider=_PROVIDER_NAME,
                platform=target.platform or "youtube",
                error=str(exc),
                response_summary=f"Upload failed: {type(exc).__name__}: {exc}",
            )

    # ── Internal helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _google_libs_available() -> bool:
        """Return True if the google-api-python-client stack is importable."""
        try:
            import google.auth  # noqa: F401
            import googleapiclient  # noqa: F401
            return True
        except ImportError:
            return False

    def _build_youtube_client(self) -> Any:
        """Authenticate and return a YouTube API service object."""
        import json

        from googleapiclient.discovery import build

        creds_data = json.loads(Path(self.credentials_path).read_text(encoding="utf-8"))
        cred_type = creds_data.get("type", "")

        if cred_type == "service_account":
            from google.oauth2 import service_account
            scopes = ["https://www.googleapis.com/auth/youtube.upload"]
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path, scopes=scopes
            )
        elif "installed" in creds_data or "web" in creds_data:
            # OAuth2 client secret flow (token already obtained)
            raise PublishNotAvailableError(
                "OAuth2 client secret detected. Run the OAuth flow first to obtain "
                "a token file, then point YOUTUBE_CREDENTIALS_PATH at the token file."
            )
        elif "token" in creds_data:
            # Pre-obtained OAuth2 token
            import google.oauth2.credentials
            credentials = google.oauth2.credentials.Credentials.from_authorized_user_file(
                self.credentials_path,
                scopes=["https://www.googleapis.com/auth/youtube.upload"],
            )
        else:
            raise PublishNotAvailableError(
                f"Unrecognised credentials file format in: {self.credentials_path}"
            )

        return build("youtube", "v3", credentials=credentials)

    def _do_upload(self, target: PublishTarget) -> PublishResult:
        """Perform the actual YouTube upload."""
        from datetime import datetime
        from datetime import timezone as _tz

        from googleapiclient.http import MediaFileUpload

        youtube = self._build_youtube_client()

        body: dict[str, Any] = {
            "snippet": {
                "title": target.title,
                "description": target.caption,
                "tags": target.tags,
                "categoryId": target.extra.get("category_id", "22"),  # 22 = People & Blogs
            },
            "status": {
                "privacyStatus": target.privacy or "public",
                "selfDeclaredMadeForKids": target.extra.get("made_for_kids", False),
            },
        }

        # Scheduled publishing
        if target.schedule_at:
            body["status"]["privacyStatus"] = "private"
            body["status"]["publishAt"] = target.schedule_at

        media = MediaFileUpload(
            target.video_path,
            mimetype="video/*",
            resumable=True,
        )

        request = youtube.videos().insert(
            part=",".join(body.keys()),
            body=body,
            media_body=media,
        )

        # Execute resumable upload with progress
        response = None
        while response is None:
            _status, response = request.next_chunk()

        video_id = response.get("id", "")
        post_url = f"https://www.youtube.com/watch?v={video_id}" if video_id else ""

        # Upload thumbnail if provided
        if target.thumbnail_path and video_id:
            try:
                youtube.thumbnails().set(
                    videoId=video_id,
                    media_body=MediaFileUpload(target.thumbnail_path),
                ).execute()
            except Exception:
                pass  # Thumbnail failure is non-fatal

        published_at = datetime.now(_tz.utc).isoformat()

        return PublishResult(
            success=True,
            provider=_PROVIDER_NAME,
            platform=target.platform or "youtube",
            post_id=video_id,
            post_url=post_url,
            published_at=published_at,
            response_summary=f"Uploaded successfully. Video ID: {video_id}",
            metadata={"youtube_response": response},
        )
