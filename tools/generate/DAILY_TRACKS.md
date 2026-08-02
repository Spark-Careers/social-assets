# Daily masterclass tracks

The curriculum-driven replacement for the old theme-and-research weekly model.
Two sequential tracks publish one post each per day, Monday through Saturday,
at different times.

| Track | Time (America/Edmonton) | Destination | Series length | Posts |
|---|---|---|---|---|
| B2B | 08:00 | hire.risepointcareers.com | 25 weeks | 150 |
| B2C | 12:00 | spark.risepointcareers.com | 11 weeks | 66 |

One run produces one calendar week: 12 posts, 30 placements.

## What changed from the old model

| | Old | New |
|---|---|---|
| Driver | Weekday themes plus a mandatory weekly web-research pass | A fixed curriculum consumed in sequence |
| Cadence | 5 B2B + 5 B2C per week | 6 B2B + 6 B2C per week, Mon to Sat |
| Content origin | Generated per week by a headless Claude call | Authored in the refined schedule DOCX, extracted once |
| Continuity | Each week standalone | Multi-week arc, posts build on each other |
| Visuals | 5 weekday-themed layouts | 3 directions from the design handoff |

The research pass no longer applies. The curriculum is the anchor, so nothing
in this path calls `claude --print`, which also removes the JSON-parse and
timeout failures the old weekly runs kept hitting.

## Pipeline

```
content/Spark_B2{B,C}_Daily_Content_Schedule_Refined.docx   authored source
        |
        |  extract_curriculum.py          (run only when a DOCX changes)
        v
content/b2{b,c}_curriculum.json           machine-readable, validated
        |
        |  run_daily_weekly.py            (run weekly)
        v
YYYY/WNN/*.png                            12 posters, 1080x1350
YYYY/WNN/manifest.json                    what was published and why
~/Downloads/spark-YYYY-wNN-buffer/_source/*.csv
        |
        |  ../finalize_buffer_csvs.py     (unchanged, already compatible)
        v
~/Downloads/spark-YYYY-wNN-buffer/*-final.csv    upload to Buffer
```

## Commands

```bash
# Re-extract after editing either source DOCX
python tools/generate/extract_curriculum.py
python tools/generate/extract_curriculum.py --audience b2b

# See what next week would contain, without writing anything
python tools/generate/run_daily_weekly.py --dry-run

# Build a week
python tools/generate/run_daily_weekly.py --iso-week 2026-W34

# Build one track only, or replay a specific curriculum week
python tools/generate/run_daily_weekly.py --tracks b2c --b2c-series-week 3

# Build without moving the cursor (useful when re-rendering a week)
python tools/generate/run_daily_weekly.py --iso-week 2026-W34 --no-advance
```

## Template directions

Implemented from `design/b2c-template-system/README.md` at the specified
values. Canvas is a fixed 1080 x 1350, rendered at 2x and downsampled so the
hairlines survive.

| Direction | Name | Ground | Current use |
|---|---|---|---|
| `1a` | Cut Numeral | cream `#F4F1EA` | B2C, Tuesday to Saturday |
| `1b` | Spine | ink `#16181A` | B2B, Tuesday to Saturday |
| `1c` | Field | teal `#2C7F92` | Both tracks, Monday (module opener) |

Assignments live in the `TRACKS` table at the top of `run_daily_weekly.py` and
are one edit away from changing.

### Deviation from the prototype

The prototype hard-codes its headline line breaks at a fixed 118px. Real
headlines run from 19 to 85 characters, which at a fixed size overflows the
headline box on roughly half the set. Each direction therefore declares a size
range and a vertical budget, and the renderer steps the size down until the
block fits (`HEADLINE_FIT` in `poster_renderer.py`). Everything else is
reproduced at the specified values.

### Poster numeral

Keys off `week_in_series`, not the module number. The B2B curriculum restarts
module numbering at week 16 where it moves from the recruitment track to the
HRMS track, so module number is not unique across a series.

### Body copy

The `Topic` column in the source DOCX is an internal label and usually restates
the headline, so it is not used on the poster. The body is taken from the
opening sentences of the post copy instead, capped at 24 words, skipping the
first sentence when it merely repeats the headline.

## State

`content/curriculum_state.json` holds a cursor per track:

```json
{
  "b2b": {"next_series_week": 1, "cycle": 1},
  "b2c": {"next_series_week": 1, "cycle": 1}
}
```

Each run consumes one series week per track and advances that track's cursor.
The two tracks advance independently, so they do not have to stay in step.

Passing `--b2b-series-week` or `--b2c-series-week` makes a run reproducible:
the same series week always yields the same posts.

## Open items

**Series length mismatch.** B2C runs out after 11 weeks while B2B continues to
25. When a curriculum is exhausted the run wraps to week 1 and increments
`cycle`, logging that it did so. That keeps the schedule full but republishes
B2C content from week 12 onward. Options are to extend the B2C curriculum, hold
B2C at a lower cadence, or accept the repeat with refreshed copy. Needs a
decision before week 12.

**Nothing runs unattended.** The scheduled task `SparkCareers\WeeklyContentBuild`
was disabled on 2026-08-02. Weeks are built by hand:

```bash
python tools/generate/run_daily_weekly.py --dry-run     # check first
python tools/generate/run_daily_weekly.py               # build the next week
```

Then push the posters and run `tools/finalize_buffer_csvs.py`. The task still
points at the old `run_weekly.ps1` and is not wired to this pipeline at all.
To re-enable automation later, repoint that wrapper at `run_daily_weekly.py`
first, then `Enable-ScheduledTask -TaskName WeeklyContentBuild -TaskPath
"\SparkCareers\"`. Enabling it as-is would generate old-format content and
collide with the daily tracks.

**Instagram for B2B.** B2B is currently set to LinkedIn and Facebook only,
carried over from the previous model on the reasoning that operator content
underperforms on Instagram. Add `"instagram"` to the B2B `channels` list in
`run_daily_weekly.py` to change that.
