

import argparse
import datetime as dt
import json
import os
import re
import sys

import requests
from bs4 import BeautifulSoup

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_PATH = os.path.join(ROOT, "data", "contributions.json")

DEFAULT_USER = "krauzX"


HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/126.0 Safari/537.36",
}


def fetch_html(user: str) -> str:
    """Partial endpoint first, profile page as fallback. Exits 1 on total failure.

    Since 2025 GitHub stopped embedding the calendar in the profile HTML and
    lazy-loads it from the /users/{user}/contributions partial instead; that
    endpoint returns the same <table class="ContributionCalendar-grid">.
    """
    partial_url = f"https://github.com/users/{user}/contributions"
    profile_url = f"https://github.com/{user}"
    for url, label in ((partial_url, "partial"), (profile_url, "profile")):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=30)
            resp.raise_for_status()
            print(f"fetched {label} page: {url} ({len(resp.text)} bytes)", file=sys.stderr)
            return resp.text
        except requests.RequestException as exc:
            print(f"{label} fetch failed: {exc}", file=sys.stderr)
    sys.exit("could not fetch contribution data from GitHub")


def parse_calendar(html: str, user: str = DEFAULT_USER) -> dict:
    soup = BeautifulSoup(html, "html.parser")

    table = soup.select_one("table.ContributionCalendar-grid")
    if table is None:
        raise ValueError("contribution calendar table not found in page")

    cells = table.select("[data-date][data-level]")
    if not cells:
        raise ValueError("no day cells ([data-date][data-level]) found in calendar")

    # Map <tool-tip for="cell-id"> -> contribution count, when present.
    counts: dict = {}
    for tip in soup.select("tool-tip"):
        m = re.search(r"(\d+)\s+contributions?", tip.get_text())
        if tip.get("for") and m:
            counts[tip["for"]] = int(m.group(1))

    days = []
    for cell in cells:
        date_str = cell.get("data-date")
        try:
            date = dt.date.fromisoformat(date_str)
        except (TypeError, ValueError):
            continue
        level = int(cell.get("data-level", 0))
        ix = cell.get("data-ix")
        count = counts.get(cell.get("id"), None) if cell.get("id") else None
        days.append({
            "date": date_str,
            "level": level,
            "count": count,
            "col": int(ix) if ix is not None else None,
            "dow": (date.weekday() + 1) % 7,  # 0 = Sunday (GitHub week start)
        })

    if not days:
        raise ValueError("calendar contained no parseable dates")

    # --- Grid coordinates ------------------------------------------------
    # Exact week columns come from data-ix when the DOM provides them;
    # otherwise derive them from the ISO dates (robust fallback).
    if all(d["col"] is not None for d in days):
        ncols = max(d["col"] for d in days) + 1
    else:
        first = min(dt.date.fromisoformat(d["date"]) for d in days)
        first_sunday = first - dt.timedelta(days=(first.weekday() + 1) % 7)
        for d in days:
            d["col"] = (dt.date.fromisoformat(d["date"]) - first_sunday).days // 7
        ncols = max(d["col"] for d in days) + 1

    grid = [[None for _ in range(7)] for _ in range(ncols)]
    total_level = 0
    for d in days:
        grid[d["col"]][d["dow"]] = {"date": d["date"], "level": d["level"], "count": d["count"]}
        total_level += d["level"]

    total = sum(
        (d["count"] if d["count"] is not None else d["level"])
        for d in days
    )

    return {
        "user": user,
        "source": f"https://github.com/{user}",
        "fetched_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "columns": ncols,
        "rows": 7,
        "total": total,
        "total_level": total_level,
        "max_level": max(d["level"] for d in days),
        "grid": grid,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Fetch a GitHub contribution calendar.")
    ap.add_argument("--user", default=DEFAULT_USER,
                    help=f"GitHub username to scrape (default: {DEFAULT_USER})")
    args = ap.parse_args()

    html = fetch_html(args.user)
    try:
        data = parse_calendar(html, args.user)
    except (ValueError, TypeError) as exc:
        sys.exit(f"failed to parse contribution calendar: {exc}")

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1)
    print(f"saved {OUT_PATH} ({data['columns']} weeks, {data['total']} contributions)")


if __name__ == "__main__":
    main()
