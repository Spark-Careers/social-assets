# -*- coding: utf-8 -*-
"""One-off: Sprint 3 B2C organic posts.

NOT part of the weekly pipeline. Nothing here reads or writes the curricula,
the cursors in content/curriculum_state.json, or the YYYY/WNN week folders.

Ten posts, one per weekday at 12:00, Thu 30 Oct to Wed 12 Nov 2026, on all
three B2C channels. The creatives are already designed at 1080x1350 and are
copied in as-is, so no poster is rendered.

    python tools/oneoff/sprint3_organic.py --copy      # stage images into the repo
    python tools/oneoff/sprint3_organic.py --csv       # write the Buffer CSVs

Run --copy, push, then --csv: the CSVs carry live raw.githubusercontent.com
URLs, so the images have to be on the remote before the CSVs are written.
"""

from __future__ import annotations

import argparse
import csv
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SOURCE = Path(r"C:\Users\HP\Desktop\Personal Docs\Post Shell Projects\IdleSpark"
              r"\Marketing\Ad Creatives\sprint3-statics\designed")
DEST = REPO / "2026" / "sprint3-organic"
OUT = Path.home() / "Downloads" / "spark-sprint3-organic-buffer"

RAW = ("https://raw.githubusercontent.com/Spark-Careers/social-assets/main/"
       "2026/sprint3-organic/")

CHANNELS = ["linkedin", "facebook", "instagram"]
TIME = "12:00"
URL = "spark.risepointcareers.com"

# (date, image basename, caption body). The link line is appended below, so
# the body is the whole caption apart from it.
POSTS = [
    ("2026-10-30", "Khalid_Morning_4x5_1080x1350.png",
     "Most job hunts start with the same question every morning: what is new "
     "today? Autopilot answers it before you wake up. It checks every new job "
     "against your CV and keeps the ones that fit."),
    ("2026-10-31", "Andrea_Commute_4x5_1080x1350.png",
     "A commute is a hard place to job hunt. Small screen, patchy signal, ten "
     "tabs open. Autopilot does the searching in the background, so the ride "
     "can just be a ride."),
    ("2026-11-03", "Thandi_BeforeAfter_4x5_1080x1350.png",
     "Searching is not the hard part of finding a job. Sorting is. Hundreds of "
     "listings, most of them wrong for you. Autopilot sorts them against your "
     "CV, so you only see the ones worth applying to."),
    ("2026-11-04", "Aisyah_Commute_4x5_1080x1350.png",
     "Same train, same scroll, same listings you saw yesterday. Autopilot only "
     "shows you what is new and what fits your CV."),
    ("2026-11-05", "Rahul_Morning_4x5_1080x1350.png",
     "Moving countries for work means learning a new job market from scratch. "
     "Autopilot reads it for you, checking every new role against your CV, "
     "every day."),
    ("2026-11-06", "Noura_Commute_4x5_1080x1350.png",
     "A good match is more than a job title. It is the skills on your CV "
     "lining up with the skills a role needs. That is what Autopilot checks, "
     "for every new job."),
    ("2026-11-07", "Mark_BeforeAfter_4x5_1080x1350.png",
     "Before: forty open tabs and no idea which roles fit. After: one ranked "
     "list, built from your CV."),
    ("2026-11-10", "Kagiso_Morning_4x5_1080x1350.png",
     "Wake up, make coffee, check your matches. Job hunting does not have to "
     "feel like a second job."),
    ("2026-11-11", "Wei_Jie_BeforeAfter_4x5_1080x1350.png",
     "You should not need a spreadsheet to track your job search. Autopilot "
     "keeps your best matches in one place, scored against your skills."),
    ("2026-11-12", "Grace_Commute_4x5_1080x1350.png",
     "Hospitality means long shifts and little time to search. Autopilot keeps "
     "looking while you work, so your best matches are ready when your shift "
     "ends."),
]

FORBIDDEN = [("\u2014", "em-dash"), ("\u2013", "en-dash"), ("--", "double-hyphen"),
             ("!", "exclamation point"), ("\u2026", "ellipsis")]
CONTRACTIONS = ["n't", "'re", "'ve", "'ll", "it's", "I'm", "'d "]


def caption(body: str) -> str:
    return f"{body}\n\n{URL}"


def validate() -> list[str]:
    """House rules, plus the things that quietly break a bulk upload."""
    issues = []
    seen_dates, seen_images = set(), set()
    for date, image, body in POSTS:
        tag = f"{date} {image}"
        for bad, name in FORBIDDEN:
            if bad in body:
                issues.append(f"{tag}: contains {name}")
        for c in CONTRACTIONS:
            if c in body:
                issues.append(f"{tag}: contraction {c!r}")
        if re.search(r"[\U0001F300-\U0001FAFF\u2700-\u27BF]", body):
            issues.append(f"{tag}: contains an emoji")
        if not (SOURCE / image).exists():
            issues.append(f"{tag}: image not found in {SOURCE.name}")
        if date in seen_dates:
            issues.append(f"{tag}: duplicate date")
        if image in seen_images:
            issues.append(f"{tag}: duplicate image")
        seen_dates.add(date)
        seen_images.add(image)
    return issues


def copy_images() -> None:
    DEST.mkdir(parents=True, exist_ok=True)
    for _, image, _ in POSTS:
        shutil.copy2(SOURCE / image, DEST / image)
        print(f"  {image}")
    print(f"[copy] {len(POSTS)} images -> {DEST}")


def write_csvs() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for channel in CHANNELS:
        path = OUT / f"spark-sprint3-organic-{channel}-final.csv"
        with path.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["text", "image_url", "tags", "posting_time"],
                               quoting=csv.QUOTE_ALL)
            w.writeheader()
            for date, image, body in POSTS:
                w.writerow({"text": caption(body), "image_url": RAW + image,
                            "tags": "", "posting_time": f"{date} {TIME}"})
        print(f"  [csv] {path.name}: {len(POSTS)} rows")
    print(f"[csv] -> {OUT}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--copy", action="store_true", help="stage images into the repo")
    ap.add_argument("--csv", action="store_true", help="write the Buffer CSVs")
    args = ap.parse_args()

    issues = validate()
    if issues:
        print("VALIDATION ISSUES:")
        for i in issues:
            print(f"  - {i}")
        return 1
    print(f"[validate] {len(POSTS)} posts clean")

    if args.copy:
        copy_images()
    if args.csv:
        write_csvs()
    if not (args.copy or args.csv):
        print("nothing to do, pass --copy and/or --csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
