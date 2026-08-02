# -*- coding: utf-8 -*-
"""Extract a daily curriculum from a refined schedule DOCX into JSON.

Sources of truth:
    content/Spark_B2C_Daily_Content_Schedule_Refined.docx    11 modules, 66 posts
    content/Spark_B2B_Daily_Content_Schedule_Refined.docx    25 modules, 150 posts

Output:
    content/b2c_curriculum.json
    content/b2b_curriculum.json

Both documents share one schema: a day-role table, one or more week-sequence
tables (Week / Pillar / Module / Central lesson), one 6-column table per module
(Day / Editorial role / Topic / Visual headline / Post copy / CTA), then pillar
and claim-boundary tables.

Two audience-specific details are handled here:

* The B2B document restarts module numbering at week 16, where the curriculum
  moves from the recruitment track to the HRMS track. Module number is therefore
  not unique across the series, so the poster numeral keys off `week_in_series`.
* Visual headlines are written as two parts, e.g. "Structure is not bureaucracy.
  Unclear ownership is." The template renders part one in ink and part two in the
  accent, so the split happens here rather than at render time.

Run this whenever a source DOCX changes. It is not part of the weekly run.

    python tools/generate/extract_curriculum.py                # both audiences
    python tools/generate/extract_curriculum.py --audience b2b
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from docx import Document

REPO = Path(__file__).resolve().parents[2]
CONTENT = REPO / "content"

AUDIENCES = {
    "b2c": {
        "docx": "Spark_B2C_Daily_Content_Schedule_Refined.docx",
        "out": "b2c_curriculum.json",
        "url": "spark.risepointcareers.com",
        "label": "Job seekers",
        "expected_posts": 66,
        "post_time": "12:00",
    },
    "b2b": {
        "docx": "Spark_B2B_Daily_Content_Schedule_Refined.docx",
        "out": "b2b_curriculum.json",
        "url": "hire.risepointcareers.com",
        "label": "Employers",
        "expected_posts": 150,
        "post_time": "08:00",
    },
}

DAY_ORDER = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
FORBIDDEN = [("—", "em-dash"), ("–", "en-dash"), ("--", "double-hyphen")]
CONTRACTIONS = ["n't", "'re", "'ve", "'ll", "it's", "I'm", "'d "]


def split_headline(text: str) -> tuple[str, str]:
    """Split a visual headline into an ink part and an accent part."""
    text = " ".join(text.split())

    boundaries = list(re.finditer(r"(?<=[.?!])\s+", text))
    if boundaries:
        mid = len(text) / 2
        best = min(boundaries, key=lambda m: abs(m.start() - mid))
        a, b = text[:best.start()].strip(), text[best.end():].strip()
        if a and b:
            return a, b

    if "," in text:
        i = text.rindex(",")
        a, b = text[:i + 1].strip(), text[i + 1:].strip()
        if a and b:
            return a, b

    words = text.split()
    if len(words) > 4:
        h = (len(words) + 1) // 2
        return " ".join(words[:h]), " ".join(words[h:])

    return text, ""


def derive_body(post_copy: str, headline: str, *, max_words: int = 24) -> str:
    """Pick the supporting line that sits under the headline on the poster.

    The template's body slot wants roughly twenty words of real sentence. The
    `Topic` column is an internal label that usually restates the headline, so
    the body comes from the opening of the post copy instead. If the first
    sentence merely repeats the headline, the next one is used so the poster is
    not saying the same thing twice.
    """
    flat = " ".join(post_copy.split())
    sentences = [s.strip() for s in re.split(r"(?<=[.?!])\s+", flat) if s.strip()]
    if not sentences:
        return ""

    def norm(s: str) -> str:
        return re.sub(r"[^a-z0-9 ]", "", s.lower()).strip()

    head_n = norm(headline)
    start = 1 if norm(sentences[0]) in (head_n, head_n.rstrip(".")) else 0

    picked: list[str] = []
    for s in sentences[start:]:
        candidate = picked + [s]
        if len(" ".join(candidate).split()) > max_words and picked:
            break
        picked = candidate
        if len(" ".join(picked).split()) >= 12:
            break

    if picked:
        return " ".join(picked)
    return sentences[start] if start < len(sentences) else sentences[0]


def _cell_text(cell) -> str:
    return cell.text.strip()


def parse(docx_path: Path, cfg: dict) -> dict:
    doc = Document(str(docx_path))
    tables = doc.tables

    # Week-sequence tables. There can be more than one when the curriculum has
    # multiple tracks (B2B splits recruitment and HRMS).
    seq_rows = []
    for t in tables:
        if len(t.columns) == 4 and _cell_text(t.rows[0].cells[0]) == "Week":
            seq_rows.extend(t.rows[1:])

    modules_meta = []
    for row in seq_rows:
        c = [_cell_text(x) for x in row.cells]
        title_raw = c[2]
        m = re.match(r"Module\s+(\d+)\s*[.:]\s*(.+)", title_raw)
        modules_meta.append({
            "week": int(c[0]),
            "module_number": int(m.group(1)) if m else len(modules_meta) + 1,
            "pillar": c[1],
            "title": m.group(2).strip() if m else title_raw,
            "central_lesson": c[3],
        })

    mod_tables = [t for t in tables
                  if len(t.columns) == 6 and len(t.rows) == 7
                  and _cell_text(t.rows[0].cells[0]) == "Day"]

    if len(mod_tables) != len(modules_meta):
        sys.exit(f"{docx_path.name}: {len(mod_tables)} module tables vs "
                 f"{len(modules_meta)} week rows")

    posts = []
    for meta, tbl in zip(modules_meta, mod_tables):
        for ri, day in enumerate(DAY_ORDER, start=1):
            c = tbl.rows[ri].cells
            got = _cell_text(c[0])
            if got != day:
                sys.exit(f"{docx_path.name} week {meta['week']} row {ri}: "
                         f"expected {day}, got {got}")
            visual = " ".join(c[3].text.split())
            ha, hb = split_headline(visual)
            post_copy = _cell_text(c[4])
            posts.append({
                "seq": len(posts) + 1,
                "week_in_series": meta["week"],
                "module_number": meta["module_number"],
                "module_title": meta["title"],
                "pillar": meta["pillar"],
                "central_lesson": meta["central_lesson"],
                "day": day,
                "role": _cell_text(c[1]),
                "topic": _cell_text(c[2]),
                "visual_headline": visual,
                "headline_a": ha,
                "headline_b": hb,
                "body": derive_body(post_copy, visual),
                "post": post_copy,
                "cta": _cell_text(c[5]),
            })

    return {
        "audience": cfg["audience"],
        "audience_label": cfg["label"],
        "source": docx_path.name,
        "url": cfg["url"],
        "post_time": cfg["post_time"],
        "cadence": "Mon-Sat, one post per day, one module per week",
        "weeks": len(modules_meta),
        "total_posts": len(posts),
        "modules": modules_meta,
        "posts": posts,
    }


def validate(data: dict, cfg: dict) -> list[str]:
    issues = []
    if data["total_posts"] != cfg["expected_posts"]:
        issues.append(f"expected {cfg['expected_posts']} posts, got {data['total_posts']}")

    weeks = [m["week"] for m in data["modules"]]
    if weeks != sorted(weeks) or len(set(weeks)) != len(weeks):
        issues.append("week numbers are not unique and ascending")

    for p in data["posts"]:
        tag = f"wk{p['week_in_series']} {p['day']}"
        for field in ("visual_headline", "post", "topic", "body"):
            v = p[field]
            for bad, name in FORBIDDEN:
                if bad in v:
                    issues.append(f"{tag} {field}: contains {name}")
            if "!" in v:
                issues.append(f"{tag} {field}: contains exclamation point")
        for c in CONTRACTIONS:
            if c in p["post"]:
                issues.append(f"{tag} post: contraction {c!r}")
        # Four words or fewer renders as a single ink part; templates treat
        # headline_b as optional. Anything longer losing its accent is a defect.
        if not p["headline_b"] and len(p["visual_headline"].split()) > 4:
            issues.append(f"{tag}: headline did not split into two parts")
        if len(p["visual_headline"]) > 120:
            issues.append(f"{tag}: visual headline {len(p['visual_headline'])} chars, may overflow")
        if not p["body"]:
            issues.append(f"{tag}: empty body")
    return issues


def run(audience: str) -> int:
    cfg = dict(AUDIENCES[audience], audience=audience)
    src = CONTENT / cfg["docx"]
    if not src.exists():
        sys.exit(f"source not found: {src}")

    data = parse(src, cfg)
    issues = validate(data, cfg)

    out = CONTENT / cfg["out"]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"{audience.upper()}  ->  {out.name}")
    print(f"  weeks: {data['weeks']}   posts: {data['total_posts']}   "
          f"url: {data['url']}   time: {data['post_time']}")
    if issues:
        print(f"  VALIDATION ISSUES ({len(issues)}):")
        for i in issues[:25]:
            print(f"    - {i}")
        if len(issues) > 25:
            print(f"    ... and {len(issues) - 25} more")
        return 1
    print("  validation: clean")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--audience", choices=sorted(AUDIENCES) + ["all"], default="all")
    args = ap.parse_args()

    targets = sorted(AUDIENCES) if args.audience == "all" else [args.audience]
    rc = 0
    for a in targets:
        rc |= run(a)
        print()
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
