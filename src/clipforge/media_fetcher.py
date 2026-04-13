"""Stock media fetcher for ClipForge.

Downloads royalty-free video/image assets from Pexels and Pixabay.
Falls back gracefully when API keys are missing or requests fail.
"""

from __future__ import annotations

import logging
import os
import tempfile
import time
from pathlib import Path
from typing import Any

import requests

from clipforge.utils import ensure_dir

logger = logging.getLogger(__name__)

# Request settings
_TIMEOUT = 10          # seconds per API call
_DOWNLOAD_TIMEOUT = 30  # seconds for asset download
_MAX_RETRIES = 2
_RETRY_DELAY = 1.0     # seconds between retries


class MediaFetcher:
    """Fetch stock media for each scene from Pexels and Pixabay.

    Usage::

        fetcher = MediaFetcher(pexels_key="...", pixabay_key="...")
        path, source = fetcher.fetch_for_scene(scene, config, cache_dir)
        # path is a local file path, or None if all sources failed
        # source is "pexels", "pixabay", or "fallback"
    """

    def __init__(
        self,
        pexels_key: str | None = None,
        pixabay_key: str | None = None,
        cache_dir: str | Path = "assets/downloads",
    ) -> None:
        self._pexels_key = pexels_key or os.environ.get("PEXELS_API_KEY", "")
        self._pixabay_key = pixabay_key or os.environ.get("PIXABAY_API_KEY", "")
        self._cache_dir = Path(cache_dir)
        # Track used media IDs to avoid duplicates
        self._used_ids: set[str] = set()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fetch_for_scene(
        self,
        scene: dict[str, Any],
        width: int,
        height: int,
    ) -> tuple[str | None, str]:
        """Fetch the best available media for *scene*.

        Returns:
            (local_path, source) where source is one of:
            "pexels_video", "pexels_image", "pixabay_video",
            "pixabay_image", or "fallback".
        """
        query = scene.get("query", "abstract background")

        if self._pexels_key:
            path = self._try_pexels_video(query, width, height)
            if path:
                return path, "pexels_video"
            path = self._try_pexels_image(query)
            if path:
                return path, "pexels_image"
        else:
            logger.debug("PEXELS_API_KEY not set — skipping Pexels search.")

        if self._pixabay_key:
            path = self._try_pixabay_video(query)
            if path:
                return path, "pixabay_video"
            path = self._try_pixabay_image(query)
            if path:
                return path, "pixabay_image"
        else:
            logger.debug("PIXABAY_API_KEY not set — skipping Pixabay search.")

        return None, "fallback"

    def warn_if_no_keys(self) -> list[str]:
        """Return a list of warning strings for missing API keys."""
        warnings: list[str] = []
        if not self._pexels_key:
            warnings.append(
                "PEXELS_API_KEY not set — stock videos/images from Pexels unavailable. "
                "Solid-colour backgrounds will be used instead."
            )
        if not self._pixabay_key:
            warnings.append(
                "PIXABAY_API_KEY not set — stock media from Pixabay unavailable."
            )
        return warnings

    # ------------------------------------------------------------------
    # Pexels
    # ------------------------------------------------------------------

    def _try_pexels_video(self, query: str, width: int, height: int) -> str | None:
        """Search Pexels for a video clip matching *query*."""
        orientation = "portrait" if height > width else "landscape"
        url = "https://api.pexels.com/videos/search"
        params = {"query": query, "per_page": 10, "orientation": orientation}
        headers = {"Authorization": self._pexels_key}

        try:
            data = self._get_json(url, params=params, headers=headers)
        except Exception as exc:
            logger.warning("Pexels video search failed for %r: %s", query, exc)
            return None

        videos = data.get("videos", [])
        for video in videos:
            vid_id = f"pexels_v_{video.get('id')}"
            if vid_id in self._used_ids:
                continue
            files = video.get("video_files", [])
            # Pick the file closest to desired resolution
            best = self._pick_best_video_file(files, width, height)
            if best:
                path = self._download(best["link"], f"{vid_id}.mp4")
                if path:
                    self._used_ids.add(vid_id)
                    return path
        return None

    def _try_pexels_image(self, query: str) -> str | None:
        """Search Pexels for an image matching *query*."""
        url = "https://api.pexels.com/v1/search"
        params = {"query": query, "per_page": 10}
        headers = {"Authorization": self._pexels_key}

        try:
            data = self._get_json(url, params=params, headers=headers)
        except Exception as exc:
            logger.warning("Pexels image search failed for %r: %s", query, exc)
            return None

        photos = data.get("photos", [])
        for photo in photos:
            photo_id = f"pexels_i_{photo.get('id')}"
            if photo_id in self._used_ids:
                continue
            src = photo.get("src", {})
            link = src.get("large2x") or src.get("large") or src.get("original")
            if link:
                path = self._download(link, f"{photo_id}.jpg")
                if path:
                    self._used_ids.add(photo_id)
                    return path
        return None

    # ------------------------------------------------------------------
    # Pixabay
    # ------------------------------------------------------------------

    def _try_pixabay_video(self, query: str) -> str | None:
        """Search Pixabay for a video matching *query*."""
        url = "https://pixabay.com/api/videos/"
        params = {"key": self._pixabay_key, "q": query, "per_page": 10}

        try:
            data = self._get_json(url, params=params)
        except Exception as exc:
            logger.warning("Pixabay video search failed for %r: %s", query, exc)
            return None

        hits = data.get("hits", [])
        for hit in hits:
            hit_id = f"pixabay_v_{hit.get('id')}"
            if hit_id in self._used_ids:
                continue
            videos = hit.get("videos", {})
            # Try medium first, then small, then large
            for size in ("medium", "small", "large"):
                vdata = videos.get(size, {})
                link = vdata.get("url", "")
                if link:
                    path = self._download(link, f"{hit_id}.mp4")
                    if path:
                        self._used_ids.add(hit_id)
                        return path
        return None

    def _try_pixabay_image(self, query: str) -> str | None:
        """Search Pixabay for an image matching *query*."""
        url = "https://pixabay.com/api/"
        params = {
            "key": self._pixabay_key,
            "q": query,
            "per_page": 10,
            "image_type": "photo",
        }

        try:
            data = self._get_json(url, params=params)
        except Exception as exc:
            logger.warning("Pixabay image search failed for %r: %s", query, exc)
            return None

        hits = data.get("hits", [])
        for hit in hits:
            hit_id = f"pixabay_i_{hit.get('id')}"
            if hit_id in self._used_ids:
                continue
            link = hit.get("largeImageURL") or hit.get("webformatURL")
            if link:
                path = self._download(link, f"{hit_id}.jpg")
                if path:
                    self._used_ids.add(hit_id)
                    return path
        return None

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_json(
        self,
        url: str,
        params: dict | None = None,
        headers: dict | None = None,
    ) -> dict:
        """GET *url* with retries, return parsed JSON."""
        last_exc: Exception | None = None
        for attempt in range(_MAX_RETRIES + 1):
            try:
                resp = requests.get(
                    url, params=params, headers=headers, timeout=_TIMEOUT
                )
                resp.raise_for_status()
                return resp.json()
            except requests.exceptions.Timeout as exc:
                last_exc = exc
                logger.debug("Request timeout (attempt %d): %s", attempt + 1, url)
            except requests.exceptions.HTTPError as exc:
                # 401/403 = bad key — don't retry
                if exc.response is not None and exc.response.status_code in (401, 403):
                    logger.warning(
                        "API key rejected by %s (HTTP %d). "
                        "Check your .env file.",
                        url.split("/")[2],
                        exc.response.status_code,
                    )
                    raise
                last_exc = exc
            except requests.exceptions.RequestException as exc:
                last_exc = exc

            if attempt < _MAX_RETRIES:
                time.sleep(_RETRY_DELAY)

        raise last_exc or RuntimeError(f"GET {url} failed after {_MAX_RETRIES + 1} attempts")

    def _download(self, url: str, filename: str) -> str | None:
        """Download *url* to cache dir as *filename*. Returns local path or None."""
        ensure_dir(self._cache_dir)
        dest = self._cache_dir / filename
        if dest.exists():
            return str(dest)
        try:
            resp = requests.get(url, timeout=_DOWNLOAD_TIMEOUT, stream=True)
            resp.raise_for_status()
            with dest.open("wb") as fh:
                for chunk in resp.iter_content(chunk_size=65536):
                    fh.write(chunk)
            return str(dest)
        except Exception as exc:
            logger.warning("Download failed for %s: %s", url, exc)
            if dest.exists():
                dest.unlink(missing_ok=True)
            return None

    def _pick_best_video_file(
        self,
        files: list[dict],
        target_w: int,
        target_h: int,
    ) -> dict | None:
        """Pick the video file closest to the target resolution."""
        candidates = [f for f in files if f.get("link")]
        if not candidates:
            return None
        target_px = target_w * target_h

        def score(f: dict) -> int:
            w = f.get("width", 0) or 0
            h = f.get("height", 0) or 0
            return abs(w * h - target_px)

        return min(candidates, key=score)
