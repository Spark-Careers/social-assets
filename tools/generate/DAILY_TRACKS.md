# Daily masterclass tracks

Two audience curricula, consumed in sequence, one post per publishing day.
The tracks alternate through the week and each runs until its curriculum is
exhausted.

| Day | Track | Time (America/Edmonton) | Destination | Direction |
|---|---|---|---|---|
| Mon | B2B | 08:00 | hire.risepointcareers.com | `2b` ink |
| Tue | B2C | 12:00 | spark.risepointcareers.com | `2a` cream |
| Wed | B2B | 08:00 | hire.risepointcareers.com | `2b` ink |
| Thu | B2C | 12:00 | spark.risepointcareers.com | `2a` cream |
| Fri | B2B | 08:00 | hire.risepointcareers.com | `2b` ink |

Saturday and Sunday are dark. One run produces one calendar week: five posts,
fifteen placements.

| Track | Posts | Per week | Lasts | Runs out |
|---|---|---|---|---|
| B2B | 150 | 3 | 50 weeks | Aug 2027, starting 2026-W38 |
| B2C | 66 | 2 | 33 weeks | Apr 2027, starting 2026-W38 |

## What changed from the module-week model

| | Before | Now |
|---|---|---|
| Cadence | 6 B2B + 6 B2C per week, Mon to Sat | 3 B2B + 2 B2C per week, Mon to Fri |
| Built vs published | 12 built, 10 published | 5 built, 5 published |
| Posts discarded | 2 every week, permanently | none |
| Roles never used | B2B lost The Frame, B2C lost The Mechanism | none |
| Scheduling unit | one six-post module per calendar week | individual posts, taken in order |
| Cursor | `next_series_week` | `next_post_seq` |
| Caption tail | `{CTA}: {tracked URL with UTM}` | the bare domain |
| Poster | `1a` / `1b` / `1c`, with labelling furniture | `2a` / `2b`, stripped |
| Channels | B2B on LinkedIn + Facebook | both tracks on all three |
| At the cap | LinkedIn 10/10 | LinkedIn 5/10 |

A module no longer fits inside a calendar week. At three posts a week a B2B
module takes two weeks to run; at two a week a B2C module takes three. That is
the reason the cursor had to become a post position rather than a week number,
and why an old state file is reset rather than migrated: a series week does not
map onto a post number once the two tracks advance at different rates.

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
YYYY/WNN/*.png                            5 posters, 1080x1350
YYYY/WNN/manifest.json                    what published, and what is left
~/Downloads/spark-YYYY-wNN-buffer/_source/*.csv
        |
        |  ../finalize_buffer_csvs.py
        v
~/Downloads/spark-YYYY-wNN-buffer/*-final.csv    upload to Buffer
```

## Commands

```bash
# Re-extract after editing either source DOCX
python tools/generate/extract_curriculum.py

# See what next week would contain, without writing anything
python tools/generate/run_daily_weekly.py --dry-run

# Build a week
python tools/generate/run_daily_weekly.py --iso-week 2026-W38

# Build one track only, or replay from a specific post number
python tools/generate/run_daily_weekly.py --tracks b2c --b2c-start-seq 7

# Build without moving the cursor (useful when re-rendering a week)
python tools/generate/run_daily_weekly.py --iso-week 2026-W38 --no-advance
```

## Template directions

Canvas is a fixed 1080 x 1350, rendered at 2x and downsampled so hairlines
survive.

The `1x` family is the original design handoff, implemented at the specified
values. It is no longer used by the weekly run but is kept for one-offs.

| Direction | Name | Ground |
|---|---|---|
| `1a` | Cut Numeral | cream `#F4F1EA` |
| `1b` | Spine | ink `#16181A` |
| `1c` | Field | teal `#2C7F92` |

The `2x` family is the minimal set the daily tracks now use. Same type system
and tokens, with everything that labels a post rather than saying something
removed: no editorial role, no week numeral, no progress counter, no grid, no
rings, no spine. Four elements remain, down from nine.

| Direction | Ground | Used by |
|---|---|---|
| `2a` | cream `#F4F1EA` | B2C |
| `2b` | ink `#16181A` | B2B |
| `2c` | teal `#2C7F92` | spare |

Since there is no fixed furniture to sit around, the headline and body are
centred as a block in the space above the footer. Headlines run from 19 to 85
characters and a fixed top anchor leaves the short ones stranded high.

### Headline sizing

Each direction declares a size range and a vertical budget, and the renderer
steps the size down until the block fits (`HEADLINE_FIT` in
`poster_renderer.py`). Verified at both extremes: 19 characters and 85.

Headlines of four words or fewer render as a single ink part with no accent
colour, by design. `split_headline` returns an empty second part rather than
breaking a short line in an arbitrary place.

### Body copy

The `Topic` column in the source DOCX is an internal label that usually
restates the headline, so it is not used. The body is taken from the opening
sentences of the post copy, capped at 24 words, skipping the first sentence
when it merely repeats the headline.

## Captions

Post copy, a blank line, then the track's bare domain. No call to action.

The curriculum's CTA column was dropped for two reasons. B2C reuses seven
phrases across sixty-six posts, one of them eighteen times. And the verbs point
at exercises the site does not host, so "Map your hiring workflow" was followed
by a link to a home page with no workflow mapper on it.

The bare domain also carries no UTM parameters, which keeps the caption clean
but means posts are not attributable in analytics beyond referrer. Restore the
tracking by reinstating a `tracked_url` helper in `build_captions`.

## State

`content/curriculum_state.json` holds a cursor per track:

```json
{
  "b2b": {"next_seq": 1},
  "b2c": {"next_seq": 1}
}
```

`next_seq` is a 1-based position in the curriculum's `posts` array. Each run
takes as many posts as that track has slots and advances past the last one.
The tracks advance independently.

Passing `--b2b-start-seq` or `--b2c-start-seq` makes a run reproducible: the
same start always yields the same posts.

## Running out

Both curricula are finite and neither wraps. A track with fewer posts left than
slots publishes a short week and says so. A track with none left is skipped and
says so. When both are empty the run writes nothing and exits cleanly.

B2C empties about sixteen weeks before B2B. From that point the week is three
B2B posts until B2B empties too. Extending the B2C curriculum, or slowing it to
one post a week, are the ways to keep the two in step. Neither is done.

## Nothing runs unattended

The scheduled task `SparkCareers\WeeklyContentBuild` was disabled on
2026-08-02 and still points at the retired `run_weekly.ps1`. Weeks are built by
hand. Re-enabling the task as it stands would generate old-format content and
collide with these tracks.
