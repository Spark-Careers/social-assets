---
name: spark-weekly-content
description: Generate the weekly Spark Careers / RisePoint Careers social-post bundle (docx review doc, 3 channel CSVs, 10 brand-styled PNGs). Triggers when user asks for a weekly content batch, week N posts, Spark social calendar, RisePoint weekly bundle, or invokes `/spark-weekly-content`. Output matches the Week 22 baseline exactly so style never drifts. Mode 1 (current default) produces a self-contained prompt for claude.ai; Mode 2 (future) will produce the bundle natively in Claude Code.
---

# Spark Careers Weekly Content — Skill

## What this skill does

Produces (or in Mode 1, produces the prompt to produce) the weekly content bundle for Spark Careers / RisePoint Careers across LinkedIn, Facebook, and Instagram. One bundle = one ISO week, Mon–Fri, two audiences (B2B + B2C), 24 scheduled placements.

## Modes

This skill currently runs in **Mode 1**. Mode 2 is a planned upgrade.

- **Mode 1 — claude.ai relay (default until ~2026-W25):** Skill calculates the week's date range, embeds the full playbook below, and writes a self-contained prompt to `<social-assets-repo>/prompts/<week>-prompt.md`. The user opens claude.ai, pastes the prompt, attaches the brand-guide PDFs, and receives the bundle as a downloadable zip. We use claude.ai for now because brand-quality PNG generation isn't yet wired up in Claude Code.
- **Mode 2 — Claude Code native (future):** After the Phase 3 visual-generation pipeline is built (Python + Pillow or HTML + Playwright templates), this skill will produce the full bundle locally without claude.ai. Defer until 3 consecutive weeks of Mode 1 output have been reviewed and the style is locked.

## How to invoke

```
/spark-weekly-content 2026-W23
```

If the week argument is missing, default to the ISO week starting the next Monday after today.

## Step-by-step for the agent (Mode 1)

1. **Parse the week.** Compute Monday and Friday of the given ISO week. Verify the week is in the future or current — refuse to generate for a past week unless the user explicitly confirms.
2. **Optionally do a research pass.** Use WebSearch to scan headlines from the past 7 days on: SMB hiring trends, US/Canada job market reports, layoffs/hiring waves at big tech, ATS news, AI-in-resumes news, career-change discourse. Pick 2–3 hooks worth referencing in captions. Skip if the user says "skip research" or if the session is offline.
3. **Compose the prompt.** Use the template at the bottom of this file (`PROMPT_TEMPLATE`). Fill placeholders with the week's specifics (dates, week label, current rotation lens for Mission Monday, research hooks if any).
4. **Save the prompt** to `<repo-root>/prompts/<week>-prompt.md`. Repo root is the local clone of `Spark-Careers/social-assets` — check the memory file `social-buffer-workflow.md` for the path (typically `IdleSpark/Marketing/social-assets/`).
5. **Tell the user** the prompt is ready, what to do with it, and what to do after the bundle arrives. Include the exact post-arrival sequence (push PNGs to repo → run finalize script → bulk-upload CSVs to Buffer).

## Step-by-step for the agent (Mode 2 — placeholder until built)

> Not yet implemented. When implemented, this section will describe: load brand assets from `IdleSpark/Branding Files/`, instantiate the 5 layout templates, render PNGs, generate captions per the playbook, write docx via the docx skill, write CSVs via the finalize script, push to GitHub. Until then, fall back to Mode 1.

---

## THE PLAYBOOK (this is the canonical recipe)

### Products

| Product | Audience | URL | Free trial |
|---|---|---|---|
| Spark Careers (B2C) | Job seekers — resume/ATS optimization, CV rewrites | `spark.stepupcareers.com` (migrating to `spark.risepointcareers.com`) | n/a, freemium |
| Spark Careers Enterprise (B2B) | 0–20 person founder-led SMBs needing a lightweight ATS | `hire.risepointcareers.com` | 7-day free trial |

Parent: **RisePoint Careers Corp.** Marketing site: `risepointcareers.com`.

### ICPs

**B2C:** No geographic or vertical focus yet — every market is fair game. Audience spans entry-level, mid-career, career-changers. Tone: warm, plain-spoken, slightly coachy.

**B2B:** Founder-led, 0–20 person startups/small businesses actively hiring but managing recruitment manually through email/spreadsheets/LinkedIn DMs/Google Forms/WhatsApp. Buyer titles: Founder, CEO, Owner, Operations Manager, Office Manager, Practice Manager, Clinic Manager, HR Manager (if they have one). Best segments: founder-led startups (SaaS, marketplace, AI), small service businesses (agencies, consulting), undigitized local businesses (clinics, trades, restaurants), small recruitment-heavy teams (staffing, field service). Tone: founder-to-founder, busy operator, no jargon, no patronizing.

### Voice rules

- **Voice:** Corporate-professional with an inspirational undercurrent. Plain-spoken, not buzzwordy. Slightly different register per audience (see above).
- **No emojis. Anywhere.**
- **No exclamation points** unless quoting someone.
- Reading level: ~grade 9. Short sentences. Sentence fragments OK when intentional.
- Avoid: "leverage", "synergy", "game-changer", "revolutionary", "unleash", "supercharge". Avoid stacking adjectives.
- B2C: address the reader directly ("you", "your CV"). Acknowledge frustration without wallowing in it.
- B2C never says "you failed" — the system filtered you out.
- B2B: acknowledge the operator's reality (running everything else; hiring between client calls). Never moralize about how they "should have" done it differently.

### Two brand systems

| Day | Brand | Primary | Accent | Notes |
|---|---|---|---|---|
| Mon (Mission Monday) | **RisePoint Careers** | Cloud Burst `#212D45` (dark navy) | Deep Saffron `#FFAB30` (warm orange) | Bold saffron slab top-right, rising-bars motif bottom-right, "RISEPOINT CAREERS" wordmark, saffron rule across footer |
| Tue–Fri | **Spark Careers** | Cadet Blue `#499AA9` | Arsenic `#414042` (charcoal) | Cream backgrounds where appropriate; use the fully-cream Spark logo for cadet-blue panels |

Brand asset folder (local): `C:\Users\HP\Desktop\Personal Docs\Post Shell Projects\IdleSpark\Branding Files\`. Contains:
- `RisePoint Logo/` (and `RisePoint Logo.zip`)
- `Spark_Stepup Logo files/`
- `SparkCareer.{svg,png,pdf,eps,jpg}`
- `Brand Guide SparkCareer .pdf`
- `Brand Guide StepUpCareer.pdf`, `Brand Guide StepUpCareer_02.pdf`

**Typography:** Nexa Bold + Nexa Book preferred (Fontfabric commercial — user has not provided files yet). Fallback: Montserrat Bold + Montserrat Regular.

### Five layouts (one per weekday)

| Day | Layout | Style |
|---|---|---|
| Mon (Mission) | Geometric slab + rising bars + bold statement | RisePoint brand; saffron slab top-right; rising-bars motif bottom-right; bold statement headline; saffron rule at footer |
| Tue (Trade Secrets) | Numbered tactical card | Side rail with "NO. NN" badge top-left; "The Insight" overline; headline; subline below; Spark brand |
| Wed (Spotlight) | Conversational address | Large quotation mark; direct address to ICP; conversational tone; Spark brand |
| Thu (Commitment) | Reflective inspiration | Dot pattern accent; "we see you" reflective subline; Spark brand |
| Fri (Feature Friday) | 55/45 split-color CTA | Left panel headline; right panel CTA + URL + arrow + "Try it now"; Spark brand |

Each layout has **two variants**: B2B (typically dark-on-light or vice versa for audience differentiation) and B2C. Within a single visual, **highlight 1–2 key words** in the headline using the brand accent color.

All visuals are **1080 × 1350** (4:5 aspect ratio).

Filename convention: `{iso-week}-{weekday-3-letter}-{audience}.png`, e.g., `2026-W22-mon-b2b.png`.

### Theme rotation by weekday

Each weekday has a primary theme. To avoid month-over-month repetition, Mission Monday rotates through three sub-lenses:

| Mon week-in-cycle | Lens | Hook example |
|---|---|---|
| Cycle 1 | **Mission lens** | What we're building, why it matters |
| Cycle 2 | **Problem lens** | The specific pain we solve |
| Cycle 3 | **Origin lens** | Why this exists, founder story angle |

Cycle resets every 3 weeks. Determine current lens: `((week_number - 1) % 3) + 1`.

| Day | Theme | What to write about |
|---|---|---|
| Mon | Mission/Problem/Origin (rotates) | High-altitude purpose; the change we're making in hiring/job-seeking |
| Tue | Trade Secrets | Tactical tips — ATS tricks (B2C), pipeline hygiene (B2B), success-pattern observations |
| Wed | ICP Spotlight | Speak directly to the ideal customer; pain points; industry trends |
| Thu | Commitment Refresh | "We see you" inspiration; resilience for job seekers; permission for operators |
| Fri | Feature Friday | One specific product feature, soft CTA, "try it" |

**One flex slot per week** is reserved for reactive content (industry news, viral debate, hiring report). The flex slot replaces one of the 10 posts at the agent's discretion when something newsworthy lands. If nothing newsworthy that week, keep the planned 10.

### Channel distribution rules

Two posts per day (B2B AM, B2C PM by default), distributed across channels:

- **LinkedIn:** ~70% B2B, ~30% B2C → 9 posts/week. All B2B posts go to LinkedIn; only career-development-flavored B2C posts (Mon, Wed, Thu, Fri) go to LinkedIn. Tactical-CV-advice B2C (Tue) skips LinkedIn.
- **Facebook:** ~50/50 → 10 posts/week. All 10 B2B+B2C posts go to Facebook.
- **Instagram:** B2C-heavy → 5 posts/week. Only B2C posts go to Instagram (skip dense B2B operator content).

Result: 9 + 10 + 5 = **24 placements** per week.

### Caption formatting per channel

- **LinkedIn + Facebook:** Caption ends with the tracked URL inline (`https://...`).
- **Instagram:** Caption ends with `Link in bio: <stripped URL>` since IG strips inline links.
- Caption length: LinkedIn allows long form (200–500 words for B2B think-pieces; 100–250 for B2C). Facebook: 80–200 words. Instagram: 80–200 words; lead with the hook in the first 125 chars (before the truncation).
- No hashtag spam. 0–3 hashtags max. None if it cheapens the post.

### UTM tagging

Every URL in captions gets:
```
?utm_source=social&utm_medium=post&utm_campaign=w{NN}-{weekday}-{audience}
```

Example: `https://hire.risepointcareers.com/?utm_source=social&utm_medium=post&utm_campaign=w22-mon-b2b`.

### Posting times (Calgary MT, America/Edmonton)

| Audience | Time |
|---|---|
| B2B | 08:00 MT (catches morning founders before standups) |
| B2C | 12:00 MT (catches job-seeker lunch-break scrolling) |

### Output bundle structure

Match Week 22 exactly. Three deliverables:

1. **`spark-w{NN}-content-calendar.docx`** — review doc with cover page, week-at-a-glance table, per-post layouts (day/time/audience/channels/tracked URL/caption/alt text). User edits captions here if needed.
2. **Three Buffer CSVs** in the user's Buffer-native schema (`text, image_url, tags, posting_time`):
   - `spark-w{NN}-buffer-linkedin.csv` (9 rows)
   - `spark-w{NN}-buffer-facebook.csv` (10 rows)
   - `spark-w{NN}-buffer-instagram.csv` (5 rows)
   - Image URLs use the **placeholder** form: `https://drive.google.com/uc?export=view&id=__REPLACE_{basename}__` — the finalize script swaps these for raw.githubusercontent.com URLs after the user pushes PNGs to the repo.
   - `posting_time` format: `YYYY-MM-DD HH:MM` (Buffer reads this in the channel's configured timezone, which should be set to America/Edmonton).
3. **`visuals/` folder** with 10 PNGs at 1080×1350, named `{iso-week}-{weekday}-{audience}.png`.

Optional 4th: **`spark-w{NN}-contact-sheet.png`** — a 2-column × 5-row montage of all 10 visuals for at-a-glance review.

### Operational handoff (what user does after the bundle arrives)

This is the existing pipeline — do not change without flagging to user:

```powershell
# 1. Save the bundle from claude.ai to Downloads (default location)

# 2. Copy PNGs into the repo's week folder
cp "C:\Users\HP\Downloads\spark-w{NN}-drive-bundle\visuals\*.png" `
   "C:\Users\HP\Desktop\Personal Docs\Post Shell Projects\IdleSpark\Marketing\social-assets\YYYY\W{NN}\"

# 3. Commit and push
cd "C:\Users\HP\Desktop\Personal Docs\Post Shell Projects\IdleSpark\Marketing\social-assets"
git add . ; git commit -m "w{NN}: visuals" ; git push

# 4. Run the finalizer — swaps placeholder URLs for live GitHub raw URLs, rewrites schema to Buffer's format
python tools/finalize_buffer_csvs.py --week YYYY-W{NN} `
    --input  "C:\Users\HP\Downloads\spark-w{NN}-drive-bundle\buffer" `
    --output "C:\Users\HP\Downloads\spark-w{NN}-drive-bundle\buffer"

# 5. Bulk-upload each -final.csv to Buffer:
#    Publish tab → channel → ⚙ → General → Bulk Upload → upload → confirm.
#    One CSV per channel (LinkedIn, Facebook, Instagram).
```

### Weekly research checklist

Before composing captions, the agent should briefly check (via WebSearch):

- **B2B competitor watch:** BambooHR, Workable, Greenhouse, JazzHR, Manatal — what are they posting/announcing this week?
- **B2C competitor watch:** Jobright.ai, Teal, Jobscan, Kickresume, Rezi — feature launches, content angles?
- **Job market headlines:** US/Canada SMB hiring data, layoff news, grad season, seasonal hiring waves (retail, hospitality, etc.)
- **AI-in-hiring discourse:** anything trending about ATS, AI-generated CVs, employer pushback, etc.

Pick 2–3 hooks worth referencing across the 10 posts. Don't shoehorn — if nothing is genuinely useful, skip the reference.

### Banned topics & sensitive areas

- No US political content
- No commentary on specific employers' layoffs unless framed compassionately about workers
- No commentary on race/gender in hiring as anything other than acknowledging structural bias exists
- No AI doom or AI utopia framing — keep it pragmatic
- Don't claim metrics we don't have ("our users see 40% more interviews" — we have no testimonials yet)

### Quality bar before delivery

The agent must self-review the bundle against:

- [ ] All 10 captions follow the voice rules (no emojis, no banned words, correct register per audience)
- [ ] All 10 PNGs are 1080×1350, brand-correct, no overlapping text/elements, no awkward whitespace
- [ ] Mission Monday uses RisePoint brand only; Tue–Fri use Spark brand only
- [ ] UTM tags present on every URL with the correct `w{NN}-{weekday}-{audience}` campaign tag
- [ ] CSVs have exactly 9/10/5 rows in the right order, posting_time format is `YYYY-MM-DD HH:MM`
- [ ] Image URLs in CSVs use the `__REPLACE_<basename>__` placeholder form, not direct URLs
- [ ] Filenames match the convention `{iso-week}-{weekday}-{audience}.png`
- [ ] If the week falls on a holiday or major industry event, the agent has flagged this to the user

---

## PROMPT_TEMPLATE (Mode 1 output)

Below is the template the skill writes into `<repo>/prompts/<week>-prompt.md`. The user pastes this verbatim into a fresh claude.ai chat.

```
I need the Spark Careers / RisePoint Careers weekly social-post bundle for {WEEK_LABEL} ({WEEK_MON_DATE} through {WEEK_FRI_DATE}).

The bundle must match the Week 22 baseline exactly. Below is the full playbook — follow it.

============================================================
PRODUCTS
============================================================
- Spark Careers (B2C): job-seeker tool — resume review, ATS optimization, CV rewrites. URL: spark.stepupcareers.com (moving to spark.risepointcareers.com).
- Spark Careers Enterprise (B2B): lightweight ATS for 0–20-person founder-led SMBs. URL: hire.risepointcareers.com. 7-day free trial.
- Parent: RisePoint Careers Corp. Marketing site: risepointcareers.com.

============================================================
ICPs
============================================================
B2C: All career stages, all geographies, no vertical focus yet. Job seekers under pressure.
B2B: Founder-led 0–20 person startups/small businesses hiring manually through email/spreadsheets/LinkedIn/forms. Buyer titles: Founder, CEO, Owner, Operations/Office/Practice/Clinic Manager, HR Manager (if any).

============================================================
VOICE
============================================================
- Corporate-professional + inspirational undercurrent. Plain-spoken, not buzzwordy.
- NO emojis. No exclamation points unless quoting.
- Reading level grade 9. Short sentences OK. Sentence fragments OK when intentional.
- Avoid: leverage, synergy, game-changer, revolutionary, unleash, supercharge.
- B2C: warm, address reader directly, never "you failed" — the system filtered you out.
- B2B: founder-to-founder, busy operator, no patronizing.

============================================================
TWO BRAND SYSTEMS
============================================================
Mon (Mission Monday) = RisePoint Careers brand:
  Primary: Cloud Burst #212D45 (dark navy)
  Accent:  Deep Saffron #FFAB30 (warm orange)
  Treatment: bold saffron slab top-right, rising-bars motif bottom-right echoing the upward-arrow logo, "RISEPOINT CAREERS" wordmark, saffron rule across footer

Tue–Fri = Spark Careers brand:
  Primary: Cadet Blue #499AA9
  Accent:  Arsenic #414042 (charcoal)
  Treatment: cream backgrounds where appropriate; use fully-cream Spark logo on cadet panels

Typography: Nexa Bold + Nexa Book preferred (commercial). Fallback: Montserrat Bold + Regular.

============================================================
FIVE LAYOUTS (one per weekday)
============================================================
- Mon (Mission): Geometric slab + rising bars + bold statement headline + saffron footer rule. RisePoint brand.
- Tue (Trade Secrets): Numbered tactical card with side rail, "NO. NN" badge top-left, "The Insight" overline, headline + subline. Spark brand.
- Wed (Spotlight): Large quotation mark + direct conversational address to the ICP. Spark brand.
- Thu (Commitment): Dot-pattern accent + "we see you" reflective subline. Spark brand.
- Fri (Feature Friday): 55/45 split-color, CTA panel on right with URL + arrow + "Try it now". Spark brand.

Each layout has B2B and B2C variants (different color emphasis for audience differentiation).
Highlight 1–2 key words in the headline using the brand accent.

All visuals: 1080×1350 (4:5).
Filename: {iso-week}-{weekday-3-letter}-{audience}.png, e.g., {WEEK_LABEL_LOWER}-mon-b2b.png.

============================================================
THEMES (with Mon sub-rotation)
============================================================
This week, Mission Monday lens = {MISSION_LENS} (mission | problem | origin — rotates every 3 weeks).

- Mon: {MISSION_LENS} angle — high-altitude purpose
- Tue: Trade Secrets — tactical tips (B2C ATS tricks, B2B pipeline hygiene)
- Wed: ICP Spotlight — speak directly to the ICP, pain points, trends
- Thu: Commitment Refresh — "we see you" inspiration
- Fri: Feature Friday — one specific product feature, soft CTA

One of the 10 slots is a "flex" reserved for reactive content if something newsworthy lands this week. If not, ship the planned 10.

============================================================
CHANNELS (24 placements total)
============================================================
- LinkedIn: 9 posts/week. All B2B (5). Career-development B2C (Mon, Wed, Thu, Fri = 4). Skip tactical B2C (Tue).
- Facebook: 10 posts/week. All B2B (5) + all B2C (5).
- Instagram: 5 posts/week. All B2C only.

============================================================
CAPTION FORMAT PER CHANNEL
============================================================
- LinkedIn + Facebook: tracked URL appears inline at the end.
- Instagram: caption ends with "Link in bio: <stripped URL>".
- Length: LinkedIn long-form (200–500w B2B think-pieces, 100–250w B2C); FB/IG 80–200w; lead first 125 chars with the hook.
- Hashtags: 0–3 max, none if cheapening.

============================================================
UTM TAGGING
============================================================
Every URL gets: ?utm_source=social&utm_medium=post&utm_campaign=w{NN_NUM}-{weekday}-{audience}
Example: https://hire.risepointcareers.com/?utm_source=social&utm_medium=post&utm_campaign=w{NN_NUM}-mon-b2b

============================================================
POSTING TIMES (America/Edmonton)
============================================================
B2B = 08:00. B2C = 12:00.

============================================================
DATES THIS WEEK
============================================================
{DATE_TABLE}

============================================================
OUTPUT BUNDLE (three files, match Week 22 exactly)
============================================================
1. spark-w{NN_NUM}-content-calendar.docx — cover + week-at-a-glance table + per-post layouts.
2. Three Buffer CSVs with schema: Date, Time, Text, Image URL, Tags (Title Case — my Claude Code finalize-script rewrites to Buffer's actual schema and swaps image placeholders for real URLs):
   - spark-w{NN_NUM}-buffer-linkedin.csv (9 rows)
   - spark-w{NN_NUM}-buffer-facebook.csv (10 rows)
   - spark-w{NN_NUM}-buffer-instagram.csv (5 rows)
   Image URL column uses placeholder form: https://drive.google.com/uc?export=view&id=__REPLACE_{WEEK_LABEL}-{weekday}-{audience}__
3. visuals/ folder with 10 PNGs at 1080×1350, named {WEEK_LABEL_LOWER}-{weekday-3-letter}-{audience}.png.

Optional 4th: spark-w{NN_NUM}-contact-sheet.png — 2×5 montage for at-a-glance review.

Bundle all four into a single zip named spark-w{NN_NUM}-drive-bundle.zip.

============================================================
RESEARCH CONTEXT (this week's hooks)
============================================================
{RESEARCH_HOOKS}

============================================================
BANNED / SENSITIVE
============================================================
- No US political content
- No specific-employer layoff commentary unless framed compassionately about workers
- No race/gender hiring takes beyond acknowledging structural bias exists
- No AI doom/utopia framing — pragmatic
- No fake metrics — we have no testimonials yet

============================================================
QUALITY GATE
============================================================
Before delivering, verify:
- 10 captions follow voice rules
- 10 PNGs are 1080×1350, brand-correct, no overlapping elements
- Mon = RisePoint brand only; Tue–Fri = Spark brand only
- UTM tags on every URL with correct campaign tag
- CSVs have 9/10/5 rows
- Image URLs in CSVs use __REPLACE_<basename>__ placeholder form

Brand asset reference (to be attached):
- Brand Guide SparkCareer .pdf
- Brand Guide StepUpCareer.pdf
- RisePoint logo files
- Spark/StepUp logo files

Begin.
```

---

## Source of truth & sync

This skill exists in two places:
- **User-scoped (active):** `C:\Users\HP\.claude\skills\spark-weekly-content\SKILL.md`
- **Version-controlled (canonical):** `<social-assets-repo>/.claude/skills/spark-weekly-content/SKILL.md` → https://github.com/Spark-Careers/social-assets

When updating the playbook, edit the repo version, commit, then copy to the user-scoped location:
```powershell
cp ".../social-assets/.claude/skills/spark-weekly-content/SKILL.md" `
   "C:/Users/HP/.claude/skills/spark-weekly-content/SKILL.md"
```
