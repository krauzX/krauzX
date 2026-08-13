#!/usr/bin/env python3


import argparse
import json
import math
import os
import sys
from xml.sax.saxutils import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(ROOT, "data", "contributions.json")
OUT_PATH = os.path.join(ROOT, "contrib-heatmap.svg")

DEFAULT_USER = "krauzX"

CELL = 9.0
GAP = 2.0
PITCH = CELL + GAP            # 11px per day slot
TOP = 100.0                   # headroom for title + raised cells
BOTTOM = 165.0                # monthly bar chart + legend + footer
PAD_X = 60.0
COS45 = math.cos(math.radians(45.0))

MONO_FONT = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"
MONTHS = "JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split()

ELEVATION = {0: 0, 1: 5, 2: 10, 3: 15, 4: 20}   # Z extrusion per intensity
FILL = {0: "#232220", 1: "#3a3835", 2: "#6a675f", 3: "#a5a198", 4: "#f2efe9"}
WALL = {0: "#232220", 1: "#2b2927", 2: "#45423e", 3: "#6a675f", 4: "#8f8b82"}


def project(ux: float, uy: float):
    """Map grid-relative coords onto the screen plane exactly as CSS
    `rotateX(60deg) rotateZ(-45deg)` does (screen z dropped)."""
    sx = (ux + 0.5 * uy) * COS45
    sy = (0.5 * uy - ux) * COS45
    return sx, sy


def load_data() -> dict | None:
    if not os.path.exists(DATA_PATH):
        return None
    try:
        with open(DATA_PATH, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError) as exc:
        print(f"warning: could not read {DATA_PATH}: {exc}", file=sys.stderr)
        return None
    if not data.get("grid"):
        return None
    return data


def build_heatmap(data: dict, user: str | None = None) -> str:
    grid = data["grid"]
    user = user or str(data.get("user") or DEFAULT_USER)
    ncols = len(grid)
    W = ncols * PITCH
    H = 7 * PITCH

    # Projected bounding box of the rotated grid.
    corners = [project(dx, dy) for dx, dy in
               ((W / 2, H / 2), (-W / 2, H / 2), (-W / 2, -H / 2), (W / 2, -H / 2))]
    proj_w = max(p[0] for p in corners) - min(p[0] for p in corners)
    proj_h = max(p[1] for p in corners) - min(p[1] for p in corners)

    view_w = proj_w + 2 * PAD_X
    view_h = TOP + proj_h + BOTTOM
    cx, cy = view_w / 2.0, TOP + proj_h / 2.0

    # ---- cells + walls ---------------------------------------------------
   
    rects, walls = [], []
    for col in range(ncols):
        for row in range(7):
            day = grid[col][row]
            if not day:
                continue
            level = int(day.get("level", 0))
            level = max(0, min(4, level))
            x = col * PITCH
            y = row * PITCH
            rects.append(
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{CELL}" height="{CELL}" '
                f'rx="1.5" class="intensity-{level}"/>'
            )
            if level > 0:
                walls.append(
                    f'<rect x="{x:.1f}" y="{y + CELL - 1:.1f}" width="{CELL}" '
                    f'height="{ELEVATION[level]}" fill="{WALL[level]}"/>'
                )
    cells = "\n      ".join(rects)
    wall_block = "\n      ".join(walls)

    # ---- ground plate (plain 2D shadow of the grid's footprint) ----------
    plate = " ".join(
        f"{cx + sx:.1f},{cy + sy:.1f}" for sx, sy in corners
    )

    # ---- month labels along the projected top edge ------------------------
    labels = []
    last_month = None
    for col in range(ncols):
        month = None
        for row in range(7):
            day = grid[col][row]
            if day and day.get("date"):
                month = int(day["date"][5:7])
                break
        if month is None or month == last_month:
            continue
        last_month = month
        ux = col * PITCH + CELL / 2 - W / 2
        uy = -(H / 2 + 10)                      # hover just above the top edge
        sx, sy = project(ux, uy)
        labels.append(
            f'<text x="{cx + sx:.1f}" y="{cy + sy:.1f}" text-anchor="middle" '
            f'class="month">{MONTHS[month - 1]}</text>'
        )
    month_block = "\n    ".join(labels)

    total = data.get("total") or data.get("total_level") or 0
    fetched = data.get("fetched_at", "")

    # ---- monthly bar chart (data graph, live-refreshed by the cron) -------
    # Keyed by 'YYYY-MM' so August 2025 and August 2026 stay separate bars.
    monthly = {}
    for col in grid:
        for row in range(7):
            day = col[row]
            if day and day.get("date"):
                key = day["date"][:7]
                val = day.get("count")
                if val is None:
                    val = day.get("level", 0)
                monthly[key] = monthly.get(key, 0) + val
    months_sorted = sorted(monthly)
    max_val = max(monthly.values()) if monthly else 1
    peak = max(months_sorted, key=lambda k: monthly[k]) if months_sorted else None

    n_bars = len(months_sorted)
    bar_w, gap = 12.0, 8.0
    total_bar_w = n_bars * bar_w + (n_bars - 1) * gap
    bx0 = cx - total_bar_w / 2.0
    gb = TOP + proj_h                     # bottom edge of the isometric diamond
    base_y = gb + 80.0                     # bar baselines
    chart_label_y = gb + 36.0
    bars = []
    for i, key in enumerate(months_sorted):
        v = monthly[key]
        h = max(2.0, 76.0 * v / max_val)
        x = bx0 + i * (bar_w + gap)
        bars.append(
            f'<rect class="bar" x="{x:.1f}" y="{base_y - h:.1f}" width="{bar_w}" '
            f'height="{h:.1f}" rx="2" '
            f'fill="{"#f2efe9" if v == max_val else "#8a877e"}" '
            f'style="animation-delay:{0.08 * i:.2f}s"/>'
        )
        bars.append(
            f'<text x="{x + bar_w / 2:.1f}" y="{base_y + 13:.1f}" '
            f'text-anchor="middle" class="month">{MONTHS[int(key[5:7]) - 1]}</text>'
        )
        if i == 0 or key[:4] != months_sorted[i - 1][:4]:
            bars.append(
                f'<text x="{x + bar_w / 2:.1f}" y="{base_y + 26:.1f}" '
                f'text-anchor="middle" class="month">\'{key[2:4]}</text>'
            )
    bar_block = "\n    ".join(bars)
    baseline = (f'<line x1="{bx0 - 4:.1f}" y1="{base_y:.1f}" '
                f'x2="{bx0 + total_bar_w + 4:.1f}" y2="{base_y:.1f}" '
                f'stroke="#3a3835" stroke-width="1"/>')
    peak_text = f"{MONTHS[int(peak[5:7]) - 1]} {peak[:4]} ({monthly[peak]})" if peak else "-"

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%" viewBox="0 0 {view_w:.0f} {view_h:.0f}" role="img" aria-label="Isometric GitHub contribution heatmap for {escape(user)}">
  <style>
    .frame {{ fill: #171716; stroke: #3a3a36; }}
    #heatmap-container {{ perspective: 800px; transform-style: preserve-3d; }}
    .isometric-grid {{
      transform-origin: 50% 50%;
      transform-box: fill-box;
      transform: rotateX(60deg) rotateY(0deg) rotateZ(-45deg);
      animation: elevateGrid 2s ease-out forwards;
      transform-style: preserve-3d;
    }}
    @keyframes elevateGrid {{
      from {{ transform: rotateX(60deg) rotateZ(-45deg) translateZ(-50px); opacity: 0; }}
      to   {{ transform: rotateX(60deg) rotateZ(-45deg) translateZ(0px); opacity: 1; }}
    }}
    .intensity-0 {{ fill: {FILL[0]}; transform: translateZ({ELEVATION[0]}px); }}
    .intensity-1 {{ fill: {FILL[1]}; transform: translateZ({ELEVATION[1]}px); }}
    .intensity-2 {{ fill: {FILL[2]}; transform: translateZ({ELEVATION[2]}px); }}
    .intensity-3 {{ fill: {FILL[3]}; transform: translateZ({ELEVATION[3]}px); }}
    .intensity-4 {{ fill: {FILL[4]}; transform: translateZ({ELEVATION[4]}px); }}
    .title {{ fill: #f2efe9; font-size: 17px; letter-spacing: 3px; }}
    .sub   {{ fill: #9c988e; font-size: 10px; letter-spacing: 1.5px; }}
    .month {{ fill: #7d7a72; font-size: 9px; letter-spacing: 1px; }}
    .legend-label {{ fill: #9c988e; font-size: 9px; letter-spacing: 1px; }}
    .footer {{ fill: #6a675f; font-size: 8.5px; letter-spacing: 1px; }}
    .bar {{
      transform: scaleY(0);
      transform-box: fill-box;
      transform-origin: bottom;
      animation: barRise 0.9s cubic-bezier(0.22, 0.9, 0.35, 1) forwards;
    }}
    @keyframes barRise {{
      from {{ transform: scaleY(0); }}
      to   {{ transform: scaleY(1); }}
    }}
    text {{ font-family: {MONO_FONT}; }}
  </style>

  <rect class="frame" x="0" y="0" width="{view_w:.0f}" height="{view_h:.0f}" rx="10"/>

  <text x="{cx:.1f}" y="34" text-anchor="middle" class="title">GITHUB ACTIVITY \u2014 {escape(user)}</text>
  <text x="{cx:.1f}" y="56" text-anchor="middle" class="sub">TOTAL CONTRIBUTIONS: {total} \u00b7 {ncols} WEEKS \u00b7 AUTO-REFRESH 00:00 UTC</text>

  <polygon points="{plate}" fill="#201f1d" stroke="#33312e" stroke-width="1"/>

  <g id="heatmap-container" transform="translate({cx - W / 2:.1f} {cy - H / 2:.1f})">
    <g class="isometric-grid">
      {wall_block}
      {cells}
    </g>
  </g>

    {month_block}

  <text x="{cx:.1f}" y="{chart_label_y:.1f}" text-anchor="middle" class="sub">MONTHLY ACTIVITY \u2014 {sum(monthly.values())} CONTRIBUTIONS \u00b7 PEAK {escape(peak_text)}</text>
  {baseline}
    {bar_block}

  <g>
    <text x="{cx - 118:.1f}" y="{view_h - 32:.1f}" class="legend-label" text-anchor="middle">LESS</text>
    {''.join(f'<rect x="{cx - 88 + i * 14:.1f}" y="{view_h - 38:.1f}" width="9" height="9" rx="1.5" class="intensity-{i}"/>' for i in range(5))}
    <text x="{cx + 118:.1f}" y="{view_h - 32:.1f}" class="legend-label" text-anchor="middle">MORE</text>
  </g>
  <text x="{cx:.1f}" y="{view_h - 12:.1f}" text-anchor="middle" class="footer">GENERATED {escape(fetched[:10] or 'LOCALLY')} \u00b7 {escape(user)}/profile \u00b7 MONOCHROME TERMINAL EDITION</text>
</svg>
"""


def build_placeholder() -> str:
    """Fallback card used only when no heatmap exists yet and no data is available."""
    return """<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%" viewBox="0 0 760 320" role="img" aria-label="Contribution heatmap unavailable">
  <style>
    .frame { fill: #171716; stroke: #3a3a36; }
    text { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace; }
    .big   { fill: #f2efe9; font-size: 20px; letter-spacing: 4px; }
    .small { fill: #9c988e; font-size: 11px; letter-spacing: 1.5px; }
  </style>
  <rect class="frame" x="0" y="0" width="760" height="320" rx="10"/>
  <text x="380" y="140" text-anchor="middle" class="big">NO SIGNAL</text>
  <text x="380" y="176" text-anchor="middle" class="small">CONTRIBUTION FEED UNAVAILABLE \u00b7 RETRYING AT 00:00 UTC</text>
</svg>
"""


def main() -> None:
    ap = argparse.ArgumentParser(description="Render the isometric contribution heatmap.")
    ap.add_argument("--user", default=None,
                    help=f"GitHub username for the card header (default: from "
                         f"contributions.json, else {DEFAULT_USER})")
    args = ap.parse_args()

    data = load_data()
    if data is None:
        if os.path.exists(OUT_PATH):
            print(f"no contribution data — keeping existing {OUT_PATH}")
            sys.exit(0)
        svg = build_placeholder()
        print(f"no contribution data — writing placeholder {OUT_PATH}")
    else:
        svg = build_heatmap(data, args.user)
        print(f"saved {OUT_PATH} ({data['columns']} weeks, {data['total']} contributions)")
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        fh.write(svg)


if __name__ == "__main__":
    main()
