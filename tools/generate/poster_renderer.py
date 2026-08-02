# -*- coding: utf-8 -*-
"""Render daily masterclass posters using the Spark social template system.

Serves both audience tracks. The templates are audience-agnostic; the caller
picks a direction and supplies the content payload.

Implements the three directions specified in
    design/b2c-template-system/README.md

    1a  Cut Numeral  cream, editorial grid   (default / primary)
    1b  Spine        ink ground, vertical index
    1c  Field        teal block, poster scale

Canvas is a fixed 1080 x 1350 poster. Per the handoff, rendering is done at
2x device pixel ratio and downsampled so the hairline rules survive.

One deviation from the prototype, deliberately: the prototype hard-codes its
headline line breaks at a fixed 118px. Real headlines in the curriculum run
from 19 to 62 characters, which at a fixed size would overflow the headline
box on roughly half the set. Each direction therefore declares a headline
size range and a vertical budget, and the renderer steps the size down until
the block fits. Everything else is reproduced at the specified values.
"""

from __future__ import annotations

import html as html_mod
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parents[2]

FONTS = ("https://fonts.googleapis.com/css2?"
         "family=Archivo:wght@400;500;600;700;800;900&"
         "family=Space+Mono:wght@400;700&display=swap")

# Design tokens, from the handoff.
CREAM = "#F4F1EA"
INK = "#1A1A18"
INK_DEEP = "#16181A"
INK_TEAL = "#0F1416"
TEAL = "#2C7F92"
TEAL_SHADOW = "#08252C"
BODY_WARM = "#4A4640"
BODY_WARM_ALT = "#3A3630"
BODY_COOL = "#A8AFB4"
MUTED_WARM = "#8C877C"
MUTED_COOL = "#7C8790"
HAIRLINE_DARK_GRID = "rgba(26,26,24,0.055)"
HAIRLINE_DARK_STROKE = "rgba(26,26,24,0.16)"
HAIRLINE_LIGHT = "rgba(244,241,234,0.14)"

CANVAS_W, CANVAS_H = 1080, 1350

# direction -> (start_px, min_px, vertical budget px)
HEADLINE_FIT = {
    "1a": (118, 72, 376),
    "1b": (112, 68, 470),
    "1c": (104, 64, 487),
}


def _esc(s: str) -> str:
    return html_mod.escape(s or "", quote=False)


def _fit_script(direction: str) -> str:
    start, floor, budget = HEADLINE_FIT[direction]
    return f"""
    (function () {{
      var box = document.getElementById('headline');
      if (!box) return;
      var size = {start};
      box.style.fontSize = size + 'px';
      while (size > {floor} && box.scrollHeight > {budget}) {{
        size -= 2;
        box.style.fontSize = size + 'px';
      }}
      document.body.setAttribute('data-fitted', size);
    }})();
    """


# --------------------------------------------------------------------------- 1a
def _html_1a(p: dict) -> str:
    cols = "".join(
        f'<div style="border-right:1px solid {HAIRLINE_DARK_GRID}"></div>' for _ in range(5)
    ) + "<div></div>"
    hb = (f'<span style="color:{TEAL}">{_esc(p["headline_b"])}</span>'
          if p.get("headline_b") else "")
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="{FONTS}" rel="stylesheet">
<style>
 *{{box-sizing:border-box;margin:0;padding:0}}
 html,body{{width:{CANVAS_W}px;height:{CANVAS_H}px;overflow:hidden}}
 body{{font-family:Archivo,Helvetica,sans-serif;background:{CREAM};
   -webkit-font-smoothing:antialiased}}
 .poster{{position:relative;width:{CANVAS_W}px;height:{CANVAS_H}px;overflow:hidden}}
 .grid{{position:absolute;inset:0;display:grid;grid-template-columns:repeat(6,1fr);
   pointer-events:none}}
 .ghost{{position:absolute;right:-96px;top:96px;font-weight:900;font-size:620px;
   line-height:.74;letter-spacing:-.06em;color:transparent;
   -webkit-text-stroke:2px {HAIRLINE_DARK_STROKE}}}
 .rule{{position:absolute;left:0;top:470px;width:560px;height:14px;background:{TEAL}}}
 .eyebrow{{position:absolute;left:88px;top:88px;display:flex;align-items:center;gap:18px}}
 .dash{{width:34px;height:2px;background:{TEAL}}}
 .idx{{font-family:'Space Mono',monospace;font-weight:700;font-size:19px;
   letter-spacing:.26em;text-transform:uppercase;color:{INK}}}
 .series{{font-family:'Space Mono',monospace;font-weight:400;font-size:19px;
   letter-spacing:.26em;text-transform:uppercase;color:{MUTED_WARM}}}
 #headline{{position:absolute;left:88px;right:120px;top:530px;font-weight:800;
   line-height:.92;letter-spacing:-.045em;color:{INK};text-wrap:balance}}
 .body{{position:absolute;left:88px;top:906px;width:760px;font-weight:400;font-size:40px;
   line-height:1.36;color:{BODY_WARM};text-wrap:pretty}}
 .footer{{position:absolute;left:0;right:0;bottom:0;height:132px;padding:0 88px;
   border-top:2px solid {INK};display:flex;align-items:center;
   justify-content:space-between}}
 .brand{{font-weight:800;font-size:26px;letter-spacing:.12em;text-transform:uppercase;
   white-space:nowrap;color:{INK}}}
 .url{{font-family:'Space Mono',monospace;font-weight:400;font-size:21px;color:{TEAL}}}
</style></head><body>
<div class="poster">
  <div class="grid">{cols}</div>
  <div class="ghost">{_esc(p["index"])}</div>
  <div class="rule"></div>
  <div class="eyebrow">
    <div class="dash"></div>
    <div class="idx">{_esc(p["index"])}</div>
    <div class="series">{_esc(p["series"])}</div>
  </div>
  <div id="headline">{_esc(p["headline_a"])} {hb}</div>
  <div class="body">{_esc(p["body"])}</div>
  <div class="footer">
    <div class="brand">{_esc(p["brand"])}</div>
    <div class="url">{_esc(p["url"])}</div>
  </div>
</div>
<script>{_fit_script("1a")}</script>
</body></html>"""


# --------------------------------------------------------------------------- 1b
def _html_1b(p: dict) -> str:
    hb = ""
    if p.get("headline_b"):
        hb = f"""
    <div style="display:flex;gap:24px;align-items:stretch">
      <div style="width:8px;background:{TEAL};flex:none"></div>
      <div style="color:{TEAL}">{_esc(p["headline_b"])}</div>
    </div>"""
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="{FONTS}" rel="stylesheet">
<style>
 *{{box-sizing:border-box;margin:0;padding:0}}
 html,body{{width:{CANVAS_W}px;height:{CANVAS_H}px;overflow:hidden}}
 body{{font-family:Archivo,Helvetica,sans-serif;background:{INK_DEEP};
   -webkit-font-smoothing:antialiased}}
 .poster{{position:relative;width:{CANVAS_W}px;height:{CANVAS_H}px;overflow:hidden}}
 .spine{{position:absolute;left:0;top:0;bottom:132px;width:132px;
   border-right:1px solid {HAIRLINE_LIGHT};display:flex;flex-direction:column;
   align-items:center;justify-content:space-between;padding:64px 0;overflow:hidden}}
 .spine .series{{font-family:'Space Mono',monospace;font-weight:700;font-size:18px;
   letter-spacing:.3em;text-transform:uppercase;writing-mode:vertical-rl;color:{TEAL}}}
 .spine .num{{font-weight:900;font-size:92px;line-height:.8;letter-spacing:-.06em;
   color:{CREAM}}}
 .header{{position:absolute;left:132px;right:0;top:0;height:150px;
   border-bottom:1px solid {HAIRLINE_LIGHT};padding:0 88px;display:flex;
   align-items:center;justify-content:space-between}}
 .header .lock{{font-family:'Space Mono',monospace;font-weight:700;font-size:19px;
   letter-spacing:.26em;text-transform:uppercase;color:{CREAM}}}
 .header .prog{{font-family:'Space Mono',monospace;font-weight:400;font-size:19px;
   letter-spacing:.26em;color:{MUTED_COOL}}}
 .block{{position:absolute;left:220px;right:88px;top:290px;display:flex;
   flex-direction:column;gap:44px}}
 #headline{{font-weight:800;line-height:.94;letter-spacing:-.045em;color:{CREAM};
   display:flex;flex-direction:column;gap:44px}}
 .body{{margin-top:20px;max-width:760px;font-weight:400;font-size:40px;line-height:1.36;
   color:{BODY_COOL};text-wrap:pretty}}
 .footer{{position:absolute;left:0;right:0;bottom:0;height:132px;background:{TEAL};
   padding:0 88px 0 44px;display:flex;align-items:center;justify-content:space-between}}
 .brand{{font-weight:800;font-size:26px;letter-spacing:.12em;text-transform:uppercase;
   white-space:nowrap;color:{INK_TEAL}}}
 .url{{font-family:'Space Mono',monospace;font-weight:400;font-size:21px;color:{INK_TEAL}}}
</style></head><body>
<div class="poster">
  <div class="spine">
    <div class="series">{_esc(p["series"])}</div>
    <div class="num">{_esc(p["index"])}</div>
  </div>
  <div class="header">
    <div class="lock">{_esc(p["brand"])}</div>
    <div class="prog">{_esc(p["progress"])}</div>
  </div>
  <div class="block">
    <div id="headline">
      <div>{_esc(p["headline_a"])}</div>{hb}
    </div>
    <div class="body">{_esc(p["body"])}</div>
  </div>
  <div class="footer">
    <div class="brand">{_esc(p["brand"])}</div>
    <div class="url">{_esc(p["url"])}</div>
  </div>
</div>
<script>{_fit_script("1b")}</script>
</body></html>"""


# --------------------------------------------------------------------------- 1c
def _html_1c(p: dict) -> str:
    hb = (f'<div style="color:{CREAM}">{_esc(p["headline_b"])}</div>'
          if p.get("headline_b") else "")
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="{FONTS}" rel="stylesheet">
<style>
 *{{box-sizing:border-box;margin:0;padding:0}}
 html,body{{width:{CANVAS_W}px;height:{CANVAS_H}px;overflow:hidden}}
 body{{font-family:Archivo,Helvetica,sans-serif;background:{TEAL};
   -webkit-font-smoothing:antialiased}}
 .poster{{position:relative;width:{CANVAS_W}px;height:{CANVAS_H}px;overflow:hidden}}
 .ring1{{position:absolute;right:-180px;top:-160px;width:760px;height:760px;
   border-radius:50%;border:2px solid rgba(244,241,234,.22)}}
 .ring2{{position:absolute;right:-60px;top:-40px;width:520px;height:520px;
   border-radius:50%;border:2px solid rgba(244,241,234,.16)}}
 .eyebrow{{position:absolute;left:88px;right:88px;top:88px;display:flex;
   justify-content:space-between;align-items:center}}
 .eyebrow .idx{{font-family:'Space Mono',monospace;font-weight:700;font-size:19px;
   letter-spacing:.26em;text-transform:uppercase;color:#EAF4F6}}
 .eyebrow .series{{font-family:'Space Mono',monospace;font-weight:700;font-size:19px;
   letter-spacing:.26em;text-transform:uppercase;color:rgba(234,244,246,.62)}}
 .stack{{position:absolute;left:88px;right:88px;top:216px}}
 .numeral{{font-weight:900;font-size:250px;line-height:.78;letter-spacing:-.07em;
   color:{CREAM}}}
 #headline{{margin-top:52px;font-weight:800;line-height:.96;letter-spacing:-.04em;
   max-width:900px;color:{TEAL_SHADOW}}}
 .base{{position:absolute;left:0;right:0;bottom:0;height:400px;background:{CREAM};
   padding:76px 88px 0;display:flex;flex-direction:column;justify-content:space-between}}
 .body{{font-weight:400;font-size:40px;line-height:1.36;max-width:840px;
   color:{BODY_WARM_ALT};text-wrap:pretty}}
 .footer{{height:132px;border-top:2px solid {INK};display:flex;align-items:center;
   justify-content:space-between;margin:0 -88px;padding:0 88px}}
 .brand{{font-weight:800;font-size:26px;letter-spacing:.12em;text-transform:uppercase;
   white-space:nowrap;color:{INK}}}
 .url{{font-family:'Space Mono',monospace;font-weight:400;font-size:21px;color:{TEAL}}}
</style></head><body>
<div class="poster">
  <div class="ring1"></div>
  <div class="ring2"></div>
  <div class="eyebrow">
    <div class="idx">{_esc(p["index"])}</div>
    <div class="series">{_esc(p["series"])}</div>
  </div>
  <div class="stack">
    <div class="numeral">{_esc(p["index"])}</div>
    <div id="headline">
      <div>{_esc(p["headline_a"])}</div>{hb}
    </div>
  </div>
  <div class="base">
    <div class="body">{_esc(p["body"])}</div>
    <div class="footer">
      <div class="brand">{_esc(p["brand"])}</div>
      <div class="url">{_esc(p["url"])}</div>
    </div>
  </div>
</div>
<script>{_fit_script("1c")}</script>
</body></html>"""


BUILDERS = {"1a": _html_1a, "1b": _html_1b, "1c": _html_1c}


def payload_from_curriculum(post: dict, *, series_len: int = 6,
                            brand: str = "Spark Careers",
                            url: str = "spark.risepointcareers.com") -> dict:
    """Map a curriculum record onto the template content model.

    The poster numeral keys off `week_in_series` rather than the module number:
    the B2B curriculum restarts module numbering at week 16 when it moves from
    the recruitment track to the HRMS track, so module number is not unique
    across a series. Callers may override `index` afterwards.
    """
    day_pos = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].index(post["day"]) + 1
    index = post.get("week_in_series") or post.get("module_number") or 0
    return {
        "index": f"{int(index):02d}",
        "series": post["role"],
        "progress": f"{day_pos:02d} / {series_len:02d}",
        "headline_a": post["headline_a"],
        "headline_b": post.get("headline_b", ""),
        "body": post["body"],
        "brand": brand,
        "url": url,
    }


def render_posts(payloads: list[tuple[dict, Path]], direction: str = "1a") -> None:
    """Render a batch of payloads. Each tuple is (payload, output_path).

    Rendered at 2x and downsampled to 1080x1350 so hairlines survive, per the
    handoff's export note.
    """
    if direction not in BUILDERS:
        raise ValueError(f"unknown direction {direction!r}, expected one of {list(BUILDERS)}")

    from PIL import Image

    scratch = Path(__file__).resolve().parent / "_poster_html"
    scratch.mkdir(exist_ok=True)
    build = BUILDERS[direction]

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = browser.new_context(viewport={"width": CANVAS_W, "height": CANVAS_H},
                                  device_scale_factor=2)
        page = ctx.new_page()
        for payload, out in payloads:
            f = scratch / f"_{direction}_{out.stem}.html"
            f.write_text(build(payload), encoding="utf-8")
            page.goto(f"file:///{f.as_posix()}", wait_until="networkidle")
            page.wait_for_timeout(700)
            out.parent.mkdir(parents=True, exist_ok=True)
            tmp = out.with_suffix(".2x.png")
            page.screenshot(path=str(tmp),
                            clip={"x": 0, "y": 0, "width": CANVAS_W, "height": CANVAS_H})
            with Image.open(tmp) as im:
                im.resize((CANVAS_W, CANVAS_H), Image.LANCZOS).save(out)
            tmp.unlink(missing_ok=True)
            f.unlink(missing_ok=True)
        browser.close()


def load_curriculum() -> dict:
    return json.loads((REPO / "content" / "b2c_curriculum.json").read_text(encoding="utf-8"))
