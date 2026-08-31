#!/usr/bin/env python3
"""
texify_bookmap.py — the MAP: one hand-written YAML that is the single source of truth for
converting the paper.

`.texify_work/<paper>.map.yaml` records, in 1-based physical page numbers (what a PDF viewer
shows): the body's page span and the paper's own sections, and the page span of the reference
list. Everything downstream is DERIVED from it — the temporary `<paper>_NN.pdf` body slice and
`<paper>_ref.pdf` reference slice are carved on demand and deleted after use, `<paper>.bib` is
collected from the reference span, and the body is content-aware chunked from the sections.

THE MAP IS WRITTEN BY HAND. The book pipeline built it with an LLM probe (`--probe`), which
cannot work on a single-division source — it needs >= 2 top-level divisions, so on a paper it
either aborts or promotes the paper's own sections to divisions, which strands a
section-parented equation counter at every bogus boundary. The probe and the map WRITER
(save_map, and the schema header it emitted) are therefore gone; this module only READS.

ENGINE-FREE (no backend): it defines the schema, reads the YAML, derives the temporary PDFs,
and converts the sections into the chunker's `OutlineEntry` list.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml
from pypdf import PdfReader, PdfWriter

from texify_chunker import OutlineEntry

log = logging.getLogger("texify.bookmap")


# ------------------------------------------------------------------ schema ----

@dataclass
class Section:
    level: int            # 1 = section, 2 = subsection
    page: int             # 1-based physical page where it begins
    title: str


@dataclass
class Division:
    nn: str               # "01", "02", ... (output suffix: <name>_NN)
    title: str
    kind: str             # 'chapter' | 'appendix'
    start: int            # 1-based inclusive physical page
    end: int              # 1-based inclusive physical page
    sections: list[Section] = field(default_factory=list)

    @property
    def n_pages(self) -> int:
        return self.end - self.start + 1


@dataclass
class RefSpan:
    scope: str            # 'book' | 'chapter'
    start: int            # 1-based inclusive
    end: int              # 1-based inclusive
    chapter: Optional[str] = None   # the chapter nn, when scope == 'chapter'
    title: str = "References"


@dataclass
class BookMap:
    book: str
    source: str           # the source PDF filename (in src/)
    pages: int
    chapters: list[Division] = field(default_factory=list)
    references: list[RefSpan] = field(default_factory=list)
    skipped: list[dict] = field(default_factory=list)   # {title, page}


# ------------------------------------------------------------------- IO -------

def load_map(path: Path) -> BookMap:
    """Read a (possibly hand-edited) map. Tolerant of missing optional keys."""
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    chapters = [
        Division(nn=str(d.get("nn", f"{i+1:02d}")), title=str(d.get("title", "")),
                 kind=str(d.get("kind", "chapter")),
                 start=int(d["start"]), end=int(d["end"]),
                 sections=[Section(level=int(s.get("level", 1)),
                                   page=int(s["page"]), title=str(s.get("title", "")))
                           for s in (d.get("sections") or [])])
        for i, d in enumerate(data.get("chapters") or [])
    ]
    references = [
        RefSpan(scope=str(r.get("scope", "book")), start=int(r["start"]),
                end=int(r["end"]), chapter=(str(r["chapter"]) if r.get("chapter") else None),
                title=str(r.get("title", "References")))
        for r in (data.get("references") or [])
    ]
    return BookMap(book=str(data.get("book", path.stem.split(".")[0])),
                   source=str(data.get("source", "")),
                   pages=int(data.get("pages", 0)),
                   chapters=chapters, references=references,
                   skipped=list(data.get("skipped") or []))


# --------------------------------------------------------------- derive -------

def _write_pages(reader: PdfReader, start1: int, end1: int, out_path: Path) -> Path:
    """Write 1-based inclusive page span [start1, end1] to out_path."""
    writer = PdfWriter()
    lo, hi = max(1, start1), min(end1, len(reader.pages))
    for p in range(lo - 1, hi):           # 1-based -> 0-based
        writer.add_page(reader.pages[p])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "wb") as f:
        writer.write(f)
    return out_path


def derive_chapter_pdf(book_pdf: Path, div: Division, out_dir: Path,
                       prefix: str) -> Path:
    """Carve a chapter's pages into out_dir/<prefix>_<nn>.pdf (a disposable temp slice
    whose stem fixes the converted body's name, <prefix>_<nn>)."""
    reader = PdfReader(str(book_pdf))
    return _write_pages(reader, div.start, div.end, out_dir / f"{prefix}_{div.nn}.pdf")


def derive_reference_pdf(book_pdf: Path, ref: RefSpan, out_dir: Path,
                         prefix: str) -> Path:
    """Carve a reference span into <prefix>_ref.pdf (book scope) or
    <prefix>_<nn>_ref.pdf (chapter scope) — the names the bib step consumes."""
    reader = PdfReader(str(book_pdf))
    name = (f"{prefix}_ref.pdf" if ref.scope == "book"
            else f"{prefix}_{ref.chapter}_ref.pdf")
    return _write_pages(reader, ref.start, ref.end, out_dir / name)


def to_chunk_outline(div: Division) -> list[OutlineEntry]:
    """A chapter's sections → the chunker's OutlineEntry list (0-based pages WITHIN the
    chapter slice; level 0 = section, 1 = subsection), so content-aware chunking runs
    off the map with no embedded-outline read and no per-chapter re-probe."""
    out: list[OutlineEntry] = []
    for s in div.sections:
        page0 = max(0, s.page - div.start)         # 1-based book page -> 0-based in slice
        out.append(OutlineEntry(title=s.title, level=0 if s.level <= 1 else 1,
                                page0=page0))
    return out
