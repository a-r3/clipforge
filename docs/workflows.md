# ClipForge v1.0 — Workflows

Recommended end-to-end workflows for common use cases.

---

## 1. Single video (quick path)

The fastest path from idea to published video.

```bash
# 1. Preview scene breakdown
clipforge scenes --script-file my_script.txt

# 2. Render
clipforge make --script-file my_script.txt --platform reels --output output/ep01.mp4

# 3. Generate social content
clipforge social-pack --script-file my_script.txt --platform reels

# 4. Create a publish manifest
clipforge publish-manifest create \
    --video-file output/ep01.mp4\
    --platform reels \
    --title "5 Tips You Need" \
    --job-name ep01

# 5. Dry-run the publish (always do this first)
clipforge publish dry-run ep01.manifest.json

# 6. Execute
clipforge publish execute ep01.manifest.json
```

---

## 2. Batch content pipeline

For producing multiple videos in one run.

```bash
# 1. Initialise a batch config
clipforge init-batch --output jobs.json
# Edit jobs.json to add your script files and platform variants

# 2. Run all jobs
clipforge batch --batch-file jobs.json

# 3. Export bundles (video + thumbnail + social pack per job)
# Use export-bundle per output, or add --publish-manifest --add-to-queue to batch
```

---

## 3. Full publish workflow (with queue)

The queue gives you staging, status tracking, and bulk execution.

```bash
# 1. Initialise a queue
clipforge queue init publish_queue

# 2. Build and add videos to the queue
clipforge export-bundle \
    --video output/ep01.mp4 \
    --script-file script.txt \
    --platform youtube \
    --output-dir bundles/ep01 \
    --publish-manifest \
    --add-to-queue publish_queue

# 3. Review what's queued
clipforge queue summary publish_queue

# 4. Mark items ready for publishing
clipforge queue status publish_queue <manifest-id> ready

# 5. Dry-run everything ready
clipforge queue execute publish_queue --dry-run

# 6. Execute for real
clipforge queue execute publish_queue

# 7. Retry any failures
clipforge queue retry-failed publish_queue
```

---

## 4. YouTube publishing (real API)

Prerequisites: `pip install -e ".[publish-youtube]"` and valid Google credentials.

```bash
# Set in .env:
# YOUTUBE_CREDENTIALS_PATH=/path/to/credentials.json

# 1. Validate credentials + metadata
clipforge publish validate manifest.json

# 2. Dry-run (no API call)
clipforge publish dry-run manifest.json

# 3. Upload
clipforge publish execute manifest.json
```

See `docs/publish.md` for credential setup details.

---

## 5. Analytics collection

After your video is live, collect performance data.

```bash
# Fetch analytics for one manifest (YouTube = real API, others = stub/manual)
clipforge analytics fetch manifest.json

# Or fetch for all published items in a queue
clipforge analytics fetch --queue publish_queue

# For TikTok / Reels, enter metrics manually
clipforge analytics fetch manifest.json --manual

# View latest snapshot
clipforge analytics show manifest.json

# Aggregate summary
clipforge analytics summary --platform youtube

# Compare templates side by side
clipforge analytics compare --by template
```

---

## 6. Optimization feedback loop

Use analytics to improve your next video.

```bash
# After collecting 5+ records, run the optimizer
clipforge optimize report

# Filter to recent performance
clipforge optimize report --last-n 20 --platform youtube

# Preview before saving
clipforge optimize simulate

# Save recommendations for reference
clipforge optimize apply --output optimization_notes.json
```

The optimizer surfaces: CTR vs benchmark, retention issues, best posting day, top template, engagement trend, publishing cadence.

---

## 7. Interactive Studio (all-in-one)

The Studio walks you through every workflow interactively — no flags needed.

```bash
clipforge studio
```

Covers: render → preview → social pack → publish prep → analytics → optimize.

Ideal for:
- New users exploring the tool
- Single-video sessions where you want guided prompts
- Quick analytics/optimization checks without remembering flags

---

## 8. Project-based workflow

For long-running content series with shared config, profile, and queue.

```bash
# 1. Initialise a project
clipforge project init my_series
# Sets up a project folder with config, profile, and queue

# 2. Make videos using the project
clipforge make --script-file scripts/ep01.txt \
    --project-dir my_series \
    --platform youtube

# 3. The project's queue and analytics store are shared across all episodes
clipforge queue summary my_series/queue
clipforge analytics summary --store my_series/analytics_store
clipforge optimize report --store my_series/analytics_store
```

---

## Safety reminders

- **Always dry-run before execute.** `clipforge publish dry-run manifest.json` validates everything without making API calls.
- **Manual first.** If YouTube credentials aren't configured, publishing falls back to `ManualPublishProvider`, which writes a checklist file — never silently fails.
- **Optimize is advisory.** `clipforge optimize apply` writes a notes file; it never modifies manifests, queues, or project configs.
- **Analytics are local.** All records are stored as JSON in your `analytics_store` directory. Nothing is sent to external services beyond the platform APIs you configure.
