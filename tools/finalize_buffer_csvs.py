"""Finalize Spark Careers Buffer bulk-upload CSVs.

Two transforms in one pass:

1.  Substitute __REPLACE_<basename>__ placeholders in source CSVs with public
    raw.githubusercontent.com URLs that point at PNGs already pushed to the
    Spark-Careers/social-assets repo.

2.  Rewrite the source schema ('Date','Time','Text','Image URL','Tags') into
    Buffer's actual bulk-upload schema ('text','image_url','tags','posting_time').
    Date + Time get combined into a single 'YYYY-MM-DD HH:MM' posting_time
    string. (Buffer interprets it in the channel's configured timezone.)

Usage:
    python finalize_buffer_csvs.py --week 2026-W22 \
        --input  "C:/.../spark-w22-drive-bundle/buffer" \
        --output "C:/.../spark-w22-drive-bundle/buffer"
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

REPO_OWNER = "Spark-Careers"
REPO_NAME = "social-assets"
BRANCH = "main"
RAW_URL_BASE = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/{BRANCH}"

WEEK_RE = re.compile(r"^(\d{4})-W(\d{1,2})$")

BUFFER_FIELDS = ["text", "image_url", "tags", "posting_time"]


def parse_week(week: str) -> tuple[str, str]:
    m = WEEK_RE.match(week)
    if not m:
        sys.exit(f"--week must look like '2026-W22', got: {week!r}")
    return m.group(1), f"W{m.group(2).zfill(2)}"


def build_url_map(png_dir: Path, repo_rel: str) -> dict[str, str]:
    return {
        png.stem: f"{RAW_URL_BASE}/{repo_rel}/{png.name}"
        for png in sorted(png_dir.glob("*.png"))
    }


def substitute_url(raw_cell: str, urls: dict[str, str]) -> tuple[str, bool]:
    """Swap a placeholder image URL for the GitHub raw URL. Returns (new, changed)."""
    for basename, url in urls.items():
        drive_form = f"https://drive.google.com/uc?export=view&id=__REPLACE_{basename}__"
        plain_form = f"__REPLACE_{basename}__"
        if drive_form in raw_cell:
            return raw_cell.replace(drive_form, url), True
        if plain_form in raw_cell:
            return raw_cell.replace(plain_form, url), True
    return raw_cell, False


def finalize_csv(src: Path, dst: Path, urls: dict[str, str]) -> tuple[int, int]:
    """Returns (rows_written, image_replacements)."""
    rows_out = []
    replacements = 0

    with src.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            new_image, changed = substitute_url(row.get("Image URL", ""), urls)
            if changed:
                replacements += 1

            posting_time = f"{row.get('Date', '').strip()} {row.get('Time', '').strip()}".strip()

            rows_out.append({
                "text": row.get("Text", ""),
                "image_url": new_image,
                "tags": row.get("Tags", ""),
                "posting_time": posting_time,
            })

    with dst.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=BUFFER_FIELDS, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows_out)

    return len(rows_out), replacements


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--week", required=True, help="ISO week, e.g. 2026-W22")
    parser.add_argument("--input", required=True, type=Path,
                        help="Directory containing source spark-*-buffer-*.csv files")
    parser.add_argument("--output", required=True, type=Path,
                        help="Directory to write *-final.csv files into")
    parser.add_argument("--png-dir", type=Path, default=None,
                        help="Override path to PNG folder (defaults to <repo>/YYYY/Wnn)")
    args = parser.parse_args()

    year, week_label = parse_week(args.week)
    repo_root = Path(__file__).resolve().parent.parent
    png_dir = args.png_dir or (repo_root / year / week_label)
    repo_rel = f"{year}/{week_label}"

    if not png_dir.is_dir():
        sys.exit(f"PNG folder not found: {png_dir}")
    if not args.input.is_dir():
        sys.exit(f"--input folder not found: {args.input}")
    args.output.mkdir(parents=True, exist_ok=True)

    urls = build_url_map(png_dir, repo_rel)
    print(f"Found {len(urls)} PNG(s) under {png_dir}")
    if not urls:
        sys.exit("No PNGs found. Push visuals to the repo first.")

    csvs = sorted(p for p in args.input.glob("*buffer*.csv")
                  if "-final" not in p.stem)
    if not csvs:
        sys.exit(f"No source 'buffer' CSVs found in {args.input}")

    total_rows = 0
    total_replacements = 0
    for src in csvs:
        dst = args.output / f"{src.stem}-final.csv"
        rows, repl = finalize_csv(src, dst, urls)
        total_rows += rows
        total_replacements += repl
        print(f"  {src.name} -> {dst.name} ({rows} rows, {repl} image URLs replaced)")

    print(f"Done. {len(csvs)} CSV(s), {total_rows} rows, "
          f"{total_replacements} image URL substitutions.")
    print("Output schema: text,image_url,tags,posting_time (Buffer's bulk-upload format).")


if __name__ == "__main__":
    main()
