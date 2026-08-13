#!/usr/bin/env python3
"""
make_preview.py — generate a self-contained preview.html for the profile art.

Inlines banner.svg + the three generated SVGs (the static preview host
cannot serve subdirectory files, so external <img> refs would 404) and lays
the page out exactly like the README:

    1. banner (full width)
    2. the 50/50 card pair (avi-ascii.svg | info-card.svg), identical width
       and height so they mirror-align at identical font scale
    3. the Devanagari calligraphy shloka (calligraphy.svg)
    4. the full-width isometric heatmap
    5. a responsive check showing the pair at mobile / tablet / desktop widths

Usage:
    python scripts/make_preview.py                 # -> ../preview.html
    python scripts/make_preview.py --out X.html    # custom destination
"""

import argparse
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUT = os.path.join(os.path.dirname(ROOT), "preview.html")

TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>krauzX — profile art preview</title>
<style>
  body {{ background:#0d0d0c; margin:0; padding:24px; font-family: system-ui, sans-serif; }}
  .wrap {{ max-width:1012px; margin:0 auto; }}
  .note {{ color:#9c988e; font: 12px ui-monospace, monospace; letter-spacing:1px;
           margin:0 0 14px; }}
  .lbl  {{ color:#7d7a72; font: 11px ui-monospace, monospace; letter-spacing:2px;
           margin:26px 0 10px; border-bottom:1px solid #2a2a26; padding-bottom:6px; }}
  table {{ border:0; border-collapse:collapse; width:100%; table-layout:fixed; }}
  td {{ vertical-align:middle; padding:0 8px; }}
  svg, img {{ width:100%; height:auto; display:block; }}
  .banner {{ margin-bottom:18px; }}
  .heat {{ margin-top:18px; }}
  .bp {{ background:#111110; border:1px solid #2a2a26; border-radius:8px;
         padding:14px; margin:0 auto; }}
</style>
</head>
<body><div class="wrap">
  <p class="note">LIVE PREVIEW — replica of the README layout. All motion is CSS @keyframes (Camo-safe).</p>

  <p class="lbl">01 · README REPLICA — BANNER</p>
  <div class="banner">__BANNER__</div>

  <p class="lbl">02 · README REPLICA — CARD PAIR (50 / 50, identical scale)</p>
  __PAIR__

  <p class="lbl">03 · README REPLICA — CALLIGRAPHY (CHANAKYA NITI SHLOKA)</p>
  <div class="heat" style="max-width:800px">__CALLIGRAPHY__</div>

  <p class="lbl">04 · README REPLICA — ISOMETRIC HEATMAP</p>
  <div class="heat">__HEAT__</div>

  <p class="lbl">04 · RESPONSIVE CHECK — MOBILE 360PX</p>
  <div class="bp" style="width:360px">__PAIR__</div>

  <p class="lbl">05 · RESPONSIVE CHECK — TABLET 768PX</p>
  <div class="bp" style="width:768px">__PAIR__</div>

  <p class="lbl">06 · RESPONSIVE CHECK — DESKTOP 1012PX</p>
  <div class="bp" style="width:1012px">__PAIR__</div>
</div></body></html>
"""


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate the profile-art preview page.")
    ap.add_argument("--out", default=DEFAULT_OUT,
                    help=f"destination html file (default: {DEFAULT_OUT})")
    args = ap.parse_args()

    def read(name: str) -> str:
        with open(os.path.join(ROOT, name), encoding="utf-8") as fh:
            return fh.read()

    banner, ascii_, info, calligraphy, heat = (
        read("banner.svg"), read("avi-ascii.svg"),
        read("info-card.svg"), read("calligraphy.svg"),
        read("contrib-heatmap.svg"),
    )

    pair = ('<table><tr>\n'
            f'      <td width="50%">{ascii_}</td>\n'
            f'      <td width="50%">{info}</td>\n'
            "    </tr></table>")

    html = (TEMPLATE
            .replace("__BANNER__", banner)
            .replace("__PAIR__", pair)
            .replace("__CALLIGRAPHY__", calligraphy)
            .replace("__HEAT__", heat))

    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(html)
    print(f"saved {args.out} ({len(html):,} bytes)")


if __name__ == "__main__":
    main()
