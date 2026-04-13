"""
`autovideo doctor` subcommand.

Checks whether required dependencies and environment variables are present.
"""

import argparse

from autovideo.utils import load_env, is_ffmpeg_available


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="autovideo doctor", description="Check environment readiness.")
    parser.parse_args(argv)
    env = load_env()
    ok = True
    if not is_ffmpeg_available():
        print("FFmpeg not found in PATH.")
        ok = False
    if not env.get("PEXELS_API_KEY") and not env.get("PIXABAY_API_KEY"):
        print("No stock media API keys found in environment.")
        ok = False
    if ok:
        print("Environment looks good.")
    else:
        print("Environment issues detected.")
