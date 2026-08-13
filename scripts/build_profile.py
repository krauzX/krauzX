#!/usr/bin/env python3
"""
build_profile.py — one-command pipeline for the profile-art ecosystem.

Runs every generator in dependency order:
    prep_photo -> make_banner -> make_ascii_svg -> make_info_card
    -> make_calligraphy -> fetch_contributions -> render_heatmap_svg

Usage:
    python scripts/build_profile.py --photo image.png   # full local build (needs rembg)
    python scripts/build_profile.py --no-photo          # reuse existing source-prepped.png
    python scripts/build_profile.py --no-fetch          # render heatmap from existing data
    python scripts/build_profile.py --user somehandle   # any GitHub profile (default: krauzX)

--skip-photo / --skip-fetch are accepted as legacy aliases.
"""

import argparse
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "scripts")
PREPPED = os.path.join(ROOT, "source-prepped.png")


def run(name: str, *extra: str) -> None:
    args = " ".join(extra)
    print(f"\n>>> python scripts/{name}" + (f" {args}" if args else ""))
    subprocess.run([sys.executable, os.path.join(SCRIPTS, name), *extra], check=True)


def main() -> None:
    ap = argparse.ArgumentParser(description="Build all profile-art SVGs.")
    ap.add_argument("--photo", metavar="PATH",
                    help="source portrait for prep_photo.py (requires rembg)")
    ap.add_argument("--no-photo", "--skip-photo", dest="skip_photo",
                    action="store_true",
                    help="reuse existing source-prepped.png")
    ap.add_argument("--no-fetch", "--skip-fetch", dest="skip_fetch",
                    action="store_true",
                    help="render heatmap from existing data/contributions.json")
    ap.add_argument("--user", default=None,
                    help="GitHub username for the cards and the contribution scrape "
                         "(default: krauzX)")
    args = ap.parse_args()

    user_args = ["--user", args.user] if args.user else []

    if not args.skip_photo:
        if not args.photo:
            if not os.path.exists(PREPPED):
                ap.error(f"{os.path.basename(PREPPED)} is missing — "
                         "pass --photo <image> to run prep_photo.py first")
        else:
            if not os.path.exists(args.photo):
                ap.error(f"photo not found: {args.photo}")
            run("prep_photo.py", args.photo)

    run("make_banner.py")
    run("make_ascii_svg.py", *user_args)
    run("make_info_card.py")
    run("make_calligraphy.py")
    if not args.skip_fetch:
        run("fetch_contributions.py", *user_args)
    run("render_heatmap_svg.py", *user_args)

    print("\nDone. Generated: banner, cards, calligraphy, heatmap SVGs")


if __name__ == "__main__":
    main()
