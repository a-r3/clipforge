# ClipForge v1.0 — CLI Usage Reference

All commands follow the pattern:

```bash
clipforge <command> [options]
clipforge <command> --help      # full options for any command
```

---

## Quick reference

| Command | Purpose |
|---|---|
| `doctor` | Check system requirements and configuration |
| `wizard` | Guided interactive setup |
| `make` | Render a video from a script |
| `scenes` | Preview scene breakdown before rendering |
| `social-pack` | Generate title, caption, hashtags |
| `thumbnail` | Create a thumbnail image |
| `batch` | Run multiple render jobs |
| `export-bundle` | Bundle video + thumbnail + social pack |
| `studio` | Interactive TUI (recommended for new users) |
| `templates` | Manage content template packs |
| `project` | Manage reusable project folders |
| `presets` | List available style presets |
| `init-config` | Write a starter config JSON |
| `init-profile` | Write a starter brand profile JSON |
| `init-batch` | Write a starter batch jobs JSON |
| `publish-manifest` | Create and validate publish manifests |
| `queue` | Manage publish queues |
| `publish` | Execute publish jobs |
| `analytics` | Fetch and analyse content performance |
| `optimize` | Data-driven recommendations for next video |

---

## System check

```bash
clipforge doctor
```

Verifies Python version, FFmpeg, moviepy, optional packages, and `.env` values. Run this first after installation.

---

## Rendering

### make

```bash
clipforge make --script-file my_script.txt
clipforge make --script-file my_script.txt --platform reels --audio-mode voiceover
clipforge make --config-file config.json --output output/video.mp4
clipforge make --script-file script.txt --dry-run     # preview without rendering
```

Key options:

| Option | Values | Default |
|---|---|---|
| `--script-file` | path | — |
| `--config-file` | path | — |
| `--platform` | `reels`, `tiktok`, `youtube-shorts`, `youtube`, `landscape` | `reels` |
| `--audio-mode` | `silent`, `music`, `voiceover`, `voiceover+music` | `silent` |
| `--text-mode` | `none`, `subtitle`, `title_cards` | `subtitle` |
| `--style` | `clean`, `bold`, `minimal`, `cinematic` | `bold` |
| `--output` | path | `output/video.mp4` |
| `--dry-run` | flag | off |

### scenes

Preview scene segmentation without rendering:

```bash
clipforge scenes --script-file my_script.txt
```

---

## Social content

### social-pack

Generate platform-optimised title, caption, and hashtags:

```bash
clipforge social-pack --script-file my_script.txt --platform reels
clipforge social-pack --script-file my_script.txt --platform youtube --brand-name "Acme Co"
clipforge social-pack --script-file my_script.txt --save-json output/pack.json
```

### thumbnail

Create a thumbnail image:

```bash
clipforge thumbnail --text "5 Python Tips" --platform youtube
clipforge thumbnail --text "My Hook" --style bold --output thumb.jpg
```

---

## Batch processing

```bash
# Create a batch config
clipforge init-batch --output jobs.json

# Run all jobs
clipforge batch --batch-file jobs.json
```

---

## Export bundle

Bundle video + thumbnail + social pack into a single folder:

```bash
clipforge export-bundle --video output/video.mp4 --script-file script.txt \
    --platform reels --output-dir bundles/ep01

# Auto-create a publish manifest and add to queue:
clipforge export-bundle --video output/video.mp4 --script-file script.txt \
    --platform reels --output-dir bundles/ep01 \
    --publish-manifest --add-to-queue publish_queue
```

---

## Publish manifest

A publish manifest captures everything needed to publish a video: file path, platform, title, caption, hashtags, schedule, campaign.

```bash
# Create a manifest
clipforge publish-manifest create \
    --video-file output/video.mp4 \
    --platform youtube \
    --title "My Video Title" \
    --caption "Watch this!" \
    --job-name ep01

# Show manifest details
clipforge publish-manifest show manifest.json
clipforge publish-manifest show manifest.json --json

# Validate against platform rules
clipforge publish-manifest validate manifest.json
```

---

## Queue

The publish queue manages manifests through their lifecycle: draft → pending → ready → published.

```bash
# Initialise a queue directory
clipforge queue init my_queue

# Add a manifest to the queue
clipforge queue add my_queue manifest.json

# List queue contents
clipforge queue list my_queue
clipforge queue summary my_queue

# Change a manifest's status
clipforge queue status my_queue <manifest-id> ready

# Execute all ready items
clipforge queue execute my_queue
clipforge queue execute my_queue --dry-run   # preview only

# Retry failed items
clipforge queue retry-failed my_queue
```

---

## Publish

Execute, dry-run, validate, or retry publish jobs.

```bash
# Validate before publishing
clipforge publish validate manifest.json

# Dry-run — see exactly what would happen, no API calls
clipforge publish dry-run manifest.json

# Execute — requires confirmation
clipforge publish execute manifest.json
clipforge publish execute manifest.json --yes   # skip confirmation

# Retry a failed manifest
clipforge publish retry manifest.json
```

Supported providers:

| Platform | Provider | Real upload |
|---|---|---|
| `youtube`, `youtube-shorts` | YouTubePublishProvider | Yes (requires credentials) |
| `reels`, `tiktok`, `landscape` | ManualPublishProvider | No — produces a checklist file |

---

## Analytics

```bash
# Fetch analytics for one manifest
clipforge analytics fetch manifest.json

# Fetch for all published items in a queue
clipforge analytics fetch --queue my_queue

# Enter metrics by hand (for TikTok/Reels)
clipforge analytics fetch manifest.json --manual

# Show latest analytics
clipforge analytics show manifest.json
clipforge analytics show manifest.json --all    # all snapshots
clipforge analytics show manifest.json --json

# Summary across all records
clipforge analytics summary
clipforge analytics summary --platform youtube
clipforge analytics summary --campaign Q2-2024

# Compare across dimensions
clipforge analytics compare --by platform
clipforge analytics compare --by template
clipforge analytics compare --by campaign --json
```

---

## Optimize

```bash
# Show recommendations
clipforge optimize report
clipforge optimize report --platform youtube --last-n 20

# Preview without saving (identical output)
clipforge optimize simulate

# Save recommendations to file
clipforge optimize apply --output optimization_notes.json
clipforge optimize apply --output optimization_notes.json --yes   # skip confirm
```

Recommendations cover: CTR vs platform benchmark, retention, best posting day/time, top template, platform comparison, engagement trend, publishing frequency.

---

## Templates

Content template packs for structured video series.

```bash
clipforge templates list
clipforge templates show <template-name>
clipforge templates apply <template-name> --output config.json
```

---

## Projects

Reusable project folders that bundle config, profile, queue, and defaults.

```bash
clipforge project init my_project
clipforge project show my_project
clipforge project list
```

---

## Studio (interactive TUI)

The Studio is the recommended entry point for new users. It provides a full interactive menu covering all major workflows — no flags to remember.

```bash
clipforge studio
```

Menu options:

| Key | Action |
|---|---|
| 1 | Build a video (with preview) |
| 2 | Preview scene breakdown |
| 3 | Generate social pack |
| 4 | Create thumbnail |
| 5 | List presets |
| 6 | List templates |
| 7 | Run doctor check |
| 8 | Publish prep (manifest + queue) |
| 9 | Analytics summary |
| 0 | Optimization recommendations |
| q | Quit |

Requires `pip install rich` (included with `.[tts]` and higher).

---

## Profiles and presets

```bash
# List available style presets
clipforge presets

# Create a brand profile
clipforge init-profile --output my_profile.json
# Edit my_profile.json, then reference it in make:
clipforge make --script-file script.txt --profile-file my_profile.json
```

---

## Global flags

```bash
clipforge --version
clipforge --help
clipforge <command> --help
```
