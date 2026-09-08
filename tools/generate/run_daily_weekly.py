# -*- coding: utf-8 -*-
"""Weekly build for the daily masterclass tracks.

One post per publishing day, five days a week, the two audiences alternating:

    Mon  B2B  08:00   hire.risepointcareers.com
    Tue  B2C  12:00   spark.risepointcareers.com
    Wed  B2B  08:00
    Thu  B2C  12:00
    Fri  B2B  08:00

Each track walks its own curriculum in order and stops when it runs out. B2B
has 150 posts, so at three a week it lasts 50 weeks. B2C has 66, so at two a
week it lasts 33. Nothing is skipped and nothing repeats.

    python tools/generate/run_daily_weekly.py --dry-run
    python tools/generate/run_daily_weekly.py --iso-week 2026-W38
    python tools/generate/run_daily_weekly.py --iso-week 2026-W38 --b2c-start-seq 7

Nothing here pushes to git or uploads anywhere. It renders posters and writes
the channel CSVs in the source schema that tools/finalize_buffer_csvs.py
consumes.
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

# Which audience publishes on which day, in publishing order. Saturday and
# Sunday are dark. Changing this table is the only thing needed to change the
# cadence or the mix.
DAY_PLAN = [
    ("Mon", "b2b"),
    ("Tue", "b2c"),
    ("Wed", "b2b"),
    ("Thu", "b2c"),
    ("Fri", "b2b"),
]

# Buffer allows at most this many posts per channel per week. The current plan
# puts five on each, so this is a guard rather than a constraint that binds.
MAX_POSTS_PER_CHANNEL = 10

TRACKS = {
    "b2b": {
        "curriculum": "b2b_curriculum.json",
        "time": "08:00",
        "url": "hire.risepointcareers.com",
        "brand": "Spark Careers",
        "channels": ["linkedin", "facebook", "instagram"],
        "direction": "2b",       # minimal, ink ground
    },
    "b2c": {
        "curriculum": "b2c_curriculum.json",
        "time": "12:00",
        "url": "spark.risepointcareers.com",
        "brand": "Spark Careers",
        "channels": ["linkedin", "facebook", "instagram"],
        "direction": "2a",       # minimal, cream ground
    },
}

DAY_INDEX = {"Mon": 0, "Tue": 1, "Wed": 2, "Thu": 3, "Fri": 4, "Sat": 5, "Sun": 6}
ISO_RE = re.compile(r"^(\d{4})-W(\d{1,2})$")


# ----------------------------------------------------------------- scheduling
def parse_iso_week(label: str) -> tuple[int, int]:
    m = ISO_RE.match(label)
    if not m:
        sys.exit(f"--iso-week must look like 2026-W38, got {label!r}")
    return int(m.group(1)), int(m.group(2))


def default_iso_week(today: date | None = None) -> tuple[int, int, str]:
    """First ISO week whose Monday is at least seven days out.

    A build always targets a week that has not started, leaving a full weekend
    plus a spare week to catch a missed run.
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
    return (monday + timedelta(days=DAY_INDEX[day])).isoformat()


def slots_for(track: str) -> list[str]:
    """Publishing days assigned to a track, in order."""
    return [day for day, t in DAY_PLAN if t == track]


# ---------------------------------------------------------------------- state
def load_state() -> dict:
    """Cursor per track, as a position in the curriculum's post sequence.

    The previous model consumed a whole six-post module per calendar week and
    stored `next_series_week`. Posts are now taken individually, so a week
    cursor cannot express where a track is. An old state file is reset rather
    than guessed at, since a series week does not map onto a post number once
    the two tracks run at different rates.
    """
    if not STATE_FILE.exists():
        return {t: {"next_seq": 1} for t in TRACKS}

    raw = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    if any("next_series_week" in v for v in raw.values() if isinstance(v, dict)):
        print("  [state] found a series-week cursor from the old weekly model, "
              "resetting both tracks to post 1")
        return {t: {"next_seq": 1} for t in TRACKS}
    return raw


def save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def load_curriculum(track: str) -> dict:
    path = CONTENT / TRACKS[track]["curriculum"]
    if not path.exists():
        sys.exit(f"curriculum missing: {path}. Run extract_curriculum.py first.")
    return json.loads(path.read_text(encoding="utf-8"))


def take_next(cur: dict, next_seq: int, count: int) -> tuple[list[dict], int]:
    """Take the next `count` posts in sequence. Returns (posts, remaining_after).

    Short weeks are allowed. A track that has fewer posts left than slots
    publishes what it has and then goes quiet, rather than wrapping back to the
    start and republishing.
    """
    remaining = [p for p in cur["posts"] if p["seq"] >= next_seq]
    taken = remaining[:count]
    return taken, len(remaining) - len(taken)


def check_channel_caps(rows_by_channel: dict[str, list[dict]]) -> None:
    over = {ch: len(rows) for ch, rows in rows_by_channel.items()
            if len(rows) > MAX_POSTS_PER_CHANNEL}
    if over:
        detail = ", ".join(f"{ch} {n}" for ch, n in sorted(over.items()))
        sys.exit(f"channel cap exceeded (max {MAX_POSTS_PER_CHANNEL} per channel): "
                 f"{detail}. Adjust DAY_PLAN.")


# ------------------------------------------------------------------- captions
def build_captions(post: dict, track: str) -> dict:
    """Post copy, then the track's address on its own line.

    No call to action. The curriculum's CTA column repeats heavily on B2C
    (seven phrases across sixty-six posts) and its verbs point at exercises the
    site does not host, so the instruction was doing more harm than the link.
    The bare domain carries no UTM parameters, which keeps the caption clean at
    the cost of campaign attribution.
    """
    text = f"{post['post'].strip()}\n\n{TRACKS[track]['url']}"
    return {channel: text for channel in ("linkedin", "facebook", "instagram")}


# --------------------------------------------------------------------- render
def render_week(track: str, scheduled: list[tuple[str, dict]], out_dir: Path,
                iso_label: str) -> None:
    cfg = TRACKS[track]
    batch = []
    for day, post in scheduled:
        payload = payload_from_curriculum(post, brand=cfg["brand"], url=cfg["url"])
        out = out_dir / f"{iso_label}-{track}-{day.lower()}.png"
        batch.append((payload, out))
    render_posts(batch, direction=cfg["direction"])


# ----------------------------------------------------------------------- csvs
def write_channel_csvs(rows_by_channel: dict[str, list[dict]], out_dir: Path,
                       iso_label: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for channel, rows in rows_by_channel.items():
        rows.sort(key=lambda r: (r["Date"], r["Time"]))
        path = out_dir / f"spark-{iso_label.lower()}-buffer-{channel}.csv"
        with path.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["Date", "Time", "Text", "Image URL", "Tags"],
                               quoting=csv.QUOTE_ALL)
            w.writeheader()
            w.writerows(rows)
        print(f"  [csv] {path.name}: {len(rows)} rows")


# ----------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--iso-week", default=None,
                    help="Calendar week to publish, e.g. 2026-W38. Defaults to the "
                         "first week starting at least seven days out.")
    ap.add_argument("--b2b-start-seq", type=int, default=None,
                    help="Override which B2B post number the week starts from.")
    ap.add_argument("--b2c-start-seq", type=int, default=None,
                    help="Override which B2C post number the week starts from.")
    ap.add_argument("--tracks", default="b2b,b2c",
                    help="Comma-separated tracks to build. Default both.")
    ap.add_argument("--downloads-dir", type=Path, default=Path.home() / "Downloads")
    ap.add_argument("--dry-run", action="store_true",
                    help="Report what would be produced and exit without rendering "
                         "or advancing the cursor.")
    ap.add_argument("--no-advance", action="store_true",
                    help="Render normally but leave the cursors where they are.")
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

    print(f"=== Spark daily tracks: calendar week {iso_label} ===")
    print(f"Repo: {REPO}")

    state = load_state()
    overrides = {"b2b": args.b2b_start_seq, "b2c": args.b2c_start_seq}

    plan: dict[str, dict] = {}
    for track in tracks:
        cur = load_curriculum(track)
        st = state.setdefault(track, {"next_seq": 1})
        start = overrides[track] or st["next_seq"]
        days = slots_for(track)
        posts, left = take_next(cur, start, len(days))

        if not posts:
            print(f"  [{track}] curriculum exhausted at post {cur['total_posts']}, "
                  f"nothing left to publish")
            plan[track] = {"scheduled": [], "left": 0, "total": cur["total_posts"]}
            continue
        if len(posts) < len(days):
            noun = "post" if len(posts) == 1 else "posts"
            print(f"  [{track}] only {len(posts)} {noun} left for {len(days)} slots, "
                  f"publishing a short week")

        scheduled = list(zip(days, posts))
        plan[track] = {"scheduled": scheduled, "left": left,
                       "total": cur["total_posts"], "start": start}

        weeks_left = -(-left // len(days)) if left else 0
        print(f"  [{track}] posts {posts[0]['seq']} to {posts[-1]['seq']} "
              f"of {cur['total_posts']}   time {TRACKS[track]['time']}   "
              f"direction {TRACKS[track]['direction']}")
        print(f"          {left} posts left after this week, about {weeks_left} more weeks")
        for day, p in scheduled:
            print(f"            {day}  m{p['module_number']:02d} {p['role']:<14} "
                  f"{p['visual_headline'][:58]}")

    per_channel: dict[str, int] = {}
    for t in tracks:
        for ch in TRACKS[t]["channels"]:
            per_channel[ch] = per_channel.get(ch, 0) + len(plan[t]["scheduled"])
    total_posts = sum(len(plan[t]["scheduled"]) for t in tracks)
    print("\n  per channel: " + ", ".join(f"{ch} {n}/{MAX_POSTS_PER_CHANNEL}"
                                          for ch, n in sorted(per_channel.items())))

    if args.dry_run:
        print(f"\n[dry-run] would produce {total_posts} posts, "
              f"{sum(per_channel.values())} placements. Nothing written.")
        return 0

    if not total_posts:
        print("\n[done] both curricula are exhausted, nothing to build")
        return 0

    week_dir = REPO / str(year) / f"W{week:02d}"
    bundle = args.downloads_dir / f"spark-{iso_label.lower()}-buffer"
    source_csv_dir = bundle / "_source"
    week_dir.mkdir(parents=True, exist_ok=True)

    rows_by_channel: dict[str, list[dict]] = {"linkedin": [], "facebook": [], "instagram": []}
    review_rows = []

    for track in tracks:
        scheduled = plan[track]["scheduled"]
        if not scheduled:
            continue
        cfg = TRACKS[track]
        print(f"\n[render] {track}: {len(scheduled)} posters -> {week_dir}")
        render_week(track, scheduled, week_dir, iso_label)

        for day, post in scheduled:
            caps = build_captions(post, track)
            png = f"{iso_label}-{track}-{day.lower()}.png"
            placeholder = (f"https://drive.google.com/uc?export=view"
                           f"&id=__REPLACE_{png[:-4]}__")
            for channel in cfg["channels"]:
                rows_by_channel[channel].append({
                    "Date": date_for(year, week, day),
                    "Time": cfg["time"],
                    "Text": caps[channel],
                    "Image URL": placeholder,
                    "Tags": "",
                })
            review_rows.append({
                "track": track, "day": day, "time": cfg["time"], "seq": post["seq"],
                "role": post["role"], "headline": post["visual_headline"],
                "module": post["module_title"], "media": png,
                "channels": ", ".join(cfg["channels"]),
            })

    check_channel_caps(rows_by_channel)
    print(f"\n[csv] writing source CSVs -> {source_csv_dir}")
    write_channel_csvs(rows_by_channel, source_csv_dir, iso_label)

    manifest = week_dir / "manifest.json"
    manifest.write_text(json.dumps({
        "iso_week": iso_label,
        "day_plan": [{"day": d, "track": t} for d, t in DAY_PLAN],
        "tracks": {t: {"start_seq": plan[t].get("start"),
                       "published_seq": [p["seq"] for _, p in plan[t]["scheduled"]],
                       "posts_remaining": plan[t]["left"],
                       "total_posts": plan[t]["total"]}
                   for t in tracks},
        "posts": review_rows,
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[manifest] {manifest}")

    if not args.no_advance:
        for track in tracks:
            scheduled = plan[track]["scheduled"]
            if scheduled:
                state[track]["next_seq"] = scheduled[-1][1]["seq"] + 1
        save_state(state)
        print("[state] cursors advanced -> "
              + ", ".join(f"{t}:{state[t]['next_seq']}" for t in tracks))
    else:
        print("[state] --no-advance, cursors unchanged")

    print(f"\n[done] {total_posts} posters in {week_dir}")
    print(f"       source CSVs in {source_csv_dir}")
    print("       next: push posters, then run tools/finalize_buffer_csvs.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
