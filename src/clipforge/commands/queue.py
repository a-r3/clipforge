"""queue command group — manage local publish queues."""

from __future__ import annotations

import sys
from pathlib import Path

import click


@click.group("queue")
def queue_cmd() -> None:
    """Manage local publish queues.

    \b
    A queue is a folder-based store of publish manifests with lifecycle
    statuses (draft → pending → ready → scheduled → published).

    \b
    Examples:
      clipforge queue init ./publish_queue
      clipforge queue add ./publish_queue manifest.json
      clipforge queue list ./publish_queue
      clipforge queue summary ./publish_queue
      clipforge queue status ./publish_queue <manifest-id> ready
    """


# ── init ──────────────────────────────────────────────────────────────────────


@queue_cmd.command("init")
@click.argument("queue_dir")
@click.option("--name", "-n", default="",
              help="Human-readable queue name (defaults to folder name).")
def queue_init(queue_dir: str, name: str) -> None:
    """Create a new publish queue at QUEUE_DIR."""
    from clipforge.publish_queue import PublishQueue

    p = Path(queue_dir)
    if p.exists() and (p / "queue.json").exists():
        click.echo(f"  Queue already exists at {queue_dir}")
        click.echo(f"  Use 'clipforge queue summary {queue_dir}' to inspect it.")
        sys.exit(1)

    q = PublishQueue.init(p, name=name)
    click.echo()
    click.echo(f"  Queue created: {queue_dir}")
    click.echo(f"  Name        : {q.name}")
    click.echo()
    click.echo("  To add a manifest:")
    click.echo(f"    clipforge queue add {queue_dir} <manifest.json>")
    click.echo()


# ── add ───────────────────────────────────────────────────────────────────────


@queue_cmd.command("add")
@click.argument("queue_dir")
@click.argument("manifest_file")
@click.option("--status", default="",
              type=click.Choice(["", "draft", "pending", "ready"]),
              help="Override the manifest's initial status before adding.")
def queue_add(queue_dir: str, manifest_file: str, status: str) -> None:
    """Add a manifest JSON file to a queue."""
    from clipforge.publish_manifest import PublishManifest
    from clipforge.publish_queue import PublishQueue

    try:
        q = PublishQueue.load(queue_dir)
    except FileNotFoundError:
        click.echo(f"  Error: No queue found at '{queue_dir}'.", err=True)
        click.echo(f"  Run: clipforge queue init {queue_dir}", err=True)
        sys.exit(1)

    try:
        m = PublishManifest.load(manifest_file)
    except FileNotFoundError as exc:
        click.echo(f"  Error: {exc}", err=True)
        sys.exit(1)

    if status:
        m.status = status

    try:
        q.append(m)
    except ValueError as exc:
        click.echo(f"  Error: {exc}", err=True)
        sys.exit(1)

    click.echo()
    click.echo(f"  Added to queue: {q.name}")
    click.echo(f"  Manifest ID : {m.manifest_id}")
    click.echo(f"  Job         : {m.job_name}")
    click.echo(f"  Platform    : {m.platform}")
    click.echo(f"  Status      : {m.status}")
    click.echo(f"  Queue total : {len(q)} item(s)")
    click.echo()


# ── list ──────────────────────────────────────────────────────────────────────


@queue_cmd.command("list")
@click.argument("queue_dir")
@click.option("--status", "-s", default="",
              help="Filter by status (e.g. draft, ready, scheduled).")
@click.option("--platform", "-p", default="",
              help="Filter by platform.")
@click.option("--campaign", default="",
              help="Filter by campaign name.")
def queue_list(queue_dir: str, status: str, platform: str, campaign: str) -> None:
    """List manifests in a queue."""
    from clipforge.publish_queue import PublishQueue

    try:
        q = PublishQueue.load(queue_dir)
    except FileNotFoundError:
        click.echo(f"  Error: No queue found at '{queue_dir}'.", err=True)
        sys.exit(1)

    manifests = q.list()
    if status:
        manifests = [m for m in manifests if m.status == status]
    if platform:
        manifests = [m for m in manifests if m.platform == platform]
    if campaign:
        manifests = [m for m in manifests if m.campaign_name == campaign]

    click.echo()
    if not manifests:
        filters = " ".join(filter(None, [
            f"status={status}" if status else "",
            f"platform={platform}" if platform else "",
            f"campaign={campaign}" if campaign else "",
        ]))
        click.echo(f"  Queue '{q.name}' — no items" + (f" matching {filters}" if filters else ""))
        click.echo()
        return

    click.echo(f"  Queue: {q.name}  ({len(manifests)} item(s))")
    click.echo()
    click.echo(f"  {'Job':<28} {'Platform':<16} {'Status':<24} {'Scheduled'}")
    click.echo("  " + "-" * 80)
    for m in manifests:
        sched = m.publish_at[:19] if m.publish_at else "(unscheduled)"
        job = (m.job_name[:26] + "..") if len(m.job_name) > 28 else m.job_name
        click.echo(f"  {job:<28} {m.platform:<16} {m.status:<24} {sched}")
    click.echo()


# ── summary ───────────────────────────────────────────────────────────────────


@queue_cmd.command("summary")
@click.argument("queue_dir")
def queue_summary(queue_dir: str) -> None:
    """Show a status summary for a queue."""
    from clipforge.publish_queue import PublishQueue

    try:
        q = PublishQueue.load(queue_dir)
    except FileNotFoundError:
        click.echo(f"  Error: No queue found at '{queue_dir}'.", err=True)
        sys.exit(1)

    s = q.summary()
    click.echo()
    click.echo(f"  Queue  : {s['name']}")
    click.echo(f"  Path   : {s['path']}")
    click.echo(f"  Total  : {s['total']} item(s)")
    click.echo(f"  Updated: {s['updated_at']}")
    click.echo()
    click.echo("  By status:")
    for status, count in sorted(s["by_status"].items()):
        if count:
            click.echo(f"    {status:<28} {count}")
    click.echo()


# ── status ────────────────────────────────────────────────────────────────────


@queue_cmd.command("status")
@click.argument("queue_dir")
@click.argument("manifest_id")
@click.argument("new_status")
def queue_status(queue_dir: str, manifest_id: str, new_status: str) -> None:
    """Update the status of a manifest in the queue.

    \b
    Valid statuses:
      draft, pending, ready, scheduled, manual_action_required,
      published, failed, archived
    """
    from clipforge.publish_queue import PublishQueue

    try:
        q = PublishQueue.load(queue_dir)
    except FileNotFoundError:
        click.echo(f"  Error: No queue found at '{queue_dir}'.", err=True)
        sys.exit(1)

    try:
        q.update_status(manifest_id, new_status)
    except (KeyError, ValueError) as exc:
        click.echo(f"  Error: {exc}", err=True)
        sys.exit(1)

    click.echo()
    click.echo(f"  Updated: {manifest_id[:12]}…")
    click.echo(f"  New status: {new_status}")
    click.echo()


# ── execute ───────────────────────────────────────────────────────────────────


@queue_cmd.command("execute")
@click.argument("queue_dir")
@click.option("--publish-config", "config_file", default="",
              help="Path to publish_config.json (optional).")
@click.option("--status-filter", default="ready",
              help="Only execute items with this status (default: ready).")
@click.option("--dry-run", "dry_run_only", is_flag=True, default=False,
              help="Dry-run all items without publishing.")
@click.option("--yes", "-y", is_flag=True, default=False,
              help="Skip per-item confirmation prompts.")
def queue_execute(
    queue_dir: str,
    config_file: str,
    status_filter: str,
    dry_run_only: bool,
    yes: bool,
) -> None:
    """Execute all publish-ready items in a queue.

    \b
    Items with status matching --status-filter (default: ready) are processed.
    After execution:
      - Successful uploads → status: published
      - Manual provider items → status: manual_action_required
      - Failures → status: failed
    """
    from clipforge.publish_queue import PublishQueue
    from clipforge.publish_config import PublishConfig
    from clipforge.providers.publish.factory import PublishProviderFactory
    from clipforge.providers.publish.base import PublishNotAvailableError

    try:
        q = PublishQueue.load(queue_dir)
    except FileNotFoundError:
        click.echo(f"  Error: No queue found at '{queue_dir}'.", err=True)
        sys.exit(1)

    config = PublishConfig.load_or_default(config_file or None)
    items = q.filter_by_status(status_filter)

    click.echo()
    click.echo(f"  Queue   : {q.name}")
    click.echo(f"  Filter  : status={status_filter}")
    click.echo(f"  Items   : {len(items)}")
    click.echo(f"  Mode    : {'dry-run' if dry_run_only else 'execute'}")
    click.echo()

    if not items:
        click.echo(f"  No items with status '{status_filter}'. Nothing to do.")
        click.echo()
        return

    results_summary = {"published": 0, "manual_action_required": 0, "failed": 0, "dry_run_ok": 0}

    for idx, manifest in enumerate(items, 1):
        click.echo(f"  [{idx}/{len(items)}] {manifest.job_name or manifest.manifest_id[:12]}")
        click.echo(f"    Platform : {manifest.platform}")

        provider = PublishProviderFactory.for_manifest(manifest, config)
        click.echo(f"    Provider : {provider.provider_name()}")

        target = manifest.as_publish_target()

        if dry_run_only:
            result = provider.dry_run_publish(target)
            status_icon = "OK" if result.success else "FAIL"
            click.echo(f"    Dry-run  : {status_icon}")
            if not result.success:
                click.echo(f"    Error    : {result.error}")
            results_summary["dry_run_ok" if result.success else "failed"] += 1
        else:
            dry = provider.dry_run_publish(target)
            if not dry.success:
                click.echo(f"    Pre-flight FAIL: {dry.error}")
                click.echo("    Skipping — mark as failed? Use: clipforge queue status")
                results_summary["failed"] += 1
                click.echo()
                continue

            if not yes:
                confirmed = click.confirm(f"    Publish '{manifest.job_name}'?", default=False)
                if not confirmed:
                    click.echo("    Skipped.")
                    click.echo()
                    continue

            try:
                result = provider.publish(target)
            except PublishNotAvailableError as exc:
                click.echo(f"    Error: {exc}")
                results_summary["failed"] += 1
                click.echo()
                continue

            manifest.record_attempt(result)
            mpath = q._manifest_path(manifest.manifest_id)
            manifest.save(mpath)

            if result.manual_action_required:
                new_status = "manual_action_required"
                click.echo("    Status: manual_action_required")
                results_summary["manual_action_required"] += 1
            elif result.success:
                new_status = "published"
                click.echo(f"    Published: {result.post_url or '(no URL)'}")
                results_summary["published"] += 1
            else:
                new_status = "failed"
                click.echo(f"    Failed: {result.error}")
                results_summary["failed"] += 1

            q.update_status(manifest.manifest_id, new_status)

        click.echo()

    click.echo("  Summary:")
    if dry_run_only:
        click.echo(f"    dry-run OK   : {results_summary['dry_run_ok']}")
        click.echo(f"    dry-run FAIL : {results_summary['failed']}")
    else:
        for k, v in results_summary.items():
            if k != "dry_run_ok" and v:
                click.echo(f"    {k:<28} {v}")
    click.echo()


# ── retry-failed ──────────────────────────────────────────────────────────────


@queue_cmd.command("retry-failed")
@click.argument("queue_dir")
@click.option("--publish-config", "config_file", default="",
              help="Path to publish_config.json (optional).")
@click.option("--yes", "-y", is_flag=True, default=False,
              help="Skip confirmation prompts.")
def queue_retry_failed(queue_dir: str, config_file: str, yes: bool) -> None:
    """Retry all 'failed' items in a queue.

    Resets each failed item to 'pending' and attempts to publish again.
    """
    from clipforge.publish_queue import PublishQueue

    try:
        q = PublishQueue.load(queue_dir)
    except FileNotFoundError:
        click.echo(f"  Error: No queue found at '{queue_dir}'.", err=True)
        sys.exit(1)

    failed_items = q.filter_by_status("failed")
    click.echo()
    click.echo(f"  Queue        : {q.name}")
    click.echo(f"  Failed items : {len(failed_items)}")
    click.echo()

    if not failed_items:
        click.echo("  No failed items to retry.")
        click.echo()
        return

    # Reset failed → pending, then re-run execute
    for m in failed_items:
        q.update_status(m.manifest_id, "pending")
    click.echo(f"  Reset {len(failed_items)} item(s) to 'pending'.")

    # Delegate to queue execute with pending filter
    from click.testing import CliRunner
    from clipforge.cli import main
    args = ["queue", "execute", queue_dir, "--status-filter", "pending"]
    if config_file:
        args += ["--publish-config", config_file]
    if yes:
        args += ["--yes"]

    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(main, args, catch_exceptions=False)
    if result.output:
        click.echo(result.output, nl=False)
    sys.exit(result.exit_code)
