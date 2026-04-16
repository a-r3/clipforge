"""publish command group — execute, dry-run, validate, and retry publish jobs."""

from __future__ import annotations

import sys

import click


@click.group("publish")
def publish_cmd() -> None:
    """Execute publish jobs from manifests or queue items.

    \b
    The publish command connects validated manifests to publish providers.
    Always run 'dry-run' before 'execute' to verify what will be sent.

    \b
    Examples:
      clipforge publish validate manifest.json
      clipforge publish dry-run  manifest.json
      clipforge publish execute  manifest.json
      clipforge publish retry    manifest.json
    """


# ── validate ──────────────────────────────────────────────────────────────────


@publish_cmd.command("validate")
@click.argument("manifest_file")
@click.option("--publish-config", "config_file", default="",
              help="Path to publish_config.json (optional).")
def publish_validate(manifest_file: str, config_file: str) -> None:
    """Validate a manifest against its platform rules and provider requirements.

    Checks:
    - Manifest schema (video_path, platform, status, etc.)
    - Platform constraints (title/caption/hashtag limits)
    - Provider availability (libraries installed, credentials present)
    """
    from clipforge.providers.publish.factory import PublishProviderFactory
    from clipforge.publish_config import PublishConfig
    from clipforge.publish_format import validate_for_platform
    from clipforge.publish_manifest import PublishManifest

    try:
        m = PublishManifest.load(manifest_file)
    except FileNotFoundError as exc:
        click.echo(f"  Error: {exc}", err=True)
        sys.exit(1)

    config = PublishConfig.load_or_default(config_file or None)
    provider = PublishProviderFactory.for_manifest(m, config)
    target = m.as_publish_target()

    schema_errors = m.validate()
    platform_errors = validate_for_platform(m)
    provider_errors = provider.validate_target(target)

    all_errors = schema_errors + platform_errors + provider_errors

    click.echo()
    click.echo(f"  Manifest : {manifest_file}")
    click.echo(f"  Platform : {m.platform}")
    click.echo(f"  Provider : {provider.provider_name()}")
    click.echo(f"  Available: {'yes' if provider.is_available() else 'no'}")
    click.echo()

    if all_errors:
        click.echo(f"  Status: INVALID ({len(all_errors)} issue(s))")
        click.echo()
        for e in all_errors:
            click.echo(f"    ! {e}")
        click.echo()
        sys.exit(1)
    else:
        click.echo("  Status: OK — ready to publish")
        click.echo()


# ── dry-run ───────────────────────────────────────────────────────────────────


@publish_cmd.command("dry-run")
@click.argument("manifest_file")
@click.option("--publish-config", "config_file", default="",
              help="Path to publish_config.json (optional).")
@click.option("--provider", "provider_name", default="",
              help="Override the provider (e.g. youtube, manual).")
def publish_dry_run(
    manifest_file: str,
    config_file: str,
    provider_name: str,
) -> None:
    """Simulate a publish without uploading anything.

    \b
    Shows:
    - Which provider would be used
    - Which files and metadata would be sent
    - Whether all files exist and metadata is valid
    - Auth/credential status

    No uploads. No side effects.
    """
    from clipforge.providers.publish.factory import PublishProviderFactory
    from clipforge.publish_config import PublishConfig
    from clipforge.publish_manifest import PublishManifest

    try:
        m = PublishManifest.load(manifest_file)
    except FileNotFoundError as exc:
        click.echo(f"  Error: {exc}", err=True)
        sys.exit(1)

    config = PublishConfig.load_or_default(config_file or None)

    if provider_name:
        from clipforge.providers.publish.factory import PublishProviderFactory
        provider = PublishProviderFactory._build(provider_name, config)
    else:
        provider = PublishProviderFactory.for_manifest(m, config)

    target = m.as_publish_target()

    click.echo()
    click.echo(f"  Manifest : {manifest_file}")
    click.echo(f"  Job      : {m.job_name or '(none)'}")
    click.echo(f"  Platform : {m.platform}")
    click.echo(f"  Provider : {provider.provider_name()}")
    click.echo(f"  Available: {'yes' if provider.is_available() else 'no — see notes below'}")
    click.echo()

    result = provider.dry_run_publish(target)

    # Print the provider's summary
    if result.response_summary:
        for line in result.response_summary.splitlines():
            click.echo(f"  {line}" if not line.startswith("  ") else line)

    click.echo()
    if result.success:
        click.echo("  Dry-run result: PASS — would publish if executed")
    else:
        click.echo(f"  Dry-run result: FAIL — {result.error or 'see above'}")
        sys.exit(1)
    click.echo()


# ── execute ───────────────────────────────────────────────────────────────────


@publish_cmd.command("execute")
@click.argument("manifest_file")
@click.option("--publish-config", "config_file", default="",
              help="Path to publish_config.json (optional).")
@click.option("--provider", "provider_name", default="",
              help="Override the provider (e.g. youtube, manual).")
@click.option("--queue-dir", default="",
              help="If provided, update this queue's item status after execution.")
@click.option("--yes", "-y", is_flag=True, default=False,
              help="Skip confirmation prompt.")
def publish_execute(
    manifest_file: str,
    config_file: str,
    provider_name: str,
    queue_dir: str,
    yes: bool,
) -> None:
    """Execute a publish job for a manifest.

    \b
    The manifest status must be 'ready' or 'scheduled'.
    Always runs a dry-run first and asks for confirmation unless --yes is set.

    Updates manifest with the attempt record.
    If --queue-dir is given, updates the queue item status.
    """
    from clipforge.providers.publish.base import PublishNotAvailableError
    from clipforge.providers.publish.factory import PublishProviderFactory
    from clipforge.publish_config import PublishConfig
    from clipforge.publish_manifest import PublishManifest

    try:
        m = PublishManifest.load(manifest_file)
    except FileNotFoundError as exc:
        click.echo(f"  Error: {exc}", err=True)
        sys.exit(1)

    # Status guard — only execute ready or scheduled items
    if m.status not in ("ready", "scheduled", "pending"):
        click.echo(
            f"  Error: manifest status is '{m.status}' "
            "(expected: ready, scheduled, or pending)",
            err=True,
        )
        click.echo("  Use 'clipforge queue status' to update it first.", err=True)
        sys.exit(1)

    config = PublishConfig.load_or_default(config_file or None)

    if provider_name:
        provider = PublishProviderFactory._build(provider_name, config)
    else:
        provider = PublishProviderFactory.for_manifest(m, config)

    target = m.as_publish_target()

    # Always dry-run first
    click.echo()
    click.echo(f"  Pre-flight dry-run for: {m.job_name or manifest_file}")
    dry = provider.dry_run_publish(target)
    if not dry.success:
        click.echo(f"  Pre-flight FAILED: {dry.error or 'see dry-run output'}", err=True)
        click.echo("  Run 'clipforge publish dry-run' for details.", err=True)
        sys.exit(1)
    click.echo(f"  Pre-flight OK — provider: {provider.provider_name()}")
    click.echo()

    if not yes:
        confirmed = click.confirm("  Proceed with publish?", default=False)
        if not confirmed:
            click.echo("  Cancelled.")
            sys.exit(0)

    click.echo()
    click.echo(f"  Publishing via {provider.provider_name()}…")

    try:
        result = provider.publish(target)
    except PublishNotAvailableError as exc:
        click.echo(f"  Error: {exc}", err=True)
        sys.exit(1)

    # Record attempt in manifest
    m.record_attempt(result)
    m.save(manifest_file)

    # Determine new status
    if result.manual_action_required:
        new_status = "manual_action_required"
    elif result.success:
        new_status = "published"
    else:
        new_status = "failed"

    # Update queue if provided
    if queue_dir:
        try:
            from clipforge.publish_queue import PublishQueue
            q = PublishQueue.load(queue_dir)
            q.update_status(m.manifest_id, new_status)
        except (FileNotFoundError, KeyError) as exc:
            click.echo(f"  Warning: Could not update queue: {exc}", err=True)

    click.echo()
    if result.success:
        click.echo(f"  Published: {result.post_url or '(no URL returned)'}")
    elif result.manual_action_required:
        click.echo("  Status: manual_action_required")
        if result.response_summary:
            click.echo()
            for line in result.response_summary.splitlines()[:6]:
                click.echo(f"  {line}")
    else:
        click.echo(f"  Failed: {result.error}")

    click.echo(f"  New status : {new_status}")
    click.echo(f"  Manifest   : {manifest_file} (updated with attempt record)")
    click.echo()


# ── retry ─────────────────────────────────────────────────────────────────────


@publish_cmd.command("retry")
@click.argument("manifest_file")
@click.option("--publish-config", "config_file", default="",
              help="Path to publish_config.json (optional).")
@click.option("--provider", "provider_name", default="",
              help="Override the provider.")
@click.option("--queue-dir", default="",
              help="Queue directory to update status in.")
@click.option("--yes", "-y", is_flag=True, default=False,
              help="Skip confirmation prompt.")
def publish_retry(
    manifest_file: str,
    config_file: str,
    provider_name: str,
    queue_dir: str,
    yes: bool,
) -> None:
    """Retry a failed publish job.

    Resets status to 'pending' and re-executes.
    Only works on manifests with status 'failed'.
    """
    from clipforge.publish_manifest import PublishManifest

    try:
        m = PublishManifest.load(manifest_file)
    except FileNotFoundError as exc:
        click.echo(f"  Error: {exc}", err=True)
        sys.exit(1)

    if m.status != "failed":
        click.echo(
            f"  Error: manifest status is '{m.status}' (expected: failed)",
            err=True,
        )
        sys.exit(1)

    # Update attempt count on last record
    retry_count = (m.last_attempt() or {}).get("retry_count", 0) + 1
    m.status = "pending"
    m.save(manifest_file)
    click.echo(f"  Retry #{retry_count} — status reset to pending")

    # Re-use execute logic
    from click.testing import CliRunner

    from clipforge.cli import main
    args = ["publish", "execute", manifest_file]
    if config_file:
        args += ["--publish-config", config_file]
    if provider_name:
        args += ["--provider", provider_name]
    if queue_dir:
        args += ["--queue-dir", queue_dir]
    if yes:
        args += ["--yes"]

    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(main, args, catch_exceptions=False)
    if result.output:
        click.echo(result.output, nl=False)
    sys.exit(result.exit_code)
