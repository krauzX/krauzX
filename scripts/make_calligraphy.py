#!/usr/bin/env python3
"""
make_calligraphy.py — generate calligraphy.svg, a Devanagari calligraphy
card for the profile.

Renders a Chanakya Niti shloka using system Devanagari fonts (no external
webfonts, so GitHub/Camo renders it) on the same dark-phosphor terminal
chrome as the rest of the suite. The Devanagari stays a quiet accent while
the English transliteration and meaning carry the visual weight — a
professional, readable centerpiece. The verse is inked in with a gentle
sequential fade — pure CSS @keyframes.

    उद्यमेन हि सिध्यन्ति कार्याणि न मनोरथैः
    BY EFFORT, NOT BY WISHES, ARE DEEDS ACCOMPLISHED.

Usage:
    python scripts/make_calligraphy.py
"""

import os
from xml.sax.saxutils import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_PATH = os.path.join(ROOT, "calligraphy.svg")

WIDTH = 1012.0
H = 360.0
TITLE_BAR = 38.0
C = WIDTH / 2

MONO_FONT = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"
DEVA_FONT = ("'Noto Sans Devanagari', 'Nirmala UI', 'Devanagari Sangam MN', "
             "system-ui, sans-serif")

SHLOKA_L1 = "उद्यमेन हि सिध्यन्ति"
SHLOKA_L2 = "कार्याणि न मनोरथैः"
ROMAN = "UDYAMENA HI SIDDHYANTI KARYĀṆI NA MANORATHAIH"
MEANING = "BY EFFORT, NOT BY WISHES, ARE DEEDS ACCOMPLISHED"
ATTR = "— चाणक्य नीति · CHANAKYA NITI"


def build() -> str:
    deva_style = (f'font-family:{DEVA_FONT}; fill:#f2efe9; font-size:34px; '
                  f'letter-spacing:1px; text-anchor:middle;')
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%" viewBox="0 0 {WIDTH:.0f} {H:.0f}" role="img" aria-label="उद्यमेन हि सिध्यन्ति कार्याणि न मनोरथैः">
  <style>
    .frame {{ fill: #171716; stroke: #3a3a36; }}
    .titlebar {{ fill: #1e1d1b; }}
    text {{ font-family: {MONO_FONT}; }}
    .deva {{ {deva_style} }}
    .roman {{ fill: #e8e5de; font-size: 19px; letter-spacing: 1px; text-anchor: middle; }}
    .meaning {{ fill: #b5b2a8; font-size: 14.5px; letter-spacing: 2px; text-anchor: middle; }}
    .attr {{ fill: #9c988e; font-size: 12.5px; letter-spacing: 1.5px; text-anchor: middle; }}
    .rule {{ stroke: #3a3a36; stroke-width: 1.5; }}
    .deco {{ fill: #6a675f; }}
    .seal {{ fill: none; stroke: #6a675f; stroke-width: 1.5; }}
    .tdot {{ animation: dotPulse 1.6s ease-in-out infinite; }}
    @keyframes dotPulse {{ 0%, 100% {{ opacity: 0.25; }} 50% {{ opacity: 1; }} }}
    .tl {{ opacity: 0; animation: inkIn 1.1s ease-out forwards; }}
    @keyframes inkIn {{
      from {{ opacity: 0; transform: translateY(6px); }}
      to   {{ opacity: 1; transform: translateY(0); }}
    }}
    .cursor {{ opacity: 0; animation: cursorBlink 1.1s steps(1) infinite; }}
    @keyframes cursorBlink {{ 0%, 55% {{ opacity: 1; }} 56%, 100% {{ opacity: 0; }} }}
  </style>
  <defs>
    <radialGradient id="vig" cx="50%" cy="46%" r="75%">
      <stop offset="60%" stop-color="#000000" stop-opacity="0"/>
      <stop offset="100%" stop-color="#000000" stop-opacity="0.22"/>
    </radialGradient>
  </defs>
  <rect class="frame" x="0" y="0" width="{WIDTH:.0f}" height="{H:.0f}" rx="10"/>
  <rect class="titlebar" x="0" y="0" width="{WIDTH:.0f}" height="{TITLE_BAR}" rx="10"/>
  <rect x="0" y="{TITLE_BAR - 8}" width="{WIDTH:.0f}" height="8" fill="#3a3a36"/>
  <circle class="tdot" cx="22" cy="{TITLE_BAR / 2}" r="4" fill="#4a4844" style="animation-delay:0s"/>
  <circle class="tdot" cx="34" cy="{TITLE_BAR / 2}" r="4" fill="#5a5852" style="animation-delay:0.25s"/>
  <circle class="tdot" cx="46" cy="{TITLE_BAR / 2}" r="4" fill="#6a6860" style="animation-delay:0.5s"/>
  <text x="{C}" y="{TITLE_BAR / 2 + 4}" text-anchor="middle" font-size="11px" fill="#9c988e" letter-spacing="1">aryan@dev — ~/shloka.txt</text>
  <text x="{WIDTH - 14}" y="{TITLE_BAR / 2 + 4}" text-anchor="end" font-size="10.5px" fill="#7d7a72">zsh</text>

  <line class="rule" x1="250" y1="122" x2="{C - 20:.0f}" y2="122"/>
  <text class="deco" x="{C}" y="128" text-anchor="middle" font-size="14px">◆</text>
  <line class="rule" x1="{C + 20:.0f}" y1="122" x2="762" y2="122"/>

  <text class="deva tl" x="{C}" y="166" style="animation-delay:0.25s">{SHLOKA_L1}</text>
  <text class="deva tl" x="{C}" y="202" style="animation-delay:0.5s">{SHLOKA_L2}</text>

  <line class="rule" x1="250" y1="226" x2="{C - 20:.0f}" y2="226"/>
  <text class="deco" x="{C}" y="232" text-anchor="middle" font-size="12px">◆</text>
  <line class="rule" x1="{C + 20:.0f}" y1="226" x2="762" y2="226"/>

  <text class="roman tl" x="{C}" y="266" style="animation-delay:0.8s">{escape(ROMAN)}</text>
  <text class="meaning tl" x="{C}" y="294" style="animation-delay:1.05s">{escape(MEANING)}</text>
  <text class="attr tl" x="{C}" y="322" style="animation-delay:1.3s">{ATTR}<tspan class="cursor"> ▍</tspan></text>

  <g transform="translate(938 118)">
    <rect class="seal" x="-19" y="-19" width="38" height="38" rx="4" transform="rotate(45)"/>
    <text x="0" y="7" text-anchor="middle" font-size="15px" fill="#b5b2a8" font-family="{DEVA_FONT}">क्र</text>
  </g>

  <rect x="0" y="0" width="{WIDTH:.0f}" height="{H:.0f}" fill="url(#vig)"/>
</svg>
"""


def main() -> None:
    svg = build()
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        fh.write(svg)
    print(f"saved {OUT_PATH} ({WIDTH:.0f}x{H:.0f}px)")


if __name__ == "__main__":
    main()
