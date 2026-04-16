"""publish-manifest command group — create, show, and validate publish manifests."""

from __future__ import annotations

import sys
from pathlib import Path

import click


@click.group("publish-manifest")
def publish_manifest_cmd() -> None:
    """Create, inspect, and validate publish manifests.

    \b
    A publish manifest is a structured JSON record that captures everything
    needed to describe a publishable content item: video path, social metadata,
    scheduling, and provenance (profile/template used).

    \b
    Examples:
      clipforge publish-manifest create --video-file output/video.mp4 --platform reels
      clipforge publish-manifest show manifest.json
      clipforge publish-manifest validate manifest.json
    """


# ── create ────────────────────────────────────────────────────────────────────


@publish_manifest_cmd.command("create")
@click.option("--video-file", "-v", required=True,
              help="Path to the rendered video file.")
@click.option("--platform", "-p", default="reels",
              type=click.Choice(["reels", "tiktok", "youtube-shorts", "youtube", "landscape"]),
              help="Target platform.")
@click.option("--job-name", "-n", default="",
              help="Short name for this content job (used in filenames).")
@click.option("--project-name", default="",
              help="Name of the ClipForge project this belongs to.")
@click.option("--thumbnail-file", "-t", default="",
              help="Path to thumbnail image.")
@click.option("--script-file", "-s", default="",
              help="Path to original script file.")
@click.option("--bundle-dir", default="",
              help="Path to an existing export bundle directory.")
@click.option("--title", default="",
              help="Video title.")
@click.option("--caption", default="",
              help="Platform caption / description.")
@click.option("--hashtags", default="",
              help="Hashtags (space-separated, e.g. '#AI #reels').")
@click.option("--cta", default="",
              help="Call-to-action text.")
@click.option("--hook", default="",
              help="Opening hook line.")
@click.option("--social-json", default="",
              help="Social pack JSON file to import title/caption/hashtags/cta/hook from.")
@click.option("--publish-at", default="",
              help="Scheduled publish time (ISO-8601, e.g. 2026-05-01T18:00:00Z).")
@click.option("--timezone", "tz", default="UTC",
              help="Timezone label for display (e.g. 'America/New_York').")
@click.option("--campaign-name", default="",
              help="Campaign this item belongs to.")
@click.option("--queue-name", default="default",
              help="Queue to add this manifest to (default: 'default').")
@click.option("--priority", default="normal",
              type=click.Choice(["low", "normal", "high"]),
              help="Scheduling priority.")
@click.option("--publish-target", default="",
              help="Named publish destination (e.g. 'instagram_main').")
@click.option("--manual-review", is_flag=True, default=False,
              help="Flag this manifest as requiring manual review before publishing.")
@click.option("--profile-ref", default="",
              help="Profile JSON path or name used to build this content.")
@click.option("--template-ref", default="",
              help="Template name used to build this content.")
@click.option("--brand-name", default="",
              help="Brand name.")
@click.option("--notes", default="",
              help="Free-text notes about this manifest.")
@click.option("--status", default="draft",
              type=click.Choice(["draft", "pending", "ready"]),
              help="Initial status (default: draft).")
@click.option("--output", "-o", default="",
              help="Path to save the manifest JSON (default: <job_name>.manifest.json).")
def create_manifest(
    video_file: str,
    platform: str,
    job_name: str,
    project_name: str,
    thumbnail_file: str,
    script_file: str,
    bundle_dir: str,
    title: str,
    caption: str,
    hashtags: str,
    cta: str,
    hook: str,
    social_json: str,
    publish_at: str,
    tz: str,
    campaign_name: str,
    queue_name: str,
    priority: str,
    publish_target: str,
    manual_review: bool,
    profile_ref: str,
    template_ref: str,
    brand_name: str,
    notes: str,
    status: str,
    output: str,
) -> None:
    """Create a new publish manifest JSON file."""
    import json as _json

    from clipforge.publish_manifest import PublishManifest

    # Import social metadata from a social pack JSON if provided
    if social_json:
        sp = Path(social_json)
        if not sp.exists():
            click.echo(f"  Error: social-json file not found: {social_json}", err=True)
            sys.exit(1)
        pack = _json.loads(sp.read_text(encoding="utf-8"))
        title = title or pack.get("title", "")
        caption = caption or pack.get("caption", "")
        hashtags = hashtags or pack.get("hashtags", "")
        cta = cta or pack.get("cta", "")
        hook = hook or pack.get("hook", "")

    # Derive job name from video filename if not given
    if not job_name:
        job_name = Path(video_file).stem

    m = PublishManifest(
        job_name=job_name,
        project_name=project_name,
        platform=platform,
        video_path=video_file,
        thumbnail_path=thumbnail_file,
        script_path=script_file,
        bundle_dir=bundle_dir,
        title=title,
        caption=caption,
        hashtags=hashtags,
        cta=cta,
        hook=hook,
        publish_at=publish_at,
        timezone=tz,
        campaign_name=campaign_name,
        queue_name=queue_name,
        priority=priority,
        publish_target=publish_target,
        manual_review_required=manual_review,
        profile_ref=profile_ref,
        template_ref=template_ref,
        brand_name=brand_name,
        notes=notes,
        status=status,
    )

    # Validate before saving
    errors = m.validate()
    if errors:
        click.echo("  Validation warnings:")
        for e in errors:
            click.echo(f"    ! {e}")

    # Determine output path
    out_path = Path(output) if output else Path(f"{job_name}.manifest.json")
    m.save(out_path)

    click.echo()
    click.echo(f"  Manifest created: {out_path}")
    click.echo(f"  ID      : {m.manifest_id}")
    click.echo(f"  Job     : {m.job_name}")
    click.echo(f"  Platform: {m.platform}")
    click.echo(f"  Status  : {m.status}")
    if m.publish_at:
        click.echo(f"  Sched   : {m.publish_at} ({m.timezone})")
    click.echo()


# ── show ──────────────────────────────────────────────────────────────────────


@publish_manifest_cmd.command("show")
@click.argument("manifest_file")
@click.option("--json", "as_json", is_flag=True, default=False,
              help="Output raw JSON.")
def show_manifest(manifest_file: str, as_json: bool) -> None:
    """Display the contents of a publish manifest."""
    import json as _json

    from clipforge.publish_manifest import PublishManifest

    try:
        m = PublishManifest.load(manifest_file)
    except FileNotFoundError as exc:
        click.echo(f"  Error: {exc}", err=True)
        sys.exit(1)

    if as_json:
        click.echo(_json.dumps(m.to_dict(), indent=2))
        return

    click.echo()
    click.echo(f"  Manifest: {manifest_file}")
    click.echo(f"  {'ID':<22} {m.manifest_id}")
    click.echo(f"  {'Job':<22} {m.job_name or '(none)'}")
    click.echo(f"  {'Project':<22} {m.project_name or '(none)'}")
    click.echo(f"  {'Platform':<22} {m.platform}")
    click.echo(f"  {'Status':<22} {m.status}")
    click.echo(f"  {'Priority':<22} {m.priority}")
    click.echo()
    click.echo("  Content")
    click.echo(f"  {'  Video':<22} {m.video_path or '(none)'}")
    click.echo(f"  {'  Thumbnail':<22} {m.thumbnail_path or '(none)'}")
    click.echo(f"  {'  Script':<22} {m.script_path or '(none)'}")
    click.echo(f"  {'  Bundle dir':<22} {m.bundle_dir or '(none)'}")
    click.echo()
    click.echo("  Social metadata")
    click.echo(f"  {'  Title':<22} {m.title or '(none)'}")
    click.echo(f"  {'  Hook':<22} {m.hook or '(none)'}")
    click.echo(f"  {'  Caption':<22} {(m.caption[:60] + '…') if len(m.caption) > 60 else m.caption or '(none)'}")
    click.echo(f"  {'  Hashtags':<22} {m.hashtags or '(none)'}")
    click.echo(f"  {'  CTA':<22} {m.cta or '(none)'}")
    if m.title_variants:
        click.echo(f"  {'  Title variants':<22} {len(m.title_variants)} variant(s)")
    click.echo()
    click.echo("  Scheduling")
    click.echo(f"  {'  Publish at':<22} {m.publish_at or '(unscheduled)'}")
    click.echo(f"  {'  Timezone':<22} {m.timezone}")
    click.echo(f"  {'  Campaign':<22} {m.campaign_name or '(none)'}")
    click.echo(f"  {'  Queue':<22} {m.queue_name}")
    click.echo(f"  {'  Target':<22} {m.publish_target or '(none)'}")
    click.echo(f"  {'  Manual review':<22} {'yes' if m.manual_review_required else 'no'}")
    click.echo()
    click.echo("  Provenance")
    click.echo(f"  {'  Profile ref':<22} {m.profile_ref or '(none)'}")
    click.echo(f"  {'  Template ref':<22} {m.template_ref or '(none)'}")
    click.echo(f"  {'  Brand':<22} {m.brand_name or '(none)'}")
    if m.notes:
        click.echo()
        click.echo(f"  Notes: {m.notes}")
    click.echo()
    click.echo(f"  Created  : {m.created_at}")
    click.echo(f"  Updated  : {m.updated_at}")
    click.echo()


# ── validate ──────────────────────────────────────────────────────────────────


@publish_manifest_cmd.command("validate")
@click.argument("manifest_file")
@click.option("--platform", "-p", default="",
              help="Override platform for validation (defaults to manifest's platform).")
def validate_manifest(manifest_file: str, platform: str) -> None:
    """Validate a manifest file against schema and platform rules."""
    from clipforge.publish_format import validate_for_platform
    from clipforge.publish_manifest import PublishManifest

    try:
        m = PublishManifest.load(manifest_file)
    except FileNotFoundError as exc:
        click.echo(f"  Error: {exc}", err=True)
        sys.exit(1)

    errors: list[str] = []
    errors.extend(m.validate())
    errors.extend(validate_for_platform(m, platform or None))

    click.echo()
    if errors:
        click.echo(f"  Manifest: {manifest_file}  [INVALID]")
        click.echo()
        for e in errors:
            click.echo(f"    ! {e}")
        click.echo()
        sys.exit(1)
    else:
        click.echo(f"  Manifest: {manifest_file}  [OK]")
        click.echo(f"  Platform : {m.platform}")
        click.echo(f"  Status   : {m.status}")
        click.echo(f"  Job      : {m.job_name}")
        click.echo()
