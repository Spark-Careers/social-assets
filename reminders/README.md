# Weekly bundle reminder

## Purpose

The real trigger is now the Windows scheduled task `SparkCareers\WeeklyContentBuild`
(see `tools/generate/install-task.ps1`). It fires every **Friday 08:30
America/Edmonton**, builds the next week's bundle, and pops a Windows toast
when done.

This calendar event is a **backstop** — a recurring nudge **at 09:30 every
Friday** to remind you to check `Downloads\spark-w{NN}-buffer\` and bulk-upload
the 3 CSVs to Buffer. If for some reason the toast was missed (laptop muted,
notification cleared too fast, etc.), the calendar reminder catches it.

Toast notification *only* = also fine. Calendar reminder *only* and toast
missing = something's wrong, check `social-assets\runs\wrapper-*.log`.

## Install

### Google Calendar
1. https://calendar.google.com → gear → Settings → Import & export →
   Select file → `spark-weekly-content.ics` → Import.

### Outlook
1. File → Open & Export → Import/Export → Import an iCalendar (.ics) file →
   browse to `spark-weekly-content.ics`.

### Apple Calendar
1. Double-click the `.ics` file (Mac) or email it to yourself and tap (iOS).

## First occurrence

**Fri May 29, 2026 at 09:30 MT** — covering the build of Week 23 (Jun 1–5)
which happens at 08:30 the same morning.
