# Handoff: Spark Careers — Social Post Template System

## Overview
A reusable social-post template system for Spark Careers educational content ("modules" delivered as a numbered series). Three design directions for the same content payload — an eyebrow/index, a two-part headline, a short body line, and a brand footer — sized for 1080 × 1350 (4:5, Instagram/LinkedIn portrait).

The intent is that one direction is chosen and then extended into a full post set (title card, list card, quote card, CTA card) using the same tokens and grid.

## About the Design Files
The file in this bundle is a **design reference created in HTML** — a prototype showing intended look and composition, not production code to copy directly. The task is to **recreate these designs in the target codebase's existing environment** (React, Vue, a template renderer, an image-generation pipeline such as Satori/Puppeteer, etc.) using its established patterns and libraries. If no environment exists yet, choose the most appropriate one for the job — for static image export, an HTML → PNG renderer at 1080 × 1350 is the natural fit.

All layout in the prototype uses absolute positioning inside a fixed 1080 × 1350 box. That is deliberate: these are posters, not responsive pages. Keep the fixed canvas; do not make it fluid.

## Fidelity
**High-fidelity.** Colors, type sizes, weights, letter-spacing, and positions are final and should be reproduced exactly. All values below are in CSS px on a 1080 × 1350 canvas.

## Canvas & Grid
- Canvas: **1080 × 1350**, `overflow: hidden`.
- Outer margin: **88px** left/right and top on all three directions.
- Footer band: **132px** tall, full bleed, pinned to the bottom.
- 1A also draws a six-column grid overlay: `grid-template-columns: repeat(6, 1fr)`, each column with a `1px solid rgba(26,26,24,0.055)` right border (last column has none). Decorative only, `pointer-events: none`.

## Screens / Views

### 1A — "Cut Numeral" (cream, editorial grid)
**Purpose:** default/primary post. Light, editorial, feed-friendly.

Layout, top to bottom:
| Element | Position | Spec |
|---|---|---|
| Background | full | `#F4F1EA` |
| Grid overlay | inset 0 | see Grid above |
| Ghost numeral "03" | `right: -96px; top: 96px` | Archivo 900, `font-size: 620px`, `line-height: 0.74`, `letter-spacing: -0.06em`, `color: transparent`, `-webkit-text-stroke: 2px rgba(26,26,24,0.16)`. Intentionally bleeds off the right edge and sits behind the headline. |
| Teal rule | `left: 0; top: 470px` | `560 × 14px`, `#2C7F92`, bleeds off the left edge |
| Eyebrow row | `left: 88px; top: 88px` | flex, `align-items: center`, `gap: 18px` — a `34 × 2px` `#2C7F92` dash, then `03` (Space Mono 700, 19px, `letter-spacing: 0.26em`, uppercase, `#1A1A18`), then `The Action` (Space Mono 400, same size/tracking, `#8C877C`) |
| Headline | `left: 88px; right: 120px; top: 530px` | Archivo 800, **118px**, `line-height: 0.92`, `letter-spacing: -0.045em`, `#1A1A18`. Manual line breaks: "Take one" / "live posting." / "Label every line." — the third line is `#2C7F92`. |
| Body | `left: 88px; top: 906px; width: 760px` | Archivo 400, **40px**, `line-height: 1.36`, `#4A4640`, `text-wrap: pretty` |
| Footer | bottom, `height: 132px`, `padding: 0 88px` | `border-top: 2px solid #1A1A18`, flex space-between. Left: "SPARK CAREERS" Archivo 800, 26px, `letter-spacing: 0.12em`, uppercase, `white-space: nowrap`, `#1A1A18`. Right: URL Space Mono 400, 21px, `#2C7F92`. |

### 1B — "Spine" (ink ground, vertical index)
**Purpose:** high-contrast variant for punchier / more declarative posts.

| Element | Position | Spec |
|---|---|---|
| Background | full | `#16181A` |
| Spine | `left: 0; top: 0; bottom: 132px; width: 132px` | `border-right: 1px solid rgba(244,241,234,0.14)`, flex column, `align-items: center`, `justify-content: space-between`, `padding: 64px 0`, `overflow: hidden`. Top: "The Action" Space Mono 700, 18px, `letter-spacing: 0.3em`, uppercase, `writing-mode: vertical-rl`, `#2C7F92`. Bottom: "03" Archivo 900, 92px, `line-height: 0.8`, `letter-spacing: -0.06em`, `#F4F1EA`. |
| Header rule | `left: 132px; right: 0; top: 0; height: 150px` | `border-bottom: 1px solid rgba(244,241,234,0.14)`, `padding: 0 88px`, space-between. Left: "SPARK CAREERS" Space Mono 700, 19px, `0.26em`, `#F4F1EA`. Right: "03 / 05" Space Mono 400, 19px, `0.26em`, `#7C8790`. |
| Headline block | `left: 220px; right: 88px; top: 290px` | flex column, `gap: 44px`. Line 1 `<h1>`: "Take one live posting." Archivo 800, **112px**, `line-height: 0.94`, `letter-spacing: -0.045em`, `#F4F1EA`. Line 2 `<h2>`: same metrics, `#2C7F92`, preceded by an `8px`-wide full-height `#2C7F92` bar with `gap: 24px`. |
| Body | in the same flex column, `margin-top: 20px`, `max-width: 760px` | Archivo 400, 40px, `line-height: 1.36`, `#A8AFB4` |
| Footer | bottom, `height: 132px`, full bleed | background `#2C7F92`, `padding: 0 88px 0 44px`. Text `#0F1416` (both lockup and URL), same type specs as 1A. |

### 1C — "Field" (teal block, poster scale)
**Purpose:** loudest variant — announcements, series openers.

| Element | Position | Spec |
|---|---|---|
| Background | full | `#2C7F92` |
| Ring 1 | `right: -180px; top: -160px` | `760 × 760px`, `border-radius: 50%`, `2px solid rgba(244,241,234,0.22)` |
| Ring 2 | `right: -60px; top: -40px` | `520 × 520px`, `border-radius: 50%`, `2px solid rgba(244,241,234,0.16)` |
| Eyebrow row | `left/right: 88px; top: 88px` | space-between. Left "03" Space Mono 700, 19px, `0.26em`, `#EAF4F6`. Right "The Action", same, `rgba(234,244,246,0.62)`. |
| Display numeral | `left/right: 88px; top: 216px` | "03" Archivo 900, **250px**, `line-height: 0.78`, `letter-spacing: -0.07em`, `#F4F1EA` |
| Headline | `margin-top: 52px` under the numeral | Archivo 800, **104px**, `line-height: 0.96`, `letter-spacing: -0.04em`, `max-width: 900px`. Line 1 `#08252C`, line 2 (`<br>`-separated) `#F4F1EA`. |
| Base block | bottom, full width, `height: 400px` | `#F4F1EA`, `padding: 76px 88px 0`, flex column, `justify-content: space-between`. Body: Archivo 400, 40px, `line-height: 1.36`, `max-width: 840px`, `#3A3630`. |
| Footer | last child of the base block, `height: 132px` | `border-top: 2px solid #1A1A18`, same lockup/URL specs as 1A |

## Content Model
Every direction renders the same payload. Implement as a single data object:

```
{
  index:    "03",              // series number, also the display numeral
  series:   "The Action",      // series/topic label
  progress: "03 / 05",         // 1B header only
  headlineA:"Take one live posting.",
  headlineB:"Label every line.",   // rendered in the accent color
  body:     "Read it line by line before you write a word back. Most people disqualify themselves before they ever apply.",
  brand:    "Spark Careers",
  url:      "spark.risepointcareers.com"
}
```

**Copy is placeholder.** `body` in particular is a stand-in written to fit the measure — replace with real copy per post. Headline should stay at or under ~6 words per part; body at or under ~22 words, or the fixed positions in 1A will need adjusting.

## Interactions & Behavior
None — these are static export templates. There are no hover, focus, loading, or error states and no responsive behavior. If rendered in a browser-based editor, the only dynamic requirement is re-rendering when the content model changes.

If exported as images: render at 1080 × 1350 at 2× device pixel ratio (2160 × 2700) and downsample, so the hairline rules survive.

## State Management
None required beyond the content object. In an authoring tool: one `post` object plus a `variant` enum (`'1a' | '1b' | '1c'`).

## Design Tokens

Colors
| Token | Hex | Use |
|---|---|---|
| `cream` | `#F4F1EA` | light ground, light-on-dark text |
| `cream-page` | `#E8E5DE` | canvas/desk background (prototype only) |
| `ink` | `#1A1A18` | primary text on cream, footer rule |
| `ink-deep` | `#16181A` | 1B ground |
| `ink-teal` | `#0F1416` | text on teal footer (1B) |
| `teal` | `#2C7F92` | accent — rules, second headline part, URLs |
| `teal-shadow` | `#08252C` | first headline line on teal ground (1C) |
| `body-warm` | `#4A4640` / `#3A3630` | body copy on cream |
| `body-cool` | `#A8AFB4` | body copy on ink |
| `muted-warm` | `#8C877C`, `#A29C90` | secondary eyebrow text on cream |
| `muted-cool` | `#7C8790` | secondary eyebrow text on ink |
| `hairline-dark` | `rgba(26,26,24,0.055)` grid · `rgba(26,26,24,0.16)` ghost stroke · `rgba(26,26,24,0.22)` rules | |
| `hairline-light` | `rgba(244,241,234,0.14)` | rules on ink |

Typography
- Display / UI: **Archivo** (Google Fonts) — 400, 800, 900.
- Mono / eyebrow / URL: **Space Mono** (Google Fonts) — 400, 700.
- Scale (px): 620 / 250 / 118 / 112 / 104 / 92 (display) · 40 (body) · 28 / 26 (lockup) · 21 / 19 / 18 (mono labels).
- Display tracking: `-0.04em` to `-0.07em`. Mono label tracking: `0.26em` (eyebrow), `0.3em` (vertical), `0.12em` (lockup).
- Minimum type size on canvas is 18px, which is ~1.7% of canvas height — safe at feed thumbnail scale.

Spacing
- 8 / 14 / 18 / 24 / 44 / 52 / 64 / 88 / 132 px. 88 is the page margin, 132 the footer height.

Radius / shadows
- No radii anywhere except the two decorative rings in 1C (`50%`).
- No shadows inside the poster. The drop shadows in the prototype are on the poster containers themselves (canvas presentation only) — do **not** reproduce them in export.

## Assets
No images or icons. All graphics are CSS: rules, borders, circles, and outlined type (`-webkit-text-stroke`). Fonts load from Google Fonts:
`https://fonts.googleapis.com/css2?family=Archivo:wght@400;500;600;700;800;900&family=Space+Mono:wght@400;700&display=swap`
If the render pipeline is offline (Satori, headless export), self-host both families instead.

## Files
- `Spark Social Template.dc.html` — all three directions on one canvas. Each poster is the `div[data-screen-label]` element (`1A`, `1B`, `1C`); everything outside those elements (turn caption, option badges, drop shadows, page background) is presentation scaffolding, not part of the design.

## Known open questions
- Only the "action/CTA" card is designed. The rest of the post set (title, list, quote) still needs layouts in the chosen direction.
- `03 / 05` in 1B assumes a five-part series; confirm the real series length.
