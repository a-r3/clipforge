"""analytics command group — fetch, show, summarise, and compare content analytics.

Commands::

    clipforge analytics fetch <manifest_file>          # fetch analytics for one manifest
    clipforge analytics fetch --queue <queue_dir>      # fetch for all published items in queue
    clipforge analytics show  <manifest_file>          # show latest analytics for a manifest
    clipforge analytics summary                        # aggregate summary over a store
    clipforge analytics compare --by platform          # compare by platform / template / campaign
"""

from __future__ import annotations

import json
import sys

import click


@click.group("analytics")
def analytics_cmd() -> None:
    """Collect and inspect analytics for published content.

    \b
    Fetch analytics:
      clipforge analytics fetch manifest.json
      clipforge analytics fetch --queue ./my_queue
      clipforge analytics fetch manifest.json --manual

    \b
    View analytics:
      clipforge analytics show manifest.json
      clipforge analytics summary --store ./analytics_store
      clipforge analytics compare --store ./analytics_store --by platform
    """


# ── fetch ─────────────────────────────────────────────────────────────────────


@analytics_cmd.command("fetch")
@click.argument("manifest_file", default="", required=False)
@click.option("--queue", "queue_dir", default="",
              help="Fetch analytics for all published items in this queue directory.")
@click.option("--store", "store_dir", default="analytics_store",
              show_default=True,
              help="Directory where analytics records are saved.")
@click.option("--publish-config", "config_file", default="",
              help="Path to publish_config.json (optional).")
@click.option("--manual", is_flag=True, default=False,
              help="Enter metrics by hand (prompts for each metric).")
@click.option("--force", is_flag=True, default=False,
              help="Re-fetch even if a recent record already exists.")
def analytics_fetch(
    manifest_file: str,
    queue_dir: str,
    store_dir: str,
    config_file: str,
    manual: bool,
    force: bool,
) -> None:
    """Fetch analytics for a manifest or all published queue items.

    \b
    Examples:
      clipforge analytics fetch manifest.json
      clipforge analytics fetch manifest.json --manual
      clipforge analytics fetch --queue ./my_queue --store ./analytics
    """
    from clipforge.analytics.factory import AnalyticsCollectorFactory
    from clipforge.analytics.storage import AnalyticsStore
    from clipforge.publish_config import PublishConfig
    from clipforge.publish_manifest import PublishManifest
    from clipforge.publish_queue import PublishQueue

    if not manifest_file and not queue_dir:
        click.echo("Error: provide MANIFEST_FILE or --queue QUEUE_DIR.", err=True)
        sys.exit(1)

    config = PublishConfig.load_or_default(config_file or None)
    store = AnalyticsStore(store_dir)

    manifests: list[PublishManifest] = []

    if queue_dir:
        try:
            q = PublishQueue.load(queue_dir)
        except Exception as exc:
            click.echo(f"Error loading queue: {exc}", err=True)
            sys.exit(1)
        manifests = q.filter_by_status("published")
        if not manifests:
            click.echo("No published items in queue.")
            return
    else:
        try:
            manifests = [PublishManifest.load(manifest_file)]
        except FileNotFoundError:
            click.echo(f"Error: manifest not found: {manifest_file}", err=True)
            sys.exit(1)

    fetched = 0
    skipped = 0
    for manifest in manifests:
        if not force:
            existing = store.latest_for_manifest(manifest.manifest_id)
            if existing and existing.is_real():
                click.echo(
                    f"  Skipping {manifest.job_name or manifest.manifest_id} "
                    f"(already have API record from {existing.fetched_at[:10]}). "
                    f"Use --force to re-fetch."
                )
                skipped += 1
                continue

        if manual:
            record = _manual_entry(manifest)
        else:
            collector = AnalyticsCollectorFactory.for_platform(manifest.platform, config)
            record = collector.fetch(manifest)

        path = store.save(record)
        status = "manual" if manual else record.data_source
        if record.fetch_error:
            click.echo(
                f"  {manifest.job_name or manifest.manifest_id}: "
                f"{status} — {record.fetch_error}"
            )
        else:
            click.echo(
                f"  {manifest.job_name or manifest.manifest_id}: "
                f"saved ({status}) → {path.name}"
            )
        fetched += 1

    click.echo(f"\nFetched: {fetched}  Skipped: {skipped}")


# ── show ──────────────────────────────────────────────────────────────────────


@analytics_cmd.command("show")
@click.argument("manifest_file")
@click.option("--store", "store_dir", default="analytics_store", show_default=True,
              help="Analytics store directory.")
@click.option("--all", "show_all", is_flag=True, default=False,
              help="Show all snapshots, not just the latest.")
@click.option("--json", "as_json", is_flag=True, default=False,
              help="Output as JSON.")
def analytics_show(
    manifest_file: str,
    store_dir: str,
    show_all: bool,
    as_json: bool,
) -> None:
    """Show analytics for a manifest (latest snapshot by default).

    \b
    Examples:
      clipforge analytics show manifest.json
      clipforge analytics show manifest.json --all
      clipforge analytics show manifest.json --json
    """
    from clipforge.analytics.storage import AnalyticsStore
    from clipforge.publish_manifest import PublishManifest

    try:
        manifest = PublishManifest.load(manifest_file)
    except FileNotFoundError:
        click.echo(f"Error: manifest not found: {manifest_file}", err=True)
        sys.exit(1)

    store = AnalyticsStore(store_dir)

    if show_all:
        records = store.for_manifest(manifest.manifest_id)
    else:
        latest = store.latest_for_manifest(manifest.manifest_id)
        records = [latest] if latest else []

    if not records:
        click.echo(f"No analytics found for manifest: {manifest.manifest_id}")
        return

    if as_json:
        click.echo(json.dumps([r.to_dict() for r in records], indent=2))
        return

    for rec in records:
        _print_record(rec)
        if show_all and len(records) > 1:
            click.echo()


# ── summary ───────────────────────────────────────────────────────────────────


@analytics_cmd.command("summary")
@click.option("--store", "store_dir", default="analytics_store", show_default=True,
              help="Analytics store directory.")
@click.option("--platform", "platform_filter", default="",
              help="Filter to a specific platform.")
@click.option("--campaign", "campaign_filter", default="",
              help="Filter to a specific campaign.")
@click.option("--json", "as_json", is_flag=True, default=False,
              help="Output as JSON.")
def analytics_summary(
    store_dir: str,
    platform_filter: str,
    campaign_filter: str,
    as_json: bool,
) -> None:
    """Print aggregate metrics summary over analytics records.

    \b
    Examples:
      clipforge analytics summary
      clipforge analytics summary --store ./analytics
      clipforge analytics summary --platform youtube
      clipforge analytics summary --campaign Q1-2025
      clipforge analytics summary --json
    """
    from clipforge.analytics.aggregator import AnalyticsAggregator
    from clipforge.analytics.storage import AnalyticsStore

    store = AnalyticsStore(store_dir)
    records = store.list()

    if platform_filter:
        records = [r for r in records if r.platform == platform_filter]
    if campaign_filter:
        records = [r for r in records if r.campaign_name == campaign_filter]

    if not records:
        click.echo("No analytics records found.")
        return

    agg = AnalyticsAggregator(records)
    result = agg.summary()

    if as_json:
        click.echo(json.dumps(result, indent=2))
        return

    _print_summary(result, platform_filter=platform_filter, campaign_filter=campaign_filter)


# ── compare ───────────────────────────────────────────────────────────────────


@analytics_cmd.command("compare")
@click.option("--store", "store_dir", default="analytics_store", show_default=True,
              help="Analytics store directory.")
@click.option("--by", "group_by",
              type=click.Choice(["platform", "template", "campaign"]),
              default="platform", show_default=True,
              help="Dimension to compare across.")
@click.option("--json", "as_json", is_flag=True, default=False,
              help="Output as JSON.")
def analytics_compare(
    store_dir: str,
    group_by: str,
    as_json: bool,
) -> None:
    """Compare analytics across platforms, templates, or campaigns.

    \b
    Examples:
      clipforge analytics compare --by platform
      clipforge analytics compare --by campaign
      clipforge analytics compare --by template --json
    """
    from clipforge.analytics.aggregator import AnalyticsAggregator
    from clipforge.analytics.storage import AnalyticsStore

    store = AnalyticsStore(store_dir)
    records = store.list()

    if not records:
        click.echo("No analytics records found.")
        return

    agg = AnalyticsAggregator(records)

    if group_by == "platform":
        grouped = agg.by_platform()
    elif group_by == "template":
        grouped = agg.by_template()
    else:
        grouped = agg.by_campaign()

    if as_json:
        click.echo(json.dumps(grouped, indent=2))
        return

    _print_grouped(grouped, group_by)


# ── Private helpers ───────────────────────────────────────────────────────────


def _manual_entry(manifest):
    """Prompt the user to enter metrics by hand. Returns a ContentAnalytics record."""

    from clipforge.analytics.models import ContentAnalytics

    click.echo(f"\nManual analytics entry for: {manifest.job_name or manifest.manifest_id}")
    click.echo("Press Enter to skip a metric (leaves it at 0).\n")

    def _int(prompt: str) -> int:
        val = click.prompt(f"  {prompt}", default="0", show_default=False).strip()
        try:
            return max(0, int(val))
        except ValueError:
            return 0

    def _float(prompt: str) -> float:
        val = click.prompt(f"  {prompt}", default="0.0", show_default=False).strip()
        try:
            return max(0.0, float(val))
        except ValueError:
            return 0.0

    views = _int("Views")
    likes = _int("Likes")
    comments = _int("Comments")
    shares = _int("Shares")
    impressions = _int("Impressions")
    reach = _int("Reach")
    ctr = _float("CTR % (e.g. 3.5)")
    retention_pct = _float("Retention % (e.g. 45.0)")
    avg_view_s = _float("Avg view duration (seconds)")

    eng = round((likes + comments + shares) / max(1, views) * 100, 4) if views else 0.0

    last = manifest.last_attempt() or {}
    return ContentAnalytics(
        manifest_id=manifest.manifest_id,
        post_id=last.get("post_id", ""),
        post_url=last.get("post_url", ""),
        platform=manifest.platform,
        published_at=last.get("published_at", manifest.publish_at),
        views=views,
        likes=likes,
        comments=comments,
        shares=shares,
        impressions=impressions,
        reach=reach,
        ctr=ctr,
        retention_pct=retention_pct,
        avg_view_duration_s=avg_view_s,
        engagement_rate=eng,
        job_name=manifest.job_name,
        campaign_name=manifest.campaign_name,
        template_ref=manifest.template_ref,
        profile_ref=manifest.profile_ref,
        data_source="manual",
    )


def _print_record(rec) -> None:
    """Pretty-print a single ContentAnalytics record."""
    from clipforge.analytics.models import ContentAnalytics
    r: ContentAnalytics = rec

    source_tag = f"[{r.data_source}]"
    if r.fetch_error:
        source_tag += f" ⚠  {r.fetch_error}"

    click.echo(f"Analytics — {r.platform}  {source_tag}")
    click.echo(f"  Fetched:      {r.fetched_at[:19].replace('T', ' ')}")
    if r.job_name:
        click.echo(f"  Job:          {r.job_name}")
    if r.campaign_name:
        click.echo(f"  Campaign:     {r.campaign_name}")
    click.echo("")
    click.echo(f"  Views:        {r.views:,}")
    click.echo(f"  Likes:        {r.likes:,}")
    click.echo(f"  Comments:     {r.comments:,}")
    click.echo(f"  Shares:       {r.shares:,}")
    click.echo(f"  Impressions:  {r.impressions:,}")
    click.echo(f"  Reach:        {r.reach:,}")
    click.echo(f"  CTR:          {r.ctr:.2f}%")
    click.echo(f"  Retention:    {r.retention_pct:.1f}%")
    click.echo(f"  Avg view:     {r.avg_view_duration_s:.0f}s")
    click.echo(f"  Engagement:   {r.engagement_rate:.2f}%")


def _print_summary(result: dict, platform_filter: str = "", campaign_filter: str = "") -> None:
    """Pretty-print a summary dict from AnalyticsAggregator.summary()."""
    filters = []
    if platform_filter:
        filters.append(f"platform={platform_filter}")
    if campaign_filter:
        filters.append(f"campaign={campaign_filter}")
    label = "  (" + ", ".join(filters) + ")" if filters else ""

    click.echo(f"Analytics Summary{label}")
    click.echo(f"  Records: {result['count']}")
    click.echo("")

    totals = result.get("totals", {})
    avgs = result.get("averages", {})

    click.echo("  Metric          Total           Avg")
    click.echo("  " + "-" * 50)
    metrics = [
        ("views", "Views"),
        ("likes", "Likes"),
        ("comments", "Comments"),
        ("shares", "Shares"),
        ("impressions", "Impressions"),
        ("reach", "Reach"),
        ("ctr", "CTR %"),
        ("retention_pct", "Retention %"),
        ("engagement_rate", "Engagement %"),
    ]
    for key, label in metrics:
        total_val = totals.get(key, 0)
        avg_val = avgs.get(key, 0)
        if isinstance(total_val, float) or isinstance(avg_val, float):
            click.echo(f"  {label:<16} {total_val:>12.2f}    {avg_val:>10.2f}")
        else:
            click.echo(f"  {label:<16} {total_val:>12,}    {avg_val:>10,.0f}")


def _print_grouped(grouped: dict, dimension: str) -> None:
    """Pretty-print grouped comparison output."""
    click.echo(f"Analytics by {dimension}\n")
    for key, data in grouped.items():
        click.echo(f"  {dimension.capitalize()}: {key}  (n={data['count']})")
        avgs = data.get("averages", {})
        click.echo(
            f"    Views: {avgs.get('views', 0):,.0f}  "
            f"Likes: {avgs.get('likes', 0):,.0f}  "
            f"Engagement: {avgs.get('engagement_rate', 0):.2f}%  "
            f"CTR: {avgs.get('ctr', 0):.2f}%"
        )
        click.echo()
