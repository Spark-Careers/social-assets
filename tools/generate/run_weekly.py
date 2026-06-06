"""Spark Careers weekly autonomous orchestrator.

Run this once a week (via Windows Task Scheduler, manually, etc.) to:

  1. Determine target ISO week (default: the ISO week starting next Monday)
  2. Generate 10 captions via Claude headless mode
  3. Render 10 brand-styled PNGs at 1080x1350
  4. Write the content-calendar DOCX
  5. Write 3 channel CSVs (Title-Case schema, placeholder image URLs)
  6. git add + commit + push the new PNGs to Spark-Careers/social-assets
  7. Run finalize_buffer_csvs.py to swap placeholders for raw URLs
     and rewrite to Buffer's actual schema
  8. Copy the final CSVs + DOCX to Downloads\\spark-w{NN}-buffer\\
  9. Pop a Windows toast notification

Failure at any step: log to <repo>/runs/<week>.log, toast a failure notification.

Usage:
    python run_weekly.py                      # auto-pick next ISO week
    python run_weekly.py --year 2026 --week 23
    python run_weekly.py --skip-push          # don't git push (dry-run)
    python run_weekly.py --skip-captions      # reuse existing captions.json
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import traceback
from datetime import date, timedelta
from pathlib import Path

GENERATE_DIR = Path(__file__).resolve().parent
TOOLS_DIR = GENERATE_DIR.parent
REPO_ROOT = TOOLS_DIR.parent
FINALIZE_SCRIPT = TOOLS_DIR / "finalize_buffer_csvs.py"
RUNS_DIR = REPO_ROOT / "runs"

sys.path.insert(0, str(GENERATE_DIR))
from captions import generate_captions
from csv_writer import write_channel_csvs
from docx_writer import write_calendar_docx
from notify import notify_failure, notify_success
from renderer import render_post_simple


def default_target_week(today: date | None = None) -> tuple[int, int, str]:
    """Default: the ISO week that begins at least 7 days from today.

    Rationale: when the autonomous run fires on Friday at 08:30, the next
    Monday is only 3 days away — not enough lead time to review and
    bulk-upload before Mon 08:00 posts go live. Adding the 7-day floor means
    Friday's delivery is always for Monday-after-next (10 days out), giving
    a full weekend + week to review.

    Examples:
      today = Tue May 19  -> next Mon = May 25 (6 days), skip -> Mon Jun 1 = W23
      today = Fri May 22  -> next Mon = May 25 (3 days), skip -> Mon Jun 1 = W23
      today = Sun May 24  -> next Mon = May 25 (1 day),  skip -> Mon Jun 1 = W23
      today = Mon May 25  -> next Mon = Jun 1  (7 days), keep -> W23
      today = Tue May 26  -> next Mon = Jun 1  (6 days), skip -> Mon Jun 8 = W24
    """
    today = today or date.today()
    # Find the first Monday that is >= 7 days from today.
    days_until_next_mon = (7 - today.weekday()) % 7 or 7
    candidate = today + timedelta(days=days_until_next_mon)
    if (candidate - today).days < 7:
        candidate += timedelta(days=7)
    year, week, _ = candidate.isocalendar()
    return year, week, f"{year}-W{week:02d}"


def log(line: str, *, also_print: bool = True, log_handle=None) -> None:
    line_clean = line.rstrip()
    if also_print:
        print(line_clean, flush=True)
    if log_handle is not None:
        log_handle.write(line_clean + "\n")
        log_handle.flush()


def push_to_github(repo_root: Path, week_label: str, log_h) -> None:
    log(f"[git] cd {repo_root}", log_handle=log_h)
    log(f"[git] git add 2026/", log_handle=log_h)
    subprocess.run(["git", "add", "."], cwd=repo_root, check=True,
                    capture_output=True, text=True, encoding="utf-8", errors="replace")
    status = subprocess.run(["git", "status", "--porcelain"], cwd=repo_root,
                             capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
    if not status.strip():
        log("[git] nothing to commit (working tree clean)", log_handle=log_h)
        return
    log(f"[git] commit", log_handle=log_h)
    subprocess.run(["git", "commit", "-m", f"{week_label}: visuals + bundle artifacts"],
                    cwd=repo_root, check=True,
                    capture_output=True, text=True, encoding="utf-8", errors="replace")
    log(f"[git] push", log_handle=log_h)
    subprocess.run(["git", "push"], cwd=repo_root, check=True,
                    capture_output=True, text=True, encoding="utf-8", errors="replace")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, default=None)
    parser.add_argument("--week", type=int, default=None)
    parser.add_argument("--skip-push", action="store_true",
                        help="Skip git add/commit/push (rendered PNGs stay local).")
    parser.add_argument("--skip-captions", action="store_true",
                        help="Reuse existing captions.json instead of invoking Claude.")
    parser.add_argument("--research", default="",
                        help="Optional research hooks string injected into the caption prompt.")
    parser.add_argument("--downloads-dir", type=Path,
                        default=Path.home() / "Downloads",
                        help="Where to copy final CSVs + docx for Buffer upload.")
    args = parser.parse_args()

    if args.year and args.week:
        year, week_num = args.year, args.week
        week_label = f"{year}-W{week_num:02d}"
    else:
        year, week_num, week_label = default_target_week()

    nn = f"{week_num:02d}"

    RUNS_DIR.mkdir(exist_ok=True)
    log_path = RUNS_DIR / f"{week_label}.log"
    log_h = log_path.open("w", encoding="utf-8")

    try:
        log(f"=== Spark Careers weekly build: {week_label} ===", log_handle=log_h)
        log(f"Repo root: {REPO_ROOT}", log_handle=log_h)

        # 1. Captions
        week_dir = REPO_ROOT / str(year) / f"W{nn}"
        captions_path = week_dir / "captions.json"

        if args.skip_captions and captions_path.exists():
            import json
            log(f"[captions] reusing {captions_path}", log_handle=log_h)
            payload = json.loads(captions_path.read_text(encoding="utf-8"))
            # Accept both new {_research, captions} object and legacy bare-array forms
            captions = payload["captions"] if isinstance(payload, dict) and "captions" in payload else payload
        else:
            captions = generate_captions(year, week_num, week_label,
                                          args.research, captions_path)

        # 2. PNGs
        log(f"[render] rendering 10 PNGs to {week_dir}", log_handle=log_h)
        for c in captions:
            out = week_dir / f"{week_label}-{c['day']}-{c['audience']}.png"
            render_post_simple(c, out)
            log(f"[render]   {out.name}", log_handle=log_h)

        # 3. DOCX
        bundle_dir = args.downloads_dir / f"spark-w{nn}-buffer"
        bundle_dir.mkdir(parents=True, exist_ok=True)
        docx_path = bundle_dir / f"spark-w{nn}-content-calendar.docx"
        write_calendar_docx(captions, year, week_num, docx_path)
        log(f"[docx] wrote {docx_path}", log_handle=log_h)

        # 4. Source CSVs (Title-Case schema, placeholder URLs) — in a scratch dir
        scratch_csvs = bundle_dir / "_source"
        scratch_csvs.mkdir(exist_ok=True)
        write_channel_csvs(captions, year, week_num, scratch_csvs)

        # 5. Push to GitHub (so raw URLs resolve before finalize)
        if not args.skip_push:
            push_to_github(REPO_ROOT, week_label, log_h)
        else:
            log("[git] (--skip-push) skipped", log_handle=log_h)

        # 6. Run finalizer (placeholder -> raw URL, Title-Case -> Buffer schema)
        log("[finalize] running finalize_buffer_csvs.py", log_handle=log_h)
        subprocess.run([
            sys.executable, str(FINALIZE_SCRIPT),
            "--week", week_label,
            "--input", str(scratch_csvs),
            "--output", str(bundle_dir),
        ], check=True, capture_output=True, text=True, encoding="utf-8", errors="replace")

        # Clean up the scratch source CSVs — keep only the -final.csv files
        shutil.rmtree(scratch_csvs, ignore_errors=True)

        # 7. Tally + notify
        png_count = len(list(week_dir.glob("*.png")))
        csv_count = len(list(bundle_dir.glob("*-final.csv")))
        log(f"[done] {png_count} PNGs in repo, {csv_count} final CSVs in {bundle_dir}",
             log_handle=log_h)
        notify_success(week_label, bundle_dir, csv_count, png_count)
        return 0

    except Exception as exc:
        tb = traceback.format_exc()
        log(f"[ERROR] {exc}\n{tb}", log_handle=log_h)
        notify_failure(week_label, f"{type(exc).__name__}: {exc}", log_path)
        return 1
    finally:
        log_h.close()


if __name__ == "__main__":
    raise SystemExit(main())
