"""
texify_chunker.py — structure-aware chunk planning for the texify pipeline.

This is the component that keeps the converter from ever cutting through the
middle of a matrix, an align block, a proof, or a list. It chooses chunk
boundaries by document STRUCTURE, not by a fixed page count.

Strategy, in strict order of preference:

  1. PDF OUTLINE (bookmarks), CONTENT-AWARE. Take the shallowest outline level
     with >= 2 in-document entries (the section level for a chapter), then COALESCE
     adjacent sections into the fewest chunks that stay under the size budget,
     ALWAYS breaking before a different content type — a lab, the exercises, an
     appendix — so each becomes its own chunk. This replaces naive one-chunk-per-
     section: a 1-page intro merges into the next section, while a code lab and the
     exercises stay whole and separate. (Overview before the first heading joins
     the first chunk.)

  2. OVERSIZE SECTION -> sub-split at the NEXT outline level, then COALESCE those
     subsections the same way (step 1) so a chapter with many small subsections
     becomes a few budget-sized chunks, not one tiny chunk each. A span is only
     broken up when it exceeds the ceiling; each piece is still a clean boundary.

  3. OVERSIZE LEAF (a single subsection past the ceiling, or a section with no
     subsections) -> page windows *within that span only*, marked
     clean_boundary=False so the orchestrator leans on the continuity handoff to
     stitch the seam. This is the ONLY path that cuts mid-structure.

  4. NO USABLE OUTLINE, but an `outline_probe` is injected -> the "intelligent
     cut": the backend READS the PDF (so it works even when text extraction is
     blocked, e.g. a copyright-protected or scanned source, or when bookmarks
     were stripped during a hand-split) and proposes section / subsection
     boundaries, which then flow through steps 1-3 exactly as a real outline
     would. The orchestrator injects the probe; the chunker stays
     backend-agnostic and never imports an engine.

  5. NO OUTLINE AND NO PROBE -> scan page text for section-heading patterns and
     split there. Semi-clean.

  6. LAST RESORT ONLY -> fixed page windows with 1-page overlap,
     clean_boundary=False. The degraded mode, always flagged so nothing
     pretends a blind cut is clean.

Chunks are sized to the Claude Read tool's limits: adjacent structural units are
COALESCED toward a soft TARGET (SOFT_MAX_PAGES, the tool's clean single-pass size)
and NEVER exceed a hard CEILING (MAX_CHUNK_PAGES, the tool's per-request page cap).
A clean structural unit larger than the ceiling is broken at the NEXT outline level
(step 2); only a single leaf unit that is STILL too big is windowed mid-structure
(step 3) — the lone non-clean cut, always flagged so the orchestrator's continuity
handoff (open-env stack + tail LaTeX + page overlap) stitches the seam.

Page indices throughout are 0-based and INCLUSIVE on both ends.
"""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass
from typing import Callable, Optional

log = logging.getLogger("texify.chunker")

try:
    from pypdf import PdfReader, PdfWriter
    _HAS_PYPDF = True
except Exception:  # pragma: no cover
    _HAS_PYPDF = False


# ------------------------------------------------------------------ config ----

# A coalesced chunk is "too big for one generation" when its extracted text exceeds
# this. An OUTPUT-budget proxy (modern Pro/Opus emit well over this from a chunk this
# size). Structural units are COALESCED up to this size AND the page target below,
# whichever binds first. Tune per model with --max-chunk-chars.
MAX_CHUNK_CHARS = 60_000

# Soft page TARGET for coalescing: adjacent structural units merge until they reach
# ~this many pages. Sized to the Claude Read tool's clean single-pass limit (it reads
# PDFs <= 10pp whole), so a coalesced chunk is ingested in ONE Read call. NOT a hard
# cap — a single structural unit bigger than this is kept whole if it fits the ceiling.
SOFT_MAX_PAGES = 10

# Hard page CEILING for any emitted chunk. The Read tool accepts at most 20 pages per
# request (READ_REQUEST_PAGE_LIMIT in the backend), so a unit wider than this is
# sub-split at the next outline level, or windowed if it is an indivisible leaf. A
# clean chunk never exceeds it. Tune with --max-chunk-pages.
MAX_CHUNK_PAGES = 20

# Window geometry: slices a single leaf unit that is itself past the ceiling (and the
# last-resort no-structure fallback). A window is <= the target so it too is a clean
# single-pass read; consecutive windows overlap by 1 page to feed the seam handoff.
WINDOW_PAGES = 10
WINDOW_OVERLAP = 1


# ------------------------------------------------------------------- types ----

@dataclass
class OutlineEntry:
    title: str
    level: int      # 0 = shallowest present
    page0: int      # 0-based page the destination lands on


@dataclass
class ChunkSpec:
    index: int
    page_start: int           # inclusive, 0-based
    page_end: int             # inclusive, 0-based
    title: str                # nearest heading, for logging/labels
    source: str               # 'outline' | 'subsection' | 'text-scan' | 'window'
    clean_boundary: bool      # False => orchestrator must rely on continuity

    @property
    def n_pages(self) -> int:
        return self.page_end - self.page_start + 1


# --------------------------------------------------------------- outline io ---


# --------------------------------------------------------------- planning ----

def _spans_from_boundaries(boundaries: list[int], lo: int, hi: int
                           ) -> list[tuple[int, int]]:
    """Turn a set of start-pages into inclusive [start, end] spans covering
    [lo, hi]. Prepends `lo` so any content before the first boundary becomes its
    own head span."""
    bs = sorted({b for b in boundaries if lo <= b <= hi})
    if not bs or bs[0] > lo:
        bs = [lo] + bs
    spans = []
    for i, b in enumerate(bs):
        end = (bs[i + 1] - 1) if i + 1 < len(bs) else hi
        if end >= b:
            spans.append((b, end))
    return spans


def _chars_in(reader: "PdfReader", lo: int, hi: int) -> int:
    total = 0
    for p in range(lo, hi + 1):
        try:
            total += len(reader.pages[p].extract_text() or "")
        except Exception:
            pass
    return total


def _is_oversize(reader: "PdfReader", lo: int, hi: int,
                 max_chars: int, max_pages: int) -> bool:
    if (hi - lo + 1) > max_pages:
        return True
    return _chars_in(reader, lo, hi) > max_chars


def _title_at(entries: list[OutlineEntry], page0: int) -> str:
    best = ""
    for e in entries:
        if e.page0 <= page0:
            best = e.title
    return best


def _window_spans(n: int, win: int, overlap: int) -> list[tuple[int, int]]:
    spans = []
    start = 0
    while start < n:
        end = min(start + win - 1, n - 1)
        spans.append((start, end))
        if end == n - 1:
            break
        start = end - overlap + 1
    return spans


def _coalesce_sections(reader: "PdfReader", sec_spans: list[tuple[int, int, str]],
                       max_chars: int, max_pages: int, boundary_re
                       ) -> list[tuple[int, int]]:
    """Content-aware chunking: merge adjacent structural spans (sections, or the
    subsections of an oversize section) into the FEWEST size-bounded chunks, instead
    of one chunk per unit. A span whose title marks a different content type (lab /
    exercises / appendix — `boundary_re`) always starts a fresh chunk and is never
    merged into the exposition before it, so a code lab or the end-of-chapter
    exercises stay intact and on their own.

    `sec_spans` is [(lo, hi, title)] in document order (the head span before the
    first heading carries title ""); returns merged [(lo, hi)] spans. A single
    span larger than the budget is returned as-is — the caller sub-splits/windows it."""
    groups: list[tuple[int, int]] = []
    cur: Optional[tuple[int, int, int]] = None   # (lo, hi, chars)

    def flush():
        nonlocal cur
        if cur is not None:
            groups.append((cur[0], cur[1]))
            cur = None

    for lo, hi, title in sec_spans:
        if boundary_re.search(title or ""):
            flush()
            groups.append((lo, hi))            # content-type unit stands alone
            continue
        ch = _chars_in(reader, lo, hi)
        if cur is None:
            cur = (lo, hi, ch)
        elif cur[2] + ch <= max_chars and hi - cur[0] + 1 <= max_pages:
            cur = (cur[0], hi, cur[2] + ch)    # coalesce into the running chunk
        else:
            flush()
            cur = (lo, hi, ch)
    flush()
    return groups


def _dedupe_boundaries(items: list[tuple[int, str]], hi_bound: int
                       ) -> list[tuple[int, str]]:
    """`items` = sorted [(page0, title)] section boundaries from the map. Return them clamped
    into range, with CO-LOCATED headings COLLAPSED to one boundary (the first one wins).

    Two headings really can share a page — white's map has both "4. Summary and Comments" and
    "Appendix" starting on p8 — and a page cannot be split, so they are one boundary and one
    chunk-start. Collapsing is the only honest thing to do.

    The book pipeline instead forced boundaries to be STRICTLY INCREASING by walking a duplicate
    backwards a page, which silently mis-attributed it: "4. Summary" got dragged from p8 to p7, a
    page it does not begin on, corrupting the chunk's title and — on a paper long enough to split —
    putting the cut on the wrong page. It also *moved* each boundary to where the heading text
    actually began, to compensate for PDF bookmarks pointing a page or two early. A hand-written
    map has neither problem: its page numbers are exact, so there is nothing to refine and nothing
    to shove."""
    out: list[tuple[int, str]] = []
    for pg, title in items:
        pg = max(0, min(pg, hi_bound - 1))
        if out and pg == out[-1][0]:
            continue                      # same page as the previous heading -> same boundary
        out.append((pg, title))
    return out


def plan_chunks(pdf_path: str, *,
                max_chunk_chars: int = MAX_CHUNK_CHARS,
                soft_max_pages: int = SOFT_MAX_PAGES,
                max_chunk_pages: int = MAX_CHUNK_PAGES,
                window_pages: int = WINDOW_PAGES,
                window_overlap: int = WINDOW_OVERLAP,
                content_boundary_re: Optional[str] = None,
                outline_entries: "list[OutlineEntry]" = ()) -> list[ChunkSpec]:
    """Produce an ordered, structure-aware chunk plan for the body PDF.

    `outline_entries` IS the structure — the paper's own sections, straight from the
    hand-written map (0-based pages within this PDF; level 0 = section, 1 = subsection). The
    book pipeline could also read a PDF's embedded outline, text-scan for headings, or ask a
    backend for an "intelligent cut" when a chapter slice had lost its bookmarks; a paper's map
    is hand-written and always has the sections, so all three fallbacks are gone.

    A typical paper coalesces to ONE chunk (8 pages, ~13k chars, both well under the budgets)
    and is converted in a single call with no seam. The splitting paths below exist for a long
    paper: an oversize group is sub-split at subsections, and a single oversize subsection is
    windowed — the one cut that can land mid-structure, which the seam handoff then stitches.
    """
    if not _HAS_PYPDF:
        raise RuntimeError("pypdf is required for chunk planning.")
    reader = PdfReader(pdf_path)
    n = len(reader.pages)
    entries = sorted((e for e in (outline_entries or ()) if 0 <= e.page0 < n),
                     key=lambda e: (e.page0, e.level))
    sec_src, sub_src = "map", "map-sub"
    # Section titles that must each get their own chunk. Defaults to matching NOTHING: the
    # book default forced a break at any "Appendix" heading, which on an 8-page article only
    # manufactures a seam. Pass a real regex for a long paper whose supplement must be cut off.
    boundary_re = re.compile(content_boundary_re or r"(?!)", re.I)

    specs: list[ChunkSpec] = []
    idx = 0

    def emit(lo, hi, source, clean):
        nonlocal idx
        specs.append(ChunkSpec(index=idx, page_start=lo, page_end=hi,
                               title=_title_at(entries, lo), source=source,
                               clean_boundary=clean))
        idx += 1

    if len(entries) >= 2:
        split_level = min(e.level for e in entries)
        top = sorted((e for e in entries if e.level == split_level),
                     key=lambda e: e.page0)
        # Content-aware: coalesce adjacent sections up to the budget, breaking at
        # content-type boundaries (lab / exercises / …), rather than emitting one
        # chunk per section. So a 1-page intro joins the next section, while a code
        # lab and the exercises stay whole and on their own.
        top_items = _dedupe_boundaries([(e.page0, e.title) for e in top], n)
        starts = [p for p, _ in top_items]
        title_at = dict(top_items)
        sec_spans = [(lo, hi, title_at.get(lo, ""))
                     for lo, hi in _spans_from_boundaries(starts, 0, n - 1)]
        for lo, hi in _coalesce_sections(reader, sec_spans, max_chunk_chars,
                                         soft_max_pages, boundary_re):
            if not _is_oversize(reader, lo, hi, max_chunk_chars, max_chunk_pages):
                emit(lo, hi, sec_src, True)
                continue
            # oversize -> try the next level down (subsections) inside this span
            children = sorted((e for e in entries
                               if e.level == split_level + 1 and lo <= e.page0 <= hi),
                              key=lambda e: e.page0)
            child_items = _dedupe_boundaries([(c.page0, c.title) for c in children], hi + 1)
            child_starts = [p for p, _ in child_items]
            sub = _spans_from_boundaries(child_starts, lo, hi)
            if len(sub) >= 2:
                # Content-aware AT THE SUBSECTION LEVEL too: coalesce the subsections
                # toward the same page/char target before emitting, so an oversize
                # chapter with many small subsections (e.g. ch.13's 13.1-13.13) becomes
                # a few budget-sized chunks, not one tiny chunk each. The leading span
                # before the first subsection (the section intro) carries title "" and
                # merges into the first group; a content-type subsection still splits
                # out via boundary_re.
                ctitle_at = dict(child_items)
                sub_spans = [(a, b, ctitle_at.get(a, "")) for a, b in sub]
                for slo, shi in _coalesce_sections(reader, sub_spans, max_chunk_chars,
                                                   soft_max_pages, boundary_re):
                    # the finest level we have; if a single subsection is ITSELF past
                    # the ceiling (a long, dense one), window it — the lone mid-structure
                    # cut, stitched by the seam handoff.
                    if _is_oversize(reader, slo, shi, max_chunk_chars, max_chunk_pages):
                        log.info("oversize subsection %d-%d; windowing it", slo, shi)
                        for wlo, whi in _window_spans(shi - slo + 1, window_pages,
                                                      window_overlap):
                            emit(slo + wlo, slo + whi, "window", False)
                    else:
                        emit(slo, shi, sub_src, True)
            else:
                log.warning("oversize span %d-%d has no subsections; windowing it",
                            lo, hi)
                for slo, shi in _window_spans(hi - lo + 1, window_pages, window_overlap):
                    emit(lo + slo, lo + shi, "window", False)
        return specs

    # The map lists fewer than 2 sections. The map is authoritative — never guess — so emit the
    # whole body as one chunk, windowing only if it is genuinely oversize. (The book pipeline
    # fell back to text-scanning for headings or to blind page windows here; a paper's map is
    # hand-written and always carries the sections, so there is nothing left to guess at.)
    if _is_oversize(reader, 0, n - 1, max_chunk_chars, max_chunk_pages):
        log.warning("map lists <2 sections and the body is oversize (%dpp); windowing", n)
        for lo, hi in _window_spans(n, window_pages, window_overlap):
            emit(lo, hi, "window", False)
    else:
        emit(0, n - 1, sec_src, True)
    return specs


# ----------------------------------------------------- materialize / handoff --

def materialize_chunk(pdf_path: str, spec: ChunkSpec, out_dir: str) -> str:
    """Write a chunk's page range to a standalone PDF (for upload / clean Read)."""
    reader = PdfReader(pdf_path)
    writer = PdfWriter()
    for p in range(spec.page_start, spec.page_end + 1):
        writer.add_page(reader.pages[p])
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir,
                        f"chunk_{spec.index:02d}_p{spec.page_start}-{spec.page_end}.pdf")
    with open(path, "wb") as f:
        writer.write(f)
    return path


def build_context_handoff(open_envs: list[str], tail_latex: str) -> str:
    """Format the cross-chunk handoff (open-env stack + trailing LaTeX) appended to
    the next chunk's task prompt. Engine-independent: every backend consumes this.

    The wording around `open_envs` is load-bearing and hard-won. A chunk that resumes
    inside a proof "wants" to make its own output self-contained, so a model will happily
    write `\\begin{proof}[Proof (continued)] ... \\end{proof}` — internally balanced, and
    fatal, because the ORIGINAL `\\begin{proof}` in the previous chunk is then never
    closed and the assembled chapter will not compile. Saying "do NOT re-\\begin" once was
    not enough (observed on Claude Opus 4.8 and on Mistral); the instruction has to name
    that exact temptation and say what to emit first instead.
    """
    if not open_envs and not tail_latex.strip():
        return ""
    parts = ["CONTINUATION CONTEXT — this PDF continues a previous chunk."]
    if open_envs:
        envs = ", ".join(open_envs)
        inner = open_envs[-1]   # innermost: the one the text actually resumes inside
        parts.append(
            f"These LaTeX environments are ALREADY OPEN in the assembled chapter and "
            f"MUST NOT be opened again: {envs}.\n"
            f"  1. START by transcribing the REMAINING BODY of {inner} exactly as it "
            f"appears on these pages — the sentences, equations and list items that "
            f"continue it. This text has NOT been emitted yet; it is not 'earlier "
            f"content'. Reproduce every word of it.\n"
            f"  2. ONLY THEN, where that body truly ends (at its QED box, or at its last "
            f"sentence before the next heading), emit \\end{{{inner}}}.\n"
            f"  - Do NOT make \\end{{{inner}}} your first output and do NOT skip straight "
            f"to it: that silently deletes the continuation text, which is the worst "
            f"possible error.\n"
            f"  - Do NOT write \\begin{{{inner}}}, nor \\begin{{{inner}}}[... continued], "
            f"nor any other re-opening: that leaves the original \\begin{{{inner}}} "
            f"unclosed and the chapter will not compile.\n"
            f"  - Never emit \\qed, \\qedsymbol, $\\square$ or $\\blacksquare$: "
            f"\\end{{...}} draws the QED box itself.")
    if tail_latex.strip():
        parts.append("The previous output ended with this exact code:\n"
                     f"```\n{tail_latex.strip()}\n```")
    parts.append("Resume at the very next word of the source after that code. Do not "
                 "repeat anything already shown above, and do not skip anything between "
                 "it and the next content on these pages.")
    return "\n".join(parts)


# ------------------------------------------------------------------- debug ----

if __name__ == "__main__":
    import argparse
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    ap = argparse.ArgumentParser(description="Print the chunk plan for a PDF.")
    ap.add_argument("pdf")
    args = ap.parse_args()
    for s in plan_chunks(args.pdf):
        flag = "" if s.clean_boundary else "  [seam -> needs continuity]"
        print(f"#{s.index:02d}  p{s.page_start}-{s.page_end} "
              f"({s.n_pages}pp)  {s.source:<11} {s.title}{flag}")
