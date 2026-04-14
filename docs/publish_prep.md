# Publish Prep — v0.5.0

ClipForge v0.5.0 introduces a **publish preparation layer**: a local, file-based
system for describing, organising, and scheduling content items before they reach
any publishing platform.

> **What V4 does and does not do.**
> V4 creates and manages publish manifests and queues *locally*.
> It does **not** publish to Instagram, TikTok, YouTube, or any other platform.
> Actual publishing is a V5 concern (concrete `PublishProvider` implementations).

---

## Core concepts

### Publish manifest

A **publish manifest** (`PublishManifest`) is a single JSON file that records
everything about a publishable content item:

| Field group   | Key fields |
|---|---|
| Identity      | `manifest_id`, `job_name`, `project_name` |
| Content       | `platform`, `video_path`, `thumbnail_path`, `script_path`, `bundle_dir` |
| Social        | `title`, `caption`, `hashtags`, `cta`, `hook`, `*_variants` |
| Schedule      | `publish_at` (ISO-8601), `timezone`, `campaign_name`, `queue_name`, `priority`, `publish_target`, `manual_review_required` |
| Provenance    | `profile_ref`, `template_ref`, `brand_name` |
| Status        | `status` (see lifecycle below) |

### Manifest lifecycle (statuses)

```
draft → pending → ready → scheduled → published
                       ↘ manual_action_required
                       ↘ failed
                       ↘ archived
```

| Status | Meaning |
|---|---|
| `draft` | Created but not yet reviewed |
| `pending` | Submitted for approval |
| `ready` | Approved, waiting for scheduling |
| `scheduled` | Has a `publish_at` time set |
| `manual_action_required` | Needs human intervention |
| `published` | Successfully published (terminal) |
| `failed` | Publish attempt failed (terminal) |
| `archived` | Removed from active queue (terminal) |

### Publish queue

A **publish queue** (`PublishQueue`) is a folder containing:

```
my_queue/
    queue.json          # metadata + ordered list of manifest IDs
    manifests/
        <uuid>.json     # one file per manifest
```

Multiple queues can coexist (e.g. one per platform, one per brand, one per campaign).

---

## CLI quick start

### Create a manifest

```bash
# Minimal — just the video
clipforge publish-manifest create --video-file output/video.mp4 --platform reels

# Full — social metadata + scheduling
clipforge publish-manifest create \
  --video-file output/video.mp4 \
  --platform reels \
  --job-name ep-42 \
  --title "AI is changing everything" \
  --hashtags "#AI #productivity #reels" \
  --publish-at 2026-05-01T18:00:00Z \
  --campaign-name spring2026 \
  --output manifests/ep-42.manifest.json

# Import social metadata from a social-pack JSON
clipforge publish-manifest create \
  --video-file output/video.mp4 \
  --social-json output/social_pack.json \
  --output manifests/ep-42.manifest.json
```

### Inspect and validate

```bash
# Show human-readable summary
clipforge publish-manifest show manifests/ep-42.manifest.json

# Show raw JSON
clipforge publish-manifest show --json manifests/ep-42.manifest.json

# Validate against schema and platform rules
clipforge publish-manifest validate manifests/ep-42.manifest.json
```

### Manage a queue

```bash
# Create a queue
clipforge queue init ./content_queue

# Add a manifest
clipforge queue add ./content_queue manifests/ep-42.manifest.json

# List all items
clipforge queue list ./content_queue

# Filter by status
clipforge queue list ./content_queue --status ready

# Filter by platform
clipforge queue list ./content_queue --platform reels

# Show status summary
clipforge queue summary ./content_queue

# Update a manifest's status
clipforge queue status ./content_queue <manifest-id> ready
```

### Export bundle with manifest

The `export-bundle` command now automatically generates a `publish_manifest.json`
in every bundle:

```bash
clipforge export-bundle \
  --video-file output/video.mp4 \
  --thumbnail-file output/thumb.jpg \
  --social-json output/social_pack.json \
  --output-dir bundle/ep-42

# Bundle now contains:
#   bundle/ep-42/video.mp4
#   bundle/ep-42/social_pack.json
#   bundle/ep-42/social_pack.txt
#   bundle/ep-42/publish_manifest.json   ← auto-generated
#   bundle/ep-42/manifest.json           ← bundle index
```

Pass an existing manifest to override the auto-generated one:

```bash
clipforge export-bundle \
  --video-file output/video.mp4 \
  --publish-manifest manifests/ep-42.manifest.json \
  --output-dir bundle/ep-42
```

Add the bundle to a queue in one step:

```bash
clipforge export-bundle \
  --video-file output/video.mp4 \
  --output-dir bundle/ep-42 \
  --add-to-queue ./content_queue
```

---

## Project integration

A `ClipForgeProject` can define default publish settings that are automatically
applied to every manifest created from that project:

```json
// project.json
{
  "name": "TechBrief",
  "platform": "reels",
  "default_queue": "content_queue",
  "default_campaign": "q2-2026",
  "default_publish_target": "instagram_main",
  "manual_review_required": false
}
```

```python
from clipforge.project import ClipForgeProject

project = ClipForgeProject.load("./my-project")
m = project.make_manifest(job_name="ep-42", video_path="output/video.mp4")
# m.queue_name   == "content_queue"
# m.campaign_name == "q2-2026"
# m.platform     == "reels"
```

The project's `queue_dir()` returns `<project>/publish_queue` as the conventional
queue path for that project.

---

## Platform formatting rules

`clipforge.publish_format` provides per-platform constraints:

| Platform | Title max | Caption max | Hashtag max | Thumbnail required | Aspect |
|---|---|---|---|---|---|
| reels | — | 2200 | 30 | no | 9:16 |
| tiktok | 150 | 2200 | — | no | 9:16 |
| youtube-shorts | 100 | 5000 | 15 | no | 9:16 |
| youtube | 100 | 5000 | 15 | **yes** | 16:9 |
| landscape | — | — | — | no | 16:9 |

```python
from clipforge.publish_format import validate_for_platform, format_for_platform

errors = validate_for_platform(manifest)        # returns list[str]
formatted = format_for_platform(manifest, truncate=True)  # returns dict
```

The `publish-manifest validate` command runs both schema validation and
platform-constraint checks.

---

## Studio integration

The interactive Studio (`clipforge studio`) now includes option `[8] Publish prep`:

1. Enter the video file path
2. Select platform and job name
3. The manifest is created and validated automatically
4. Optionally add to an existing (or new) queue

---

## Python API

```python
from clipforge.publish_manifest import PublishManifest
from clipforge.publish_queue import PublishQueue
from clipforge.publish_format import get_rules, validate_for_platform

# Create
m = PublishManifest(
    job_name="ep-42",
    platform="reels",
    video_path="output/video.mp4",
    title="AI is changing everything",
    publish_at="2026-05-01T18:00:00Z",
)
m.save("manifests/ep-42.manifest.json")

# Validate
errors = m.validate()
platform_errors = validate_for_platform(m)

# Queue
q = PublishQueue.init("./content_queue")
q.append(m)
q.update_status(m.manifest_id, "ready")

ready_items = q.filter_by_status("ready")
summary = q.summary()
```

---

## What's coming in V5

V5 will add concrete `PublishProvider` implementations for each platform,
turning the draft manifests in your queue into actual published posts.
The V4 manifest schema is designed to carry all the data V5 publishers will need.
