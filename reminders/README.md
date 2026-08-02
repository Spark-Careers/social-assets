# Weekly bundle reminder

## Purpose

**The scheduled task is disabled as of 2026-08-02.** Weeks are now built by
hand, so this calendar event is the only prompt you get. There is no toast
notification any more.

The event fires **09:30 every Friday** as a nudge to build the coming week and
upload it to Buffer.

## What to do when it fires

```bash
cd "C:\Users\HP\Desktop\Personal Docs\Post Shell Projects\IdleSpark\Marketing\social-assets"

python tools/generate/run_daily_weekly.py --dry-run     # confirm the week and modules
python tools/generate/run_daily_weekly.py               # render 12 posters, write source CSVs

git add 2026/ content/curriculum_state.json
git commit -m "2026-WNN: daily tracks"
git push                                                 # posters must be live before finalizing

python tools/finalize_buffer_csvs.py --week 2026-WNN \
    --input  "C:\Users\HP\Downloads\spark-2026-wNN-buffer\_source" \
    --output "C:\Users\HP\Downloads\spark-2026-wNN-buffer"
```

Then open Buffer and bulk-upload the three `*-final.csv` files, one per channel:
Publish tab, channel, gear icon, General, Bulk Upload.

Full detail lives in `tools/generate/DAILY_TRACKS.md`.

## Install

### Google Calendar
1. https://calendar.google.com → gear → Settings → Import & export →
   Select file → `spark-weekly-content.ics` → Import.

### Outlook
1. File → Open & Export → Import/Export → Import an iCalendar (.ics) file →
   browse to `spark-weekly-content.ics`.

### Apple Calendar
1. Double-click the `.ics` file (Mac) or email it to yourself and tap (iOS).

## History

Until 2026-08-02 the real trigger was the Windows scheduled task
`SparkCareers\WeeklyContentBuild`, firing every Friday 08:30 America/Edmonton
and popping a toast when the bundle was ready. That task ran the old
theme-and-research pipeline. It has been disabled rather than removed, so the
definition is still there if automation is wanted again later. Re-enabling it
without first repointing `run_weekly.ps1` at `run_daily_weekly.py` would
generate old-format content and collide with the daily tracks.
