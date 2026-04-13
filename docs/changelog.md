# Changelog

## v0.2.0 — 2026-04-14

### New features

- **Stock media** (`media_fetcher.py`): Pexels and Pixabay API integration with
  timeout, retries, per-key warnings, and duplicate-avoidance tracking.
- **`make` render summary**: after each build, prints scenes, stock hits,
  fallbacks, total duration, audio/text/subtitle modes, and output path.
- **`make --dry-run`**: improved output shows query, visual type, and duration
  for every planned scene plus a one-line summary.
- **`social-pack --save-json`**: save the generated pack to a JSON file.
- **`social-pack --save-txt`**: save the generated pack to a plain-text file.
- **Hashtag cleanup**: topic-derived hashtags are now limited to single words
  (max 20 chars), capped at 8 total — no more unreadable slug-monsters.
- **`thumbnail --style`**: choose `clean`, `bold`, or `minimal` preset.
- **`thumbnail` PNG support**: output path can now be `.png` as well as `.jpg`.
- **`thumbnail` font fallback chain**: tries multiple system font paths before
  falling back to PIL's built-in font.
- **`thumbnail` output validation**: rejects non-.jpg/.png extensions with a
  clear error message.
- **Config validation improvements**: subtitle_mode validated; file paths
  (script_file, music_file, logo_file) checked for existence when non-empty;
  all error messages include the bad value and the list of valid options.
- **Batch runner improvements**: per-job timing, scene count, stop-on-error
  support, and a cleaner final summary table.

### Fixes

- Removed `src/autovideo/` stale package and `test_patch.txt` from the repo.
- All docs purged of `autovideo` references.
- `moviepy` pinned to `1.0.3` (was `>=1.0.3`).

### Tests

- Added `test_media_fetcher.py` (18 tests): API mocking, duplicate avoidance,
  fallback on timeout, best-file selection.
- Added `test_batch_runner.py` (10 tests): load, dry-run, continue/stop on
  error, summary structure.
- Extended `test_config_loader.py`: subtitle_mode, path existence, error
  message content.
- Extended `test_social_pack.py`: hashtag length, count, format, save-json,
  save-txt.
- Extended `test_builder.py`: BuildSummary dataclass and print().
- Extended `test_cli.py`: thumbnail styles, PNG, bad extension, social-pack
  save-json/txt, make dry-run, invalid platform rejection.
- **Total: 184 tests passing.**

---

## v0.1.0 — 2026-04-13

- Initial release.
- Script parsing, scene planning, video builder, audio engine, text engine.
- Doctor command, presets, wizard, init commands.
- Social pack, thumbnail, batch, export-bundle.
- AI skeleton (OpenAI / Anthropic / Gemini providers, graceful no-op).
- GitHub CI workflow (Python 3.10–3.12).
