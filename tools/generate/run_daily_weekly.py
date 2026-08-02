# -*- coding: utf-8 -*-
"""Weekly build for the daily masterclass tracks.

Replaces the old theme-and-research weekly model with a curriculum model:
two sequential tracks, each publishing one post per day, Monday through
Saturday, at different times of day.

    B2B   08:00 America/Edmonton   hire.risepointcareers.com    25 weeks, 150 posts
    B2C   12:00 America/Edmonton   spark.risepointcareers.com   11 weeks,  66 posts

One run produces one calendar week: six B2B posts and six B2C posts, twelve
posts and thirty placements. Each track advances through its own curriculum
independently, so their series weeks do not have to line up.

    python tools/generate/run_daily_weekly.py --dry-run
    python tools/generate/run_daily_weekly.py --iso-week 2026-W34
    python tools/generate/run_daily_weekly.py --iso-week 2026-W34 --b2c-series-week 3

Nothing here pushes to git or uploads anywhere. It renders posters, writes a
review DOCX, and writes the three channel CSVs in the source schema that
tools/finalize_buffer_csvs.py consumes.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))

from poster_renderer import payload_from_curriculum, render_posts  # noqa: E402

CONTENT = REPO / "content"
STATE_FILE = CONTENT / "curriculum_state.json"

DAY_ORDER = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

# Buffer allows at most this many posts per channel per week.
MAX_POSTS_PER_CHANNEL = 10

TRACKS = {
    "b2b": {
        "curriculum": "b2b_curriculum.json",
        "time": "08:00",
        "url": "hire.risepointcareers.com",
        "brand": "Spark Careers",
        "footer_note": "For employers",
        "channels": ["linkedin", "facebook"],
        # Ink ground. Reads as the declarative, operator-facing track.
        "direction": "1b",
        # The loud poster opens each track's week. Applied to the first day the
        # track actually publishes, which is not always Monday once slots are
        # skipped.
        "opener_direction": "1c",
        # Skipped to hold each channel at MAX_POSTS_PER_CHANNEL. The lesson in a
        # skipped slot is dropped for good, it does not carry into a later week,
        # so every module publishes five of its six posts and B2B never runs
        # The Frame.
        "skip_days": ["Mon"],
    },
    "b2c": {
        "curriculum": "b2c_curriculum.json",
        "time": "12:00",
        "url": "spark.risepointcareers.com",
        "brand": "Spark Careers",
        "footer_note": "For job seekers",
        "channels": ["linkedin", "facebook", "instagram"],
        # Cream editorial. The lighter, feed-friendly default.
        "direction": "1a",
        "opener_direction": "1c",
        # B2C keeps Monday (The Frame) and drops Tuesday (The Mechanism).
        "skip_days": ["Tue"],
    },
}

ISO_RE = re.compile(r"^(\d{4})-W(\d{1,2})$")


# ----------------------------------------------------------------- scheduling
def parse_iso_week(label: str) -> tuple[int, int]:
    m = ISO_RE.match(label)
    if not m:
        sys.exit(f"--iso-week must look like 2026-W34, got {label!r}")
    return int(m.group(1)), int(m.group(2))


def default_iso_week(today: date | None = None) -> tuple[int, int, str]:
    """First ISO week whose Monday is at least seven days out.

    Matches the lead-time rule the previous pipeline settled on: a Friday build
    targets the Monday after next, leaving a full weekend plus a spare week to
    catch a missed run.
    """
    today = today or date.today()
    days_ahead = (7 - today.weekday()) % 7 or 7
    monday = today + timedelta(days=days_ahead)
    if (monday - today).days < 7:
        monday += timedelta(days=7)
    y, w, _ = monday.isocalendar()
    return y, w, f"{y}-W{w:02d}"


def date_for(year: int, week: int, day: str) -> str:
    monday = date.fromisocalendar(year, week, 1)
    return (monday + timedelta(days=DAY_ORDER.index(day))).isoformat()


# ---------------------------------------------------------------------- state
def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {t: {"next_series_week": 1, "cycle": 1} for t in TRACKS}


def save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def load_curriculum(track: str) -> dict:
    path = CONTENT / TRACKS[track]["curriculum"]
    if not path.exists():
        sys.exit(f"curriculum missing: {path}. Run extract_curriculum.py first.")
    return json.loads(path.read_text(encoding="utf-8"))


def take_series_week(cur: dict, series_week: int) -> list[dict]:
    posts = [p for p in cur["posts"] if p["week_in_series"] == series_week]
    if len(posts) != 6:
        sys.exit(f"series week {series_week} has {len(posts)} posts, expected 6")
    return sorted(posts, key=lambda p: DAY_ORDER.index(p["day"]))


def split_published(track: str, posts: list[dict]) -> tuple[list[dict], list[dict]]:
    """Partition a series week into what publishes and what is dropped."""
    skip = set(TRACKS[track].get("skip_days", []))
    published = [p for p in posts if p["day"] not in skip]
    dropped = [p for p in posts if p["day"] in skip]
    return published, dropped


def check_channel_caps(rows_by_channel: dict[str, list[dict]]) -> None:
    """Refuse to emit a week that would exceed the per-channel cap."""
    over = {ch: len(rows) for ch, rows in rows_by_channel.items()
            if len(rows) > MAX_POSTS_PER_CHANNEL}
    if over:
        detail = ", ".join(f"{ch} {n}" for ch, n in sorted(over.items()))
        sys.exit(f"channel cap exceeded (max {MAX_POSTS_PER_CHANNEL} per channel): {detail}. "
                 f"Adjust skip_days in TRACKS.")


# ------------------------------------------------------------------- captions
def tracked_url(base: str, track: str, series_week: int, day: str) -> str:
    campaign = f"{track}-s{series_week:02d}-{day.lower()}"
    return (f"https://{base}/?utm_source=social&utm_medium=post"
            f"&utm_campaign={campaign}")


def build_captions(post: dict, track: str, series_week: int) -> dict:
    cfg = TRACKS[track]
    url = tracked_url(cfg["url"], track, series_week, post["day"])
    body = post["post"].strip()
    cta = post["cta"].strip()

    long_form = f"{body}\n\n{cta}: {url}"
    short_form = f"{body}\n\n{cta}: {url}"
    ig = f"{body}\n\n{cta}.\n\nLink in bio: https://{cfg['url']}/"
    return {"linkedin": long_form, "facebook": short_form, "instagram": ig}


# --------------------------------------------------------------------- render
def render_week(track: str, posts: list[dict], series_week: int,
                out_dir: Path, iso_label: str) -> list[Path]:
    cfg = TRACKS[track]
    by_direction: dict[str, list[tuple[dict, Path]]] = {}
    written: list[Path] = []

    # The loud poster opens the track's week, which is its first published day
    # rather than Monday once slots are skipped.
    opener_day = posts[0]["day"] if posts else None

    for post in posts:
        direction = cfg["opener_direction"] if post["day"] == opener_day else cfg["direction"]
        payload = payload_from_curriculum(post, series_len=6,
                                          brand=cfg["brand"], url=cfg["url"])
        # Poster numeral keys off the series week, which stays unique across a
        # curriculum even when module numbers restart on a track change.
        payload["index"] = f"{series_week:02d}"
        out = out_dir / f"{iso_label}-{track}-{post['day'].lower()}.png"
        by_direction.setdefault(direction, []).append((payload, out))
        written.append(out)

    for direction, batch in by_direction.items():
        render_posts(batch, direction=direction)
    return written


# ----------------------------------------------------------------------- csvs
def write_channel_csvs(rows_by_channel: dict[str, list[dict]], out_dir: Path,
                       iso_label: str) -> dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written = {}
    for channel, rows in rows_by_channel.items():
        rows.sort(key=lambda r: (r["Date"], r["Time"]))
        path = out_dir / f"spark-{iso_label.lower()}-buffer-{channel}.csv"
        with path.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["Date", "Time", "Text", "Image URL", "Tags"],
                               quoting=csv.QUOTE_ALL)
            w.writeheader()
            w.writerows(rows)
        written[channel] = path
        print(f"  [csv] {path.name}: {len(rows)} rows")
    return written


# ----------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--iso-week", default=None,
                    help="Calendar week to publish, e.g. 2026-W34. Defaults to the "
                         "first week starting at least seven days out.")
    ap.add_argument("--b2b-series-week", type=int, default=None,
                    help="Override which B2B curriculum week to consume.")
    ap.add_argument("--b2c-series-week", type=int, default=None,
                    help="Override which B2C curriculum week to consume.")
    ap.add_argument("--tracks", default="b2b,b2c",
                    help="Comma-separated tracks to build. Default both.")
    ap.add_argument("--downloads-dir", type=Path, default=Path.home() / "Downloads")
    ap.add_argument("--dry-run", action="store_true",
                    help="Report what would be produced and exit without rendering "
                         "or advancing the cursor.")
    ap.add_argument("--no-advance", action="store_true",
                    help="Render normally but leave the cursor where it is.")
    args = ap.parse_args()

    tracks = [t.strip() for t in args.tracks.split(",") if t.strip()]
    for t in tracks:
        if t not in TRACKS:
            sys.exit(f"unknown track {t!r}")

    if args.iso_week:
        year, week = parse_iso_week(args.iso_week)
        iso_label = f"{year}-W{week:02d}"
    else:
        year, week, iso_label = default_iso_week()

    state = load_state()
    overrides = {"b2b": args.b2b_series_week, "b2c": args.b2c_series_week}

    print(f"=== Spark daily tracks: calendar week {iso_label} ===")
    print(f"Repo: {REPO}")

    plan = {}
    for track in tracks:
        cur = load_curriculum(track)
        total_weeks = cur["weeks"]
        st = state.setdefault(track, {"next_series_week": 1, "cycle": 1})
        series_week = overrides[track] or st["next_series_week"]

        if series_week > total_weeks:
            # Curriculum exhausted. Wrap to the start and count the cycle so the
            # repeat is visible rather than silent. B2C runs out at week 11 while
            # B2B runs to 25, so this will fire on B2C first.
            print(f"  [{track}] curriculum exhausted at week {total_weeks}, "
                  f"wrapping to week 1 (cycle {st['cycle'] + 1})")
            series_week = 1
            st["cycle"] += 1

        all_posts = take_series_week(cur, series_week)
        posts, dropped = split_published(track, all_posts)
        plan[track] = {"cur": cur, "series_week": series_week, "posts": posts,
                       "dropped": dropped, "total_weeks": total_weeks,
                       "cycle": st["cycle"]}

        module = all_posts[0]
        print(f"  [{track}] series week {series_week}/{total_weeks} "
              f"(cycle {st['cycle']})  ·  {module['module_title']}")
        print(f"          pillar: {module['pillar']}   time: {TRACKS[track]['time']}   "
              f"channels: {', '.join(TRACKS[track]['channels'])}")
        for p in posts:
            print(f"            {p['day']}  {p['role']:<14} {p['visual_headline'][:62]}")
        for p in dropped:
            print(f"            {p['day']}  {p['role']:<14} "
                  f"[skipped, not published] {p['visual_headline'][:40]}")

    total_posts = sum(len(plan[t]["posts"]) for t in tracks)
    total_dropped = sum(len(plan[t]["dropped"]) for t in tracks)
    per_channel: dict[str, int] = {}
    for t in tracks:
        for ch in TRACKS[t]["channels"]:
            per_channel[ch] = per_channel.get(ch, 0) + len(plan[t]["posts"])
    cap_line = ", ".join(f"{ch} {n}/{MAX_POSTS_PER_CHANNEL}"
                         for ch, n in sorted(per_channel.items()))
    print(f"\n  per channel: {cap_line}")

    if args.dry_run:
        print(f"\n[dry-run] would produce {total_posts} posts "
              f"({total_dropped} skipped), {sum(per_channel.values())} placements. "
              f"Nothing written.")
        return 0

    week_dir = REPO / str(year) / f"W{week:02d}"
    bundle = args.downloads_dir / f"spark-{iso_label.lower()}-buffer"
    source_csv_dir = bundle / "_source"
    week_dir.mkdir(parents=True, exist_ok=True)

    rows_by_channel: dict[str, list[dict]] = {"linkedin": [], "facebook": [], "instagram": []}
    review_rows = []

    for track in tracks:
        p = plan[track]
        cfg = TRACKS[track]
        print(f"\n[render] {track}: {len(p['posts'])} posters -> {week_dir}")
        render_week(track, p["posts"], p["series_week"], week_dir, iso_label)

        for post in p["posts"]:
            caps = build_captions(post, track, p["series_week"])
            png = f"{iso_label}-{track}-{post['day'].lower()}.png"
            placeholder = (f"https://drive.google.com/uc?export=view"
                           f"&id=__REPLACE_{png[:-4]}__")
            for channel in cfg["channels"]:
                rows_by_channel[channel].append({
                    "Date": date_for(year, week, post["day"]),
                    "Time": cfg["time"],
                    "Text": caps[channel],
                    "Image URL": placeholder,
                    "Tags": "",
                })
            review_rows.append({
                "track": track, "day": post["day"], "time": cfg["time"],
                "role": post["role"], "headline": post["visual_headline"],
                "module": post["module_title"], "cta": post["cta"],
                "media": png, "channels": ", ".join(cfg["channels"]),
            })

    check_channel_caps(rows_by_channel)
    print(f"\n[csv] writing source CSVs -> {source_csv_dir}")
    write_channel_csvs(rows_by_channel, source_csv_dir, iso_label)

    manifest = week_dir / "manifest.json"
    manifest.write_text(json.dumps({
        "iso_week": iso_label,
        "max_posts_per_channel": MAX_POSTS_PER_CHANNEL,
        "tracks": {t: {"series_week": plan[t]["series_week"],
                       "cycle": plan[t]["cycle"],
                       "module": plan[t]["posts"][0]["module_title"],
                       "published_days": [p["day"] for p in plan[t]["posts"]],
                       "skipped": [{"day": p["day"], "role": p["role"],
                                    "headline": p["visual_headline"]}
                                   for p in plan[t]["dropped"]]}
                   for t in tracks},
        "posts": review_rows,
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[manifest] {manifest}")

    if not args.no_advance:
        for track in tracks:
            state[track]["next_series_week"] = plan[track]["series_week"] + 1
        save_state(state)
        print(f"[state] cursors advanced -> "
              + ", ".join(f"{t}:{state[t]['next_series_week']}" for t in tracks))
    else:
        print("[state] --no-advance, cursors unchanged")

    print(f"\n[done] {total_posts} posters in {week_dir} ({total_dropped} slots skipped)")
    print(f"       source CSVs in {source_csv_dir}")
    print("       next: push posters, then run tools/finalize_buffer_csvs.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
