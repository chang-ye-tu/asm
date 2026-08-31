#!/usr/bin/env python3
r"""
texify_figs_srm.py — crop this source's 17 figures out of src/srm.pdf.

Run once, before converting:

    python3 texify_figs_srm.py            # writes assets/figs/srm_<key>.pdf, one per figure
    python3 texify_figs_srm.py --check    # + the ink-touches-the-border report

The book-agnostic half lives in `texify_figcrop.py` (copied verbatim from books/islr):
`text_lines`, `Union`, `pull_back`, `edge_ink`. Everything below is what only this source
can know.

WHY THIS SOURCE NEEDS ITS OWN EXTRACTOR, AND WHY IT IS SMALL
------------------------------------------------------------
The fleet's book extractors hunt for figures by CAPTION ("Figure 3.2"), because a textbook
labels every plate. This source labels none: a figure is simply artwork sitting between two
paragraphs of a question, referred to as "the following scree plot" or "the graph". There is
nothing to pattern-match, so the inventory is HAND-WRITTEN below and read off the page
images. Seventeen entries, once.

That also makes the job easy in the other direction. Sixteen of the seventeen are EMBEDDED
RASTERS, so their exact extent is `page.get_image_rects(xref)` — no union to build, no floor
to scan, no caption to pull back off. Every one of the sixteen was checked for intruding
glyphs (a `show_pdf_page(clip=…)` renders every glyph inside the rect, not just the ones the
crop meant to keep) and all sixteen are clean: the "I."/"II."/"III." labels on p19 and the
"(A)"-"(E)" labels on p35 sit OUTSIDE their panels.

⚠ THE ONE VECTOR FIGURE IS q57, AND IT SHARES ITS PAGE WITH A TABLE. p42 carries 280
drawings; 142 of them are the cell rules of the R/X/Y/Z data table at y=175..281 and the
other 138 are the regression tree at y=364..498. A whole-page union of the drawings would
box the table into the figure. The band below cuts between them, and the tree's own text
labels ("Z <= 3", "Y=A,B", "X=F", "T1".."T4") are admitted by the same band so the crop
keeps them.

⚠ DO NOT "IMPROVE" THIS BY DETECTING DRAWINGS AUTOMATICALLY. 20 further pages carry
drawings that are not figures at all: table rules (p3, p4, p10, p13, p20, p27, p33, p34,
p39, p40, p43, p44, p47, p51-54, p60), fraction bars and radicals (p30, p57, p63, p67, p71),
and — on p15 and p61 — white rectangles Word paints behind a line of text. A "page has
drawings => page has a figure" rule reports 26 figures where there is one.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import fitz

from texify_figcrop import Union, edge_ink, pull_back, text_lines

# ------------------------------------------------------------------ inventory ----
# (key, page1, selector) in DOCUMENT ORDER. The key is what SKILL.srm.md tells the
# converter to write: `\srmfig{q35}` -> assets/figs/srm_q35.pdf.
#
#   ("image", k)      the k-th embedded raster on the page, ordered top-to-bottom then
#                     left-to-right — the order they are read in.
#   ("band", y0, y1)  vector artwork: everything (drawings AND text) whose ink lies in the
#                     horizontal band [y0, y1] of the page, in PDF points from the top.
#
# `q48a`..`q48e` are the five ANSWER CHOICES of question 48, which are themselves pictures;
# `q48` is the tree above them. `q26a`..`q26c` are that question's three roman-numbered
# panels. Every other question has at most one figure and its key is just the question.
FIGURES = [
    ("q26a", 19, ("image", 0)),          # I.   the two-rectangle space
    ("q26b", 19, ("image", 1)),          # II.  the curved boundary
    ("q26c", 19, ("image", 2)),          # III. the diagonal boundary
    ("q33",  23, ("image", 0)),          # auto-claim regression tree (rpart plot)
    ("q35",  25, ("image", 0)),          # scree plot
    ("q39",  29, ("image", 0)),          # scatter plot, quadratic cloud
    ("q48",  35, ("image", 0)),          # the tree, above the five choices
    ("q48a", 35, ("image", 1)),
    ("q48b", 35, ("image", 2)),
    ("q48c", 35, ("image", 3)),
    ("q48d", 35, ("image", 4)),
    ("q48e", 35, ("image", 5)),
    ("q51",  37, ("image", 0)),          # duck-weight regression tree
    ("q57",  42, ("band", 330.0, 510.0)),  # THE ONE VECTOR FIGURE — see the header note
    ("q63",  47, ("image", 0)),          # car-seat regression tree (rpart plot)
    ("q66",  49, ("image", 0)),          # R1..R5 regression tree
    ("q73",  55, ("image", 0)),          # MSE-vs-tree-size line chart
]

PAD = 3.0          # points of white space kept around the ink, before any pull-back


ROW_TOL = 24.0     # two panels are on the SAME ROW if their tops differ by less than this


def _image_rects(page):
    """Every embedded raster's rect, in reading order (top-to-bottom, left-to-right).

    ⚠ ORDER IS THE INTERFACE. The inventory addresses images by index, so this order is
    what `("image", k)` means. `page.get_images()` returns them in xref order, which is
    the order they were WRITTEN, not the order they are read.

    ⚠ AND SORTING ON (y0, x0) IS NOT READING ORDER — this bit, for real, on p35. That page
    sets the five answer-choice pictures two-up, and the two panels of a row are not laid
    out to the same baseline: choice (C) starts at y=455.8 and choice (D), to its RIGHT, at
    y=454.1. A plain (y0, x0) sort is therefore 1.7pt away from putting (D) before (C) — and
    it does. Nothing downstream can see it: both crops are written, both are the right size,
    the count is 17, `edge_ink` is clean, and the built PDF shows a perfectly good picture
    under each of (C) and (D). They are just the wrong way round.

    So bucket into ROWS first (tops within ROW_TOL) and sort left-to-right inside a row."""
    rects = []
    for info in page.get_images(full=True):
        rects.extend(page.get_image_rects(info[0]))
    rects.sort(key=lambda r: r.y0)
    rows: list[list] = []
    for r in rects:
        if rows and r.y0 - rows[-1][0].y0 < ROW_TOL:
            rows[-1].append(r)
        else:
            rows.append([r])
    return [r for row in rows for r in sorted(row, key=lambda r: r.x0)]


def _band_rect(page, y0: float, y1: float):
    """The union of every drawing and every text line whose ink lies inside [y0, y1].

    Built with `Union` (four plain floats), NOT with fitz.Rect's operators: this tree is
    drawn almost entirely from ZERO-HEIGHT rects — the horizontal connectors between the
    split boxes — and `box | r` silently discards a degenerate rect, so an operator-built
    union would keep only the first genuinely 2-D box and crop the tree to it."""
    clip = fitz.Rect(0, y0, page.rect.x1, y1)
    u = Union(clip=clip)
    for d in page.get_drawings():
        u.add(d["rect"])
    for r, _spans, _t, _rot in text_lines(page):
        if y0 <= (r.y0 + r.y1) / 2 <= y1:
            u.add(r)
    if not u:
        raise SystemExit(f"band {y0}-{y1} on page {page.number + 1} is empty")
    return u.rect


def crop(doc, key: str, page1: int, sel, out_dir: Path) -> Path:
    page = doc[page1 - 1]
    if sel[0] == "image":
        rects = _image_rects(page)
        if sel[1] >= len(rects):
            raise SystemExit(f"{key}: page {page1} has {len(rects)} images, wanted #{sel[1]}")
        core = fitz.Rect(rects[sel[1]])
    else:
        core = _band_rect(page, sel[1], sel[2])

    box = fitz.Rect(core) + fitz.Rect(-PAD, -PAD, PAD, PAD)
    box &= page.rect
    # The pad may now reach into the paragraph above or below. `show_pdf_page` would print
    # that ink inside the figure, so give the pad back wherever it does — never eating into
    # `core`, which is the artwork itself.
    foreign = [r for r, _s, _t, _rot in text_lines(page)
               if not (core.y0 - 0.5 <= (r.y0 + r.y1) / 2 <= core.y1 + 0.5)]
    box = pull_back(box, core, foreign)

    out = fitz.open()
    dst = out.new_page(width=box.width, height=box.height)
    dst.show_pdf_page(dst.rect, doc, page1 - 1, clip=box)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"srm_{key}.pdf"
    out.save(str(path))
    out.close()
    return path


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", default="src/srm.pdf")
    ap.add_argument("--out", default="assets/figs")
    ap.add_argument("--contact", default=".texify_work/srm_figs_contact.pdf",
                    help="one multi-page PDF of every crop, for looking at them")
    ap.add_argument("--check", action="store_true",
                    help="report crops whose ink touches the border (a clipped figure)")
    args = ap.parse_args(argv)

    doc = fitz.open(args.src)
    out_dir = Path(args.out)
    paths = []
    for key, page1, sel in FIGURES:
        p = crop(doc, key, page1, sel, out_dir)
        d = fitz.open(str(p))
        print(f"  {key:6s} p{page1:<3d} -> {p}  "
              f"{d[0].rect.width:6.1f} x {d[0].rect.height:6.1f} pt")
        d.close()
        paths.append(p)

    contact = fitz.open()
    for p in paths:
        contact.insert_pdf(fitz.open(str(p)))
    Path(args.contact).parent.mkdir(parents=True, exist_ok=True)
    contact.save(args.contact)
    print(f"\n{len(paths)} figures; contact sheet -> {args.contact}")

    if args.check:
        # The cheapest honest check there is: a crop that shaved an axis label still writes
        # its file and still passes every count, but it cannot keep its ink off the outermost
        # pixel row. Anything reported here wants an eye at 400 dpi.
        hits = edge_ink(args.contact)
        if not hits:
            print("edge-ink: clean — no crop's ink reaches its border.")
        else:
            for pno, e in hits:
                print(f"edge-ink: figure #{pno} ({paths[pno - 1].name}) "
                      f"top/bottom/left/right = {e}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
