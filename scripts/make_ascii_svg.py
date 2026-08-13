#!/usr/bin/env python3
"""
make_ascii_svg.py — Renders source-prepped.png as a terminal-styled ASCII
portrait with a sequential "typing" boot animation.

Math:
  * Every sRGB channel is linearized exactly (IEC 61966-2-1 EOTF):
        c_lin = c / 12.92                       for c <= 0.04045
        c_lin = ((c + 0.055) / 1.055) ** 2.4    otherwise
  * ITU-R BT.709 relative luminance is computed on the linear channels:
        Y = 0.2126 * R + 0.7152 * G + 0.0722 * B
  * Y in [0, 1] is mapped onto Paul Bourke's ASCII density ramp as
    phosphor on a warm dark terminal: shadows map to the lightest glyphs
    (space, showing the card's charcoal background) and brights map to the
    densest glyphs, so the face reads as glowing characters — a high-
    contrast portrait, not a uniform dark block.

Animation:
  * The portrait is one <text xml:space="preserve"> block, one <tspan> per
    raster row.  Each row fades in on a per-line animation-delay — a pure
    CSS @keyframes boot sequence (no SMIL, no JS), so GitHub's Camo proxy
    keeps it intact.  A block cursor blinks in after the last row.

Output:
    avi-ascii.svg  (width: 490px — same width as info-card.svg so the two
    cards are a perfectly mirror-aligned pair at equal scale)
"""

import argparse
import os
import sys
from xml.sax.saxutils import escape

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_PATH = os.path.join(ROOT, "source-prepped.png")
OUT_PATH = os.path.join(ROOT, "avi-ascii.svg")

DEFAULT_USER = "krauzX"

WIDTH = 490.0               # matches info-card.svg — identical scale in a 50/50 pair
TITLE_BAR = 38.0              # terminal chrome bar on top of the card
INSET = 4.0                    # left/right margin of the glyph block
FONT_SIZE = 5.6
CHAR_ASPECT = 0.6              # monospace advance width relative to font-size
LINE_DELAY = 0.035             # seconds between consecutive row reveals
LINE_FADE = 0.10               # per-row fade duration

# Paul Bourke's ASCII density ramp — darkest -> lightest.
RAMP = "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\\|()1{}[]?-_+~<>i!lI;:,\"^`'. "

MONO_FONT = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"


def main() -> None:
    ap = argparse.ArgumentParser(description="Render the ASCII portrait SVG.")
    ap.add_argument("--user", default=DEFAULT_USER,
                    help=f"GitHub username shown in the title bar (default: {DEFAULT_USER})")
    args = ap.parse_args()

    if not os.path.exists(SRC_PATH):
        sys.exit(f"missing {SRC_PATH} — run scripts/prep_photo.py first")

    image = Image.open(SRC_PATH).convert("RGB")
    img_w, img_h = image.size

    # Grid resolution for the {WIDTH:.0f}px-wide glyph block.
    char_w = FONT_SIZE * CHAR_ASPECT
    cols = max(8, int((WIDTH - 2 * INSET) / char_w))
    rows = max(1, int(cols * (img_h / img_w) * CHAR_ASPECT))

    # Downsample, then compute linear-luminance per sampled pixel (vectorized
    # form of the exact EOTF + BT.709 equations above).
    px = np.asarray(image.resize((cols, rows), Image.LANCZOS), dtype=np.float32) / 255.0
    lin = np.where(px <= 0.04045, px / 12.92, ((px + 0.055) / 1.055) ** 2.4)
    y = 0.2126 * lin[..., 0] + 0.7152 * lin[..., 1] + 0.0722 * lin[..., 2]

    # Phosphor mapping: black -> space (charcoal shows through), white ->
    # densest glyph (glowing ink).  Combined with the S-curve from
    # prep_photo.py this yields a bright-on-dark high-contrast portrait
    # instead of a uniform block of characters.
    idx = ((1.0 - np.clip(y, 0.0, 1.0)) * (len(RAMP) - 1)).astype(np.int64)
    glyphs = np.array(list(RAMP))[idx]
    lines = ["".join(row) for row in glyphs.tolist()]

    # ------------------------------------------------------------------ SVG
    # Card chrome: 38px title bar on top, then the glyph block with one
    # leading/trailing row of padding so ascenders and the cursor block stay
    # inside the frame in every renderer.
    height = TITLE_BAR + (rows + 2) * FONT_SIZE
    total_delay = (len(lines) - 1) * LINE_DELAY + LINE_FADE
    sweep = (rows + 1) * FONT_SIZE          # caret travel across the glyph block
    boot_time = (rows + 1) * LINE_DELAY + LINE_FADE

    tspans = []
    for i, line in enumerate(lines):
        delay = i * LINE_DELAY
        tspans.append(
            f'    <tspan x="{INSET}" dy="{FONT_SIZE}" '
            f'class="tl" style="animation-delay:{delay:.2f}s">'
            f"{escape(line)}</tspan>"
        )
    # Blinking terminal cursor, typed in after the boot sequence completes.
    tspans.append(
        f'    <tspan x="{INSET}" dy="{FONT_SIZE}" class="cursor" '
        f'style="animation-delay:{total_delay + 0.15:.2f}s">\u258d</tspan>'
    )

    titlebar = (
        '<rect class="titlebar" x="0" y="0" width="'
        + str(WIDTH) + '" height="' + str(TITLE_BAR) + '" rx="8"/>\n'
        f'  <rect x="0" y="{TITLE_BAR - 8}" width="{WIDTH}" height="8" fill="#3a3a36"/>\n'
        f'  <circle class="tdot" cx="22" cy="{TITLE_BAR / 2}" r="4" fill="#4a4844" style="animation-delay:0s"/>\n'
        f'  <circle class="tdot" cx="34" cy="{TITLE_BAR / 2}" r="4" fill="#5a5852" style="animation-delay:0.25s"/>\n'
        f'  <circle class="tdot" cx="46" cy="{TITLE_BAR / 2}" r="4" fill="#6a6860" style="animation-delay:0.5s"/>\n'
        f'  <text x="{WIDTH / 2}" y="{TITLE_BAR / 2 + 4}" text-anchor="middle" '
        f'font-size="11px" fill="#9c988e" letter-spacing="1" '
        f'font-family="{MONO_FONT}">{escape(args.user)}@dev \u2014 ~/portrait.art</text>'
    )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" viewBox="0 0 {WIDTH} {height}" role="img" aria-label="ASCII portrait of Aryan Raja Pandey">    <style>
    .frame {{ fill: #171716; stroke: #3a3a36; }}
    .titlebar {{ fill: #1e1d1b; }}
    .tdot {{ animation: dotPulse 1.6s ease-in-out infinite; }}
    @keyframes dotPulse {{ 0%, 100% {{ opacity: 0.25; }} 50% {{ opacity: 1; }} }}
    text.art {{
      font-family: {MONO_FONT};
      fill: #f2efe9;
      font-size: {FONT_SIZE}px;
    }}
    .tl {{
      opacity: 0;
      animation: typeLine {LINE_FADE}s steps(1, end) forwards;
    }}
    @keyframes typeLine {{
      from {{ opacity: 0; }}
      to   {{ opacity: 1; }}
    }}
    .cursor {{
      opacity: 0;
      animation: cursorBlink 1.1s steps(1) infinite;
    }}
    @keyframes cursorBlink {{
      0%, 55%  {{ opacity: 1; }}
      56%, 100% {{ opacity: 0; }}
    }}
    .caret {{
      fill: #f2efe9;
      opacity: 0.10;
      animation: caretSweep {boot_time:.2f}s ease-in-out forwards;
      transform-box: fill-box;
      transform-origin: 0 0;
    }}
    @keyframes caretSweep {{
      0%   {{ transform: translateY(0); opacity: 0.09; }}
      85%  {{ opacity: 0.09; }}
      100% {{ transform: translateY({sweep:.1f}px); opacity: 0; }}
    }}
  </style>
  <defs>
    <pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse">
      <rect width="4" height="1.5" fill="#000000"/>
    </pattern>
    <radialGradient id="vig" cx="50%" cy="46%" r="75%">
      <stop offset="60%" stop-color="#000000" stop-opacity="0"/>
      <stop offset="100%" stop-color="#000000" stop-opacity="0.22"/>
    </radialGradient>
  </defs>
  <rect class="frame" x="0" y="0" width="{WIDTH}" height="{height}" rx="8"/>
{titlebar}
  <g transform="translate(0 {TITLE_BAR})">
  <rect class="caret" x="{INSET}" y="0" width="{WIDTH - 2 * INSET}" height="{FONT_SIZE}" rx="1.5"/>
  <text xml:space="preserve" class="art" x="{INSET}" y="0">
{chr(10).join(tspans)}
  </text>
  </g>
  <rect x="0" y="0" width="{WIDTH}" height="{height}" fill="url(#scan)" opacity="0.07"/>
  <rect x="0" y="0" width="{WIDTH}" height="{height}" fill="url(#vig)"/>
</svg>
"""
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        fh.write(svg)
    print(f"saved {OUT_PATH} ({cols}x{rows} glyphs, {height:.1f}px tall)")


if __name__ == "__main__":
    main()
