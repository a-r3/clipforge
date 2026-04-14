"""Tests for the stock media fetcher module."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from clipforge.media_fetcher import MediaFetcher


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_fetcher(pexels="", pixabay="", tmp_path=None) -> MediaFetcher:
    cache = tmp_path / "downloads" if tmp_path else Path("/tmp/cf_test_cache")
    return MediaFetcher(pexels_key=pexels, pixabay_key=pixabay, cache_dir=cache)


def _pexels_video_response(video_id=42, link="https://example.com/video.mp4"):
    return {
        "videos": [
            {
                "id": video_id,
                "video_files": [{"link": link, "width": 1080, "height": 1920}],
            }
        ]
    }


def _pexels_image_response(photo_id=7, url="https://example.com/photo.jpg"):
    return {"photos": [{"id": photo_id, "src": {"large2x": url}}]}


def _pixabay_video_response(hit_id=99, url="https://example.com/pxvideo.mp4"):
    return {"hits": [{"id": hit_id, "videos": {"medium": {"url": url}}}]}


def _pixabay_image_response(hit_id=55, url="https://example.com/pximage.jpg"):
    return {"hits": [{"id": hit_id, "largeImageURL": url}]}


# ---------------------------------------------------------------------------
# Instantiation
# ---------------------------------------------------------------------------

def test_media_fetcher_instantiates(tmp_path):
    fetcher = _make_fetcher(tmp_path=tmp_path)
    assert fetcher is not None


def test_warn_if_no_keys_both_missing(tmp_path):
    fetcher = _make_fetcher(tmp_path=tmp_path)
    warnings = fetcher.warn_if_no_keys()
    assert len(warnings) == 2
    assert any("PEXELS" in w for w in warnings)
    assert any("PIXABAY" in w for w in warnings)


def test_warn_if_no_keys_pexels_present(tmp_path):
    fetcher = _make_fetcher(pexels="SOMEKEY", tmp_path=tmp_path)
    warnings = fetcher.warn_if_no_keys()
    assert len(warnings) == 1
    assert all("PEXELS" not in w for w in warnings)


def test_warn_if_no_keys_none_missing(tmp_path):
    fetcher = _make_fetcher(pexels="K1", pixabay="K2", tmp_path=tmp_path)
    assert fetcher.warn_if_no_keys() == []


# ---------------------------------------------------------------------------
# fetch_for_scene — no API keys
# ---------------------------------------------------------------------------

def test_fetch_returns_fallback_when_no_keys(tmp_path):
    fetcher = _make_fetcher(tmp_path=tmp_path)
    scene = {"query": "technology", "visual_type": "technology"}
    path, source = fetcher.fetch_for_scene(scene, width=1080, height=1920)
    assert path is None
    assert source == "fallback"


# ---------------------------------------------------------------------------
# Pexels video path — mock HTTP
# ---------------------------------------------------------------------------

def test_pexels_video_hit(tmp_path):
    fetcher = _make_fetcher(pexels="FAKEKEY", tmp_path=tmp_path)
    scene = {"query": "technology", "visual_type": "technology"}

    fake_content = b"fakevideo"

    with patch.object(fetcher, "_get_json", return_value=_pexels_video_response()) as mock_get, \
         patch.object(fetcher, "_download", return_value=str(tmp_path / "pexels_v_42.mp4")) as mock_dl:
        path, source = fetcher.fetch_for_scene(scene, 1080, 1920)

    assert source == "pexels_video"
    assert path is not None
    mock_get.assert_called_once()
    mock_dl.assert_called_once()


def test_pexels_video_no_results_falls_to_image(tmp_path):
    fetcher = _make_fetcher(pexels="FAKEKEY", tmp_path=tmp_path)
    scene = {"query": "technology"}

    empty_videos = {"videos": []}
    image_data = _pexels_image_response()

    responses = [empty_videos, image_data]
    call_count = [0]

    def fake_get_json(url, **kwargs):
        r = responses[call_count[0]]
        call_count[0] += 1
        return r

    with patch.object(fetcher, "_get_json", side_effect=fake_get_json), \
         patch.object(fetcher, "_download", return_value=str(tmp_path / "pexels_i_7.jpg")):
        path, source = fetcher.fetch_for_scene(scene, 1080, 1920)

    assert source == "pexels_image"
    assert path is not None


# ---------------------------------------------------------------------------
# Duplicate avoidance
# ---------------------------------------------------------------------------

def test_duplicate_media_not_reused(tmp_path):
    fetcher = _make_fetcher(pexels="FAKEKEY", tmp_path=tmp_path)
    scene = {"query": "tech"}

    # Seed the used_ids set as if this asset was already used
    fetcher._used_ids.add("pexels_v_42")

    # Response contains only id=42
    with patch.object(fetcher, "_get_json", return_value=_pexels_video_response(video_id=42)):
        with patch.object(fetcher, "_download", return_value=None) as mock_dl:
            path, source = fetcher.fetch_for_scene(scene, 1080, 1920)

    # download should never be called because id 42 is already used
    mock_dl.assert_not_called()


# ---------------------------------------------------------------------------
# API error handling
# ---------------------------------------------------------------------------

def test_api_timeout_returns_fallback(tmp_path):
    import requests
    fetcher = _make_fetcher(pexels="FAKEKEY", tmp_path=tmp_path)
    scene = {"query": "city"}

    with patch.object(
        fetcher, "_get_json", side_effect=requests.exceptions.Timeout("timeout")
    ):
        path, source = fetcher.fetch_for_scene(scene, 1080, 1920)

    assert source == "fallback"
    assert path is None


def test_api_error_does_not_raise(tmp_path):
    fetcher = _make_fetcher(pexels="FAKEKEY", pixabay="FAKEKEY2", tmp_path=tmp_path)
    scene = {"query": "business"}

    with patch.object(fetcher, "_get_json", side_effect=RuntimeError("server error")):
        # Must not raise — returns fallback
        path, source = fetcher.fetch_for_scene(scene, 1080, 1920)

    assert source == "fallback"


# ---------------------------------------------------------------------------
# _pick_best_video_file
# ---------------------------------------------------------------------------

def test_pick_best_video_file_selects_closest_resolution(tmp_path):
    fetcher = _make_fetcher(tmp_path=tmp_path)
    files = [
        {"link": "a.mp4", "width": 1920, "height": 1080},
        {"link": "b.mp4", "width": 1280, "height": 720},
        {"link": "c.mp4", "width": 640, "height": 480},
    ]
    result = fetcher._pick_best_video_file(files, target_w=1280, target_h=720)
    assert result["link"] == "b.mp4"


def test_pick_best_video_file_empty_returns_none(tmp_path):
    fetcher = _make_fetcher(tmp_path=tmp_path)
    assert fetcher._pick_best_video_file([], 1080, 1920) is None


def test_pick_best_video_file_skips_entries_without_link(tmp_path):
    fetcher = _make_fetcher(tmp_path=tmp_path)
    files = [{"width": 1080, "height": 1920}, {"link": "ok.mp4", "width": 720, "height": 1280}]
    result = fetcher._pick_best_video_file(files, 720, 1280)
    assert result["link"] == "ok.mp4"


# ---------------------------------------------------------------------------
# V2 alternate query tests
# ---------------------------------------------------------------------------

def test_fetch_tries_alternate_queries_on_primary_failure(tmp_path):
    """fetch_for_scene should try alternate_queries when primary fails."""
    fetcher = _make_fetcher(pexels="key123", tmp_path=tmp_path)

    call_count = {"n": 0}
    video_url = "https://example.com/video.mp4"

    def fake_get_json(url, params=None, headers=None):
        call_count["n"] += 1
        # First call (primary query) returns no results
        if call_count["n"] == 1:
            return {"videos": []}
        # Second call (first alternate) returns a result
        return _pexels_video_response(video_id=99, link=video_url)

    def fake_download(url, filename):
        dest = tmp_path / "downloads" / filename
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(b"fake")
        return str(dest)

    fetcher._get_json = fake_get_json
    fetcher._download = fake_download

    scene = {
        "primary_query": "primary query",
        "alternate_queries": ["alternate query one", "alternate query two"],
    }
    path, source = fetcher.fetch_for_scene(scene, 1080, 1920)
    assert path is not None
    assert source == "pexels_video"
    # Verify we made at least 2 API calls (primary failed, alternate succeeded)
    assert call_count["n"] >= 2


def test_fetch_uses_primary_query_field(tmp_path):
    """fetch_for_scene should prefer primary_query over legacy query field."""
    fetcher = _make_fetcher(pexels="key", tmp_path=tmp_path)

    used_queries = []

    def fake_get_json(url, params=None, headers=None):
        if params:
            used_queries.append(params.get("query", ""))
        return {"videos": []}

    fetcher._get_json = fake_get_json

    scene = {
        "query": "old query",
        "primary_query": "new primary query",
        "alternate_queries": [],
    }
    fetcher.fetch_for_scene(scene, 1080, 1920)
    assert used_queries and used_queries[0] == "new primary query"


def test_fetch_falls_back_to_query_when_no_primary(tmp_path):
    """fetch_for_scene should use legacy 'query' if primary_query is absent."""
    fetcher = _make_fetcher(pexels="key", tmp_path=tmp_path)

    used_queries = []

    def fake_get_json(url, params=None, headers=None):
        if params:
            used_queries.append(params.get("query", ""))
        return {"videos": []}

    fetcher._get_json = fake_get_json

    scene = {"query": "legacy query", "alternate_queries": []}
    fetcher.fetch_for_scene(scene, 1080, 1920)
    assert used_queries and used_queries[0] == "legacy query"
