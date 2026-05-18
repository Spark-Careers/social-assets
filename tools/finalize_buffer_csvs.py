"""Finalize Spark Careers Buffer bulk-upload CSVs.

Replaces __REPLACE_<basename>__ placeholders in source CSVs with public
raw.githubusercontent.com URLs that point at PNGs already pushed to the
Spark-Careers/social-assets repo.

Usage:
    python finalize_buffer_csvs.py --week 2026-W22 \
        --input  "C:/.../spark-w22-drive-bundle/buffer" \
        --output "C:/.../spark-w22-drive-bundle/buffer"

The PNG folder is auto-derived from --week (YYYY/Wnn relative to this repo).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_OWNER = "Spark-Careers"
REPO_NAME = "social-assets"
BRANCH = "main"
RAW_URL_BASE = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/{BRANCH}"

WEEK_RE = re.compile(r"^(\d{4})-W(\d{1,2})$")


def parse_week(week: str) -> tuple[str, str]:
    """Return (year, 'Wnn') from a '2026-W22' style tag."""
    m = WEEK_RE.match(week)
    if not m:
        sys.exit(f"--week must look like '2026-W22', got: {week!r}")
    year, num = m.group(1), m.group(2).zfill(2)
    return year, f"W{num}"


def build_url_map(png_dir: Path, repo_rel: str) -> dict[str, str]:
    """Map PNG basename (no .png) -> public raw URL."""
    urls = {}
    for png in sorted(png_dir.glob("*.png")):
        basename = png.stem
        urls[basename] = f"{RAW_URL_BASE}/{repo_rel}/{png.name}"
    return urls


def finalize_csv(src: Path, dst: Path, urls: dict[str, str]) -> int:
    """Substitute placeholders in src, write to dst. Returns replacement count."""
    text = src.read_text(encoding="utf-8")
    count = 0
    for basename, url in urls.items():
        # Two placeholder forms shipped in the original bundle:
        #   __REPLACE_<basename>__   (plain marker)
        #   https://drive.google.com/uc?export=view&id=__REPLACE_<basename>__
        # We replace the entire Drive URL form first (so the host swap is clean),
        # then fall back to the plain marker form.
        drive_form = f"https://drive.google.com/uc?export=view&id=__REPLACE_{basename}__"
        plain_form = f"__REPLACE_{basename}__"

        new_text = text.replace(drive_form, url)
        if new_text != text:
            count += 1
            text = new_text
            continue

        new_text = text.replace(plain_form, url)
        if new_text != text:
            count += 1
            text = new_text

    dst.write_text(text, encoding="utf-8")
    return count


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

    total = 0
    for src in csvs:
        dst = args.output / f"{src.stem}-final.csv"
        n = finalize_csv(src, dst, urls)
        total += n
        print(f"  {src.name} -> {dst.name} ({n} placeholders replaced)")

    print(f"Done. {len(csvs)} CSV(s), {total} placeholder substitutions.")
    print(f"Upload the *-final.csv files to Buffer (one per channel).")


if __name__ == "__main__":
    main()
