# Changelog

## v0.6.0 — 2026-04-14

### Safe Publish Engine

- **Extended `PublishProvider` base** (`providers/publish/base.py`): added
  `validate_target()` (concrete, safe default), `dry_run_publish()` (concrete,
  runs validation without side-effects), `provider_name()`, `PublishNotAvailableError`.
  `PublishResult` gains `dry_run`, `provider`, `published_at`, `retry_count`,
  `response_summary`, `manual_action_required` fields + `to_dict()`/`from_dict()`.
  All new fields have defaults — existing subclasses unchanged.
- **`ManualPublishProvider`** (`providers/publish/manual_provider.py`): first-class
  safe publish path. Validates files + metadata, produces a human-readable publish
  checklist (`<job>_checklist.txt`), marks result as `manual_action_required`.
  Never marks `success=True`. Always available (`is_available()` → True).
- **`YouTubePublishProvider`** (`providers/publish/youtube_provider.py`): real
  YouTube Data API v3 upload. Requires `pip install clipforge[publish-youtube]`
  (google-api-python-client stack) and a credentials JSON (service account or
  OAuth2 token). Guards all API calls behind `is_available()`. `validate_target()`
  checks title/description/tags/privacy/schedule without network calls.
  `dry_run_publish()` validates metadata and reports credential status. `publish()`
  raises `PublishNotAvailableError` honestly when not configured. On success, sets
  `result.success=True`, `post_id`, `post_url`, `published_at`.
- **`PublishProviderFactory`** (`providers/publish/factory.py`): selects provider
  by platform/config. Defaults: youtube/youtube-shorts → YouTube; reels/tiktok/
  landscape → Manual. Config can override per-platform.
- **`PublishConfig`** (`publish_config.py`): provider credentials and defaults.
  `default_provider`, `dry_run_default`, `youtube_credentials_path`,
  `platform_providers`. `load(path)`, `from_env()`, `load_or_default()`, `save()`.
  Env vars: `YOUTUBE_CREDENTIALS_PATH`, `CLIPFORGE_PUBLISH_DRY_RUN`,
  `CLIPFORGE_DEFAULT_PROVIDER`. Secrets never stored in config — only file paths.
- **`PublishManifest` V5 extensions** (`publish_manifest.py`):
  - `publish_attempts: list[dict]` — full attempt history (survives save/load).
  - `record_attempt(result)` — appends a `PublishResult` record with timestamp.
  - `last_attempt()` — returns the most recent attempt dict.
  - `as_publish_target()` — converts manifest to `PublishTarget` (hashtags → tags list).
- **`publish` commands** (`commands/publish.py`):
  - `publish validate` — schema + platform + provider checks; exits nonzero on failure.
  - `publish dry-run` — full dry-run via provider; shows what would be sent.
  - `publish execute` — pre-flight dry-run → confirm → publish; records attempt;
    updates queue status if `--queue-dir` given.
  - `publish retry` — resets failed manifest to pending and re-executes.
- **`queue execute`** (`commands/queue.py`): execute all ready items; `--dry-run`
  mode; per-item status transitions (published/manual_action_required/failed);
  attempt records stored in manifest files.
- **`queue retry-failed`**: resets all failed items to pending and re-executes.
- **Studio** (`commands/studio.py`): publish-prep flow now includes dry-run step
  and optional execute-now after adding to queue.
- **`pyproject.toml`**: new `[publish-youtube]` optional dependency group.
- **Version bump** to `0.6.0`.

### Provider support matrix

| Platform | Provider | Real upload | Notes |
|---|---|---|---|
| youtube | YouTubePublishProvider | Yes (requires creds) | Dry-run always available |
| youtube-shorts | YouTubePublishProvider | Yes (requires creds) | Same as YouTube |
| reels | ManualPublishProvider | No — manual handoff | Checklist + queue status |
| tiktok | ManualPublishProvider | No — manual handoff | API too restricted for V5 |
| landscape | ManualPublishProvider | No — manual handoff | Generic export |

### Tests

- Added `test_publish_providers_v5.py` (48 tests): PublishResult V5 fields,
  base class defaults, ManualPublishProvider (validation, dry-run, publish,
  checklist writing), YouTubePublishProvider (validation, dry-run, mocked
  success/failure), PublishProviderFactory, PublishConfig (env/file/defaults).
- Added `test_publish_manifest_v5.py` (14 tests): publish_attempts, record_attempt,
  last_attempt, save/load roundtrip with attempts, as_publish_target.
- Extended `test_cli.py`: publish validate/dry-run/execute/retry, queue execute
  dry-run/empty, queue retry-failed, module importability (18 new tests).
- **Total: 472 tests passing.**

---

## v0.5.0 — 2026-04-14 (package) / v0.5.0 — 2026-04-14 (CLI)

### Publish prep layer

- **Publish manifest** (`publish_manifest.py`): `PublishManifest` class with all
  required fields — manifest_id, job_name, project_name, platform, video/thumbnail/
  script paths, bundle_dir, social metadata (title/caption/hashtags/cta/hook +
  variants), scheduling (publish_at/timezone/campaign/queue/priority/target/
  manual_review_required), provenance (profile_ref/template_ref/brand_name),
  status, notes, created_at/updated_at, extra.
  - `to_dict()`, `from_dict()`, `save()`, `load()`, `validate()`, `is_ready()`.
  - `validate()` checks: video_path required, platform/status/priority enum,
    ISO-8601 publish_at.
- **Publish queue** (`publish_queue.py`): `PublishQueue` class — folder-backed
  store with `init()`, `load()`, `save()`, `append()`, `get()`, `remove()`,
  `update_status()`, `list()`, `filter_by_status()`, `filter_by_platform()`,
  `filter_by_campaign()`, `summary()`.
  - 8 lifecycle statuses: draft, pending, ready, scheduled, manual_action_required,
    published, failed, archived.
- **Platform formatting** (`publish_format.py`): `PlatformRules` dataclass +
  `PLATFORM_RULES` dict for reels/tiktok/youtube-shorts/youtube/landscape.
  `validate_for_platform()` checks title/caption/hashtag limits and thumbnail
  requirement. `format_for_platform()` truncates to platform maximums.
- **`publish-manifest` commands** (`commands/publish_manifest.py`):
  `create`, `show`, `show --json`, `validate`.
  `create` can import social metadata from a social-pack JSON (`--social-json`).
- **`queue` commands** (`commands/queue.py`):
  `init`, `add`, `list`, `summary`, `status` (update status of a manifest).
- **Export bundle** (`commands/export_bundle.py`):
  - Auto-generates `publish_manifest.json` in every bundle.
  - New `--publish-manifest` flag to include an existing manifest.
  - New `--add-to-queue` flag to add the bundle's manifest to a queue.
- **Project integration** (`project.py`):
  - New fields: `default_queue`, `default_campaign`, `default_publish_target`,
    `manual_review_required`.
  - `make_manifest()` creates a `PublishManifest` pre-filled with project defaults.
  - `queue_dir()` returns `<project>/publish_queue`.
- **Studio TUI** (`commands/studio.py`): new menu option `[8] Publish prep` —
  create manifest → validate → add to queue, all in the interactive flow.
- **Docs**: `docs/publish_prep.md` — full guide to manifest schema, queue,
  scheduling, platform rules, project integration, Studio flow, Python API,
  and V5 roadmap.
- **Version bump** to `0.5.0`.

### Tests

- Added `test_publish_manifest.py` (36 tests): instantiation, roundtrip, save/load,
  file creation, validate (valid + all error cases), is_ready, repr.
- Added `test_publish_queue.py` (28 tests): init/load, append/get/remove,
  filter operations, update_status, summary, persistence across reload.
- Added `test_publish_format.py` (18 tests): get_rules, validate_for_platform
  (all constraint types), format_for_platform (truncation, platform override).
- Extended `test_cli.py`: publish-manifest create/show/validate, queue init/add/
  list/summary/status, export-bundle manifest generation (15 new tests).
- Extended `test_project.py`: publish fields roundtrip, make_manifest,
  queue_dir (5 new tests).
- **Total: 398 tests passing.**

---

## v0.4.0 — 2026-04-14

### Productization pass

- **Studio mode rewrite** (`commands/studio.py`): replaced placeholder menu
  with a functional interactive workflow. Build a video by answering prompts,
  see a dry-run scene preview, confirm before rendering. Social pack and
  thumbnail flows also inline. Plain-text fallback when `rich` is not installed.
- **Project/session support** (`project.py`, `commands/project.py`):
  - `ClipForgeProject` class with `init()`, `load()`, `save()`, `build_config()`,
    `list_scripts()`.
  - Project folder structure: `scripts/`, `output/`, `assets/music/logo/downloads/`.
  - Commands: `clipforge project init`, `project info`, `project build [--dry-run]`.
  - `build_config()` merges project defaults → config file → profile → overrides.
- **Export bundle improvements** (`commands/export_bundle.py`):
  - New flags: `--config-file`, `--profile-file`, `--render-summary`, `--script-file`.
  - Auto-generates social TXT alongside social JSON.
  - `manifest.json` includes per-file metadata (label, size_bytes).
  - `--force` flag; clean error when bundle dir exists.
- **Template packs** (`templates.py`, `commands/templates.py`, `data/templates/`):
  - 4 built-in packs: `business`, `ai_content`, `motivation`, `educational`.
  - `TemplateManager.apply_to_config()` — fills missing config keys from template.
  - Commands: `templates list`, `templates show`, `templates apply`, `templates sample`.
- **Provider abstraction layer** (`providers/`):
  - `providers/stock/base.py` — abstract `StockProvider` + `StockResult`.
  - `providers/tts/base.py` — abstract `TTSProvider` + `TTSResult`.
  - `providers/publish/base.py` — abstract `PublishProvider` + `PublishResult` +
    `PublishTarget` (future integration point for social publishing).
- **Version bump** to `0.4.0`.
- **pyproject.toml** improvements: classifiers, `[project.urls]`, `ruff` dev dep,
  `[tool.ruff.lint]` config.
- **CI workflow** (`ci.yml`): added lint step (ruff), version check, core module
  import smoke tests.
- **`docs/release_notes_template.md`**: standard release notes skeleton.

### Tests

- Added `test_templates.py` (15 tests): TemplateManager list/get/apply, real templates, TMP dir.
- Added `test_project.py` (17 tests): init, load, save, roundtrip, scripts, build_config, overrides.
- Added `test_providers.py` (19 tests): all 3 provider abstractions, concrete subclasses, success/failure.
- Extended `test_cli.py`: templates list/show/apply/sample, project init/info/build, export-bundle,
  version flag (13 new tests).
- **Total: 301 tests passing (at time of release).**

---

## v0.3.0 — 2026-04-14

### Usability pass — simpler UX, smarter defaults

- **Smart platform defaults** (`config_loader.py`): vertical platforms (reels,
  tiktok) now auto-select `style=bold` + `subtitle_mode=word-by-word` when
  those fields are not explicitly set. Landscape/YouTube selects `clean/static`.
  User-set values always win. `_apply_smart_defaults()` is the new helper.
- **`make` command overhaul** (`commands/make.py`):
  - New `--profile` flag to apply a brand profile directly
  - Echoes auto-selected settings line (platform, style, audio, text)
  - Shows "Profile applied" and "Preset applied" confirmations
  - Dry-run shows confidence scores; output format is cleaner
  - Better error messages with actionable hints
- **Wizard redesign** (`commands/wizard.py`):
  - 3-phase structure: Essential → Optional Extras → Advanced
  - New `--quick` flag for 3-question fast setup
  - Platform descriptions shown inline; audio options explained
  - Smart style/subtitle defaults pre-filled per platform
  - Ends with a clear "Next steps" block
- **Social pack command** (`commands/social_pack.py`):
  - Clean primary output (title, hook, CTA, hashtags)
  - New `--show-variants` flag to display A/B alternatives
  - Variants also written to TXT save files
  - Better error messaging for missing script
- **Presets command** (`commands/presets.py`):
  - Inline description for each preset
  - Cleaner formatting; usage examples at bottom
- **Doctor command** (`commands/doctor.py`):
  - Added "Quick start" block when all checks pass
  - Added "Common fixes" hints when checks fail
  - Consistent indented output format
- **init-config** (`commands/init_config.py`):
  - New `--minimal` flag for essential-only config (no clutter)
  - Smart style/subtitle defaults applied per platform
  - Next-steps message after writing
- **init-profile** (`commands/init_profile.py`):
  - Now uses `BrandProfile` class (saves real profile JSON)
  - Auto-selects style/subtitle from platform
  - Shows usage hint after writing
- **CLI group help** (`cli.py`): Rewrote the main `--help` with quick-start
  examples, a common-commands table, and "Run any command with --help" footer.
- **README**: Full beginner-friendly rewrite with 3-step quick start, smart
  defaults table, and workflow examples.

### Tests

- `test_config_loader.py`: 11 new tests for `_apply_smart_defaults` — platform
  smart defaults, explicit-key protection, unknown platform safety.
- `test_cli.py`: 12 new tests — dry-run settings output, doctor next-steps,
  presets descriptions, wizard quick mode, init-config minimal + smart defaults,
  social-pack variants, init-profile, make with --profile.
- **Total: 242 tests passing (at time of release).**

---

## v0.2.0 — 2026-04-13

### New features

- **Scene planning V2** (`scene_planner.py`): weighted keyword scoring,
  confidence values, `primary_query` + `alternate_queries` per scene,
  `_score_visual_type()` and `build_queries()` as public helpers.
- **AI wiring** (`commands/make.py`): `AIFactory.from_config(config)` now
  initialises the provider and passes it to `ScenePlanner` automatically.
- **`AIFactory.from_config()`** (`ai/factory.py`): create an AI provider
  directly from a config dict (reads provider name and API key from env).
- **`SCENE_PLAN_PROMPT_V2`** (`ai/prompts.py`): improved prompt with local
  analysis context; returns `primary_query` + `alternate_queries`.
- **Media fallback queries** (`media_fetcher.py`): `fetch_for_scene()` now
  tries `alternate_queries` in order when the primary query returns no results.
- **Brand profiles** (`profile.py`): new `BrandProfile` class with
  `save()`, `load()`, `from_dict()`, and `apply_to_config()` — platform-aware
  defaults, watermark settings, and arbitrary extra fields.
- **Social pack variants** (`social_pack.py`): `generate()` now returns
  `title_variants`, `hook_variants`, and `cta_variants` lists for A/B testing
  and scheduled posting while keeping `title`/`hook`/`cta` backward-compatible.
- **Text engine improvements** (`text_engine.py`): better line wrapping via
  `textwrap`, `wrap_width` per style, word-by-word highlight color for current
  word, improved title card sizing (larger for short titles).

### Tests

- Extended `test_scene_planner.py`: `_score_visual_type`, `_select_best_keyword`,
  `build_queries`, and V2 plan output fields (20 new tests).
- Added `test_profile.py` (14 tests): instantiation, to_dict/from_dict roundtrip,
  save/load, apply_to_config override behaviour, platform-aware defaults.
- Extended `test_social_pack.py`: title_variants, hook_variants, cta_variants,
  backward-compat checks (6 new tests).
- Extended `test_media_fetcher.py`: alternate query fallback, primary_query
  preference, legacy query field fallback (3 new tests).
- **Total: 221 tests passing (at time of release).**

---

## v0.1.0 — 2026-04-14

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
- **Total: 184 tests passing (at time of release).**

---

## v0.1.0 — 2026-04-13

- Initial release.
- Script parsing, scene planning, video builder, audio engine, text engine.
- Doctor command, presets, wizard, init commands.
- Social pack, thumbnail, batch, export-bundle.
- AI skeleton (OpenAI / Anthropic / Gemini providers, graceful no-op).
- GitHub CI workflow (Python 3.10–3.12).
