# ClipForge V6 — Analytics

Collect, store, and analyse performance metrics for your published videos — all local, no third-party dashboards required.

---

## Overview

| Platform      | Data source      | Status          |
|---------------|------------------|-----------------|
| YouTube       | YouTube Analytics API v2 | Real API (requires credentials) |
| TikTok        | TikTok Creator Center    | Manual entry only (V6) |
| Instagram Reels | Instagram Insights      | Manual entry only (V6) |
| Landscape / other | —               | Mock / manual   |

Analytics are stored as individual JSON files in a local store directory. Multiple snapshots per video are supported — fetch as often as you like.

---

## Quick start

```bash
# Fetch analytics for a single manifest
clipforge analytics fetch my_video.manifest.json

# Fetch for every published item in a queue
clipforge analytics fetch --queue ./publish_queue

# Show the latest snapshot
clipforge analytics show my_video.manifest.json

# Aggregate summary
clipforge analytics summary

# Compare across platforms
clipforge analytics compare --by platform
```

---

## Commands

### `analytics fetch`

```
clipforge analytics fetch [MANIFEST_FILE] [OPTIONS]
```

Fetch the latest analytics for one manifest or all published queue items.

| Option | Default | Description |
|--------|---------|-------------|
| `--queue QUEUE_DIR` | — | Fetch for all `published` items in the queue |
| `--store DIR` | `analytics_store` | Where to save records |
| `--publish-config FILE` | — | Path to `publish_config.json` (credentials) |
| `--manual` | off | Prompt for manual metric entry |
| `--force` | off | Re-fetch even if an API record already exists |

If the platform collector is unavailable (TikTok, Reels), a stub record is saved with a message pointing to manual entry. Use `--manual` to enter metrics by hand instead:

```bash
clipforge analytics fetch my_video.manifest.json --manual
```

This opens a prompt to enter views, likes, comments, shares, impressions, reach, CTR, retention %, and avg view duration.

---

### `analytics show`

```
clipforge analytics show MANIFEST_FILE [OPTIONS]
```

Show stored analytics for a manifest.

| Option | Default | Description |
|--------|---------|-------------|
| `--store DIR` | `analytics_store` | Store directory to read from |
| `--all` | off | Show all snapshots (not just the latest) |
| `--json` | off | Output raw JSON |

Example:

```
Analytics — youtube  [api]
  Fetched:      2024-06-15 10:30:00
  Job:          launch-promo
  Campaign:     Q2-2024

  Views:        12,340
  Likes:        580
  Comments:     34
  Shares:       91
  Impressions:  28,500
  Reach:        21,000
  CTR:          4.33%
  Retention:    52.0%
  Avg view:     78s
  Engagement:   5.72%
```

---

### `analytics summary`

```
clipforge analytics summary [OPTIONS]
```

Print aggregate totals and averages over all records (or a filtered subset).

| Option | Default | Description |
|--------|---------|-------------|
| `--store DIR` | `analytics_store` | Store directory |
| `--platform P` | — | Filter to one platform |
| `--campaign C` | — | Filter to one campaign |
| `--json` | off | Output raw JSON |

---

### `analytics compare`

```
clipforge analytics compare [OPTIONS]
```

Compare analytics across a chosen dimension.

| Option | Default | Description |
|--------|---------|-------------|
| `--store DIR` | `analytics_store` | Store directory |
| `--by` | `platform` | Dimension: `platform`, `template`, `campaign` |
| `--json` | off | Output raw JSON |

For programmatic A/B comparison (not just grouped averages), use `AnalyticsAggregator.compare()` directly in Python — see [Python API](#python-api) below.

---

## YouTube setup

YouTube analytics requires the same credentials as the YouTube publish provider, plus the additional `yt-analytics.readonly` scope.

### Using a service account (recommended)

```bash
export YOUTUBE_CREDENTIALS_PATH=/path/to/service_account.json
```

The service account must have access to the channel and be granted the `yt-analytics.readonly` scope via Domain-Wide Delegation or direct permission.

### Using OAuth2 user credentials

The OAuth2 token file must have been obtained with both the `youtube.upload` and `yt-analytics.readonly` scopes. Obtain it with:

```bash
# During initial auth, request both scopes:
# https://www.googleapis.com/auth/youtube
# https://www.googleapis.com/auth/yt-analytics.readonly
```

See `docs/youtube_publish.md` for the full credential setup walkthrough — analytics uses the same file.

### Checking availability

```bash
clipforge analytics fetch manifest.json
# If credentials are missing, you'll see:
#   stub — YouTubeAnalyticsCollector not available: credentials not configured
```

---

## TikTok and Instagram Reels

TikTok's Business API and Instagram's Graph API require special app-review approval that isn't available to general-purpose automation tools in V6.

**Workflow for TikTok / Reels:**

1. Open TikTok Creator Center / Instagram Insights in your browser.
2. Copy the metrics for your video.
3. Run `clipforge analytics fetch manifest.json --manual` and enter them.

The record is saved with `data_source: "manual"` and is included in all summaries and comparisons.

---

## Store layout

```
analytics_store/
  <analytics_id>.json   ← one file per fetch snapshot
  <analytics_id>.json
  ...
```

Each file is a self-contained JSON snapshot. No index file is maintained — the store scans all `.json` files on each operation.

**Multiple snapshots:** Running `fetch` again (without `--force`) for a manifest that already has a real API record skips it. Use `--force` to always create a new snapshot.

---

## Python API

```python
from clipforge.analytics.models import ContentAnalytics
from clipforge.analytics.storage import AnalyticsStore
from clipforge.analytics.aggregator import AnalyticsAggregator
from clipforge.analytics.factory import AnalyticsCollectorFactory
from clipforge.publish_config import PublishConfig

# Load store
store = AnalyticsStore("./analytics_store")

# Fetch for one manifest
config = PublishConfig.load_or_default("publish_config.json")
collector = AnalyticsCollectorFactory.for_platform("youtube", config)
record = collector.fetch(manifest)
store.save(record)

# Query
all_records   = store.list()
yt_records    = store.for_platform("youtube")
q1_records    = store.for_campaign("Q1-2024")
latest        = store.latest_for_manifest(manifest_id)

# Aggregate
agg = AnalyticsAggregator(all_records)
summary   = agg.summary()
by_plat   = agg.by_platform()
by_camp   = agg.by_campaign()
top_5     = agg.top_by("views", n=5)
series    = agg.time_series(bucket="month")

# A/B compare
delta = AnalyticsAggregator.compare(
    records_a=q1_records,
    records_b=q2_records,
    label_a="Q1",
    label_b="Q2",
)
# delta["metrics"]["views"]["winner"] → "Q1" or "Q2" or "tie"
# delta["metrics"]["engagement_rate"]["delta_pct"] → % improvement
```

---

## What's real vs stub

| `data_source` | Meaning |
|---------------|---------|
| `api` | Fetched from a real platform API |
| `manual` | Entered by hand via `--manual` |
| `mock` | Generated by `MockAnalyticsCollector` (CI / testing) |
| `stub` | API unavailable; metrics are zero with a `fetch_error` message |

`ContentAnalytics.is_real()` returns `True` only for `data_source == "api"`. Summaries and comparisons include all records regardless of source — filter explicitly if needed:

```python
real_records = [r for r in store.list() if r.is_real()]
```
