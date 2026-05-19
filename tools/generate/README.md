# tools/generate/ — autonomous weekly bundle pipeline

End-to-end weekly Spark Careers / RisePoint Careers social-post bundle, running
locally on Windows. Triggered by Task Scheduler every **Friday 08:30 America/Edmonton**.

## What it does

For the ISO week starting next Monday, it:

1. **Generates 10 captions** by invoking Claude in headless mode (`claude --print`)
   with the playbook from [SKILL.md](../../.claude/skills/spark-weekly-content/SKILL.md).
   Output: `<repo>/2026/W{NN}/captions.json`.
2. **Renders 10 PNGs** (1080×1350) via Playwright + headless Chromium using one
   of the 5 brand-styled HTML templates in `templates/`. Output:
   `<repo>/2026/W{NN}/<week>-<day>-<aud>.png`.
3. **Writes the content-calendar DOCX** (cover + week-at-a-glance + per-post
   layout) to `Downloads/spark-w{NN}-buffer/spark-w{NN}-content-calendar.docx`.
4. **Writes 3 source CSVs** with Title-Case schema + `__REPLACE_…__` image
   placeholders to a scratch dir.
5. **Pushes** the new PNGs to `Spark-Careers/social-assets` so raw URLs resolve.
6. **Runs `finalize_buffer_csvs.py`** which swaps placeholders for
   `raw.githubusercontent.com` URLs and rewrites the CSV schema to Buffer's
   actual format (`text, image_url, tags, posting_time`). Output: 3
   `*-final.csv` files in `Downloads/spark-w{NN}-buffer/`.
7. **Pops a Windows toast** "Spark Careers W{NN} bundle ready" with an Open
   Folder action.

Total wall-clock time: ~3–5 minutes (most of it is Claude generating captions).

## Files

```
generate/
├── README.md                  (this file)
├── run_weekly.py              orchestrator — entry point
├── run_weekly.ps1             PowerShell wrapper invoked by Task Scheduler
├── SparkWeeklyContent.xml     Task Scheduler task definition (Friday 08:30)
├── install-task.ps1           registers the scheduled task
├── uninstall-task.ps1         removes it
├── captions.py                invokes `claude --print` to get the 10 captions
├── renderer.py                Playwright HTML→PNG render pipeline
├── docx_writer.py             python-docx content-calendar writer
├── csv_writer.py              source CSV writer (placeholder URLs)
├── notify.py                  winotify toast notifications
└── templates/
    ├── css/base.css           shared 1080×1350 typography + tokens
    ├── mission_monday.html    RisePoint brand (navy + saffron)
    ├── trade_secrets.html     Spark brand (arsenic + cadet)
    ├── spotlight.html         Spark brand, ghost quotation mark
    ├── commitment.html        Spark brand, dot pattern
    ├── feature_friday.html    Spark brand, split-color CTA panel
    └── assets/
        ├── risepoint-logo-light.png
        ├── spark-logo.png       (cream-tintable via CSS filter)
        └── spark-logo.svg
```

## Manual operation

```powershell
# Default: build for the ISO week starting NEXT Monday
python tools\generate\run_weekly.py

# Specific week
python tools\generate\run_weekly.py --year 2026 --week 23

# Dry-run (don't push to GitHub)
python tools\generate\run_weekly.py --skip-push

# Reuse existing captions.json (skip Claude invocation)
python tools\generate\run_weekly.py --skip-captions

# Pass research hooks to inform the week's captions
python tools\generate\run_weekly.py --research "Major SMB hiring report Friday; LinkedIn announced AI matching tool Wednesday"
```

## Scheduled-task install (one-time)

```powershell
cd "C:\Users\HP\Desktop\Personal Docs\Post Shell Projects\IdleSpark\Marketing\social-assets\tools\generate"
powershell -ExecutionPolicy Bypass -File install-task.ps1
```

The task fires every Friday at 08:30 America/Edmonton. It will wake the laptop
from sleep if needed, run whether on battery or plugged in, and skip silently
if no network. If the laptop is fully off at 08:30, the task fires when you
next log in (because `StartWhenAvailable` is true).

Force a test run on demand:

```powershell
schtasks /Run /TN "SparkCareers\WeeklyContentBuild"
```

## Required dependencies

Already installed during initial setup:

- Python 3.13+
- `playwright` (with Chromium installed via `python -m playwright install chromium`)
- `python-docx`
- `winotify`
- `git` + `gh` authenticated as `sparkcareers` (for the push step)
- Claude Code CLI on PATH (for `claude --print` invocation)

## Logs and failure modes

- **Per-run log:** `<repo>/runs/{week-label}.log` — full stdout + stderr.
- **Wrapper log:** `<repo>/runs/wrapper-<timestamp>.log` — Task Scheduler's
  outer transcript including the Python invocation line.
- **Failure toast:** if anything fails, you get a Windows toast notification
  "Spark Careers W{NN} build FAILED" with an Open Log action.

Common failure causes and fixes:

| Symptom | Cause | Fix |
|---|---|---|
| Toast says auth error | `claude --print` not authenticated outside Claude Code | Run `claude` once interactively and complete login |
| Toast says git push failed | `gh` token expired or branch protection issue | Run `gh auth refresh` |
| Captions JSON parse error | Claude returned non-JSON text | Re-run; if persistent, inspect `runs/<week>.log` and adjust prompt in `captions.py` |
| Render fails with font issue | Google Fonts CDN unreachable | Templates fall back to Segoe UI; render still completes but typography degrades |
