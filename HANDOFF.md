# The Spark Careers weekly social-content engine

A full system description. Written for someone who wants to understand how this thing works end to end — the components, the contracts between them, the data flow, the design decisions, and the extension points — before they think about installing it or porting it. The install steps live near the end; read the rest first.

---

## Table of contents

1. [What the system does, in one paragraph](#1-what-the-system-does-in-one-paragraph)
2. [Concept of operations — the weekly rhythm](#2-concept-of-operations--the-weekly-rhythm)
3. [System architecture](#3-system-architecture)
4. [Data flow, Friday to next Friday](#4-data-flow-friday-to-next-friday)
5. [Component reference](#5-component-reference)
6. [The playbook: `SKILL.md`](#6-the-playbook-skillmd)
7. [The `captions.json` contract](#7-the-captionsjson-contract)
8. [Visual system: brand, templates, typography](#8-visual-system-brand-templates-typography)
9. [Voice, style rules, validators](#9-voice-style-rules-validators)
10. [Channel distribution logic](#10-channel-distribution-logic)
11. [The mandatory research pass](#11-the-mandatory-research-pass)
12. [The autonomous trigger — Windows Task Scheduler](#12-the-autonomous-trigger--windows-task-scheduler)
13. [Headless Claude authentication](#13-headless-claude-authentication)
14. [GitHub as an image CDN](#14-github-as-an-image-cdn)
15. [Buffer bulk upload](#15-buffer-bulk-upload)
16. [Failure modes and diagnosis](#16-failure-modes-and-diagnosis)
17. [Repository layout](#17-repository-layout)
18. [Extension points — porting to another brand](#18-extension-points--porting-to-another-brand)
19. [Setup guide (condensed)](#19-setup-guide-condensed)
20. [Design decisions and tradeoffs](#20-design-decisions-and-tradeoffs)
21. [Known gaps and roadmap](#21-known-gaps-and-roadmap)

---

## 1. What the system does, in one paragraph

Every Friday at 08:30 local time, a Windows scheduled task on the operator's laptop fires a Python orchestrator that reads a brand playbook, invokes a headless Claude subprocess to do a live web research pass and generate ten social-post captions (five B2B, five B2C, one pair per weekday), renders ten brand-styled PNG visuals at 1080×1350 using Playwright and headless Chromium, writes a Word review document, produces three Buffer-native CSV files (one per social channel), pushes the PNGs to a public GitHub repository so `raw.githubusercontent.com` can serve them as an image CDN, runs a finalizer that swaps placeholder image URLs for the real CDN URLs and rewrites the CSVs to Buffer's exact bulk-upload schema, drops the final artifacts into `Downloads\<brand>-w{NN}-buffer\`, and pops a Windows toast notification telling the operator the bundle is ready. The operator opens Buffer, bulk-uploads three CSVs (about three minutes of clicks), and Buffer schedules and publishes all twenty-four placements automatically through the week. The operator's total weekly time is roughly five minutes.

---

## 2. Concept of operations — the weekly rhythm

A week in the life of the pipeline:

| When | Who / what | What happens |
|---|---|---|
| Friday 08:30 local | Task Scheduler | Fires `WeeklyContentBuild` task, wakes machine if asleep |
| Friday 08:30–08:35 | Wrapper + Python | Runs the full pipeline; ~3-5 min end-to-end |
| Friday 08:35 | Windows toast | *"Spark Careers 2026-W{NN} bundle ready. 10 visuals, 3 CSVs in `<path>`."* |
| Friday ~09:30 | Calendar backstop | Recurring calendar event fires as a secondary reminder |
| Friday sometime | Operator | Opens `Downloads\...`, reviews the DOCX if desired, uploads 3 CSVs to Buffer |
| Following Mon 08:00 | Buffer | First B2B post publishes to LinkedIn + Facebook |
| Mon 12:00 | Buffer | First B2C post publishes to LI + FB + IG |
| ...through Friday | Buffer | Two posts publish per weekday at 08:00 and 12:00 |
| Following Friday 08:30 | Task Scheduler | Fires again, generates the next-next week's bundle |

**Lead time:** the Friday fire targets the ISO week starting **10 days later** (the Monday-after-next). Rationale: gives the operator a full weekend plus one buffer week to catch a missed run.

**Time-zone convention:** all scheduling in `America/Edmonton` (Calgary MT). Buffer stores posting times in the channel's configured timezone; posting_time in the CSV is naive local time.

---

## 3. System architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         Windows laptop (operator's machine)                    │
│                                                                                │
│  ┌──────────────┐    ┌─────────────────┐    ┌────────────────────────────┐    │
│  │Task Scheduler│───▶│run_weekly.ps1   │───▶│    run_weekly.py           │    │
│  │(Fri 08:30)   │    │(wrapper)        │    │    (orchestrator)          │    │
│  └──────────────┘    └─────────────────┘    │                            │    │
│                              │              │  ┌──────────────────────┐  │    │
│                              │              │  │ default_target_week()│  │    │
│                              │              │  │ generate_captions()  │  │    │
│                              │              │  │ render_post_simple() │  │    │
│                              │              │  │ write_calendar_docx()│  │    │
│                              │              │  │ write_channel_csvs() │  │    │
│                              │              │  │ push_to_github()     │  │    │
│                              │              │  │ finalize_buffer_csvs │  │    │
│                              │              │  │ notify_success()     │  │    │
│                              │              │  └──────────┬───────────┘  │    │
│                              │              └─────────────┼──────────────┘    │
│                              │                            │                    │
│  ┌──────────────────────┐    │  ┌───────────────────┐    │                   │
│  │Windows User Registry │────┘  │ headless          │◀───┤                   │
│  │CLAUDE_CODE_OAUTH_TOKEN│      │ `claude --print`  │    │                   │
│  └──────────────────────┘      │ (WebSearch,       │    │                   │
│                                │  reads SKILL.md,  │    │                   │
│                                │  emits JSON)      │    │                   │
│                                └───────────────────┘    │                   │
│                                                          │                   │
│  ┌──────────────────────┐    ┌─────────────────────┐    │                   │
│  │HTML/CSS templates    │◀──▶│ Playwright +        │◀───┤                   │
│  │(5 layouts + CSS +    │    │ headless Chromium   │    │                   │
│  │ brand assets)        │    │ (renderer.py)       │    │                   │
│  └──────────────────────┘    └─────────────────────┘    │                   │
│                                                          │                   │
│  ┌──────────────────────┐    ┌─────────────────────┐    │                   │
│  │python-docx           │◀──▶│ docx_writer.py      │◀───┤                   │
│  │(review doc)          │    └─────────────────────┘    │                   │
│  └──────────────────────┘                               │                   │
│                                                          │                   │
│                              ┌─────────────────────┐    │                   │
│                              │ csv_writer.py       │◀───┤                   │
│                              │ (3 source CSVs)     │    │                   │
│                              └─────────────────────┘    │                   │
│                                                          │                   │
│                              ┌─────────────────────┐    │                   │
│                              │winotify (toast)     │◀───┘                   │
│                              └─────────────────────┘                         │
└──────────────────────────────────────────┬──────────────────────────────────┘
                                            │
                    ┌───────────────────────┴──────────────────┐
                    │                                            │
                    ▼                                            ▼
    ┌───────────────────────────────┐        ┌────────────────────────────────┐
    │  GitHub public repo           │        │  Downloads\<brand>-w{NN}-buffer│
    │  Spark-Careers/social-assets  │        │  ├── 3 *-final.csv             │
    │  └── 2026/W{NN}/*.png         │        │  └── content-calendar.docx     │
    └──────────┬────────────────────┘        └──────────────┬─────────────────┘
               │                                             │
               │ raw.githubusercontent.com                   │ operator uploads
               │ (image CDN)                                 │
               │                                             ▼
               └────────────────▶  ┌──────────────────────────────┐
                                    │  Buffer (Publish tab, per   │
                                    │  channel: gear → Bulk Upload) │
                                    └──────────────┬───────────────┘
                                                   │ scheduled publishing
                                                   ▼
                                    ┌──────────────────────────────┐
                                    │ LinkedIn / Facebook / IG     │
                                    │ (24 placements/week)         │
                                    └──────────────────────────────┘
```

The critical observation: the pipeline is a chain of small deterministic transforms glued together by two live systems (the headless Claude subprocess for captions, GitHub as an image CDN). Everything else is boring Python I/O.

---

## 4. Data flow, Friday to next Friday

Follow the data from left to right.

### Step 1 — target week resolution (Python, <1 sec)

`default_target_week()` in `run_weekly.py` computes the ISO week whose Monday is the first Monday ≥ 7 days from today. On Friday, this returns the Monday-after-next. The operator can override with `--year --week`.

### Step 2 — captions generation (headless Claude, 2–8 min)

`generate_captions()` in `captions.py` builds a text prompt that:
- Names the target ISO week and its date range
- Points at `SKILL.md` (the playbook) and says "read the full playbook there first"
- States style rules inline as a hard constraint (no em-dashes, spelled-out contractions)
- States the mandatory research pass as a hard requirement (≥4 WebSearch calls, ≥5 anchored posts, both Monday posts anchored)
- Specifies the required output as a JSON object `{_research: {...}, captions: [10 objects]}` with a documented schema
- Tells the agent to output ONLY the JSON, no preamble, no markdown fences

The prompt is passed to `subprocess.run(["claude", "--print", "--permission-mode", "bypassPermissions", "--allowed-tools", "Read,WebSearch,WebFetch", "--no-session-persistence", ...])`. The `claude` CLI:
- Reads the OAuth token from `CLAUDE_CODE_OAUTH_TOKEN` env var (which the wrapper re-hydrated from the User-scope Windows registry)
- Reads `SKILL.md` from disk (using the `Read` tool it was allowed)
- Runs at least 4 `WebSearch` calls (current job-market data, ATS/AI news, B2B and B2C competitor watch)
- Composes 10 captions per the playbook, at least 5 anchored to a research hook with source URL
- Writes the JSON object to stdout and exits

`captions.py` reads stdout, extracts the JSON payload (`extract_json_payload()` handles both the object form and the legacy bare-array form and strips optional markdown fences), parses it, validates it against schema (`validate_captions()`) and against the research floor (`validate_research()`), and writes it to `2026/W{NN}/captions.json`.

Timeout is 1500 seconds (25 min) — bumped from the initial 600s after the Jun 12 autonomous run hung during the research pass.

### Step 3 — PNG rendering (Playwright, ~20 sec for 10 posts)

`render_post_simple()` in `renderer.py` picks the HTML template for the post's day (`mission_monday.html` for Mon, `trade_secrets.html` for Tue, etc.), substitutes placeholders (`{{HEADLINE_HTML}}`, `{{SUBLINE}}`, `{{THEME_TAG}}`, etc.) using `str.replace`, wraps highlighted key words in `<span class="accent">…</span>` (via `_wrap_highlights()` with case-insensitive whole-word regex), writes the merged HTML to a scratch file inside the templates directory so relative asset paths still resolve, and drives Playwright to load the file in headless Chromium and take a screenshot at 1080×1350.

Rendering is done serially in a loop (each of 10 posts spawns and tears down its own Playwright context). Total wall time is ~15–20 seconds.

Files land at `2026/W{NN}/2026-W{NN}-{day}-{audience}.png`.

### Step 4 — DOCX review doc (python-docx, ~1 sec)

`write_calendar_docx()` in `docx_writer.py` produces:
- Cover page with title + week label + date range
- Week-at-a-glance table (day / time / audience / theme / hook)
- Per-post pages with metadata (date, time, channels, tracked URL), headline, subline, LinkedIn / Facebook / Instagram caption bodies, alt text

The docx is a human-readable review artifact. The operator can edit captions here before uploading if desired (but changes to the docx do NOT propagate to the CSVs; edit `captions.json` and re-run the finalizer if you want changes to reach Buffer).

Lands at `Downloads\<brand>-w{NN}-buffer\<brand>-w{NN}-content-calendar.docx`.

### Step 5 — source CSVs (Python `csv` module, <1 sec)

`write_channel_csvs()` in `csv_writer.py` walks the caption list and emits three CSV files in the **source schema** — `Date,Time,Text,Image URL,Tags` (title case, five columns). Each row's `Image URL` is a placeholder like `https://drive.google.com/uc?export=view&id=__REPLACE_2026-W{NN}-mon-b2b__`. The placeholder is the marker that the finalizer will swap for the real raw URL two steps later. `posting_time` is not yet combined (that's the finalizer's job too).

Files land at `Downloads\<brand>-w{NN}-buffer\_source\<brand>-w{NN}-buffer-{linkedin,facebook,instagram}.csv`.

### Step 6 — git push (git CLI via subprocess, ~5 sec)

`push_to_github()` runs `git add .`, `git commit -m "{week-label}: visuals + bundle artifacts"`, `git push` in the repo working tree. The commit includes the new PNGs and the new `captions.json`.

Once pushed, `raw.githubusercontent.com/<org>/<repo>/main/2026/W{NN}/2026-W{NN}-*.png` returns 200 with the PNG bytes. Buffer will use these URLs at post time.

### Step 7 — finalize (Python, <1 sec)

`finalize_buffer_csvs.py` reads each source CSV, does two transforms:

1. **URL substitution.** For each PNG in `2026/W{NN}/`, build its raw URL. Search each row's `Image URL` cell for the placeholder marker (`__REPLACE_{basename}__`) and swap it for the raw URL. Also swap the legacy Drive-style placeholder if present.
2. **Schema rewrite.** The source schema is `Date,Time,Text,Image URL,Tags`; Buffer's actual bulk-upload schema is `text,image_url,tags,posting_time` (lowercase, four columns, date+time combined). Rewrite. `posting_time` format is `YYYY-MM-DD HH:MM`.

Handles UTF-8 BOM in source CSVs (some upstream tools ship them; Python's `csv.DictReader` gets confused if the BOM is on the first field name). Opens source files with `utf-8-sig` encoding.

Final CSVs land at `Downloads\<brand>-w{NN}-buffer\<brand>-w{NN}-buffer-{linkedin,facebook,instagram}-final.csv`.

### Step 8 — toast (winotify, <1 sec)

`notify_success()` in `notify.py` shows a Windows toast with an "Open folder" action button that opens the bundle directory.

If any earlier step raised, `notify_failure()` shows a "build FAILED" toast with an "Open log" button pointing at `runs/<week>.log`.

### Step 9 — human step (~3 min)

Operator opens `Downloads\<brand>-w{NN}-buffer\`, opens Buffer, for each channel: **Publish → channel → gear icon → General → Bulk Upload → drag CSV → confirm**. Buffer fetches each image URL, shows a preview, and if the operator confirms, schedules all rows at their `posting_time`.

### Step 10 — Buffer publishes (Mon 08:00 through Fri 12:00)

Buffer publishes each post at its scheduled `posting_time`, in the channel's configured time zone. No further operator action.

---

## 5. Component reference

Every file in `tools/generate/` explained.

### `run_weekly.ps1` — the wrapper

Task Scheduler's entry point. In order:

1. Sets `$ErrorActionPreference = "Stop"` and defines the repo path, log path, timestamp.
2. Locates the Python executable (prefers PATH, falls back to a known install path).
3. Creates the `runs\` directory if missing.
4. Unsets `CLAUDECODE` env var in scope (would otherwise block nested `claude --print`).
5. **Reads `CLAUDE_CODE_OAUTH_TOKEN` from the User-scope Windows registry** using `[System.Environment]::GetEnvironmentVariable(name, "User")`. Task Scheduler often strips user-scope env vars even with `InteractiveToken` principal; reading directly from the registry hive works around this. Exits with code 2 (with a helpful error message in the log) if the token is missing.
6. Sets `PYTHONIOENCODING=utf-8` and `PYTHONUTF8=1` so Python emits UTF-8.
7. Uses a `System.IO.StreamWriter` with explicit UTF-8 (no BOM) to write log output. Reason: PowerShell 5.1's `Tee-Object` does NOT accept `-Encoding`, so the intuitive `Tee-Object -Encoding utf8` throws a "parameter cannot be found" error, silently kills the wrapper before Python starts, and produces no useful log. The StreamWriter pattern works on PS 5.1 and PS 7.
8. Invokes Python with the orchestrator script. Redirects `2>&1` so stderr merges into the log stream. Mirrors each line to console (`Write-Host`) AND to the log file.
9. On completion, appends the exit code to the log and exits with the same code.

### `run_weekly.py` — the orchestrator

Argument parsing:
- `--year` `--week` — target a specific ISO week
- `--skip-push` — dry run; don't `git push`
- `--skip-captions` — reuse `captions.json` on disk instead of invoking Claude
- `--research "<hooks>"` — inject hooks (space-separated bullet text) into the prompt
- `--downloads-dir <path>` — where to place the final bundle (default: `~\Downloads`)

Pipeline: computes target week, invokes each stage, catches exceptions per stage and logs to `runs/<week>.log`, calls `notify_failure()` and exits 1 on any error.

Reads legacy bare-array `captions.json` OR new object-form `{_research, captions}` transparently when `--skip-captions` is used.

### `captions.py` — headless Claude subprocess + validators

Two exported functions:

- `build_caption_prompt(year, week_num, week_label, research_hooks)` — assembles the full prompt string. Templated with `SKILL.md` path, week dates, Mission Monday lens (rotates mission→problem→origin every 3 weeks), Trade Secrets badge number (= week number), URLs, UTM template, style rules, mandatory research pass instructions, JSON output schema.
- `generate_captions(year, week_num, week_label, research_hooks, output_path, timeout_seconds=1500)` — spawns `claude --print`, captures stdout+stderr, extracts the JSON payload, parses it, validates it via `validate_captions()` and `validate_research()`, writes it to disk, returns the caption list.

Internal helpers:
- `extract_json_payload(text)` — pulls the JSON object or bare array out of Claude's stdout, handles markdown code fences, detects a `RESEARCH_INSUFFICIENT` signal from the agent (in which case it raises `RuntimeError` rather than shipping an evergreen-only bundle).
- `validate_captions(captions)` — checks schema, ordering (must be Mon-B2B, Mon-B2C, Tue-B2B, …, Fri-B2C in that order), and dash discipline (no em-dashes / en-dashes / double-hyphens in any field).
- `validate_research(research)` — warns (prints to stderr) if hooks < 3, anchored posts < 5, either Monday slot missing from `anchored_posts`, or any hook missing `source` URL. Warnings, not errors — so a bundle CAN ship without research metadata if the agent absolutely refused, but the user sees the warning in the log.
- `iso_week_dates(year, week)` — returns `(monday, friday)` of the ISO week.
- `mission_lens_for_week(week_num)` — rotates mission | problem | origin.

### `renderer.py` — Playwright PNG renderer

`render_post_simple(spec, output_path)`:
1. Picks the HTML template file for `spec["day"]` (`TEMPLATE_BY_DAY` map).
2. Substitutes placeholders (`{{THEME_TAG}}`, `{{OVERLINE}}`, `{{BADGE_NUMBER}}`, `{{HEADLINE_HTML}}`, `{{SUBLINE}}`, `{{URL}}`, `{{FOOTER_META}}`, `{{AUDIENCE_CLASS}}`) with `str.replace`.
3. Wraps highlighted key words: `_wrap_highlights()` HTML-escapes the headline, then for each string in `spec["highlights"]` uses a case-insensitive whole-word regex to wrap the FIRST match in `<span class="accent">…</span>`. Multi-word highlights work (e.g. `["hiring systems"]` wraps the phrase).
4. Writes the merged HTML to `templates/_render_<day>_<audience>.html` (scratch file next to the templates, so relative `assets/spark-logo.png` and `css/base.css` paths still resolve).
5. Launches Chromium in a fresh Playwright session, sets viewport to 1080×1350, navigates to the scratch file, waits for `networkidle`, sleeps 800ms so Google Fonts settle, screenshots at `clip=(0,0,1080,1350)`.
6. Deletes the scratch HTML.

Total wall time per PNG is ~1.5 seconds. All 10 render serially in ~15–20 seconds.

### `docx_writer.py` — python-docx review doc

`write_calendar_docx(captions, year, week_num, output_path)` builds a two-part docx:

- Cover page + week-at-a-glance table (day / time / audience / theme / hook)
- Per-post pages with heading, metadata row (date/time/channels/tracked URL), media filename, tracked URL, headline, subline, LinkedIn/Facebook/Instagram caption bodies (each labeled and indented), alt text

Uses `Light Grid Accent 1` table style for the week table. Nothing sophisticated — the docx is a review artifact, not a source of truth.

### `csv_writer.py` — 3 source CSVs

`write_channel_csvs(captions, year, week_num, output_dir)`:
- Walks the caption list, for each post walks its `channels` list, and appends a row to the matching channel's row buffer.
- Row schema: `Date`, `Time`, `Text`, `Image URL`, `Tags`. `Image URL` uses the placeholder marker; `posting_time` is not yet combined.
- Text field comes from `caption_linkedin` / `caption_facebook` / `caption_instagram` depending on channel.
- Sorts each channel's rows by (Date, Time).
- Writes each channel to `spark-w{NN}-buffer-{channel}.csv` with `csv.QUOTE_ALL` so multi-line captions don't confuse Buffer's parser.

### `finalize_buffer_csvs.py` — URL substitution + schema rewrite

Two transforms in one pass, invoked as `python finalize_buffer_csvs.py --week 2026-WNN --input <src> --output <dst>`:

- **URL substitution.** For every `*.png` in `2026/W{NN}/`, computes its raw URL (`https://raw.githubusercontent.com/<owner>/<repo>/main/<year>/W{NN}/<basename>.png`) and substitutes it for any `__REPLACE_<basename>__` marker (or legacy `https://drive.google.com/uc?export=view&id=__REPLACE_<basename>__` marker) in the Image URL field.
- **Schema rewrite.** Combines `Date` + `Time` into a single `posting_time` field (`YYYY-MM-DD HH:MM`). Renames columns to lowercase. Emits Buffer's actual schema: `text,image_url,tags,posting_time`. Uses `csv.QUOTE_ALL`.

Handles UTF-8 BOM on source files with `utf-8-sig` encoding.

Also runs standalone after a human-edited claude.ai bundle if the operator ever falls back to Mode 1.

### `notify.py` — Windows toast

Wraps the `winotify` library. Two functions:

- `notify_success(week_label, bundle_dir, csv_count, png_count)` — long-duration toast with an "Open folder" action button.
- `notify_failure(week_label, error_summary, log_path)` — long-duration toast with an "Open log" action button and the IM audio cue.

Both fall back to `print()` if `winotify` is not installed (helpful for headless CI or non-Windows dev machines).

### `SparkWeeklyContent.xml` — Task Scheduler definition

Task Scheduler v1.4 XML schema. Key fields:

- `<Principal>`: `LogonType=InteractiveToken`, `RunLevel=LeastPrivilege` (runs as the current user without elevation)
- `<Triggers>/<CalendarTrigger>`: weekly on `FR` at `08:30:00` in local TZ, with `StartBoundary` a few days in the past so the first Friday counts
- `<Settings>`: `AllowStartOnDemand=true`, `MultipleInstancesPolicy=IgnoreNew` (subsequent `Start-ScheduledTask` calls while one is running are silently ignored), `WakeToRun=true`, `StartWhenAvailable=true` (fires late if the machine missed the scheduled time)
- `<Actions>/<Exec>`: `Command=powershell.exe`, `Arguments=-ExecutionPolicy Bypass -File "<repo>\tools\generate\run_weekly.ps1"`

The XML is regenerable from PowerShell (`Export-ScheduledTask`) if edits get out of sync.

### `install-task.ps1` / `uninstall-task.ps1`

Idempotent install: `Get-ScheduledTask` to check existence, `Unregister-ScheduledTask` if present, `Register-ScheduledTask -Xml (Get-Content xml -Raw) -Force`. Uses PowerShell-native cmdlets exclusively (NOT `schtasks.exe`) because PS 5.1 wraps native stderr in an ErrorRecord that `2>$null` cannot suppress.

### `reminders/spark-weekly-content.ics` + `reminders/README.md`

A recurring iCalendar event as a backstop reminder. Fires Friday 09:30 local (one hour after the toast) and reminds the operator to check `Downloads\` in case the toast was missed. Import into Google Calendar / Outlook / Apple Calendar; the built-in VALARM triggers the calendar app's own notification.

---

## 6. The playbook: `SKILL.md`

`.claude/skills/spark-weekly-content/SKILL.md` is a Markdown document that combines a Claude Code Skill definition (with a frontmatter block) and a canonical brand playbook. The headless agent that generates captions is instructed to READ this file first before composing anything. It contains, in order:

- **Frontmatter** — `name`, `description` (what triggers this skill), Mode 1/Mode 2 mode information
- **What the skill does** — a plain-language summary
- **How to invoke** — the slash command form and manual invocation forms
- **Agent instructions** — step-by-step for Mode 2 (default, autonomous) and Mode 1 (manual claude.ai fallback)
- **Products** — B2B and B2C URLs, free-trial info, brand parent
- **ICPs** — B2B ideal customer profile (with buyer titles, trigger signals, core pain), B2C audience
- **Voice rules** — corporate-professional + inspirational, no emojis, no exclamation points, NO em-dashes / en-dashes / double-hyphens, contractions spelled out in captions, banned buzzwords, register per audience
- **Two brand systems** — RisePoint Careers colors + typography for Mission Monday; Spark Careers colors + typography for Tue–Fri
- **Five layouts** — Mission / Trade Secrets / Spotlight / Commitment / Feature Friday with a one-line style description each
- **Theme rotation** — Mission Monday's 3-week sub-rotation (mission → problem → origin), Tue–Fri themes, one flex slot per week for reactive content
- **Channel distribution rules** — 9 LinkedIn / 10 Facebook / 5 Instagram = 24 placements, with the rule that B2C Tuesday skips LinkedIn (tactical CV advice fits IG/FB better)
- **Caption formatting per channel** — LinkedIn+Facebook get the tracked URL inline; Instagram ends with "Link in bio: <stripped URL>"
- **UTM tagging convention** — `?utm_source=social&utm_medium=post&utm_campaign=w{NN}-{day}-{audience}`
- **Posting times** — B2B 08:00 MT, B2C 12:00 MT
- **Output bundle structure** — the exact spec the caller expects
- **Operational handoff** — the post-bundle sequence (push → finalize → Buffer), so the agent knows what happens downstream
- **Weekly research pass — MANDATORY** — hard requirement, ≥4 WebSearch calls across 4 axes, ≥5 anchored posts, both Monday posts required, `_research` sidecar with `hooks` and `anchored_posts`
- **Banned topics & sensitive areas** — no US political content, no compassion-free layoff commentary, no race/gender takes beyond acknowledging structural bias, no AI doom/utopia framing, no fake metrics
- **Quality bar before delivery** — a checklist the agent must self-review against

Two copies of `SKILL.md` are maintained:
- **Canonical** — `.claude/skills/spark-weekly-content/SKILL.md` in the public repo (version-controlled)
- **Active** — `~/.claude/skills/spark-weekly-content/SKILL.md` on the operator's home directory (globally discoverable in any Claude Code session)

When editing, edit the canonical copy, then `cp` to the active copy. The pipeline reads from the active copy.

---

## 7. The `captions.json` contract

The single most important interface in the whole system. Everything downstream of caption generation reads this file. Everything upstream produces it.

### Top-level shape

```json
{
  "_research": {
    "performed_at": "2026-06-14T22:50Z",
    "hooks": [
      {"hook": "short description", "source": "https://..."},
      ...
    ],
    "anchored_posts": ["mon-b2b", "mon-b2c", "tue-b2b", ...]
  },
  "captions": [ /* 10 caption objects, in order */ ]
}
```

Legacy bare-array form (10 caption objects at top level) is still accepted by `extract_json_payload` and `run_weekly.py` for backward compatibility with pre-2026-05-31 bundles.

### Per-caption schema

```json
{
  "day": "mon" | "tue" | "wed" | "thu" | "fri",
  "audience": "b2b" | "b2c",
  "theme_tag": "MISSION MONDAY" | "TRADE SECRETS" | "SPOTLIGHT" | "COMMITMENT THURSDAY" | "FEATURE FRIDAY",
  "overline": string,              // "THE INSIGHT" for Tue, "THIS WEEK'S FEATURE" for Fri, empty otherwise
  "badge_number": int | null,       // week number for Tuesday, null otherwise
  "headline": string,               // 8-16 words, sentence case, period at end
  "highlights": [string, ...],      // 1-2 words/phrases from the headline to accent-color
  "subline": string,                // 6-12 words support line, sometimes empty on Trade Secrets
  "url": "hire.risepointcareers.com" | "spark.risepointcareers.com",
  "footer_meta": string,            // e.g. "For employers · Spark Careers Enterprise"
  "caption_linkedin": string,       // full LinkedIn caption, ending with tracked URL inline (empty if skip)
  "caption_facebook": string,       // full Facebook caption, ending with tracked URL inline
  "caption_instagram": string,      // full Instagram caption ending "Link in bio: <stripped URL>" (B2C only)
  "channels": ["linkedin", "facebook", "instagram"]   // subset per distribution rules
}
```

### Ordering invariant

Caption index → (day, audience):
- 0: mon-b2b, 1: mon-b2c
- 2: tue-b2b, 3: tue-b2c
- 4: wed-b2b, 5: wed-b2c
- 6: thu-b2b, 7: thu-b2c
- 8: fri-b2b, 9: fri-b2c

`validate_captions()` enforces this. Deviating breaks the renderer's `render_post_simple(spec, output_path)` loop assumptions.

### Channel distribution invariant

- All 5 B2B posts: `channels = ["linkedin", "facebook"]`
- B2C Mon/Wed/Thu/Fri: `channels = ["linkedin", "facebook", "instagram"]`
- B2C Tue: `channels = ["facebook", "instagram"]` (skip LinkedIn for tactical CV advice)

Result: 9 LI + 10 FB + 5 IG = 24 placements. `caption_instagram` is non-empty iff `"instagram" in channels`.

### Style invariants

Enforced by `validate_captions()`:
- No em-dashes (`—`), en-dashes (`–`), or double-hyphens (`--`) in any string field
- (Contractions are enforced by the prompt, not the validator — a stricter grammar would be a future addition)

Enforced by `validate_research()` as warnings:
- `_research.hooks` has ≥3 entries
- `_research.anchored_posts` has ≥5 entries
- Both `mon-b2b` and `mon-b2c` appear in `_research.anchored_posts`
- Each hook has `hook` and `source` keys

---

## 8. Visual system: brand, templates, typography

### Two brand systems

The bundle uses two visually distinct brand systems that mark audience segmentation at a glance:

**RisePoint Careers brand — Mission Monday only**
- Primary: Cloud Burst `#212D45` (dark navy)
- Accent: Deep Saffron `#FFAB30` (warm orange)
- Motif: bold saffron slab in top-right corner, rising-bars motif bottom-right (echoing the upward-arrow in the RisePoint logo), thin saffron horizontal rule across the footer, split-color "RISEPOINTCAREERS" wordmark

**Spark Careers brand — Tue through Fri**
- Primary: Cadet Blue `#499AA9`
- Accent: Arsenic `#414042` (charcoal)
- Cream `#F5F1E8` for light backgrounds (Feature Friday's top panel)
- Logo: Spark Careers icon + wordmark; on cadet-blue panels the logo uses `filter: brightness(0) invert(1)` to render fully cream

**Typography**: Nexa Bold + Nexa Book preferred (Fontfabric commercial). Fallback is Montserrat Bold + Montserrat Regular loaded from Google Fonts CDN. On offline runs, Chromium falls back to system sans (Segoe UI on Windows).

### Five layouts

Each layout is one HTML file at `templates/<name>.html` plus shared CSS at `templates/css/base.css`.

- `mission_monday.html` (RisePoint) — geometric slab + rising-bars motif + bold statement headline. Saffron accents on highlighted headline words.
- `trade_secrets.html` (Spark) — numbered tactical card. "NO. NN" badge top-left, "TRADE SECRETS" theme tag, "THE INSIGHT" overline, headline + subline, three cadet accent dots bottom-right, Spark logo cream footer.
- `spotlight.html` (Spark) — direct address. Large faded ghost quotation mark top-left, "SPOTLIGHT" theme tag with cadet rule, headline with cadet accent, short cadet rule under headline, subline, Spark cream footer.
- `commitment.html` (Spark) — reflective. "COMMITMENT THURSDAY" theme tag with lead-rule, dot-pattern accent top-right (radial-gradient CSS), headline + subline, mid-bottom short cadet rule, Spark cream footer.
- `feature_friday.html` (Spark) — 55/45 split panel. Cream top (55%) with "FEATURE FRIDAY" cadet tab, "THIS WEEK'S FEATURE" overline, headline; cadet bottom (45%) with "TRY IT NOW" overline, large URL, right-pointing arrow, subline, Spark cream footer.

Highlights are wrapped in `<span class="accent">…</span>` which gets `color: var(--risepoint-saffron)` on Mission Monday and `color: var(--spark-cadet)` on Tue-Fri.

Canvas is 1080×1350 (4:5), fixed via `.canvas { width, height, overflow: hidden }`. Padding is 80px on all sides.

---

## 9. Voice, style rules, validators

The playbook defines the voice; the validator enforces mechanical parts of it.

**Voice** (documented in `SKILL.md`, enforced by prompt, not by validator):
- Corporate-professional with an inspirational undercurrent
- Plain-spoken, not buzzwordy
- Slightly different register per audience: B2B is founder-to-founder / busy operator; B2C is warm and directly-addressed
- Reading level ~grade 9
- Short sentences; sentence fragments OK when intentional
- Banned words: leverage, synergy, game-changer, revolutionary, unleash, supercharge
- No compassion-free framing on layoff topics; the person is not at fault

**Style** (mechanical, validated):
- No em-dashes (`—`)
- No en-dashes (`–`)
- No double-hyphens (`--`) used as long-dash substitutes
- Hyphens inside compound words (`founder-led`, `24-hour`) are fine
- Captions spell out contractions: `do not` / `we have` / `you are` / `it is` / `will not` / `did not` / `I am`
- Possessives (`founder's`, `week's`) stay as-is
- No emojis
- No exclamation points unless quoting

`validate_captions()` in `captions.py` rejects any string field containing em-dash, en-dash, or double-hyphen. Contractions are enforced only in the prompt (a stricter validator would require a whitelist and word-boundary regex; deferred for now).

---

## 10. Channel distribution logic

Nine LinkedIn + ten Facebook + five Instagram = twenty-four placements per week.

**Why 9/10/5:**
- LinkedIn skews B2B. All 5 B2B posts go there. B2C Tuesday (tactical CV advice) skips LinkedIn because it lands better on IG/FB. So LinkedIn = 5 B2B + 4 B2C = 9.
- Facebook is the most general-purpose channel; all 10 posts publish there.
- Instagram is B2C-only in this system (founder ATS content doesn't perform on IG). All 5 B2C posts go there.

**Captions vary per channel:**
- LinkedIn allows long form. B2B think-pieces run 200–500 words, B2C runs 100–250.
- Facebook is condensed: 80–200 words. Same story, tighter.
- Instagram is 80–200 words with the hook in the first 125 characters (before Instagram truncates the caption). Ends with "Link in bio: <stripped URL>" because Instagram strips inline links.

**Posting times** (`posting_time` in Buffer schema):
- B2B: 08:00 local (morning founders before standups)
- B2C: 12:00 local (job seeker lunch-break scrolling)

---

## 11. The mandatory research pass

The single hardest-fought rule in the playbook, and the reason for the object-form `captions.json` schema.

**The problem it solves:** LLM-generated marketing copy is prone to generic, evergreen framing when there's no external anchor. Without deliberate current-data anchors, the same voice produces the same conceptual arguments week after week, drifting further from what's actually happening in the market.

**The rule:** every weekly bundle must include research metadata (`_research.hooks`) proving that the agent did a live web pass and that at least 5 of the 10 captions are anchored to a specific current data point, news event, competitor move, or seasonal moment.

**Enforcement layers:**
1. **Prompt** — the caption-generation prompt states the requirement as a HARD CONSTRAINT, with specific instructions on what search axes to cover and what output shape to emit.
2. **Prompt anti-shoehorn clause** — if a hook does not fit naturally, the agent is told to leave that post evergreen rather than force it. The 5-of-10 floor is the minimum, not a target.
3. **Prompt escape hatch** — if the agent absolutely cannot find 3 usable hooks (rare, quiet news week), it's told to emit `RESEARCH_INSUFFICIENT: <explanation>` on stdout and exit rather than ship an evergreen-only bundle. `extract_json_payload()` detects this string and raises `RuntimeError`.
4. **Validator warnings** — `validate_research()` writes warnings to stderr when hooks < 3, anchored < 5, either Monday missing from `anchored_posts`, or malformed hook entries. These are warnings not errors so a manual override with `--skip-captions` can bypass them.

**The `_research` sidecar** is preserved in `captions.json` so future analysis can audit which posts cite what.

---

## 12. The autonomous trigger — Windows Task Scheduler

The pipeline runs unattended weekly because a Windows Scheduled Task fires it.

**Why Task Scheduler and not cloud cron:**
- No cloud infrastructure to maintain
- No separate API billing for Claude (uses subscription via OAuth)
- Brand assets stay on the operator's local disk
- Fails safely if the machine is off (the operator can manually trigger)

**The task definition** (`SparkWeeklyContent.xml`):
- Path: `\SparkCareers\WeeklyContentBuild`
- Trigger: weekly on Friday at 08:30:00 local time (`America/Edmonton`)
- Wake to run: yes (Windows can wake the machine from sleep)
- Start when available: yes (if the machine was off at the scheduled time, fire when it wakes)
- Multiple instances policy: IgnoreNew (a manual `Start-ScheduledTask` while one is running is silently ignored)
- Principal: `InteractiveToken`, `LeastPrivilege` — runs as the current user without elevation
- Action: `powershell.exe -ExecutionPolicy Bypass -File "<repo>\tools\generate\run_weekly.ps1"`

**Constraint:** the task cannot fire if the laptop is fully powered off. If it's asleep, `WakeToRun` handles it. If it's off (dead battery, shut down), the operator either triggers manually (`Start-ScheduledTask -TaskName WeeklyContentBuild -TaskPath "\SparkCareers\"`) or waits for next Friday and accepts the missed week.

**Install/uninstall** via `install-task.ps1` / `uninstall-task.ps1` — idempotent PowerShell-native cmdlets.

---

## 13. Headless Claude authentication

Long-lived OAuth token in Windows User-scope registry.

**Why OAuth (`CLAUDE_CODE_OAUTH_TOKEN`) instead of Anthropic API key:**
- Uses the operator's existing Claude subscription (Pro/Max/Team) — no separate API billing
- 1-year token lifetime
- Not tied to a session — works headlessly under Task Scheduler where interactive OAuth flows can't happen

**Setup** (one-time): `claude setup-token` — opens a browser, completes OAuth flow, prints a token like `sk-ant-oat01-...`. Operator stores it via `[System.Environment]::SetEnvironmentVariable("CLAUDE_CODE_OAUTH_TOKEN", $token, "User")`.

**Wrapper handling:** Task Scheduler processes sometimes lose User-scope env vars even when the principal is `InteractiveToken`. The wrapper works around this by explicitly reading from the registry hive with `[System.Environment]::GetEnvironmentVariable("CLAUDE_CODE_OAUTH_TOKEN", "User")` at run time, then setting it as a process-scope env var before spawning Python. If missing entirely, the wrapper exits with code 2 and a helpful error in the log.

**Precedence order** for `claude --print` auth (documented behavior of the CLI):
1. Cloud provider envs (Bedrock, Vertex, Foundry)
2. `ANTHROPIC_AUTH_TOKEN`
3. `ANTHROPIC_API_KEY`
4. `apiKeyHelper` script
5. **`CLAUDE_CODE_OAUTH_TOKEN`** (the one we use)
6. Subscription credentials from interactive `/login`

We rely on level 5. Don't set level 2 or 3 in the same environment or Claude will bill through the API instead of the subscription.

---

## 14. GitHub as an image CDN

Buffer needs a publicly-fetchable image URL at post time. GitHub provides one for free.

**Pattern:** push PNGs to a public repo on `main`; Buffer fetches them via `https://raw.githubusercontent.com/<owner>/<repo>/main/<path>`.

**Why this works:**
- `raw.githubusercontent.com` returns the raw file bytes with `Content-Type: image/png`, no auth required for public repos
- GitHub imposes no realistic bandwidth cap for social-post image loading
- Cache-Control is 5 minutes, which is fine — Buffer fetches once at upload preview time and once at publish time
- The repo doubles as a versioned archive of every weekly bundle

**Why NOT a private repo:**
- `raw.githubusercontent.com` on a private repo requires an auth token appended as `?token=...` or an `Authorization` header, neither of which Buffer supports in a CSV row

**Why NOT ImgBB/Imgur/Cloudinary:**
- Requires an API key per operator
- Some hosts add tracking pixels or serve pages instead of raw images
- No versioned history

**Why NOT self-hosting:**
- Adds a droplet, an nginx config, a TLS cert. GitHub is free.

The URL format is a hard contract with the pipeline: `finalize_buffer_csvs.py` hardcodes the pattern in `RAW_URL_BASE`. Change the owner/repo/branch and the finalizer must be updated in lockstep.

---

## 15. Buffer bulk upload

Buffer added bulk CSV upload in August 2025 for paid plans. This system uses it because Buffer's Publishing API is inconsistently available and requires per-app approval that isn't guaranteed on lower plan tiers.

**Buffer's expected CSV schema:**
- `text` — the post caption
- `image_url` — one publicly-fetchable URL per row (Buffer fetches at upload preview time and again at publish time)
- `tags` — optional tags column (Buffer's internal categorization; we leave it empty)
- `posting_time` — combined datetime in `YYYY-MM-DD HH:MM` format, interpreted in the channel's configured Buffer timezone

Buffer's own downloadable CSV template has these four columns in lowercase with underscore-separated names. That's what `finalize_buffer_csvs.py` produces. Column order is not strict (Buffer parses by header name).

**Upload flow (per channel):**
1. Buffer web UI → Publish tab → click channel in left sidebar
2. Gear icon (⚙) next to channel name → General → Bulk Upload
3. Drag `.csv` into drop zone
4. Buffer previews each row with the image inline; operator confirms
5. Buffer schedules every row at its `posting_time`

**Cap:** 100 posts per upload. We send 5–10 per channel per week, comfortably under.

---

## 16. Failure modes and diagnosis

Every stage in the pipeline logs to `runs/<week>.log` (Python orchestrator) and `runs/wrapper-<timestamp>.log` (PowerShell wrapper). Failure at any stage triggers `notify_failure()` which pops a toast with an "Open log" button.

| Symptom | Likely cause | Where to look | Fix |
|---|---|---|---|
| No toast, no bundle | Task Scheduler didn't fire (laptop off/asleep) OR wrapper crashed before Python | `runs/wrapper-<timestamp>.log` (most recent) | Manual trigger with `Start-ScheduledTask` |
| Wrapper log: `CLAUDE_CODE_OAUTH_TOKEN is not set` | Token wasn't stored, or was set at Machine scope instead of User | Windows registry: `HKCU\Environment\CLAUDE_CODE_OAUTH_TOKEN` | Re-run `claude setup-token`, set with `SetEnvironmentVariable(name, token, "User")` |
| Wrapper log: `parameter cannot be found: 'Encoding'` | Old wrapper with `Tee-Object -Encoding` on PS 5.1 | Wrapper source | Replace `Tee-Object -Encoding` with the StreamWriter pattern |
| Python log: `RuntimeError: claude --print exited 1` + `Invalid authentication credentials` | OAuth token was rejected (expired, revoked, or bad copy) | Test `claude --print --no-session-persistence "ping"` from a fresh PowerShell | Re-run `claude setup-token`, re-set env var |
| Python log: `JSONDecodeError: Expecting property name…` | Headless Claude produced malformed JSON | Look at stdout capture in the log | Retry `Start-ScheduledTask`. If persistent: tighten the schema instruction in `build_caption_prompt()` |
| Python log: `RESEARCH_INSUFFICIENT: …` | Agent decided the research pass turned up nothing usable | Log message | Manual re-run with `--research "<hooks>"` providing anchors, or accept an evergreen week and re-run without the check |
| `validate_captions` raises: forbidden dash | Agent slipped an em-dash past the prompt rules | Log line | Retry. The prompt is explicit, so a retry usually works |
| `validate_research` warning: only N anchored | Agent didn't hit the 5-of-10 floor | Log line | Retry, or ship as-is if the anchored posts are strong |
| Toast fires but Buffer preview shows broken images | Git push hadn't propagated to raw.githubusercontent.com when the finalizer ran | `curl -I <raw-url>` — if 404, wait 30 seconds and re-run the finalizer with `--skip-captions --skip-push` semantics (i.e., re-run only the finalize step) | |
| Buffer bulk-upload dialog: "Missing column: posting_time" | Old-schema CSV (Date+Time separate) uploaded instead of `-final.csv` | Check which file was uploaded | Upload the `-final.csv` not the source |
| Buffer bulk-upload: images upload but text is truncated at newlines | CSV wasn't quoted properly | Open the `.csv` in a text editor; every field should be double-quoted | Verify `csv.QUOTE_ALL` is set in `csv_writer.py` |

**Retry strategy:** the pipeline is idempotent per week. Running it twice for the same week overwrites the PNGs and captions.json in the repo (and produces a new git commit) but doesn't corrupt anything. The finalizer overwrites `-final.csv` files.

---

## 17. Repository layout

```
social-assets/
├── .claude/
│   └── skills/
│       └── spark-weekly-content/
│           └── SKILL.md             # canonical playbook (version-controlled)
├── 2026/
│   ├── W22/                          # weekly bundle (10 PNGs + captions.json)
│   ├── W23/
│   ├── W25/                          # W24 was missed; the lead-time logic skipped it
│   ├── W26/
│   ├── W27/
│   ├── W28/
│   ├── W29/
│   └── W30/
├── prompts/                          # Mode 1 fallback prompts (deprecated)
│   └── README.md
├── reminders/
│   ├── spark-weekly-content.ics      # recurring backstop calendar reminder
│   └── README.md                     # install instructions per calendar app
├── runs/                             # local only; gitignored
│   ├── 2026-W{NN}.log                # Python orchestrator log per week
│   └── wrapper-<timestamp>.log       # PS wrapper log per run
├── tools/
│   ├── finalize_buffer_csvs.py       # placeholder URL → raw URL + schema rewrite
│   └── generate/
│       ├── captions.py               # headless Claude subprocess + validators
│       ├── renderer.py               # Playwright HTML → PNG
│       ├── docx_writer.py            # python-docx review doc
│       ├── csv_writer.py             # 3 source CSVs (source schema)
│       ├── run_weekly.py             # Python orchestrator (main entry)
│       ├── run_weekly.ps1            # PowerShell wrapper (Task Scheduler entry)
│       ├── notify.py                 # winotify toast helpers
│       ├── install-task.ps1          # register scheduled task
│       ├── uninstall-task.ps1
│       ├── SparkWeeklyContent.xml    # task definition (v1.4 XML)
│       └── templates/
│           ├── css/
│           │   └── base.css          # shared brand colors + typography
│           ├── mission_monday.html   # RisePoint layout, Mon
│           ├── trade_secrets.html    # Spark layout, Tue
│           ├── spotlight.html        # Spark layout, Wed
│           ├── commitment.html       # Spark layout, Thu
│           ├── feature_friday.html   # Spark layout, Fri
│           └── assets/               # logo PNGs used by templates
│               ├── risepoint-logo-light.png
│               ├── spark-logo.png
│               └── spark-logo.svg
├── HANDOFF.md                        # this document
└── README.md                         # repo intro
```

`.gitignore` covers `runs/`, `*.pyc`, `__pycache__/`, `_test_renders/`, `_render_*.html`, `.venv/`.

---

## 18. Extension points — porting to another brand

If another organization wants to run this system for their own brand, here's what changes and what stays.

### Rewrite (brand-specific)

- `.claude/skills/<brand>-weekly-content/SKILL.md` — the entire playbook: products, ICPs, voice, brand colors, layouts, channel distribution, UTM naming, banned topics
- `tools/generate/templates/*.html` + `templates/css/base.css` — five HTML layouts and the shared CSS, themed to the new brand
- `tools/generate/templates/assets/` — brand logos
- `captions.py` `build_caption_prompt()` — the URLs, style rules, theme tags, channel distribution, footer meta strings, path to the SKILL.md

### Reconfigure (constants at file top)

- `finalize_buffer_csvs.py` — `REPO_OWNER`, `REPO_NAME`, `BRANCH` at the top
- `run_weekly.ps1` — `$RepoRoot`
- `SparkWeeklyContent.xml` — task name/path, action command paths, trigger time
- `install-task.ps1` — task name/path constants
- `notify.py` — `app_id` string

### Copy verbatim (generic pipeline machinery)

- `renderer.py` — template-agnostic; picks templates by weekday
- `docx_writer.py` — schema-agnostic writer
- `csv_writer.py` — schema-agnostic writer
- `run_weekly.py` — orchestrator logic
- `install-task.ps1` / `uninstall-task.ps1` structure

### Redesign per brand

- Number of weekday themes (5 in Spark's case; could be 3 or 7)
- Number of audience segments (Spark has 2; single-audience brands halve everything)
- Number of channels (Spark has 3; add more, or drop Instagram)
- Weekly cadence (Spark posts twice per day; some brands would post once)

Each of those changes cascades through the whole pipeline. The Spark implementation is a good reference for the 5-day / 2-audience / 3-channel shape; other shapes need proportional edits everywhere.

---

## 19. Setup guide (condensed)

For a fresh install on a Windows laptop. Assumes Python 3.11+, git, and `gh` CLI already installed and authenticated.

**One-time (about 45 min for first install):**

1. **Fork or copy the repo.** `gh repo create <org>/<slug> --public`, clone locally.
2. **Copy the pipeline files** from `Spark-Careers/social-assets` (`tools/`, `templates/`, `install-task.ps1`, `SparkWeeklyContent.xml`). Skip `2026/`, `runs/`, `prompts/`, Spark-specific `.claude/skills/`.
3. **Write your own SKILL.md.** Base on Spark's; replace products, ICPs, brand systems, voice rules, channel distribution, URLs, UTM pattern, research checklist. Copy to `~/.claude/skills/<brand>-weekly-content/SKILL.md` for global discovery.
4. **Customize templates.** Rewrite `templates/css/base.css` with your brand colors, replace logo assets, rewrite the five HTML templates to reference your typography and wordmarks.
5. **Update constants.** `finalize_buffer_csvs.py` REPO_OWNER/NAME, `run_weekly.ps1` $RepoRoot, `SparkWeeklyContent.xml` paths, `captions.py` URLs + style rules + SKILL.md path.
6. **Install Python deps.** `pip install playwright python-docx winotify pillow`, then `python -m playwright install chromium`.
7. **Generate the OAuth token.** `claude setup-token`, then `[System.Environment]::SetEnvironmentVariable("CLAUDE_CODE_OAUTH_TOKEN", $token, "User")`. Verify in a fresh PowerShell with `claude --print --no-session-persistence "ping"`.
8. **Register the scheduled task.** `powershell -ExecutionPolicy Bypass -File tools\generate\install-task.ps1`.
9. **Test the pipeline manually.** `Start-ScheduledTask -TaskName WeeklyContentBuild -TaskPath "\<YourOrg>\"`. Watch `runs\2026-W{NN}.log`. Expect toast in 3–5 min.
10. **Import the calendar backstop.** Load `reminders/<brand>-weekly-content.ics` into your calendar app.

**Ongoing (every Friday, 5 min):** open `Downloads\<brand>-w{NN}-buffer\`, upload three CSVs to Buffer.

---

## 20. Design decisions and tradeoffs

The choices worth calling out.

**Playwright + HTML, not Pillow.** Text layout with Pillow is coordinate math; iterating on a design costs an hour per tweak. Playwright renders CSS, so the design cycle is instant, brand-quality typography works out of the box, and multi-line highlight wrapping is a `<span>` instead of a manual line-break loop. Tradeoff: ships Chromium (200 MB install).

**GitHub raw CDN, not ImgBB.** Free, versioned, no API keys, doubles as a public archive. Tradeoff: requires a public repo.

**Buffer bulk CSV, not Buffer API.** API access requires manual per-app approval on lower plan tiers and isn't guaranteed. Bulk CSV is on paid plans (which the operator already has) and is stable. Tradeoff: the "upload three files" step stays manual forever unless Buffer's API story stabilizes.

**Headless Claude via subscription OAuth, not Anthropic API.** Uses existing subscription quota (roughly $0 extra per week vs $0.50–$2 per week for API billing). Tradeoff: one manual OAuth flow every 12 months when the token expires.

**Windows Task Scheduler, not cloud cron.** No cloud infrastructure. Uses existing laptop. Free. Tradeoff: fails silently if laptop is off. Operators who travel need a mental backstop.

**PowerShell 5.1 support.** The wrapper doesn't require PS 7. This means using `StreamWriter` instead of `Tee-Object -Encoding`, and `Get-ScheduledTask` instead of `schtasks.exe`. Verbose but universal.

**Mandatory research pass, not optional.** Optional language ("should briefly check", "skip if nothing useful") became a permission to skip. Making it mandatory + gating output on it forces the agent to do the work. The anti-shoehorn clause and `RESEARCH_INSUFFICIENT` escape hatch prevent forced-fit output.

**Object-form `captions.json` with `_research` sidecar, not bare list.** Backward-compatible via `extract_json_payload()` accepting both forms. The sidecar preserves an audit trail of which posts cite what.

**Warnings, not errors, for missing research.** Warnings surface in the wrapper log without halting shipping. This gives the operator a manual override path in emergencies. Tradeoff: silent bundles that pass validators are still possible.

**Five discrete layouts, not one flexible template.** Each layout is optimized for its weekday theme. A single flexible template would be more maintainable but would look homogeneous across the week. Five distinct visual identities create rhythm.

**Deterministic weekly rhythm, not reactive publishing.** The playbook reserves one "flex slot" per week for reactive content but the default is planned batches a week in advance. This is a marketing discipline choice, not a technical constraint.

---

## 21. Known gaps and roadmap

Real gaps in the current system, in rough priority order.

**Autonomous run reliability.** Historical pattern: about 1 in 3 autonomous runs fails at the JSON parse or timeout step. The Jul 3 and Jul 10 runs both crashed. Manual retries usually work. The intermittent nature suggests the caption prompt is producing slightly-different output shapes across runs — a stricter output-shape enforcement (JSON Schema validation via `--json-schema` flag on `claude --print`?) could help.

**No visibility into whether the operator actually uploaded to Buffer.** The pipeline drops a bundle in Downloads and pops a toast, then loses track. If the operator forgot, posts don't go out that week and the pipeline doesn't know. A future enhancement could query Buffer's API just for a "posts scheduled this week?" check.

**No engagement feedback loop.** Buffer records which posts got clicks. Nothing in the pipeline reads that data. A quarterly analysis pass — pull Buffer analytics, correlate against the caption UTM tags, feed the top-performing hooks back into the SKILL.md — would meaningfully improve subsequent weeks.

**Nexa fonts still missing.** The playbook specifies Nexa Bold + Nexa Book as brand typography. We use Montserrat as fallback everywhere. Adding the actual Nexa TTF files to `templates/assets/fonts/` and referencing them via `@font-face` in `base.css` would close the gap.

**No dry-run preview before push.** The pipeline generates, pushes to git, THEN the operator sees the toast. A `--preview-first` mode that stops after rendering and asks for confirmation before pushing would be safer for weeks with sensitive topics.

**Buffer's Publishing API is unused.** If Buffer's API access ever stabilizes, replacing bulk-CSV upload with direct API scheduling would remove the last manual step. The pipeline could then be fully unattended end to end (with the operator's approval flow moved to a preview step, per the previous item).

**Contractions rule is not validator-enforced.** The style rule "spell out contractions in captions" is in the prompt but there's no `validate_captions()` check for `don't`, `can't`, `it's`, etc. A whitelist of allowed forms would need to accommodate legitimate uses (proper nouns, quoted material, possessives). Deferred.

**Ports to non-Spark brands need a scaffold.** Right now, extending to another brand is a copy-paste-and-edit exercise across ~15 files. A `create-new-brand-install.py` scaffold that takes a config JSON and stamps out the customized files would make the porting story a one-command affair.

---

*This document describes the system as of 2026-07-12. The reference implementation is at https://github.com/Spark-Careers/social-assets — check `main` for the current state before quoting file paths or line numbers.*
