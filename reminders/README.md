# Weekly content reminder

## What's here

`spark-weekly-content.ics` — recurring calendar event firing every **Friday at 12:00 PM America/Edmonton (Calgary MT)**. First occurrence: **Fri May 29, 2026** for Week 23 (Jun 1–5). Recurs weekly forever.

## How to install

### Google Calendar
1. Open https://calendar.google.com
2. Gear icon (top-right) → **Settings**
3. Left sidebar → **Import & export**
4. Click **Select file from your computer** → choose `spark-weekly-content.ics`
5. Choose the calendar to import into (your primary, or a "Spark Ops" calendar if you keep one)
6. Click **Import**

### Outlook
1. Open Outlook → **File** → **Open & Export** → **Import/Export**
2. Choose **Import an iCalendar (.ics) file** → Next
3. Browse to `spark-weekly-content.ics` → Open
4. Click **Import** (adds events to your default calendar)

### Apple Calendar (macOS / iOS)
1. Double-click `spark-weekly-content.ics` on Mac, OR email it to yourself and tap on iOS
2. Choose the calendar to add it to → Add All

### Phone notification
After import on any of the above, the event will show up on your phone's calendar app if it's synced (which it usually is). The built-in 0-minute alarm fires at exactly 12:00 PM local Calgary time every Friday.

## What the reminder says

> **Generate Spark Careers next-week content**
>
> Open Claude Code in IdleSpark/Marketing/social-assets and invoke `/spark-weekly-content YYYY-W{next-week}` to generate next week's social-post bundle. The skill writes a prompt to `prompts/`. Paste it into a fresh claude.ai chat, attach Brand Guide PDFs from `IdleSpark/Branding Files/`, receive the bundle, then follow the operational sequence in the skill file (push PNGs to repo, run finalize script, bulk-upload CSVs to Buffer).

## What you do when it fires

1. Open Claude Code in `IdleSpark/Marketing/social-assets/`
2. Run `/spark-weekly-content 2026-WNN` (replace NN with the week number you're generating for — the **next** week, not the current one)
3. Follow the instructions Claude gives you (paste into claude.ai, attach brand PDFs, save bundle to Downloads)
4. Push PNGs to repo, run finalizer, bulk-upload to Buffer

Total weekly time once you're in rhythm: ~15–20 minutes (5 min to trigger and paste, 5–8 min for claude.ai to generate, 2–3 min to review, 2–3 min for the operational handoff).

## Changing or removing

To change the reminder time/frequency, delete the imported event from your calendar and re-import an edited copy of this `.ics` file. Or just edit the recurring event directly in your calendar app.
