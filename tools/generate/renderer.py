"""Spark Careers visual renderer.

Reads a post spec, picks the right HTML template, substitutes content, and
uses Playwright + headless Chromium to produce a 1080x1350 PNG.
"""

from __future__ import annotations

import html
import re
from pathlib import Path

from playwright.sync_api import sync_playwright

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"

TEMPLATE_BY_DAY = {
    "mon": "mission_monday.html",
    "tue": "trade_secrets.html",
    "wed": "spotlight.html",
    "thu": "commitment.html",
    "fri": "feature_friday.html",
}


def _wrap_highlights(headline: str, highlights: list[str]) -> str:
    """HTML-escape headline, then wrap each highlight word in a span.

    Matches whole words case-insensitively. Each highlight is applied once
    (first match wins) so we don't double-wrap.
    """
    escaped = html.escape(headline)
    for word in highlights:
        if not word:
            continue
        word_escaped = html.escape(word)
        pattern = re.compile(rf"\b({re.escape(word_escaped)})", re.IGNORECASE)
        escaped, n = pattern.subn(r'<span class="accent">\1</span>', escaped, count=1)
    return escaped


def render_post(spec: dict, output_path: Path) -> None:
    """Render one post spec to a PNG at output_path.

    spec keys:
      - day:           'mon' | 'tue' | 'wed' | 'thu' | 'fri'
      - audience:      'b2b' | 'b2c'
      - theme_tag:     str, e.g. 'MISSION MONDAY'
      - overline:      optional str (e.g. 'THE INSIGHT')
      - badge_number:  optional int (Trade Secrets only)
      - headline:      str
      - highlights:    list[str], words to accent-color
      - subline:       str
      - url:           str (display, not the tracked one)
      - footer_meta:   str (e.g. 'For employers · Spark Careers Enterprise')
    """
    template_name = TEMPLATE_BY_DAY[spec["day"]]
    template_path = TEMPLATES_DIR / template_name
    html_text = template_path.read_text(encoding="utf-8")

    replacements = {
        "{{THEME_TAG}}": html.escape(spec.get("theme_tag", "")),
        "{{OVERLINE}}": html.escape(spec.get("overline", "")),
        "{{BADGE_NUMBER}}": f"NO. {int(spec['badge_number']):02d}" if spec.get("badge_number") else "",
        "{{HEADLINE_HTML}}": _wrap_highlights(spec.get("headline", ""), spec.get("highlights", [])),
        "{{SUBLINE}}": html.escape(spec.get("subline", "")),
        "{{URL}}": html.escape(spec.get("url", "")),
        "{{FOOTER_META}}": html.escape(spec.get("footer_meta", "")),
        "{{AUDIENCE_CLASS}}": spec.get("audience", "b2b"),
    }
    for marker, value in replacements.items():
        html_text = html_text.replace(marker, value)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(viewport={"width": 1080, "height": 1350},
                                      device_scale_factor=2)
        page = context.new_page()
        # Serve from the templates dir so the <link href="css/base.css"> resolves.
        page.goto(f"file:///{template_path.parent.as_posix()}/_render.html",
                  wait_until="domcontentloaded")
        page.set_content(html_text, wait_until="networkidle")
        # Give Google Fonts a moment to settle
        page.wait_for_timeout(500)
        page.screenshot(path=str(output_path), full_page=False,
                        clip={"x": 0, "y": 0, "width": 1080, "height": 1350},
                        omit_background=False)
        browser.close()


def render_post_simple(spec: dict, output_path: Path) -> None:
    """Variant that writes the merged HTML to a tempfile and renders from there.

    Use this if set_content() has issues with relative asset paths.
    """
    template_name = TEMPLATE_BY_DAY[spec["day"]]
    template_path = TEMPLATES_DIR / template_name
    html_text = template_path.read_text(encoding="utf-8")

    replacements = {
        "{{THEME_TAG}}": html.escape(spec.get("theme_tag", "")),
        "{{OVERLINE}}": html.escape(spec.get("overline", "")),
        "{{BADGE_NUMBER}}": f"NO. {int(spec['badge_number']):02d}" if spec.get("badge_number") else "",
        "{{HEADLINE_HTML}}": _wrap_highlights(spec.get("headline", ""), spec.get("highlights", [])),
        "{{SUBLINE}}": html.escape(spec.get("subline", "")),
        "{{URL}}": html.escape(spec.get("url", "")),
        "{{FOOTER_META}}": html.escape(spec.get("footer_meta", "")),
        "{{AUDIENCE_CLASS}}": spec.get("audience", "b2b"),
    }
    for marker, value in replacements.items():
        html_text = html_text.replace(marker, value)

    # Write rendered HTML next to the template so relative asset paths still resolve.
    tmp_html = template_path.parent / f"_render_{spec['day']}_{spec['audience']}.html"
    tmp_html.write_text(html_text, encoding="utf-8")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            context = browser.new_context(viewport={"width": 1080, "height": 1350})
            page = context.new_page()
            page.goto(f"file:///{tmp_html.as_posix()}", wait_until="networkidle")
            page.wait_for_timeout(800)  # let Google Fonts settle
            page.screenshot(path=str(output_path),
                            clip={"x": 0, "y": 0, "width": 1080, "height": 1350})
            browser.close()
    finally:
        try:
            tmp_html.unlink()
        except OSError:
            pass


if __name__ == "__main__":
    # Smoke test across all 5 layouts
    out_dir = Path(__file__).resolve().parent / "_test_renders"
    out_dir.mkdir(exist_ok=True)

    posts = [
        {
            "day": "mon", "audience": "b2b", "theme_tag": "MISSION MONDAY",
            "headline": "Hiring shouldn't run on screenshots and group chats.",
            "highlights": ["screenshots", "chats."],
            "subline": "One workspace for every applicant, every channel, every stage.",
            "url": "hire.risepointcareers.com",
            "footer_meta": "For employers · Spark Careers Enterprise",
        },
        {
            "day": "tue", "audience": "b2b", "theme_tag": "TRADE SECRETS",
            "overline": "THE INSIGHT", "badge_number": 3,
            "headline": "Three columns in a spreadsheet are not a hiring pipeline.",
            "highlights": ["pipeline."],
            "subline": "",
            "url": "hire.risepointcareers.com",
            "footer_meta": "For employers · Spark Careers Enterprise",
        },
        {
            "day": "wed", "audience": "b2c", "theme_tag": "SPOTLIGHT",
            "headline": "Career change isn't failure. It's the whole point.",
            "highlights": ["point."],
            "subline": "For the people pivoting toward something better.",
            "url": "spark.stepupcareers.com",
            "footer_meta": "For job seekers · Spark Careers",
        },
        {
            "day": "thu", "audience": "b2b", "theme_tag": "COMMITMENT THURSDAY",
            "headline": "Hiring while running everything else? That's not a flaw. That's the job.",
            "highlights": ["job."],
            "subline": "Keep going. The right tool turns admin back into momentum.",
            "url": "hire.risepointcareers.com",
            "footer_meta": "For employers · Spark Careers Enterprise",
        },
        {
            "day": "fri", "audience": "b2c", "theme_tag": "FEATURE FRIDAY",
            "overline": "THIS WEEK'S FEATURE",
            "headline": "Close the week. Sharpen the saw. Try one CV rewrite.",
            "highlights": ["Sharpen"],
            "subline": "Free · 5 minutes · Real ATS score",
            "url": "spark.stepupcareers.com",
            "footer_meta": "For job seekers · Spark Careers",
        },
    ]

    for p in posts:
        out = out_dir / f"test-{p['day']}-{p['audience']}.png"
        print(f"Rendering {p['theme_tag']} ({p['audience']})…")
        render_post_simple(p, out)
    print(f"Done. Output in {out_dir}")
