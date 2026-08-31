#!/usr/bin/env python3
r"""
texify_figcrop.py — the book-agnostic half of a figure extractor.

Every book in this fleet crops its figures out of a born-digital PDF with its own
`krop_figs.py` / `texify_figs_<book>.py`. Those scripts differ in what only they can know —
the caption face, the text column, which drawings are page furniture — but they kept
re-deriving the same handful of PyMuPDF facts, and each one re-learned them by shipping a
broken crop first. This module holds that shared half so a fix lands once.

WHAT GOES WRONG, AND WHY NONE OF IT SHOWS UP IN A PAGE COUNT
-----------------------------------------------------------
A figure extractor that places N pages for N figures looks finished. Every defect below
survives that check, `--dry-run`, and `verify.py`; only the eye and the raster test in
`edge_ink()` catch them.

  * `show_pdf_page(clip=…)` renders EVERY glyph inside the rect, not just the ones the
    union chose. A pad that reaches past the caption's top prints the caption inside the
    figure. -> `pull_back()`, and clamp the rect to the band.
  * PyMuPDF's Rect operators SILENTLY DISCARD degenerate rects: for a zero-height path
    `r & band` is empty and `box | r` is a no-op. Line art is mostly degenerate rects — an
    axis, a dashed guide, a polygon edge — so a union built on the operators keeps only the
    first 2-D path it happens to see. -> `Union`.
  * PyMuPDF splits a text line at every inline formula. A floor scan run on raw lines sees
    only fragments, none of them full measure, and leaves the tail of a paragraph inside the
    next float's band. -> `yclusters()`.
  * ...but clustering blindly also merges a figure's own labels into one wide "line", and the
    floor scan then cuts the top off the figure. -> the horizontal-contiguity gate in
    `yclusters()`.
  * A rotated axis title is artwork wherever it starts, including LEFT OF the text column on
    a wide plate, where a margin test scores it as running text. -> `rotated` in
    `text_lines()`.
  * A display equation's fraction bars are DRAWINGS. In the band above a float they join the
    artwork union and drag the crop up over the display. -> `is_math_rule()`.
  * A caption's box and a label's box overlap even when their ink does not: a label carries
    an 18pt box for 10pt of ink. Excluding a line from the figure because its box touches the
    caption's box drops genuine axis labels. -> `in_caption()` tests the line's CENTRE.

None of this is book-specific; all of it was found by rendering crops and looking.
"""
from __future__ import annotations

import re

import fitz

__all__ = ["text_lines", "yclusters", "Union", "is_text_furniture", "is_math_rule", "in_caption",
           "RowIndex",
           "pull_back", "letters", "measure_columns", "edge_ink"]

LETTER_RE = re.compile(r"[A-Za-z]")


def letters(txt: str) -> int:
    """How many ASCII letters the text carries.

    ⚠ COUNT LETTERS, NEVER WORDS. These PDFs' spans carry no inter-word spaces, so
    "hullintroducedintheAppetizer." is ONE word to a `\\w+` scan and a word-count test scores a
    whole line of prose as an artwork label."""
    return len(LETTER_RE.findall(txt))


def text_lines(page, drop_font_prefixes: tuple[str, ...] = ()):
    """Every text line as (rect, spans, text, rotated), sorted top-to-bottom then left-to-right.

    LINE-level, never BLOCK-level: PyMuPDF happily merges a figure's axis labels and its
    caption into ONE block, so a block-level font test misses the caption and a block-level
    bbox swallows the caption into the artwork.

    `rotated` is True for text set at dir=(0,±1) — the y-axis titles. ⚠ ROTATED TEXT IS
    ALWAYS ARTWORK. On the widest plates it starts left of the text column (one book sets
    "Newton iterations" at x=146 in a column that starts at 161), where every margin test
    would call it running text and raise the floor straight through the top of the figure.

    `drop_font_prefixes` drops spans by font-name prefix — for a tagged PDF whose invisible
    spoken-form runs would otherwise join the union and drag its edges outward."""
    out = []
    for b in page.get_text("dict")["blocks"]:
        if b.get("type") != 0:
            continue
        for l in b.get("lines", []):
            spans = [s for s in l["spans"]
                     if s["text"].strip()
                     and not (drop_font_prefixes
                              and s["font"].startswith(drop_font_prefixes))]
            if not spans:
                continue
            txt = " ".join(" ".join(s["text"] for s in spans).split())
            r = fitz.Rect(min(s["bbox"][0] for s in spans), min(s["bbox"][1] for s in spans),
                          max(s["bbox"][2] for s in spans), max(s["bbox"][3] for s in spans))
            # The line bbox is the safer outer bound — but ONLY when nothing was dropped. A
            # tagged PDF precedes every formula with an INVISIBLE spoken-form span, and the
            # line's own bbox still covers it; falling back to that box would re-admit exactly
            # the zero-ink extent `drop_font_prefixes` exists to remove.
            if len(spans) == len([s for s in l["spans"] if s["text"].strip()]):
                lb = fitz.Rect(l["bbox"])
                if not lb.is_empty and lb.contains(r):
                    r = lb
            out.append((r, spans, txt, abs(l["dir"][1]) > 0.5))
    return sorted(out, key=lambda t: (t[0].y0, t[0].x0))


def yclusters(lines, x_gap: float = 6.0, max_h: float = 30.0):
    """Text lines grouped by OVERLAPPING VERTICAL EXTENT *and* horizontal contiguity.

    ⚠ THE FLOOR SCAN MUST RUN ON CLUSTERS. PyMuPDF splits a text line at every inline formula,
    and this fleet's prose is made of them: "We call a point of the form θ1x1 + · · · + θkxk,
    where …" comes back as three fragments, none of them full measure. A floor scan on raw
    lines therefore leaves the tail of a paragraph — or of a display — sitting inside the next
    float's band, and the crop opens with half a line of prose.

    ⚠ THE CONTIGUITY GATE IS WHAT KEEPS THIS SAFE. The fragments of one typeset line ABUT;
    a figure's own labels do not. Merging without the gate turns a row of labels
    ("segment 4 … segment 1", or a pair of "0"s under two panels) into one 300pt, 32-letter
    "line", the floor scan calls it running text, and the top of the figure is cut off.

    ⚠ AND `max_h` IS THE OTHER HALF OF THAT GATE. A cluster exists to reassemble ONE typeset
    line, and no typeset line is 64pt tall — but a TeX arrow is, because it is drawn from
    repeated rule GLYPHS ('H', '\\x11', '\\x0e') that PyMuPDF reports as text. Those glyphs abut
    each other, so the contiguity gate happily chained a transition diagram's twelve arrow
    pieces into one 206pt-wide "line" carrying twelve 'H' letters, which the letter-count rule
    scored as running text; the floor jumped to the bottom of the arrows and the figure lost
    its top box and every arrow with it (measured: a 132.9pt figure came out 34.9pt tall).

    Rotated lines are excluded — they are artwork, and a tall rotated title would chain
    unrelated rows together. Used ONLY for the floor scan, where it may move the floor DOWN,
    never up."""
    out = []
    for r, sp, t, rot in lines:
        if rot:
            continue
        if out:
            pr, psp, pt, _ = out[-1]
            overlap = min(pr.y1, r.y1) - max(pr.y0, r.y0)
            touching = r.x0 <= pr.x1 + x_gap and pr.x0 <= r.x1 + x_gap
            merged = pr | r
            if (overlap > 0.5 * min(pr.height or 1, r.height or 1) and touching
                    and merged.height <= max_h):
                out[-1] = (merged, psp + list(sp), pt + " " + t, False)
                continue
        out.append((r, list(sp), t, False))
    return out


class Union:
    """A bounding box accumulated as FOUR PLAIN FLOATS, never as a fitz.Rect.

    ⚠ THIS IS NOT A STYLE CHOICE. This fleet's artwork is drawn almost entirely from
    DEGENERATE rects — an axis, a histogram bar edge, a dashed guide, a polygon edge are each
    a path of zero width or zero height. PyMuPDF calls such a rect `is_empty`, and BOTH of its
    rect operators then discard it silently: `r & band` returns empty and `box | r`
    (include_rect) returns box unchanged. A union built on the operators keeps only the first
    genuinely 2-D path it sees — one book's 50-drawing histogram (47 of them degenerate) came
    out as the 8pt-tall bottom rule of the frame above it, reported as a successful crop.

    `clip` is applied per-item, so an item that only partly overlaps the band contributes its
    overlapping part instead of being dropped whole."""

    __slots__ = ("box", "clip", "n")

    def __init__(self, clip: fitz.Rect | None = None):
        self.box = None
        self.clip = clip
        self.n = 0

    def add(self, r) -> bool:
        x0, y0, x1, y1 = r.x0, r.y0, r.x1, r.y1
        if self.clip is not None:
            x0, y0 = max(x0, self.clip.x0), max(y0, self.clip.y0)
            x1, y1 = min(x1, self.clip.x1), min(y1, self.clip.y1)
            if x1 < x0 or y1 < y0:
                return False
        self.box = ([x0, y0, x1, y1] if self.box is None else
                    [min(self.box[0], x0), min(self.box[1], y0),
                     max(self.box[2], x1), max(self.box[3], y1)])
        self.n += 1
        return True

    def __bool__(self):
        return self.box is not None

    @property
    def rect(self):
        return None if self.box is None else fitz.Rect(*self.box)


def is_text_furniture(rect, lines, pad: float = 1.5, near_x: float = 24.0,
                      small: float = 14.0) -> bool:
    """A DRAWING THAT BELONGS TO A LINE OF TEXT, not to a figure — a fraction bar, a radical
    overline, an \\overline, or the little end-of-proof box.

    ⚠ A DISPLAY EQUATION CONTRIBUTES DRAWINGS. Zero-height filled rects from a display sitting
    between the running text and the float join the artwork union and pull the crop up over
    the display — and since the display is centred, short and often wordless, no `is_body`
    test reliably catches its text either. The end-of-proof box is the same problem in miniature
    and it is the one that survives longest: a 7x7pt square is 2-D, so a "thin strokes only"
    filter lets it through, and it sits 14pt above the artwork, so an abutment test lets it
    through too. Measured on one page: the box at x=421.2..428.1, y=366.5..373.9 pulled the
    crop's top edge up 21pt and sliced the display above it in half.

    The signature both share: the drawing lies ON A TEXT LINE'S OWN ROW — its vertical extent
    inside that line's, and horizontally no further than `near_x` past either end of it (24pt:
    the box measured above sits 15.9pt past the end of its display and 11.7pt past the trailing
    full stop). A figure's axis, dashed guide or plot frame is nowhere near any label's row in
    that sense. Only SMALL or THIN ink qualifies; a figure's 2-D mass never does.

    ⚠ THE HOST LINE MUST ACTUALLY BE TEXT. A TeX arrow is built from repeated rule GLYPHS that
    PyMuPDF reports as text lines carrying no alphanumerics ('\\x11', '\\x0e'), and a diagram's
    ARROWHEADS then sit squarely on those "lines" — so without this test the rule quietly
    classified a transition diagram's own arrowheads as text furniture."""
    thin = rect.width < 2.5 or rect.height < 2.5
    if not (thin or (rect.width < small and rect.height < small)):
        return False
    for lr, t in _rows(lines).near(rect.y0, rect.y1):
        if lr.y0 - pad <= rect.y0 and rect.y1 <= lr.y1 + pad:
            if lr.x0 - near_x <= rect.x0 and rect.x1 <= lr.x1 + near_x:
                return True
    return False


class RowIndex:
    """Text lines bucketed by y, so `is_text_furniture` is not O(drawings x lines).

    ⚠ THIS IS A CORRECTNESS ISSUE DRESSED AS A PERFORMANCE ONE. A scatter plot is thousands of
    tiny circles, and every one of them is "small" enough to reach the line scan; on one book's
    chapter that turned a 20-second extraction into one that had not finished in ten minutes,
    which in practice means the fix gets reverted rather than waited for."""

    __slots__ = ("buckets", "n")
    H = 24.0

    def __init__(self, lines):
        self.buckets = {}
        self.n = len(lines)
        for lr, _sp, t, _rot in lines:
            if not any(c.isalnum() for c in t):
                continue          # a TeX arrow's rule glyphs are not a line of text
            for b in range(int(lr.y0 // self.H), int(lr.y1 // self.H) + 1):
                self.buckets.setdefault(b, []).append((lr, t))

    def near(self, y0, y1):
        seen, out = set(), []
        for b in range(int(y0 // self.H) - 1, int(y1 // self.H) + 2):
            for item in self.buckets.get(b, ()):
                if id(item[0]) not in seen:
                    seen.add(id(item[0]))
                    out.append(item)
        return out


_ROW_CACHE = {}


def _rows(lines):
    """RowIndex for `lines`, memoised on the list's identity and length."""
    if isinstance(lines, RowIndex):
        return lines
    key = (id(lines), len(lines))
    idx = _ROW_CACHE.get(key)
    if idx is None:
        if len(_ROW_CACHE) > 64:
            _ROW_CACHE.clear()
        idx = _ROW_CACHE[key] = RowIndex(lines)
    return idx


# the name the extractors used before end-of-proof boxes joined the story
is_math_rule = is_text_furniture


def in_caption(r, cap_rects, slack: float = 1.0) -> bool:
    """True when this line belongs to one of the page's caption blocks.

    ⚠ DECIDED ON THE LINE'S CENTRE, NOT ON BBOX OVERLAP. A label like "F1(x) = ‖Ax − b‖2"
    carries an 18pt bbox for 10pt of ink, so its box dips several points into the caption
    below it while the ink stops well clear (measured: ink ends at y=307.7, the caption's ink
    starts at 310.2). Excluding such a line on overlap dropped the x-axis label from eight
    figures of one book — each of which still placed a page and still looked plausible."""
    ctr = (r.y0 + r.y1) / 2
    return any(c.y0 - slack <= ctr <= c.y1 + slack and r.x1 > c.x0 and r.x0 < c.x1
               for c in cap_rects)


def pull_back(rect, core, foreign, pad_only: bool = True):
    """Shrink `rect`'s top/bottom off anything foreign, never past `core`. Returns `rect`.

    ⚠ THE CLIP RENDERS EVERY GLYPH INSIDE THE RECT, not just the ones the union chose. A pad
    that reaches into the line above, or into the caption below, prints half of it inside the
    figure — which is how one book shipped four figures opening with a slice of the previous
    caption and four more closing with the first line of their own.

    `core` is the unpadded union of everything the figure OWNS, so the pull-back can never eat
    the artwork: an edge is only moved back to `core`, never inside it. `foreign` is any
    iterable of rects the crop must not show.

    ⚠ ABOVE/BELOW IS DECIDED ON THE FOREIGN LINE'S CENTRE, not its box. A line of text carries a
    box far taller than its ink, so the line immediately above a figure routinely has a box that
    dips below the artwork's top edge — and a test on its lower edge then reports it as "not
    above", declines to pull back, and the pad prints the bottom of that line inside the figure.
    Where the box does overlap the artwork the pad is simply given up (`core` is the floor),
    which is the right trade: no padding beats foreign ink."""
    for fr in foreign:
        if fr.x1 <= rect.x0 or fr.x0 >= rect.x1:
            continue                     # not horizontally in the way
        ctr = (fr.y0 + fr.y1) / 2
        if ctr < core.y0 and fr.y1 > rect.y0:
            rect.y0 = min(max(rect.y0, fr.y1 + 1.0), core.y0)
        if ctr > core.y1 and fr.y0 < rect.y1:
            rect.y1 = max(min(rect.y1, fr.y0 - 1.0), core.y1)
    return rect


# ----------------------------------------------------------------------------- diagnostics
def measure_columns(doc, pages, min_width: float = 300.0, min_size: float = 9.5,
                    head_y: float = 0.0):
    """{'even': ((x0, x1), n), 'odd': ((x0, x1), n)} — the book's body measure by page parity.

    ⚠ RUN THIS BEFORE HARD-CODING A COLUMN. Several books in this fleet shift their text block
    between recto and verso (one by 54pt), and a single fixed column then clips one parity's
    artwork on one side and leaves a blank margin on the other — which looks fine in a page
    count and wrong on a contact sheet. `pages` is a 1-based iterable of physical page numbers."""
    from collections import Counter
    tally = {"even": Counter(), "odd": Counter()}
    for pno in pages:
        page = doc[pno - 1]
        key = "even" if pno % 2 == 0 else "odd"
        for r, sp, _t, rot in text_lines(page):
            if rot or r.y0 < head_y:
                continue
            if r.width > min_width and max(s["size"] for s in sp) >= min_size:
                tally[key][(round(r.x0), round(r.x1))] += 1
    return {k: (v.most_common(1)[0] if v else (None, 0)) for k, v in tally.items()}


def edge_ink(pdf, dpi: int = 200, threshold: int = 200):
    """[(page_number, (top, bottom, left, right))] — cropped pages whose INK TOUCHES the border.

    ⚠ THE CHEAPEST HONEST CHECK THERE IS. A crop that shaved an axis label or a diagram's top
    row places its page and passes every count; what it cannot do is keep its ink off the
    outermost pixel row. Anything this reports is either a genuine clip or a label that ends
    exactly at the caption — look at both, at 400dpi."""
    doc = fitz.open(pdf) if not isinstance(pdf, fitz.Document) else pdf
    hits = []
    for i in range(doc.page_count):
        pm = doc[i].get_pixmap(dpi=dpi, colorspace=fitz.csGRAY)
        w, h = pm.width, pm.height
        e = (sum(pm.pixel(x, 0)[0] < threshold for x in range(w)),
             sum(pm.pixel(x, h - 1)[0] < threshold for x in range(w)),
             sum(pm.pixel(0, y)[0] < threshold for y in range(h)),
             sum(pm.pixel(w - 1, y)[0] < threshold for y in range(h)))
        if any(e):
            hits.append((i + 1, e))
    return hits
