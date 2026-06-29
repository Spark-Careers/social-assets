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
- B2C URL: https://spark.risepointcareers.com/
- UTM template: ?utm_source=social&utm_medium=post&utm_campaign=w{nn}-{{day}}-{{audience}}
- All B2B posts post at 08:00, all B2C posts at 12:00 (America/Edmonton).

STYLE RULES (hard constraints, no exceptions):
- NO em-dashes ("—"), NO en-dashes ("–"), NO double-hyphens ("--") anywhere in headlines, sublines, or captions. Use periods, commas, parentheses, or sentence breaks instead. (Hyphens inside hyphenated compound words like "founder-led" are fine.)
- Captions spell out contractions in full: "do not" not "don't", "we have" not "we've", "you are" not "you're", "it is" not "it's", "will not" not "won't", "did not" not "didn't", "I am" not "I'm". Possessives like "founder's" stay as-is.
- Visual headlines should also lean toward the spelled-out form for consistency. Default to spelling them out unless a contraction is the only natural way the line scans.

================================================================
MANDATORY RESEARCH PASS BEFORE YOU COMPOSE ANYTHING
================================================================

User has explicitly flagged on W23 that evergreen-only content is not acceptable. This research pass is a HARD REQUIREMENT, not a "nice to have". Do not skip it.

STEP 1 — Run AT LEAST 4 WebSearch calls covering these axes:
  (a) Current job-market headlines ("SMB hiring [current month] 2026", "new grad hiring 2026", "BLS JOLTS 2026", "layoff news this week")
  (b) ATS / AI-in-hiring discourse ("applicant tracking system 2026 news", "AI resume rejection 2026", "EU AI Act hiring", "NYC Local Law 144")
  (c) B2B competitor watch (BambooHR, Workable, Greenhouse, JazzHR, Manatal — feature launches, blog posts, announcements this week)
  (d) B2C competitor watch (Jobright.ai, Teal, Jobscan, Kickresume, Rezi — same)

STEP 2 — Identify 3 to 5 concrete hooks. A hook is one of:
  - A specific number from a reputable source ("75 percent of resumes...", "974,000 new grads...", "5.6 percent YoY hiring uptick")
  - A recent news item (a product launch, a regulatory change, a layoff wave)
  - A competitor move worth referencing or contrasting against
  - A seasonal moment ripe for this specific week (grad season, Q3 hiring start, holiday wind-down)

Log each hook with its source URL.

STEP 3 — Anchor AT LEAST 5 of the 10 captions to one of those hooks.
  - Both Mission Monday posts MUST be anchored (this slot most needs current relevance).
  - Spread the rest across at least one other day's pair.
  - For an anchored caption: weave the hook naturally into the first 2-3 sentences. Do not bolt it on at the end.

STEP 4 — Pre-pend a `_research` sidecar to the output. The output is now an OBJECT, not an array:

{{
  "_research": {{
    "performed_at": "<ISO-8601 timestamp of when you ran the searches>",
    "hooks": [
      {{"hook": "short description", "source": "https://..." }},
      ...
    ],
    "anchored_posts": ["mon-b2b", "mon-b2c", "tue-b2b", ...]   // MUST contain at least 5 entries, and MUST include both mon-b2b and mon-b2c
  }},
  "captions": [ ...10 caption objects in the schema below... ]
}}

ANTI-SHOEHORN RULE: if a hook genuinely does not fit a specific post, leave that post evergreen. The 5-of-10 minimum is the floor. Better to ship 5 anchored + 5 evergreen than 10 forced.

If you cannot find 3 usable hooks after the research pass, STOP and write to stdout: `RESEARCH_INSUFFICIENT: <explanation>` and exit. Do not ship an evergreen-only bundle.

Research hooks already supplied (if any, treat as a starting point — still do your own research):
{research_hooks or "(none supplied — do all research yourself)"}

================================================================

Now output the JSON OBJECT (NOT a bare array). No markdown code fences. No preamble. No commentary after. Just the JSON object with `_research` and `captions` keys.

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
  "url": "hire.risepointcareers.com" for B2B, "spark.risepointcareers.com" for B2C,
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


def extract_json_payload(text: str) -> str:
    """Pull the first JSON object (or legacy bare array) out of Claude's stdout."""
    # Check for explicit research-insufficient signal
    if "RESEARCH_INSUFFICIENT" in text:
        raise RuntimeError(
            "Agent reported RESEARCH_INSUFFICIENT — refusing to ship evergreen-only bundle. "
            "Re-run with --research providing hooks manually, or investigate why the WebSearch returned nothing useful."
        )
    # Strip markdown fences
    fenced_obj = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced_obj:
        return fenced_obj.group(1)
    fenced_arr = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", text, re.DOTALL)
    if fenced_arr:
        return fenced_arr.group(1)
    # Find the first balanced object or array
    obj_start = text.find("{")
    arr_start = text.find("[")
    if obj_start == -1 and arr_start == -1:
        raise ValueError("No JSON object or array found in Claude output")
    # Prefer object form (current schema). Fall back to array (legacy).
    if obj_start != -1 and (arr_start == -1 or obj_start < arr_start):
        end = text.rfind("}")
        if end == -1 or end < obj_start:
            raise ValueError("Unterminated JSON object in Claude output")
        return text[obj_start : end + 1]
    end = text.rfind("]")
    if end == -1 or end < arr_start:
        raise ValueError("Unterminated JSON array in Claude output")
    return text[arr_start : end + 1]


# Backward compat: old name
extract_json_array = extract_json_payload


def generate_captions(year: int, week_num: int, week_label: str,
                       research_hooks: str = "",
                       output_path: Path | None = None,
                       timeout_seconds: int = 1500) -> list[dict]:
    """Invoke Claude headlessly and return the parsed caption list.

    Timeout default raised from 600s to 1500s (25 min) to accommodate the
    mandatory research pass (4+ WebSearch calls + composition of 10 captions
    with 3 channel variants each). The Jun 12 autonomous run hung at the
    previous 600s ceiling.

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

    # Always dump the raw stdout to a debug file so post-mortems work even
    # when the JSON parse succeeds (so we can audit what claude actually said
    # without having to re-run). Jun 19 + Jun 26 autonomous runs both crashed
    # at json.loads with no record of what claude returned.
    debug_dir = REPO_ROOT / "runs"
    debug_dir.mkdir(parents=True, exist_ok=True)
    raw_path = debug_dir / f"{week_label}-claude-stdout.txt"
    raw_path.write_text(proc.stdout or "", encoding="utf-8")

    try:
        json_text = extract_json_payload(proc.stdout)
    except (ValueError, RuntimeError) as exc:
        sys.stderr.write(f"=== JSON EXTRACTION FAILED ===\n{exc}\n")
        sys.stderr.write(f"Raw claude stdout saved to: {raw_path}\n")
        sys.stderr.write(f"First 4KB:\n{(proc.stdout or '')[:4096]}\n")
        sys.stderr.write("=== end ===\n")
        raise

    try:
        payload = json.loads(json_text)
    except json.JSONDecodeError as exc:
        sys.stderr.write(f"=== JSON PARSE FAILED at line {exc.lineno} col {exc.colno} ===\n{exc.msg}\n")
        sys.stderr.write(f"Raw claude stdout saved to: {raw_path}\n")
        sys.stderr.write(f"Extracted JSON text (first 4KB):\n{json_text[:4096]}\n")
        sys.stderr.write(f"Bytes around error position (char {exc.pos}):\n{json_text[max(0,exc.pos-100):exc.pos+100]!r}\n")
        sys.stderr.write("=== end ===\n")
        raise

    # Accept both new {_research, captions} object form and legacy bare array.
    if isinstance(payload, dict) and "captions" in payload:
        research = payload.get("_research") or {}
        captions = payload["captions"]
    elif isinstance(payload, list):
        research = {}
        captions = payload
    else:
        raise ValueError(f"Unexpected JSON shape: {type(payload).__name__}")

    if not isinstance(captions, list) or len(captions) != 10:
        raise ValueError(f"Expected 10 caption objects, got len={len(captions) if hasattr(captions, '__len__') else '?'}")

    validate_captions(captions)
    validate_research(research)

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        # Persist the full payload (research + captions) so downstream tools
        # can audit which posts cite what.
        out_payload = {"_research": research, "captions": captions} if research else captions
        output_path.write_text(json.dumps(out_payload, indent=2, ensure_ascii=False),
                                encoding="utf-8")
        print(f"[captions] wrote {output_path}")
        if research:
            anchored = research.get("anchored_posts", [])
            print(f"[captions] research: {len(research.get('hooks', []))} hooks, {len(anchored)} anchored posts: {anchored}")

    return captions


REQUIRED_KEYS = {
    "day", "audience", "theme_tag", "overline", "badge_number",
    "headline", "highlights", "subline", "url", "footer_meta",
    "caption_linkedin", "caption_facebook", "caption_instagram", "channels",
}
VALID_DAYS = ["mon", "tue", "wed", "thu", "fri"]
EXPECTED_ORDER = [(d, a) for d in VALID_DAYS for a in ("b2b", "b2c")]


def validate_captions(captions: list[dict]) -> None:
    """Sanity-check schema, ordering, style rules, and dash discipline."""
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

        # Style rule: no em-dashes, en-dashes, or double-hyphens anywhere
        for field in ("headline", "subline", "caption_linkedin",
                      "caption_facebook", "caption_instagram"):
            v = c.get(field) or ""
            for bad, name in (("—", "em-dash"), ("–", "en-dash"), ("--", "double-hyphen")):
                if bad in v:
                    raise ValueError(
                        f"caption {i} ({c['day']}-{c['audience']}) field {field} "
                        f"contains forbidden {name}. Use periods/commas/parens instead."
                    )


def validate_research(research: dict) -> None:
    """Enforce: research must be present with >= 3 hooks and >= 5 anchored posts
    including both mon-b2b and mon-b2c. Soft warning for now; promote to hard
    error once we trust the autonomous pipeline reliably populates this.
    """
    if not research:
        sys.stderr.write(
            "WARNING: bundle has no _research metadata. Captions may be evergreen. "
            "User has flagged this as not acceptable.\n"
        )
        return

    hooks = research.get("hooks") or []
    anchored = research.get("anchored_posts") or []

    issues = []
    if len(hooks) < 3:
        issues.append(f"only {len(hooks)} research hook(s); minimum is 3")
    if len(anchored) < 5:
        issues.append(f"only {len(anchored)} anchored post(s); minimum is 5")
    if "mon-b2b" not in anchored:
        issues.append("mon-b2b is not in anchored_posts (Mission Monday B2B MUST be anchored)")
    if "mon-b2c" not in anchored:
        issues.append("mon-b2c is not in anchored_posts (Mission Monday B2C MUST be anchored)")

    for h in hooks:
        if not isinstance(h, dict) or "hook" not in h or "source" not in h:
            issues.append(f"malformed hook entry: {h!r} (need 'hook' and 'source')")
            break

    if issues:
        msg = "Research pass insufficient:\n  - " + "\n  - ".join(issues)
        sys.stderr.write(f"WARNING: {msg}\n")


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
