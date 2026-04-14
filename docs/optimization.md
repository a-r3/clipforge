# ClipForge V7 — Optimization

Turn historical analytics into actionable guidance for your next video. The optimization engine analyses your `analytics_store` and surfaces concrete recommendations — no AI, no external services, no guesswork.

---

## How it works

The engine compares your own performance data against statistical benchmarks and internal patterns:

| Analysis pass | What it looks for |
|---|---|
| **Benchmark check** | CTR and retention vs typical ranges per platform |
| **Timing** | Best day-of-week and hour for views / engagement |
| **Template** | Which `template_ref` drives highest engagement |
| **Platform** | Which platform returns best results (multi-platform creators) |
| **Campaign** | Which campaign achieved highest engagement rate |
| **Trend** | Improving vs declining across first/second half of data |
| **Frequency** | Long posting gaps; consistent cadence recognition |

All analysis is local — your data never leaves your machine.

---

## Quick start

```bash
# Run optimization report over your full analytics store
clipforge optimize report

# Preview first (same output, no files written)
clipforge optimize simulate

# Save recommendations to a file
clipforge optimize apply --output project/optimization_notes.json
```

---

## Commands

### `optimize report`

```
clipforge optimize report [OPTIONS]
```

Analyse your analytics store and print recommendations.

| Option | Default | Description |
|--------|---------|-------------|
| `--store DIR` | `analytics_store` | Analytics store to read from |
| `--platform P` | — | Filter to one platform |
| `--campaign C` | — | Filter to one campaign |
| `--template T` | — | Filter to one template_ref |
| `--last-n N` | 0 (all) | Use only the most recent N records |
| `--json` | off | Output raw JSON |
| `--output FILE` | — | Save report JSON to file (then exit) |

Example output:

```
Optimization Report  —  28 records analysed
Trend:   ↑ improving (+18.4%)

Averages:
  Views: 4,312   Engagement: 6.80%   CTR: 3.10%   Retention: 54.0%

Best video: launch-promo (youtube)  12,340 views  8.20% engagement  [2024-06-15]

Recommendations (4 total):

  !! [HIGH] Template 'tmpl-bold' drives 42% more engagement
         Videos using tmpl-bold achieve 8.40% engagement, compared to
         5.90% for tmpl-clean — a 42% improvement. Prioritise
         tmpl-bold for upcoming content.
         → Suggested: tmpl-bold

   ! [MED ] Post on Thursdays for more views
         Thursday posts average 6,200 views — 35% above your overall
         average of 4,600. Schedule future posts on Thursdays.
         → Suggested: Thursday

  !! [HIGH] CTR below target on youtube
         Average CTR is 1.2%, below the typical 2–10% range for
         youtube. Test bolder thumbnails, stronger numbers/emotions in
         titles, or time-sensitive hooks.
         → Suggested: ≥2%

     [LOW ] Engagement is trending upward
         Recent videos show 7.80% engagement vs 5.90% in earlier
         ones — a 32% improvement. Stay consistent.
```

---

### `optimize simulate`

Identical to `report` but never writes any files. Use before `apply` to preview.

```bash
clipforge optimize simulate --platform youtube --last-n 20
```

---

### `optimize apply`

Generate recommendations and save them to a JSON notes file. Does **not** modify manifests, queues, project files, or publish anything.

```
clipforge optimize apply [OPTIONS]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--store DIR` | `analytics_store` | Analytics store |
| `--output FILE` | `optimization_notes.json` | Where to save the report |
| `--yes` | off | Skip confirmation prompt |
| `--platform P` | — | Filter to platform |
| `--campaign C` | — | Filter to campaign |
| `--last-n N` | 0 | Most recent N records |

After saving, review the JSON and apply the changes manually to your project, templates, or future manifests.

---

## Recommendation severity

| Severity | Meaning |
|---|---|
| `high` | Large measurable gap — act on this first |
| `medium` | Moderate signal or limited sample size |
| `low` | Informational — positive signal or minor delta |

Confidence (0.0–1.0) is based on sample size. A recommendation with `confidence < 0.6` has fewer than ~3 records in the relevant group and should be treated as a directional hint rather than a hard rule.

---

## Benchmark ranges

These are the "healthy" ranges used for CTR and retention checks:

| Platform | CTR range | Retention range |
|---|---|---|
| YouTube | 2–10% | 30–70% |
| YouTube Shorts | 1–8% | 60–90% |
| TikTok | 0.5–5% | 40–80% |
| Reels | 0.5–5% | 40–80% |

**Sources:** These ranges reflect commonly cited benchmarks from platform creator documentation and industry reporting. Your channel's actual targets may differ based on niche, audience size, and content type.

---

## Python API

```python
from clipforge.analytics.storage import AnalyticsStore
from clipforge.optimize.engine import Optimizer
from clipforge.optimize.models import OptimizationReport

store = AnalyticsStore("./analytics_store")
records = store.list()

opt = Optimizer(records)

# Full analysis
report = opt.analyze()

# Filtered analysis
report = opt.analyze(platform="youtube", last_n=20)

# Read recommendations
for rec in report.high_priority():
    print(f"[{rec.severity}] {rec.title}")
    print(f"  {rec.description}")
    if rec.suggested_value:
        print(f"  → {rec.suggested_value}")

# Group by category
timing_recs = report.by_category("timing")
template_recs = report.by_category("template")

# Trend
print(report.trend)        # "improving" | "declining" | "stable" | "insufficient_data"
print(report.trend_pct)    # +18.4 or -12.1, etc.

# Top performers
best = report.top_performers["top_by_views"]
print(best["job_name"], best["views"])

# Save and reload
report.save("optimization_notes.json")
report2 = OptimizationReport.load("optimization_notes.json")
```

---

## Minimum data requirements

| Analysis | Minimum records |
|---|---|
| Benchmark checks (CTR / retention) | 3 per platform |
| Timing (best day) | 6 total, 2 per day |
| Template comparison | 2 templates × 2 records each |
| Platform comparison | 2 platforms × 2 records each |
| Trend analysis | 6 total |
| Frequency check | 5 total with valid `published_at` |

With fewer than the minimum, the pass is skipped — no misleading recommendations from thin data.

---

## What this does NOT do

- **No AI rewrites.** Titles, captions, and scripts are never modified automatically.
- **No auto-publish.** Nothing is pushed to any platform.
- **No manifest overrides.** Existing manifests and queues are never touched.
- **No external calls.** All analysis runs locally against your own stored analytics.

The optimization layer is advisory only. You review the recommendations and decide what to act on.
