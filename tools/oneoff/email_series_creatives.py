# -*- coding: utf-8 -*-
"""One-off: LinkedIn creatives for the six-part Spark product email series.

NOT part of the weekly pipeline. Nothing here touches the curricula, the
cursors in content/curriculum_state.json, or the week folders under 2026/.
Run it by hand when the series needs regenerating.

    python tools/oneoff/email_series_creatives.py

Output goes to ~/Downloads/spark-email-series-creatives/ at 1080x1350, using
the same three directions as the daily tracks so the series sits inside the
established look rather than beside it.

Direction is varied across the six for rhythm: the two announcement-shaped
messages (the job board expansion, and the recruiter reveal that flips the
whole series around) get the loud teal Field treatment, and the four
instructional ones alternate cream and ink.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "generate"))

from poster_renderer import render_posts  # noqa: E402

OUT = Path.home() / "Downloads" / "spark-email-series-creatives"
URL = "spark.risepointcareers.com"
BRAND = "Spark Careers"
TOTAL = 6

# headline_a renders in ink, headline_b in the accent colour.
SERIES = [
    {
        "n": 1,
        "slug": "job-board",
        "direction": "1c",
        "series": "The Job Board",
        "headline_a": "Over 60 percent more jobs",
        "headline_b": "to explore.",
        "body": "New roles land continuously. The strongest openings are often "
                "filled within days of posting.",
    },
    {
        "n": 2,
        "slug": "multiple-resumes",
        "direction": "1a",
        "series": "Your Skill Inventory",
        "headline_a": "Most people have several resumes.",
        "headline_b": "Upload all of them.",
        "body": "Spark reads across every version and builds a complete picture "
                "of what you can actually do.",
    },
    {
        "n": 3,
        "slug": "skills-matching",
        "direction": "1b",
        "series": "Skills-Based Matching",
        "headline_a": "Your job title was never",
        "headline_b": "the full story.",
        "body": "We match on skills rather than titles, so you see roles you "
                "never thought to search for.",
    },
    {
        "n": 4,
        "slug": "review-and-rewrite",
        "direction": "1a",
        "series": "Review and Rewrite",
        "headline_a": "See exactly where you fall short.",
        "headline_b": "Then close the gap.",
        "body": "Analyse any resume against any job, find the gaps, and rewrite "
                "to speak the language of the role.",
    },
    {
        "n": 5,
        "slug": "application-tracker",
        "direction": "1b",
        "series": "The Tracker",
        "headline_a": "Every application, every stage,",
        "headline_b": "on one board.",
        "body": "Stop running your job search out of memory, a notes app, and a "
                "spreadsheet that is already out of date.",
    },
    {
        "n": 6,
        "slug": "discoverability",
        "direction": "1c",
        "series": "Discoverability",
        "headline_a": "Recruiters can already",
        "headline_b": "find you by your skills.",
        "body": "Your profile is visible to employers hiring on our corporate "
                "platform, by default.",
    },
]

FORBIDDEN = [("—", "em-dash"), ("–", "en-dash"), ("--", "double-hyphen")]
CONTRACTIONS = ["n't", "'re", "'ve", "'ll", "it's", "I'm"]


def validate() -> list[str]:
    """Same voice rules the curricula are held to."""
    issues = []
    for item in SERIES:
        tag = f"{item['n']:02d} {item['slug']}"
        for field in ("headline_a", "headline_b", "body", "series"):
            v = item[field]
            for bad, name in FORBIDDEN:
                if bad in v:
                    issues.append(f"{tag} {field}: contains {name}")
            if "!" in v:
                issues.append(f"{tag} {field}: contains exclamation point")
            for c in CONTRACTIONS:
                if c in v:
                    issues.append(f"{tag} {field}: contraction {c!r}")
        if len(item["body"].split()) > 26:
            issues.append(f"{tag} body: {len(item['body'].split())} words, may overflow")
    return issues


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scale", type=int, default=3,
                    help="1 = 1080x1350 (LinkedIn spec), 2 = 2160x2700, "
                         "3 = 3240x4050 (default, high resolution).")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    issues = validate()
    if issues:
        print("VALIDATION ISSUES:")
        for i in issues:
            print(f"  - {i}")
        return 1

    out_dir = args.out or OUT
    out_dir.mkdir(parents=True, exist_ok=True)
    suffix = "" if args.scale == 1 else f"@{args.scale}x"
    by_direction: dict[str, list[tuple[dict, Path]]] = {}

    for item in SERIES:
        payload = {
            "index": f"{item['n']:02d}",
            "series": item["series"],
            "progress": f"{item['n']:02d} / {TOTAL:02d}",
            "headline_a": item["headline_a"],
            "headline_b": item["headline_b"],
            "body": item["body"],
            "brand": BRAND,
            "url": URL,
        }
        out = out_dir / f"spark-email-{item['n']:02d}-{item['slug']}{suffix}.png"
        by_direction.setdefault(item["direction"], []).append((payload, out))

    print(f"[size] {1080 * args.scale} x {1350 * args.scale}  (scale {args.scale}x)")
    for direction, batch in by_direction.items():
        print(f"[render] {direction}: {len(batch)}")
        render_posts(batch, direction=direction, scale=args.scale)
        for _, out in batch:
            print(f"           {out.name}")

    print(f"\n[done] {len(SERIES)} creatives in {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
