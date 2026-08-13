#!/usr/bin/env python3


import datetime as dt
import json
import os
import re
import sys
from xml.sax.saxutils import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASCII_PATH = os.path.join(ROOT, "avi-ascii.svg")
DATA_PATH = os.path.join(ROOT, "data", "contributions.json")
OUT_PATH = os.path.join(ROOT, "info-card.svg")

WIDTH = 490.0
TITLE_BAR = 38.0
PAD_X = 14.0
PAD_TOP = 18.0
PAD_BOTTOM = 18.0
BASE_FONT = 13.0
BASE_LINE = 20.0

MONO_FONT = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"
MONTHS = "JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split()

# --------------------------------------------------------------------- data
NAME = "Aryan Raja Pandey"
ROLE = "Software Engineer \u00b7 System Architect"
TAGLINE = ("Computer Science Undergraduate (2nd-year) at IIIT Kottayam. "
           "Specializing in high-performance backends, custom language "
           "transpilers, and local AI tooling.")
PROJECTS = [
    ("EmojiScript", "TypeScript"),
    ("Expert Ebook Gen", "Python/Ollama"),
    ("Algowiz", "React Three Fiber"),
    ("Gitright", "Go"),
    ("BluePrint", "Python"),
]
GOAL = 1000                 # yearly contribution target for the XP bar
SKILLS = [
    ("BACKEND", 96),
    ("SYSTEMS", 88),
    ("AI/ML", 74),
    ("TOOLING", 91),
]
STACK_COMPACT = "GO\u00b7RUST\u00b7TS\u00b7PY | PGSQL\u00b7DOCKER | NEXT\u00b7GODOT"

BOX = {"tl": "\u250c", "tr": "\u2510", "bl": "\u2514", "br": "\u2518",
       "h": "\u2500", "v": "\u2502"}


def wrap(text: str, width: int) -> list:
    """Greedy word wrap for monospace glyph budgets."""
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(w) > width:
            if cur:
                lines.append(cur)
                cur = ""
            lines.append(w)
            continue
        cand = f"{cur} {w}".strip()
        if len(cand) <= width:
            cur = cand
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def box_table(title: str, header: list, rows: list, widths: list,
              total: int = 56, row_roles: tuple = ("name", "prog", "out")) -> list:
    """Return box-drawn table lines; each line is a list of (text, role)."""
    assert sum(widths) + 2 * (len(widths) - 1) + 4 == total, "column widths must fill the table"
    inner = total - 2
    top = f"{BOX['tl']}{BOX['h']} {title} " + \
          BOX["h"] * (inner - len(title) - 3) + BOX["tr"]
    bottom = BOX["bl"] + BOX["h"] * inner + BOX["br"]

    def row_segments(cells: list, roles: list) -> list:
        segs = [(f"{BOX['v']} ", "muted")]
        for i, (cell, w) in enumerate(zip(cells, widths)):
            assert len(cell) <= w, f"cell wider than its column: {cell!r} ({len(cell)}) > {w}"
            segs.append((cell.ljust(w), roles[i]))
            if i < len(cells) - 1:
                segs.append(("  ", "muted"))
        segs.append((f" {BOX['v']}", "muted"))
        return segs

    lines = [[(top, "muted")]]
    lines.append(row_segments(header, ["head"] * len(header)))
    for row in rows:
        lines.append(row_segments(row, list(row_roles)))
    lines.append([(bottom, "muted")])
    return lines


def compute_stats() -> dict | None:
    """Live stats from data/contributions.json, or None when unavailable."""
    if not os.path.exists(DATA_PATH):
        return None
    try:
        with open(DATA_PATH, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return None
    grid = data.get("grid") or []
    counts = {}
    for col in grid:
        for day in col:
            if day and day.get("date"):
                counts[day["date"]] = day.get("count") or day.get("level", 0)
    if not counts:
        return None

    today = dt.date.today()
    today_val = counts.get(today.isoformat(), 0)
    week = sum(counts.get((today - dt.timedelta(days=i)).isoformat(), 0)
               for i in range(7))

    # Streak of consecutive active days, ending today (or yesterday, since
    # GitHub's graph can lag a day behind the local timezone).
    d = today if today_val > 0 else today - dt.timedelta(days=1)
    streak = 0
    while counts.get(d.isoformat(), 0) > 0:
        streak += 1
        d -= dt.timedelta(days=1)

    monthly = {}
    for date_str, value in counts.items():
        monthly[date_str[:7]] = monthly.get(date_str[:7], 0) + value
    peak = max(monthly, key=monthly.get)
    peak_text = f"{MONTHS[int(peak[5:7]) - 1]} {peak[:4]} ({monthly[peak]})"
    total = sum(counts.values())
    return {
        "total": total,
        "today": today_val,
        "week": week,
        "streak": streak,
        "peak": peak_text,
        "pct": min(100, round(100 * total / GOAL)),
    }


def build_lines(usable_chars: int, stats: dict | None = None) -> list:
    """Compose the HUD; each line is a list of (text, role)."""
    lines = [
        [("PLAYER  ", "muted"), (" " + NAME, "out")],
        [("ROLE    ", "muted"), (" " + ROLE, "out")],
    ]
    for t in wrap(TAGLINE, usable_chars - 2):
        lines.append([("  ", "dim"), (t, "dim")])

    if stats:
        filled = round(34 * stats["pct"] / 100)
        bar = "\u2593" * filled + "\u2591" * (34 - filled)
        lines.append([("XP      ", "muted"),
                      (f"{stats['total']}/{GOAL}", "out"),
                      (f"  {bar}  {stats['pct']}%", "prog")])
        lines.append([("COMBO   ", "muted"),
                      (f"  TODAY {stats['today']} \u00b7 WEEK {stats['week']} "
                       f"\u00b7 STREAK {stats['streak']} \u00b7 PEAK {stats['peak']}",
                       "dim")])
    else:
        lines.append([("XP      ", "muted"),
                      (f"0/{GOAL}", "out"),
                      (f"  {'\u2591' * 34}  0%", "prog")])
        lines.append([("COMBO   ", "muted"),
                      ("  TODAY 0 \u00b7 WEEK 0 \u00b7 STREAK 0 \u00b7 PEAK -", "dim")])

    lines.append([])
    lines += box_table(
        "ENGINE",
        ["PROJECT", "ENGINE", "STATUS"],
        [[n, e, "\u25cf"] for n, e in PROJECTS],
        [22, 20, 6],
        row_roles=("name", "dim", "dot"),
    )
    skill_rows = []
    for name, value in SKILLS:
        filled = round(24 * value / 100)
        skill_rows.append([name, "\u2593" * filled + "\u2591" * (24 - filled),
                           f"{value:>3}"])
    lines += box_table("SKILLS", ["SKILL", "PROGRESS", "VAL"],
                       skill_rows, [16, 24, 8])
    lines.append([("LOADOUT ", "muted"), (" " + STACK_COMPACT, "out")])
    lines.append([("[", "muted"), ("\u2593" * 34, "prog"),
                  ("] 100% \u00b7 READY", "muted")])
    lines.append([("$ ", "dollar"), ("\u258d", "cursor"), ("  \u25d0", "spinner")])
    return lines


def read_ascii_height() -> float:
    """Height of avi-ascii.svg — the card must match it exactly."""
    if not os.path.exists(ASCII_PATH):
        sys.exit(f"missing {ASCII_PATH} — run scripts/make_ascii_svg.py first")
    with open(ASCII_PATH, encoding="utf-8") as fh:
        head = fh.read(4096)
    m = re.search(r'<svg[^>]*\bheight="([0-9.]+)"', head)
    if not m:
        sys.exit(f"could not parse height from {ASCII_PATH}")
    return float(m.group(1))


def render(rows: list, target_h: float) -> str:
    """Build the SVG, scaling typography so content fills target_h exactly."""
    chrome = TITLE_BAR + PAD_TOP + PAD_BOTTOM
    scale = max(0.55, min(1.4, (target_h - chrome) / (len(rows) * BASE_LINE)))
    fs = BASE_FONT * scale
    lh = BASE_LINE * scale

    colors = {
        "dollar": "#9c988e",
        "cmd": "#f2efe9",
        "out": "#e8e5de",
        "dim": "#b5b2a8",
        "muted": "#8a877e",
        "head": "#9c988e",
        "name": "#ffffff",
        "prog": "#e0ddd5",
    }

    texts = []
    y = TITLE_BAR + PAD_TOP
    for i, segments in enumerate(rows):
        if not segments:
            texts.append(f'    <text x="{PAD_X}" y="{y:.1f}" xml:space="preserve" '
                         f'font-size="{fs:.2f}px"></text>')
            y += lh
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
                    f'<tspan fill="{colors[role]}">{escape(text)}</tspan>'
                )
        texts.append(
            f'    <text x="{PAD_X}" y="{y:.1f}" xml:space="preserve" '
            f'font-size="{fs:.2f}px">{"".join(tspans)}</text>'
        )
        y += lh

    body = "\n".join(texts)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{target_h}" viewBox="0 0 {WIDTH} {target_h}" role="img" aria-label="Game-style terminal HUD for Aryan Raja Pandey">
  <style>
    .frame {{ fill: #171716; stroke: #3a3a36; }}
    .titlebar {{ fill: #1e1d1b; }}
    text {{ font-family: {MONO_FONT}; }}
    .tdot {{ animation: dotPulse 1.6s ease-in-out infinite; }}
    @keyframes dotPulse {{ 0%, 100% {{ opacity: 0.25; }} 50% {{ opacity: 1; }} }}
    .cursor {{ animation: cursorBlink 1.1s steps(1) infinite; }}
    @keyframes cursorBlink {{ 0%, 55% {{ opacity: 1; }} 56%, 100% {{ opacity: 0; }} }}
    .dot {{ animation: dotBlink 1.8s steps(1) infinite; }}
    @keyframes dotBlink {{ 0%, 55% {{ opacity: 1; }} 56%, 100% {{ opacity: 0.2; }} }}
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
  <rect class="frame" x="0" y="0" width="{WIDTH}" height="{target_h}" rx="8"/>
  <rect class="titlebar" x="0" y="0" width="{WIDTH}" height="{TITLE_BAR}" rx="8"/>
  <rect x="0" y="{TITLE_BAR - 8}" width="{WIDTH}" height="8" fill="#3a3a36"/>
  <circle class="tdot" cx="22" cy="{TITLE_BAR / 2}" r="4" fill="#4a4844" style="animation-delay:0s"/>
  <circle class="tdot" cx="34" cy="{TITLE_BAR / 2}" r="4" fill="#5a5852" style="animation-delay:0.25s"/>
  <circle class="tdot" cx="46" cy="{TITLE_BAR / 2}" r="4" fill="#6a6860" style="animation-delay:0.5s"/>
  <text x="{WIDTH / 2}" y="{TITLE_BAR / 2 + 4}" text-anchor="middle" font-size="11px" fill="#9c988e" letter-spacing="1">aryan@dev \u2014 ~/profile</text>
  <text x="{WIDTH - 14}" y="{TITLE_BAR / 2 + 4}" text-anchor="end" font-size="10.5px" fill="#7d7a72">zsh</text>
{body}
  <rect x="0" y="0" width="{WIDTH}" height="{target_h}" fill="url(#scan)" opacity="0.07"/>
  <rect x="0" y="0" width="{WIDTH}" height="{target_h}" fill="url(#vig)"/>
</svg>
"""


def main() -> None:
    usable = int((WIDTH - 2 * PAD_X) / (BASE_FONT * 0.6))
    target = read_ascii_height()
    rows = build_lines(usable, compute_stats())
    svg = render(rows, target)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        fh.write(svg)
    print(f"saved {OUT_PATH} ({WIDTH:.0f}x{target:.1f}px, {len(rows)} lines)")


if __name__ == "__main__":
    main()
