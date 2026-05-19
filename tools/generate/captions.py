"""Spark Careers weekly caption generator.

Invokes Claude in headless mode (`claude --print`) to produce 10 caption
specs for the given ISO week, following the SKILL.md playbook. Output is a
JSON file at `<repo>/2026/W{NN}/captions.json` that the renderer and CSV
writer consume.

The schema is documented in the prompt itself so the prompt is the contract.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SKILL_PATH = REPO_ROOT / ".claude" / "skills" / "spark-weekly-content" / "SKILL.md"


def iso_week_dates(year: int, week: int) -> tuple[date, date]:
    """Return (monday, friday) of the given ISO week."""
    monday = date.fromisocalendar(year, week, 1)
    friday = monday + timedelta(days=4)
    return monday, friday


def mission_lens_for_week(week_num: int) -> str:
    """Mission Monday rotates between mission/problem/origin every 3 weeks."""
    return ["mission", "problem", "origin"][(week_num - 1) % 3]


def build_caption_prompt(year: int, week_num: int, week_label: str,
                         research_hooks: str = "") -> str:
    monday, friday = iso_week_dates(year, week_num)
    lens = mission_lens_for_week(week_num)
    nn = f"{week_num:02d}"

    return f"""You are generating the Spark Careers / RisePoint Careers weekly social-post bundle for {week_label} ({monday.isoformat()} through {friday.isoformat()}).

First, read the full playbook at:
{SKILL_PATH.as_posix()}

It defines: brand systems (RisePoint vs Spark), voice rules (corporate-professional + inspirational, no emojis), 5 layouts (Mission/Trade Secrets/Spotlight/Commitment/Feature Friday), theme rotation, channel split (9 LinkedIn / 10 Facebook / 5 Instagram = 24 placements), UTM tagging, posting times, banned topics, and quality gate. Follow it exactly.

This week's specifics:
- Mission Monday lens: **{lens}** (mission|problem|origin rotation, calculated for week {week_num})
- Tuesday is Trade Secret NO. {nn} (use the week number as the badge number)
- B2B URL: https://hire.risepointcareers.com/
- B2C URL: https://spark.stepupcareers.com/
- UTM template: ?utm_source=social&utm_medium=post&utm_campaign=w{nn}-{{day}}-{{audience}}
- All B2B posts post at 08:00, all B2C posts at 12:00 (America/Edmonton).

Research hooks for this week (use 1-3 where they genuinely fit, never shoehorn):
{research_hooks or "(no research hooks supplied — skip the seasonal/news reference)"}

Now output **ONLY** a JSON array of 10 caption objects. No markdown code fences. No preamble. No commentary after. Just the JSON.

The 10 objects in order: mon-b2b, mon-b2c, tue-b2b, tue-b2c, wed-b2b, wed-b2c, thu-b2b, thu-b2c, fri-b2b, fri-b2c.

Each object MUST have exactly these keys:
{{
  "day": "mon"|"tue"|"wed"|"thu"|"fri",
  "audience": "b2b"|"b2c",
  "theme_tag": "MISSION MONDAY" | "TRADE SECRETS" | "SPOTLIGHT" | "COMMITMENT THURSDAY" | "FEATURE FRIDAY",
  "overline": "THE INSIGHT" for Tuesday, "THIS WEEK'S FEATURE" for Friday, "" otherwise,
  "badge_number": {week_num} for Tuesday, null otherwise,
  "headline": "Short impactful headline. 8-16 words. Sentence case. Period at end.",
  "highlights": ["word1", "word2"]  -- 1 to 2 words from the headline to color-accent. Pick visually-anchoring words. The last word/phrase of the headline often works best. Match casing exactly to the headline.,
  "subline": "Single support line. 6-12 words. Sometimes empty string is OK on Trade Secrets.",
  "url": "hire.risepointcareers.com" for B2B, "spark.stepupcareers.com" for B2C,
  "footer_meta": "For employers · Spark Careers Enterprise" for B2B, "For job seekers · Spark Careers" for B2C,
  "caption_linkedin": "Full LinkedIn caption ending with the tracked URL inline. 100-500 words depending on B2B/B2C. Plain-spoken, no emojis, no exclamation points unless quoting. The tracked URL goes inline at the end and uses the UTM template above.",
  "caption_facebook": "Full Facebook caption. 80-200 words. Tracked URL inline at end.",
  "caption_instagram": "Full Instagram caption for B2C posts only (or empty string for B2B). 80-200 words. Lead with the hook in first 125 chars. Ends with 'Link in bio: <stripped URL>' (the URL stripped of utm params).",
  "channels": list of channels this post is published to -- see the playbook for the 9/10/5 distribution
}}

Channel distribution rules (this determines the "channels" key on each post):
- All 5 B2B posts (mon-b2b through fri-b2b): channels = ["linkedin", "facebook"]
- B2C Monday, Wednesday, Thursday, Friday: channels = ["linkedin", "facebook", "instagram"]
- B2C Tuesday (tactical CV-advice): channels = ["facebook", "instagram"]  (skip LinkedIn for tactical Tuesday)

If caption_instagram is non-empty, it MUST be a B2C post AND "instagram" must be in channels.

Output the JSON array now. Nothing else."""


def extract_json_array(text: str) -> str:
    """Pull the first JSON array out of Claude's stdout, stripping any markdown fences."""
    fenced = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", text, re.DOTALL)
    if fenced:
        return fenced.group(1)
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1 or end < start:
        raise ValueError("No JSON array found in Claude output")
    return text[start : end + 1]


def generate_captions(year: int, week_num: int, week_label: str,
                       research_hooks: str = "",
                       output_path: Path | None = None,
                       timeout_seconds: int = 600) -> list[dict]:
    """Invoke Claude headlessly and return the parsed caption list.

    If output_path is supplied, also persists the raw JSON to disk.
    """
    prompt = build_caption_prompt(year, week_num, week_label, research_hooks)
    print(f"[captions] invoking claude --print for {week_label}…", flush=True)

    proc = subprocess.run(
        [
            "claude",
            "--print",
            "--permission-mode", "bypassPermissions",
            "--allowed-tools", "Read,WebSearch,WebFetch",
            "--no-session-persistence",
            "--output-format", "text",
            prompt,
        ],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=timeout_seconds,
    )
    if proc.returncode != 0:
        sys.stderr.write("=== claude --print FAILED ===\n")
        sys.stderr.write(f"exit code: {proc.returncode}\n")
        sys.stderr.write(f"stderr:\n{proc.stderr or '(empty)'}\n")
        sys.stderr.write(f"stdout (first 4KB):\n{(proc.stdout or '(empty)')[:4096]}\n")
        sys.stderr.write("=== end claude failure ===\n")
        raise RuntimeError(
            f"claude --print exited {proc.returncode}. "
            f"stdout starts: {(proc.stdout or '')[:200]!r}"
        )

    json_text = extract_json_array(proc.stdout)
    captions = json.loads(json_text)

    if not isinstance(captions, list) or len(captions) != 10:
        raise ValueError(f"Expected 10 caption objects, got {type(captions).__name__} len={len(captions) if hasattr(captions, '__len__') else '?'}")

    validate_captions(captions)

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(captions, indent=2, ensure_ascii=False),
                                encoding="utf-8")
        print(f"[captions] wrote {output_path}")

    return captions


REQUIRED_KEYS = {
    "day", "audience", "theme_tag", "overline", "badge_number",
    "headline", "highlights", "subline", "url", "footer_meta",
    "caption_linkedin", "caption_facebook", "caption_instagram", "channels",
}
VALID_DAYS = ["mon", "tue", "wed", "thu", "fri"]
EXPECTED_ORDER = [(d, a) for d in VALID_DAYS for a in ("b2b", "b2c")]


def validate_captions(captions: list[dict]) -> None:
    """Sanity-check schema and ordering."""
    for i, c in enumerate(captions):
        missing = REQUIRED_KEYS - set(c.keys())
        if missing:
            raise ValueError(f"caption {i} missing keys: {missing}")
        expected_day, expected_aud = EXPECTED_ORDER[i]
        if c["day"] != expected_day or c["audience"] != expected_aud:
            raise ValueError(
                f"caption {i} order mismatch: got {c['day']}/{c['audience']}, "
                f"expected {expected_day}/{expected_aud}"
            )
        if not isinstance(c["highlights"], list):
            raise ValueError(f"caption {i} highlights must be a list")
        if not isinstance(c["channels"], list) or not c["channels"]:
            raise ValueError(f"caption {i} channels must be a non-empty list")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--week", type=int, required=True, help="ISO week number (1-53)")
    parser.add_argument("--out", type=Path, default=None,
                        help="Output JSON file path (default: print to stdout)")
    parser.add_argument("--research", default="",
                        help="Optional research hooks string to inject")
    args = parser.parse_args()

    week_label = f"{args.year}-W{args.week:02d}"
    captions = generate_captions(args.year, args.week, week_label,
                                  args.research, args.out)
    if args.out is None:
        print(json.dumps(captions, indent=2, ensure_ascii=False))
