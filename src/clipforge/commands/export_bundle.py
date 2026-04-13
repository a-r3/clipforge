"""export-bundle command — bundle video + thumbnail + social pack."""

from __future__ import annotations

import sys
from pathlib import Path

import click


@click.command("export-bundle")
@click.option("--video-file", "-v", required=True, help="Path to the video file.")
@click.option("--social-json", "-j", default=None, help="Path to social pack JSON file.")
@click.option("--thumbnail-file", "-t", default=None, help="Path to thumbnail image.")
@click.option("--output-dir", "-o", default="bundle", show_default=True, help="Output directory.")
@click.option("--platform", "-p", default="reels", help="Platform for social pack generation.")
@click.option("--brand-name", "-b", default="", help="Brand name.")
def export_bundle(
    video_file: str,
    social_json: str | None,
    thumbnail_file: str | None,
    output_dir: str,
    platform: str,
    brand_name: str,
) -> None:
    """Bundle video, thumbnail, and social pack into an output directory."""
    import os
    import shutil
    from clipforge.utils import ensure_dir, save_json

    if not os.path.exists(video_file):
        click.echo(f"Error: Video file not found: {video_file}", err=True)
        sys.exit(1)

    out_path = ensure_dir(output_dir)
    bundle_files: list[str] = []

    # Copy video
    video_dest = out_path / Path(video_file).name
    shutil.copy2(video_file, video_dest)
    bundle_files.append(str(video_dest))
    click.echo(f"Video copied to: {video_dest}")

    # Copy or generate thumbnail
    if thumbnail_file and os.path.exists(thumbnail_file):
        thumb_dest = out_path / Path(thumbnail_file).name
        shutil.copy2(thumbnail_file, thumb_dest)
        bundle_files.append(str(thumb_dest))
        click.echo(f"Thumbnail copied to: {thumb_dest}")

    # Copy or generate social pack
    if social_json and os.path.exists(social_json):
        social_dest = out_path / Path(social_json).name
        shutil.copy2(social_json, social_dest)
        bundle_files.append(str(social_dest))
        click.echo(f"Social pack copied to: {social_dest}")
    else:
        # Generate social pack from video name
        click.echo("Generating social pack...")
        from clipforge.social_pack import generate_social_pack
        # Use video file stem as script
        stem = Path(video_file).stem.replace("-", " ").replace("_", " ")
        pack = generate_social_pack(stem, platform=platform, brand_name=brand_name)

        social_dest_json = out_path / "social_pack.json"
        social_dest_txt = out_path / "social_pack.txt"
        save_json(pack, social_dest_json)

        with social_dest_txt.open("w", encoding="utf-8") as f:
            f.write(f"TITLE:\n{pack['title']}\n\n")
            f.write(f"HOOK:\n{pack['hook']}\n\n")
            f.write(f"CAPTION:\n{pack['caption']}\n\n")
            f.write(f"CTA:\n{pack['cta']}\n\n")
            f.write(f"HASHTAGS:\n{pack['hashtags']}\n")

        bundle_files.extend([str(social_dest_json), str(social_dest_txt)])
        click.echo(f"Social pack saved to: {social_dest_json}")

    # Write bundle manifest
    manifest = {"files": bundle_files, "platform": platform, "brand_name": brand_name}
    save_json(manifest, out_path / "manifest.json")

    click.echo(f"\nBundle complete: {len(bundle_files)} file(s) in {out_path}/")
