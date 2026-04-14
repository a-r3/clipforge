# ClipForge v1.0 — Publishing Guide

Covers the full publish stack: manifests, queues, providers, credentials, and safety.

> For the V4 manifest/queue overview, see `docs/publish_prep.md`.  
> This document covers the V5 execution layer onwards.

---

## Core concepts

### Publish manifest

A manifest (`PublishManifest`) is a JSON file that records everything about one publishable video:

- Video file path and platform
- Title, caption, hashtags, schedule
- Campaign, template, profile references
- Status (draft → pending → ready → published → failed)
- Publish attempts with outcomes

### Publish queue

A queue (`PublishQueue`) is a directory of manifests organised by status. You add, execute, and retry items through the queue CLI.

### Publish providers

Providers connect a manifest to a platform API:

| Provider | Platforms | Availability |
|---|---|---|
| `ManualPublishProvider` | All | Always — writes a checklist file |
| `YouTubePublishProvider` | `youtube`, `youtube-shorts` | Requires Google credentials |

Manual is the safe default. If no real provider is configured, ClipForge uses Manual and produces a checklist `.txt` file you can follow manually.

---

## Safety rules

1. **Never auto-publish.** `clipforge publish execute` always prompts for confirmation unless `--yes` is passed.
2. **Dry-run first.** `clipforge publish dry-run` validates everything and describes what would happen — no API calls.
3. **Honest failures.** A manifest is only marked `published` when the provider confirms success. Failed attempts are recorded with their error message.
4. **Manual fallback.** If the real provider is unavailable, the system does not silently succeed — it uses `ManualPublishProvider` and sets `manual_action_required`.

---

## Manifest lifecycle

```
draft → pending → ready → published
                        → failed → (retry) → published
              → manual_action_required
              → archived
```

Use `clipforge queue status <queue-dir> <manifest-id> <new-status>` to move items.

---

## CLI: publish-manifest

```bash
# Create
clipforge publish-manifest create \
    --video-file output/ep01.mp4 \
    --platform youtube \
    --title "5 Lessons From 10 Years" \
    --caption "Here's what I learned..." \
    --hashtags "#learning #growth" \
    --job-name ep01 \
    --campaign Q2-2024 \
    --output ep01.manifest.json

# Validate
clipforge publish-manifest validate ep01.manifest.json

# Show
clipforge publish-manifest show ep01.manifest.json
clipforge publish-manifest show ep01.manifest.json --json
```

---

## CLI: queue

```bash
clipforge queue init publish_queue
clipforge queue add publish_queue ep01.manifest.json
clipforge queue list publish_queue
clipforge queue summary publish_queue
clipforge queue status publish_queue <manifest-id> ready
clipforge queue execute publish_queue
clipforge queue execute publish_queue --dry-run
clipforge queue retry-failed publish_queue
```

---

## CLI: publish

```bash
# Validate metadata + provider availability
clipforge publish validate ep01.manifest.json

# Dry-run: describe what will happen, no API calls
clipforge publish dry-run ep01.manifest.json

# Execute (prompts for confirmation)
clipforge publish execute ep01.manifest.json

# Skip confirmation (for scripts/CI)
clipforge publish execute ep01.manifest.json --yes

# Update queue status after execute
clipforge publish execute ep01.manifest.json --queue-dir publish_queue --yes

# Retry a failed manifest
clipforge publish retry ep01.manifest.json
```

---

## YouTube publish setup

### Step 1 — Install YouTube API libraries

```bash
pip install -e ".[publish-youtube]"
# or: bash install.sh --youtube
```

### Step 2 — Create Google credentials

**Option A: Service account (recommended for automation)**

1. Go to Google Cloud Console → IAM & Admin → Service Accounts
2. Create a service account
3. Download the JSON key file
4. Grant the service account access to the YouTube channel via YouTube Studio → Settings → Permissions

**Option B: OAuth2 user token**

1. Go to Google Cloud Console → APIs & Services → Credentials
2. Create an OAuth2 client ID (Desktop app)
3. Download `client_secret_*.json`
4. Run the OAuth flow to produce a token file:

```bash
# Use google-auth-oauthlib to generate token.json with required scopes:
# https://www.googleapis.com/auth/youtube
# https://www.googleapis.com/auth/yt-analytics.readonly
```

### Step 3 — Configure the path

```bash
# In .env:
YOUTUBE_CREDENTIALS_PATH=/path/to/credentials.json

# Or per-session:
export YOUTUBE_CREDENTIALS_PATH=/path/to/credentials.json
```

### Step 4 — Verify

```bash
clipforge publish validate manifest.json
# Should show: "YouTubePublishProvider: available"

clipforge publish dry-run manifest.json
# Describes the upload without calling the API
```

---

## Platform rules

ClipForge validates metadata against platform limits before publishing:

| Platform | Title limit | Caption limit | Hashtag limit |
|---|---|---|---|
| YouTube | 100 chars | 5,000 chars | 500 chars total |
| YouTube Shorts | 100 chars | 5,000 chars | 500 chars total |
| Reels | 2,200 chars (caption) | — | 30 tags |
| TikTok | 150 chars (caption) | — | 20 tags |

Run `clipforge publish validate manifest.json` to check all limits before attempting to publish.

---

## Manual provider

When the real provider is unavailable, `ManualPublishProvider` is used automatically.

It writes a checklist `.txt` file to the `checklist_dir` (default: same folder as the manifest) with:
- Platform, title, caption, hashtags
- Publish target URL (if known)
- Step-by-step instructions for manual posting
- A `clipforge queue status` command to mark as published after you post manually

This means ClipForge never silently fails — it always produces something actionable.

---

## publish_config.json

For consistent provider settings across sessions:

```json
{
    "default_provider": "youtube",
    "dry_run_default": false,
    "youtube_credentials_path": "/path/to/credentials.json",
    "platform_providers": {
        "youtube": "youtube",
        "youtube-shorts": "youtube",
        "reels": "manual",
        "tiktok": "manual"
    }
}
```

Pass it with `--publish-config publish_config.json` on any publish command.

---

## Publish attempts

Every execute attempt is recorded in the manifest under `publish_attempts`:

```json
{
  "publish_attempts": [
    {
      "success": false,
      "provider": "youtube",
      "dry_run": false,
      "attempted_at": "2024-06-15T10:00:00+00:00",
      "fetch_error": "HttpError 403: quotaExceeded",
      "manual_action_required": false
    }
  ]
}
```

Use `clipforge publish-manifest show manifest.json` to review the history.
