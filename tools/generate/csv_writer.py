"""Spark Careers weekly Buffer CSV generator.

Writes 3 channel CSVs in the SOURCE format that the existing
finalize_buffer_csvs.py expects (Title-Case columns, placeholder image URLs).
The finalizer then rewrites them into Buffer's actual schema
(text/image_url/tags/posting_time) and swaps in real raw.githubusercontent.com URLs.
"""

from __future__ import annotations

import csv
from datetime import date, timedelta
from pathlib import Path

DAY_OFFSET = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4}


def _iso_week_monday(year: int, week_num: int) -> date:
    return date.fromisocalendar(year, week_num, 1)


def _date_for(year: int, week_num: int, day: str) -> str:
    return (_iso_week_monday(year, week_num) + timedelta(days=DAY_OFFSET[day])).isoformat()


def _time_for(audience: str) -> str:
    return "08:00" if audience == "b2b" else "12:00"


def _placeholder_url(week_label: str, day: str, audience: str) -> str:
    return f"https://drive.google.com/uc?export=view&id=__REPLACE_{week_label}-{day}-{audience}__"


def write_channel_csvs(captions: list[dict], year: int, week_num: int,
                        output_dir: Path) -> dict[str, Path]:
    """Write 3 CSVs (linkedin/facebook/instagram) and return a map of channel -> path."""
    week_label = f"{year}-W{week_num:02d}"
    output_dir.mkdir(parents=True, exist_ok=True)

    channels_to_rows = {"linkedin": [], "facebook": [], "instagram": []}

    for c in captions:
        date_str = _date_for(year, week_num, c["day"])
        time_str = _time_for(c["audience"])
        image_url = _placeholder_url(week_label, c["day"], c["audience"])

        for channel in c.get("channels", []):
            if channel not in channels_to_rows:
                continue
            if channel == "instagram":
                text = c.get("caption_instagram", "") or c.get("caption_facebook", "")
            elif channel == "linkedin":
                text = c.get("caption_linkedin", "")
            else:  # facebook
                text = c.get("caption_facebook", "")
            if not text:
                continue
            channels_to_rows[channel].append({
                "Date": date_str,
                "Time": time_str,
                "Text": text,
                "Image URL": image_url,
                "Tags": "",
            })

    written = {}
    for channel, rows in channels_to_rows.items():
        # Sort each channel's rows chronologically (by date, then time)
        rows.sort(key=lambda r: (r["Date"], r["Time"]))
        path = output_dir / f"spark-w{week_num:02d}-buffer-{channel}.csv"
        with path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["Date", "Time", "Text", "Image URL", "Tags"],
                                     quoting=csv.QUOTE_ALL)
            writer.writeheader()
            writer.writerows(rows)
        written[channel] = path
        print(f"[csv] {path.name}: {len(rows)} rows")

    return written


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser()
    parser.add_argument("--captions", type=Path, required=True)
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--week", type=int, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()

    captions = json.loads(args.captions.read_text(encoding="utf-8"))
    write_channel_csvs(captions, args.year, args.week, args.out_dir)
