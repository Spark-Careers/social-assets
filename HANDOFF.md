# Drop-in setup: weekly autonomous social-content engine

This document is a self-contained guide that lets another organization replicate the weekly social-content pipeline used by Spark Careers / RisePoint Careers. Read Part 1 to understand what you get. Copy Part 2 verbatim into a fresh Claude Code session on the target org's Windows machine — Claude Code will walk the user through the setup end to end.

---

## Part 1 — What this engine actually does

**Every Friday at 08:30 local time**, a Windows scheduled task fires on the operator's laptop. It invokes a Python orchestrator that:

1. **Does a research pass** — the orchestrator spawns a headless `claude --print` subprocess that runs at least four WebSearch calls (current job-market headlines, ATS/AI-in-hiring news, B2B competitor watch, B2C competitor watch — or the equivalent axes for your industry) and identifies 3–5 concrete hooks with source URLs.
2. **Writes 10 captions** — one B2B + one B2C caption per weekday. Each caption object has a headline, subline, and full LinkedIn / Facebook / Instagram copy. At least 5 of the 10 must be anchored to a hook from step 1, including both Monday posts. Style rules (no em-dashes, no contractions in captions, no emojis) are enforced by validators.
3. **Renders 10 brand-styled PNGs** at 1080×1350 using Playwright + headless Chromium against 5 HTML layout templates (one per weekday). Highlighted key words get an accent color, brand logos and footers are baked in.
4. **Writes a review DOCX** and 3 channel CSVs (LinkedIn / Facebook / Instagram) in Buffer's bulk-upload schema.
5. **Pushes the PNGs to a public GitHub repo** so Buffer can fetch them at post time via `raw.githubusercontent.com/<org>/<repo>/main/YYYY/Wnn/<file>.png`.
6. **Runs a finalizer** that swaps placeholder image URLs for the real raw URLs and produces `-final.csv` files ready for Buffer's bulk upload.
7. **Pops a Windows toast notification** telling the operator that `Downloads\<brand>-w{NN}-buffer\` is ready.
8. The operator opens Buffer, does 3 bulk uploads (one per channel, ~3 minutes), and posts publish automatically on the schedule baked into the CSVs.

**What the operator does per week:** upload 3 CSVs to Buffer. That's it.

**What the pipeline does NOT do:** interact with Buffer's API, post directly to social networks, do image editing beyond template rendering. Buffer handles the actual scheduling and posting; the pipeline just prepares the input.

---

## Part 2 — Paste this into a fresh Claude Code session

Everything below the `================` line is a self-contained prompt. The operator opens Claude Code on the Windows machine that will host the pipeline, pastes this prompt as their first message, and Claude Code walks them through setup. It will ask clarifying questions about the operator's brand and installations.

================================================================

I want to set up an autonomous weekly social-content pipeline on this Windows machine, based on the engine documented at https://github.com/Spark-Careers/social-assets. Please walk me through the setup end to end. Ask me clarifying questions where you need answers, do not guess.

**What we are building**

Every Friday at 08:30 local time, a Windows scheduled task fires. It runs a Python orchestrator that generates 10 social posts for next week (5 B2B + 5 B2C, one pair per weekday), renders 10 brand PNGs, writes a review DOCX, produces 3 Buffer-native CSVs, pushes PNGs to a public GitHub repo, and pops a Windows toast when the bundle is ready in `Downloads\`. My only weekly job is to bulk-upload the 3 CSVs to Buffer.

**Environment I already have**

- Windows 11 laptop (this machine)
- Python 3.11+ installed and on PATH
- Git installed
- GitHub CLI (`gh`) installed and authenticated to my organization
- A Claude Code subscription (Pro / Max / Team) — will use `claude setup-token` for headless auth
- A Buffer account with LinkedIn, Facebook, and Instagram channels connected

**Environment I need you to help me set up**

- A new public GitHub repo under my org for hosting weekly PNG assets
- A local Python virtual environment with Playwright + python-docx + winotify + Pillow
- A brand-customized `.claude/skills/weekly-content/SKILL.md` playbook
- 5 HTML layout templates (Mon/Tue/Wed/Thu/Fri) themed to my brand
- The Python orchestrator + PowerShell wrapper + Windows scheduled task
- A recurring calendar reminder as a backstop

**Step-by-step plan I want you to execute**

**STEP 1 — Ask me what my brand is.**

Before writing any code, ask me for:
- Brand name and short description
- Primary brand color (hex)
- Accent brand color (hex)
- Font (with a free Google Fonts fallback if the brand font is licensed)
- Logo file(s) — I will provide the path
- Product URLs (B2B destination URL, B2C destination URL if applicable, or one URL if single audience)
- Audience segments: single audience (post once per weekday, 5 posts/week) or two audiences (post B2B + B2C per weekday, 10 posts/week)
- Buffer channels connected (LinkedIn, Facebook, Instagram, other)
- Weekday theme names (default: Mission Monday / Trade Secrets Tuesday / Spotlight Wednesday / Commitment Thursday / Feature Friday — I can rename)
- Voice rules (formal vs conversational, contraction handling, banned words)
- Weekly research axes (default: job market + ATS + competitors; other industries may want different axes)
- ISO week the pipeline should first target (default: 10 days out, so the first Friday delivery is 10 days ahead)
- Local time zone (default: America/Edmonton — matches the Spark install)

Confirm my answers back to me before proceeding.

**STEP 2 — Create the public GitHub repo.**

Run `gh repo create <org>/<repo-slug> --public --description "Public CDN for weekly social-post visuals. Buffer fetches PNGs from raw.githubusercontent.com URLs."`. Slug like `social-assets` is fine. Clone it locally to `C:\Users\<username>\Marketing\<repo-slug>\`.

**STEP 3 — Clone the reference engine.**

Clone https://github.com/Spark-Careers/social-assets into a scratch directory. Copy the following files into my new repo, preserving structure:

- `tools/generate/renderer.py`
- `tools/generate/captions.py`
- `tools/generate/docx_writer.py`
- `tools/generate/csv_writer.py`
- `tools/generate/run_weekly.py`
- `tools/generate/notify.py`
- `tools/generate/run_weekly.ps1`
- `tools/generate/install-task.ps1`
- `tools/generate/uninstall-task.ps1`
- `tools/generate/SparkWeeklyContent.xml`   (rename the task inside this XML to match my brand)
- `tools/finalize_buffer_csvs.py`
- `tools/generate/templates/css/base.css`
- `tools/generate/templates/*.html` (5 templates)

Do NOT copy `2026/`, `.claude/skills/`, `prompts/`, or `runs/` — those are Spark-specific.

**STEP 4 — Customize the templates for my brand.**

Rewrite `tools/generate/templates/css/base.css` with my brand colors. Update the 5 HTML layout templates to reference my brand-specific assets:

- Replace `--risepoint-navy` / `--risepoint-saffron` with my primary/accent color variables
- Replace the wordmark text ("RISEPOINT / CAREERS") with my brand wordmark or logo image
- Replace the Spark Careers logo in Tue-Fri templates with mine
- Update the footer meta text lines to reference my product tagline

Copy my logo file(s) into `tools/generate/templates/assets/`.

**STEP 5 — Write my `.claude/skills/weekly-content/SKILL.md`.**

Create `.claude/skills/weekly-content/SKILL.md` with my customized playbook. Base it on https://github.com/Spark-Careers/social-assets/blob/main/.claude/skills/spark-weekly-content/SKILL.md but replace:

- Products section (my brand's products + URLs)
- ICPs section (my audience descriptions)
- Voice rules (my tone + banned words)
- Brand systems (my colors + typography)
- Channel distribution (my Buffer channel counts)
- UTM tagging (my campaign naming convention)
- Posting times (my local time zone)
- Research checklist axes (customize for my industry)

Copy this file to `~/.claude/skills/weekly-content/SKILL.md` so it's discoverable in future Claude Code sessions.

**STEP 6 — Adjust `captions.py` prompt.**

Open `tools/generate/captions.py` and update `build_caption_prompt()`:
- URLs (my B2B / B2C URLs)
- Style rules (my voice)
- Theme tags (my weekday themes)
- Channel distribution rules (my channel counts)
- Footer meta strings (my brand tagline)
- Path to my SKILL.md (line near the top)

**STEP 7 — Install Python deps.**

```powershell
cd C:\Users\<username>\Marketing\<repo-slug>
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install playwright python-docx winotify pillow
python -m playwright install chromium
```

Confirm with `python -c "from playwright.sync_api import sync_playwright; print('ok')"`.

**STEP 8 — Generate the Claude OAuth token.**

Explain to me: this token authorizes headless `claude --print` calls from the scheduled task without a browser popup. It uses my Claude subscription (no separate API billing).

Have me run:

```powershell
claude setup-token
```

An interactive browser flow opens. After I complete it, a token like `sk-ant-oat01-...` prints to the terminal. Have me paste it into a variable, then store it in the Windows User registry:

```powershell
$token = "<paste-token-here>"
[System.Environment]::SetEnvironmentVariable("CLAUDE_CODE_OAUTH_TOKEN", $token, "User")
```

Verify from a NEW PowerShell window:

```powershell
[System.Environment]::GetEnvironmentVariable("CLAUDE_CODE_OAUTH_TOKEN", "User")
claude --print --no-session-persistence "reply with only the word ping"
```

If it prints "ping", auth is working.

**STEP 9 — Edit `run_weekly.ps1` for my paths.**

Update `$RepoRoot` at the top to my repo path.

**STEP 10 — Edit the scheduled-task XML.**

Open `tools/generate/SparkWeeklyContent.xml`, rename it to `<MyBrand>WeeklyContent.xml`, update:
- The task name inside `<URI>\<MyOrg>\WeeklyContentBuild</URI>`
- The command paths in `<Actions>`
- The trigger time if I want anything other than Friday 08:30 local

**STEP 11 — Register the scheduled task.**

Update `install-task.ps1` with my task name and path. Then:

```powershell
powershell -ExecutionPolicy Bypass -File tools\generate\install-task.ps1
```

Verify:

```powershell
Get-ScheduledTask -TaskName "WeeklyContentBuild" -TaskPath "\<MyOrg>\"
```

**STEP 12 — First test run.**

Kick off a manual run to prove the pipeline end-to-end BEFORE waiting for Friday:

```powershell
Start-ScheduledTask -TaskName "WeeklyContentBuild" -TaskPath "\<MyOrg>\"
Get-Content "runs\2026-W<NN>.log" -Wait -Tail 50
```

Expected progression:
- `[captions] invoking claude --print for 2026-W<NN>…`
- `[captions] wrote 2026/W<NN>/captions.json`
- `[render] rendering 10 PNGs`
- `[docx] wrote spark-w<NN>-content-calendar.docx`
- `[csv] spark-w<NN>-buffer-linkedin.csv: 9 rows`
- `[git] commit / push`
- `[finalize] running finalize_buffer_csvs.py`
- `[done] 10 PNGs in repo, 3 final CSVs in <bundle-path>`

Windows toast pops with "bundle ready". If any step fails, walk me through the log.

**STEP 13 — Set up the calendar backstop reminder.**

Copy `reminders/spark-weekly-content.ics` to `reminders/<my-brand>-weekly-content.ics`, edit the SUMMARY, DESCRIPTION, and UID for my brand, then have me import it into my calendar (Google / Outlook / Apple).

**STEP 14 — Handoff document.**

Write a short `RUNBOOK.md` I can share with anyone else on my team who needs to know how to babysit this pipeline: where things live, what the weekly rhythm is, how to trigger a manual run, and where to look when something breaks.

**Rules of engagement**

- Ask me for missing information rather than guessing.
- Batch questions (2-4 at a time) rather than one-at-a-time.
- If a step fails, show me the exact error and propose a fix, do not silently retry.
- Do not push anything to GitHub until Step 11 is complete and I have confirmed the test run works.
- Do not enable the scheduled task's autonomous fire until Step 12 succeeds.
- Save your progress in your task list so we can resume across sessions if needed.

Let's start with Step 1: what is my brand?

================================================================

## Part 3 — Cost estimate

**Claude Code subscription costs** — nothing extra. The OAuth token consumes the operator's existing subscription quota. A typical weekly run uses roughly one to two minutes of headless-Claude time (the research + composition step), well within any subscription tier.

**GitHub costs** — nothing. Public repos are free, and `raw.githubusercontent.com` has no bandwidth cap for reasonable use.

**Buffer costs** — whatever the operator's Buffer plan is. Bulk upload is available on Buffer's paid plans as of August 2025.

**Local machine requirements** — must be on and awake at Friday 08:30 local for the autonomous run to fire. The scheduled task is configured to wake the machine if it's asleep, but not if it's off. Operators who travel should either run manually via `Start-ScheduledTask` when they return, or consider a cloud cron alternative (out of scope of this handoff).

## Part 4 — Weekly operating rhythm (once installed)

- **Friday 08:30 local** — scheduled task fires, generates next week's bundle
- **Friday ~08:35 local** — Windows toast pops on operator's screen
- **Friday sometime before end of day** — operator opens `Downloads\<brand>-w<NN>-buffer\`, reviews the DOCX if desired, opens Buffer, bulk-uploads 3 CSVs (one per channel)
- **Following Monday 08:00 local** — first post of the new week publishes
- **Following Friday** — new autonomous run fires, cycle repeats

Total weekly operator time after setup: ~5 minutes.

## Part 5 — Known failure modes

| Symptom | Likely cause | Fix |
|---|---|---|
| Toast never fires | Scheduled task didn't run OR wrapper crashed silently | Check `runs\wrapper-<timestamp>.log` |
| Wrapper log says `CLAUDE_CODE_OAUTH_TOKEN is not set` | Token was set for wrong user scope or expired | Re-run `claude setup-token`, re-`SetEnvironmentVariable` at User scope, verify from a fresh shell |
| `RESEARCH_INSUFFICIENT` in log | Headless Claude couldn't find 3+ usable hooks | Rare. Manual run with `--research "…"` providing hooks |
| `JSONDecodeError` in log | Claude returned malformed JSON | Known intermittent failure. Retry `Start-ScheduledTask` manually — the caption prompt is deterministic-ish and usually parses on second attempt |
| Buffer bulk upload rejects CSV | Column names don't match Buffer's expected schema | Buffer expects lowercase `text, image_url, tags, posting_time`. The finalizer produces this format; if you edited it, verify it still does |
| PNG shows in Buffer preview as broken image | The GitHub push didn't complete before the finalizer ran, OR the URL 404s | Verify with `curl -I <raw-url>`. Retry with `--skip-captions` to reuse captions.json but re-do push + finalize |

## Part 6 — Repository layout

For reference, this is what the working install looks like:

```
<repo>/
├── .claude/
│   └── skills/
│       └── weekly-content/
│           └── SKILL.md           # playbook, canonical version
├── 2026/
│   ├── W22/                        # weekly PNGs, one folder per ISO week
│   ├── W23/
│   └── ...                         # each folder: 10 PNGs + captions.json
├── prompts/                        # optional; Mode 1 fallback prompts
├── reminders/
│   ├── <brand>-weekly-content.ics
│   └── README.md
├── runs/                           # local only, gitignored
│   ├── 2026-W<NN>.log             # orchestrator log per week
│   └── wrapper-<timestamp>.log    # scheduled-task wrapper log per run
├── tools/
│   ├── finalize_buffer_csvs.py    # placeholder URL -> raw URL + schema rewrite
│   └── generate/
│       ├── captions.py             # invokes headless claude, produces captions.json
│       ├── renderer.py             # Playwright HTML -> PNG
│       ├── docx_writer.py          # python-docx review doc
│       ├── csv_writer.py           # 3 channel CSVs
│       ├── run_weekly.py           # Python orchestrator
│       ├── run_weekly.ps1          # PowerShell wrapper (Task Scheduler entry point)
│       ├── notify.py               # winotify toast
│       ├── install-task.ps1        # register scheduled task
│       ├── uninstall-task.ps1
│       ├── SparkWeeklyContent.xml  # task definition
│       └── templates/
│           ├── css/base.css
│           ├── mission_monday.html
│           ├── trade_secrets.html
│           ├── spotlight.html
│           ├── commitment.html
│           ├── feature_friday.html
│           └── assets/             # logo PNGs / SVGs
├── HANDOFF.md                      # this document
└── README.md
```

## Part 7 — What to fork vs write from scratch

**Fork (copy verbatim, edit constants):** the Python tooling in `tools/generate/`, the finalizer, the wrapper scripts, the task XML.

**Rewrite (brand-specific):** the SKILL.md playbook, the HTML templates, the base.css, the brand assets in `templates/assets/`, the captions.py prompt text.

**Skip (Spark-specific, not needed):** the `2026/` weekly folders (start fresh), the `prompts/` folder if you're going straight to Mode 2 autonomous, any Spark-specific memory/notes.

---

*Last updated: 2026-07-12. This document describes the Spark Careers install as of that date. The reference engine at Spark-Careers/social-assets may have moved on since; verify the file list in Part 6 against `main` before starting.*
