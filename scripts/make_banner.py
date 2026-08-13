#!/usr/bin/env python3
"""
make_banner.py — generate banner.svg, the wide terminal banner that tops
the README.

Styled identically to info-card.svg (dark phosphor, same fonts, chrome and
animation tokens) so the banner, portrait card and HUD read as one cohesive
terminal suite. Carries the full profile information — name, role, tagline,
remote status, stack and projects — without the CGPA / MoE hardware details
of the old banner.

Data (NAME, ROLE, TAGLINE, PROJECTS, STACK_COMPACT) is imported from
make_info_card.py so the profile facts stay single-sourced.

Usage:
    python scripts/make_banner.py
"""

import os
from xml.sax.saxutils import escape

from make_info_card import (NAME, ROLE, TAGLINE, PROJECTS, STACK_COMPACT,
                            box_table, wrap)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_PATH = os.path.join(ROOT, "banner.svg")

WIDTH = 1012.0
TITLE_BAR = 38.0
PAD_X = 14.0
PAD_TOP = 16.0
PAD_BOTTOM = 16.0
FS = 13.0
LH = 20.0

MONO_FONT = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"

# Dark phosphor tokens — must match make_info_card.py / make_ascii_svg.py.
COLORS = {
    "cmd": "#f2efe9",
    "out": "#e8e5de",
    "dim": "#b5b2a8",
    "muted": "#8a877e",
    "head": "#9c988e",
    "name": "#ffffff",
    "prog": "#e0ddd5",
    "dollar": "#9c988e",
}


def build_lines() -> list:
    """Compose the banner lines; each line is a list of (text, role)."""
    usable = int((WIDTH - 2 * PAD_X) / (FS * 0.6))
    lines = [
        [("PLAYER  ", "muted"), (" " + NAME, "out")],
        [("ROLE    ", "muted"), (" " + ROLE, "out")],
    ]
    for t in wrap(TAGLINE, usable - 2):
        lines.append([("  ", "dim"), (t, "dim")])
    lines.append([("STATUS  ", "muted"), (" \u25cf  OPEN TO REMOTE ROLES", "dot")])
    lines.append([("STACK   ", "muted"), (" " + STACK_COMPACT, "out")])
    lines.append([])
    lines += box_table("PROJECTS",
                       ["PROJECT", "ENGINE", "STATUS"],
                       [[n, e, "\u25cf"] for n, e in PROJECTS],
                       [42, 40, 10],
                       total=100,
                       row_roles=("name", "dim", "dot"))
    lines.append([("$ ", "dollar"), ("\u258d", "cursor"), ("  \u25d0", "spinner")])
    return lines


def render(rows: list) -> str:
    height = TITLE_BAR + PAD_TOP + len(rows) * LH + PAD_BOTTOM

    texts = []
    y = TITLE_BAR + PAD_TOP
    for i, segments in enumerate(rows):
        if not segments:
            texts.append(f'    <text x="{PAD_X}" y="{y:.1f}" xml:space="preserve" '
                         f'font-size="{FS}px"></text>')
            y += LH
            continue
        tspans = []
        for text, role in segments:
            if role == "dot":
                tspans.append(
                    f'<tspan class="dot" fill="#f2efe9" '
                    f'style="animation-delay:{0.35 * (i % 7):.2f}s">'
                    f"{escape(text)}</tspan>"
                )
            elif role == "cursor":
                tspans.append(
                    f'<tspan class="cursor" fill="#f2efe9">{escape(text)}</tspan>'
                )
            elif role == "spinner":
                tspans.append(
                    f'<tspan class="spinner" fill="#c9c5bc">{escape(text)}</tspan>'
                )
            else:
                tspans.append(
                    f'<tspan fill="{COLORS[role]}">{escape(text)}</tspan>'
                )
        texts.append(
            f'    <text x="{PAD_X}" y="{y:.1f}" xml:space="preserve" '
            f'font-size="{FS}px">{"".join(tspans)}</text>'
        )
        y += LH

    body = "\n".join(texts)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" viewBox="0 0 {WIDTH} {height}" role="img" aria-label="Terminal banner for Aryan Raja Pandey">
  <style>
    .frame {{ fill: #171716; stroke: #3a3a36; }}
    .titlebar {{ fill: #1e1d1b; }}
    text {{ font-family: {MONO_FONT}; }}
    .tdot {{ animation: dotPulse 1.6s ease-in-out infinite; }}
    @keyframes dotPulse {{ 0%, 100% {{ opacity: 0.25; }} 50% {{ opacity: 1; }} }}
    .dot {{ animation: dotBlink 1.8s steps(1) infinite; }}
    @keyframes dotBlink {{ 0%, 55% {{ opacity: 1; }} 56%, 100% {{ opacity: 0.2; }} }}
    .cursor {{ animation: cursorBlink 1.1s steps(1) infinite; }}
    @keyframes cursorBlink {{ 0%, 55% {{ opacity: 1; }} 56%, 100% {{ opacity: 0; }} }}
    .spinner {{
      animation: spin 1.2s steps(4) infinite;
      transform-box: fill-box;
      transform-origin: center;
    }}
    @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
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
  <rect class="frame" x="0" y="0" width="{WIDTH}" height="{height}" rx="10"/>
  <rect class="titlebar" x="0" y="0" width="{WIDTH}" height="{TITLE_BAR}" rx="10"/>
  <rect x="0" y="{TITLE_BAR - 8}" width="{WIDTH}" height="8" fill="#3a3a36"/>
  <circle class="tdot" cx="22" cy="{TITLE_BAR / 2}" r="4" fill="#4a4844" style="animation-delay:0s"/>
  <circle class="tdot" cx="34" cy="{TITLE_BAR / 2}" r="4" fill="#5a5852" style="animation-delay:0.25s"/>
  <circle class="tdot" cx="46" cy="{TITLE_BAR / 2}" r="4" fill="#6a6860" style="animation-delay:0.5s"/>
  <text x="{WIDTH / 2}" y="{TITLE_BAR / 2 + 4}" text-anchor="middle" font-size="11px" fill="#9c988e" letter-spacing="1">aryan@dev \u2014 ~/banner.txt</text>
  <text x="{WIDTH - 14}" y="{TITLE_BAR / 2 + 4}" text-anchor="end" font-size="10.5px" fill="#7d7a72">zsh</text>
{body}
  <rect x="0" y="0" width="{WIDTH}" height="{height}" fill="url(#scan)" opacity="0.07"/>
  <rect x="0" y="0" width="{WIDTH}" height="{height}" fill="url(#vig)"/>
</svg>
"""


def main() -> None:
    rows = build_lines()
    svg = render(rows)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        fh.write(svg)
    print(f"saved {OUT_PATH} ({WIDTH:.0f}x{len(rows) * LH + TITLE_BAR + PAD_TOP + PAD_BOTTOM:.0f}px, {len(rows)} lines)")


if __name__ == "__main__":
    main()
