"""optimize command group — data-driven content improvement recommendations.

Commands::

    clipforge optimize report                       # analyse full analytics store
    clipforge optimize report --platform youtube    # filter to one platform
    clipforge optimize report --last-n 20           # recent N records only
    clipforge optimize simulate                     # same as report (alias)
    clipforge optimize apply --output notes.json    # save report to file
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click


@click.group("optimize")
def optimize_cmd() -> None:
    """Generate data-driven recommendations for your next video.

    \b
    Analyses your analytics history and surfaces actionable suggestions:
      - Best day/time to publish
      - Which template drives most engagement
      - CTR and retention vs platform benchmarks
      - Engagement trend (improving / declining)
      - Publishing frequency health

    \b
    Examples:
      clipforge optimize report
      clipforge optimize report --platform youtube --last-n 30
      clipforge optimize report --campaign Q2-2024 --json
      clipforge optimize apply --output optimization_notes.json
    """


# ── report (and simulate alias) ───────────────────────────────────────────────


@optimize_cmd.command("report")
@click.option("--store", "store_dir", default="analytics_store", show_default=True,
              help="Analytics store directory to read from.")
@click.option("--platform", "platform_filter", default="",
              help="Filter to a specific platform.")
@click.option("--campaign", "campaign_filter", default="",
              help="Filter to a specific campaign.")
@click.option("--template", "template_filter", default="",
              help="Filter to a specific template_ref.")
@click.option("--last-n", default=0, type=int,
              help="Only use the most recent N records.")
@click.option("--json", "as_json", is_flag=True, default=False,
              help="Output report as JSON.")
@click.option("--output", "output_file", default="",
              help="Save report JSON to this file path.")
def optimize_report(
    store_dir: str,
    platform_filter: str,
    campaign_filter: str,
    template_filter: str,
    last_n: int,
    as_json: bool,
    output_file: str,
) -> None:
    """Analyse analytics and print actionable recommendations.

    \b
    Examples:
      clipforge optimize report
      clipforge optimize report --store ./analytics --platform youtube
      clipforge optimize report --last-n 20 --json
    """
    from clipforge.analytics.storage import AnalyticsStore
    from clipforge.optimize.engine import Optimizer

    store = AnalyticsStore(store_dir)
    records = store.list()

    if not records:
        click.echo("No analytics records found — run 'clipforge analytics fetch' first.")
        return

    opt = Optimizer(records)
    report = opt.analyze(
        platform=platform_filter,
        campaign=campaign_filter,
        template=template_filter,
        last_n=last_n,
    )

    if output_file:
        report.save(output_file)
        click.echo(f"Report saved to: {output_file}")
        if not as_json:
            return

    if as_json:
        click.echo(json.dumps(report.to_dict(), indent=2))
        return

    _print_report(report)


# 'simulate' is an explicit alias — reads, analyses, prints; never writes files
@optimize_cmd.command("simulate")
@click.option("--store", "store_dir", default="analytics_store", show_default=True,
              help="Analytics store directory.")
@click.option("--platform", "platform_filter", default="")
@click.option("--campaign", "campaign_filter", default="")
@click.option("--template", "template_filter", default="")
@click.option("--last-n", default=0, type=int)
@click.option("--json", "as_json", is_flag=True, default=False)
def optimize_simulate(
    store_dir: str,
    platform_filter: str,
    campaign_filter: str,
    template_filter: str,
    last_n: int,
    as_json: bool,
) -> None:
    """Dry-run: show recommendations without saving any files.

    Identical to 'report' but never writes output files.
    Use this to preview what 'apply' would recommend.
    """
    from clipforge.analytics.storage import AnalyticsStore
    from clipforge.optimize.engine import Optimizer

    store = AnalyticsStore(store_dir)
    records = store.list()

    if not records:
        click.echo("No analytics records found — run 'clipforge analytics fetch' first.")
        return

    opt = Optimizer(records)
    report = opt.analyze(
        platform=platform_filter,
        campaign=campaign_filter,
        template=template_filter,
        last_n=last_n,
    )

    if as_json:
        click.echo(json.dumps(report.to_dict(), indent=2))
        return

    click.echo("[simulate mode — no files written]\n")
    _print_report(report)


# ── apply ─────────────────────────────────────────────────────────────────────


@optimize_cmd.command("apply")
@click.option("--store", "store_dir", default="analytics_store", show_default=True,
              help="Analytics store directory.")
@click.option("--platform", "platform_filter", default="")
@click.option("--campaign", "campaign_filter", default="")
@click.option("--template", "template_filter", default="")
@click.option("--last-n", default=0, type=int)
@click.option("--output", "output_file", default="optimization_notes.json",
              show_default=True,
              help="Path to write the optimization notes JSON.")
@click.option("--yes", is_flag=True, default=False,
              help="Skip confirmation prompt.")
def optimize_apply(
    store_dir: str,
    platform_filter: str,
    campaign_filter: str,
    template_filter: str,
    last_n: int,
    output_file: str,
    yes: bool,
) -> None:
    """Generate recommendations and save them to a notes file.

    \b
    What this does:
      - Analyses your analytics store
      - Writes optimization_notes.json with all recommendations
      - Does NOT modify manifests, queues, or project files
      - Does NOT publish anything

    \b
    Example:
      clipforge optimize apply --output project/optimization_notes.json
    """
    from clipforge.analytics.storage import AnalyticsStore
    from clipforge.optimize.engine import Optimizer

    store = AnalyticsStore(store_dir)
    records = store.list()

    if not records:
        click.echo("No analytics records found — run 'clipforge analytics fetch' first.")
        return

    opt = Optimizer(records)
    report = opt.analyze(
        platform=platform_filter,
        campaign=campaign_filter,
        template=template_filter,
        last_n=last_n,
    )

    if report.is_empty():
        click.echo("No records matched the given filters.")
        return

    click.echo(f"\nAnalysed {report.source_records} records.")
    click.echo(f"Found {len(report.recommendations)} recommendations "
               f"({len(report.high_priority())} high priority).\n")

    if not yes:
        click.echo(f"Will write: {output_file}")
        confirmed = click.confirm("Save optimization notes?", default=True)
        if not confirmed:
            click.echo("Cancelled.")
            return

    report.save(output_file)
    click.echo(f"Saved: {output_file}")
    click.echo()
    click.echo("Review the file, then use the recommendations to guide your next video.")
    click.echo("Run 'clipforge optimize report' any time to see the latest analysis.")


# ── Printer ───────────────────────────────────────────────────────────────────


def _print_report(report) -> None:
    from clipforge.optimize.models import OptimizationReport
    r: OptimizationReport = report

    if r.is_empty():
        click.echo("No records to analyse.")
        return

    # Header
    _trend_icon = {
        "improving": "↑",
        "declining": "↓",
        "stable": "→",
        "insufficient_data": "?",
    }
    trend_icon = _trend_icon.get(r.trend, "?")
    pct_str = f" ({r.trend_pct:+.1f}%)" if r.trend != "insufficient_data" else ""

    click.echo(f"Optimization Report  —  {r.source_records} records analysed")
    if r.filters_applied:
        fstr = "  ".join(f"{k}={v}" for k, v in r.filters_applied.items())
        click.echo(f"Filters: {fstr}")
    click.echo(f"Trend:   {trend_icon} {r.trend}{pct_str}")
    click.echo()

    # Summary metrics
    sm = r.summary_metrics
    if sm:
        click.echo("Averages:")
        click.echo(f"  Views: {sm.get('views', 0):,.0f}   "
                   f"Engagement: {sm.get('engagement_rate', 0):.2f}%   "
                   f"CTR: {sm.get('ctr', 0):.2f}%   "
                   f"Retention: {sm.get('retention_pct', 0):.1f}%")
        click.echo()

    # Top performer
    tp = r.top_performers.get("top_by_views", {})
    if tp:
        name = tp.get("job_name") or tp.get("manifest_id", "")
        click.echo(
            f"Best video: {name} ({tp.get('platform', '')})"
            f"  {tp.get('views', 0):,} views  "
            f"{tp.get('engagement_rate', 0):.2f}% engagement"
            f"  [{tp.get('published_at', '')}]"
        )
        click.echo()

    # Recommendations
    if not r.recommendations:
        click.echo("No recommendations — keep doing what you're doing!")
        return

    severity_icon = {"high": "!!", "medium": " !", "low": "  "}
    severity_label = {"high": "HIGH", "medium": "MED ", "low": "LOW "}

    click.echo(f"Recommendations ({len(r.recommendations)} total):")
    click.echo()

    for i, rec in enumerate(r.recommendations, 1):
        icon = severity_icon.get(rec.severity, "  ")
        label = severity_label.get(rec.severity, "    ")
        click.echo(f"  {icon} [{label}] {rec.title}")
        # Wrap description at ~72 chars
        words = rec.description.split()
        line, lines = [], []
        for w in words:
            if sum(len(x) for x in line) + len(line) + len(w) > 68:
                lines.append(" ".join(line))
                line = [w]
            else:
                line.append(w)
        if line:
            lines.append(" ".join(line))
        for ln in lines:
            click.echo(f"         {ln}")
        if rec.suggested_value:
            click.echo(f"         → Suggested: {rec.suggested_value}")
        if rec.confidence < 0.6:
            click.echo(f"         (low confidence — {len(rec.evidence.get('sample', [rec.evidence])):,} samples)")
        click.echo()
