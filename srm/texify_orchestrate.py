#!/usr/bin/env python3
"""
texify_orchestrate.py — the conductor for the *texify* pipeline.
================================================================

Turns one mathematics JOURNAL ARTICLE under src/ into master-embeddable LaTeX:

    python texify_orchestrate.py --paper white --bib          # references -> .bib + citemap
    python texify_orchestrate.py --paper white --chapters 01  # convert the body
    python texify_orchestrate.py --paper white --master       # assemble the master

What it owns (and what it delegates):

  * INPUT ................... `.texify_work/<paper>.map.yaml`, HAND-WRITTEN. It gives the
                              body's page span, the paper's own sections, and the reference
                              span. There is no LLM map probe: it needs >= 2 top-level
                              divisions, and a paper has one.
  * BACKEND SELECTION ....... texify_backends.get_backend(); this module never branches on
                              which engine is running.
  * CHUNKING ................ texify_chunker.plan_chunks(). A paper normally coalesces to
                              ONE chunk, i.e. a single call with no seam — confirm with
                              --dry-run.
  * CROSS-CHUNK CONTINUITY .. driven here; the *mechanism* is a text handoff (open-env stack
                              + trailing LaTeX) the chunker builds — engine-independent.
  * BIB + CITATIONS ......... `--bib` reads the reference span, freezes the keys into
                              <paper>.bib AND .texify_work/<paper>.citemap.json from one
                              extraction (so they agree by construction), and every
                              conversion prompt then carries that frozen CITATION INDEX.
  * MASTER .................. `--master` inlines the committed assets/preamble.tex, \\input's
                              the per-paper patch assets/preamble.<paper>.tex, then the body
                              and the bibliography.

`--dry-run` prints the chunk plan and spends nothing.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import shutil
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from pypdf import PdfReader

# Make sibling modules importable no matter where we're invoked from.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import texify_common as tc  # noqa: E402
from texify_backends import (  # noqa: E402
    Backend, BackendError, BlockedByPolicyError, get_backend, FallbackBackend,
    SplitRetryBackend, SEAM_CAUTION, SPLIT_MAX_DEPTH,
    scan_open_environments, scan_unmatched_ends, strip_code_fences, strip_model_preamble,
    pdf_page_count, DEFAULT_TASK_PROMPT,
    MISTRAL_OCR_MODEL, MISTRAL_TEXT_MODEL, MISTRAL_MAX_TOKENS, MISTRAL_REASONING_EFFORT,
)
from texify_chunker import (  # noqa: E402
    plan_chunks, materialize_chunk, build_context_handoff, OutlineEntry, ChunkSpec,
    MAX_CHUNK_CHARS, SOFT_MAX_PAGES, MAX_CHUNK_PAGES, WINDOW_PAGES, WINDOW_OVERLAP,
)
from texify_bookmap import (  # noqa: E402
    BookMap, Division, load_map,
    derive_chapter_pdf, derive_reference_pdf, to_chunk_outline,
)

log = logging.getLogger("texify.orchestrate")


# ============================== configuration ================================

# Where the orchestrator looks for the conversion contract, first match wins.
SPEC_CANDIDATES = [
    "SKILL.md",
    ".claude/skills/texify-math-pdf/SKILL.md",
    "src/SKILL.md",
    "src/prompt.txt",
    "prompt.txt",
]

# SEAM_CAUTION is imported from texify_backends, which also uses it for the seams a
# SplitRetryBackend creates when it halves a chunk. One definition, one wording — the
# model must hear the same rule whether the seam came from the chunker or from a split.
# It is appended to any chunk that is not the last: a section boundary bounds SECTIONS,
# not ENVIRONMENTS, so even a "clean" seam can cut a proof in half.

# Appended to the FIRST span under --spans --continues: that span is a later part of a
# chapter already converted, so the model must not restart the chapter.
CONT_NOTE = (
    "CONTINUATION: this PDF is a later part of a chapter already in progress. Do "
    "NOT emit \\chapter{...} or the chapter overview; begin directly at the first "
    "section/heading shown on these pages, and do not repeat earlier content.")

# Bibliography extraction prompts (Section 9 of the spec handles the system side,
# but we make the intent explicit at the task level too).
# The bibliography step is also the citation-STYLE PROBE: it reads the actual
# reference list and reports, per entry, the cite key + the in-text token a
# chapter would use to refer to it (the [n] bracket number for numbered lists,
# the author-year label for unnumbered ones) + clean BibTeX fields. Both the
# .bib and the citation index are then built locally from this one structured
# result, so their keys are identical by construction (no second derivation).
BIB_PROBE_SYSTEM_PROMPT = (
    "You are a bibliography and BibTeX expert. You will be shown a reference list from "
    "a book. Transcribe EVERY reference into BibTeX, reading what the document actually "
    "contains (do not invent or omit references)."
)
# The model emits BibTeX DIRECTLY — its native format, far more robust than a giant
# nested JSON object for a long bibliography (no 'Extra data' parse failures, no object
# splitting). The orchestrator parses this BibTeX to build the .bib AND the citemap
# (numbered: in-text [n] = the n-th entry in order; author-year: the entry's key).
BIB_PROBE_TASK_PROMPT = (
    "Read this PDF's reference list and output ONLY a BibTeX file — no prose, no "
    "markdown fences, nothing but BibTeX.\n\n"
    "The VERY FIRST LINE must be a style comment, exactly one of:\n"
    "  % style: numeric        (the list is numbered — entries like [12] or 12.)\n"
    "  % style: author-year    (unnumbered, alphabetical by author)\n\n"
    "Then one @entry per reference, IN THE SAME ORDER as the list — this is critical: "
    "for a numbered list the n-th entry is what the text cites as [n]. For each entry:\n"
    "  - @type: article / book / incollection / inproceedings / techreport / misc.\n"
    "  - a stable, readable cite key like cesabianchi2006prediction (surname+year+word). "
    "Keys must be unique; only if two genuinely share author+year, append a/b.\n"
    "  - every field present: author (BibTeX \"Last, First and Last, First\"), title, "
    "year, journal or booktitle, editor, volume, number, pages (ranges with --), "
    "publisher, institution, doi, url, note. Omit unknown fields.\n\n"
    "Transcribe EVERY reference in order; do not summarize, abbreviate, or drop any."
)


# How much trailing LaTeX to feed forward as Gemini's continuity handoff.
HANDOFF_TAIL_CHARS = 800

# A journal page carries far less running text than a textbook page: white.pdf averages
# ~1650 source chars/page, and the book pipeline's 800-chars-of-LaTeX-per-page stub floor
# fires false positives on it (it rejected every backend's correct 3-entry bibliography as
# a "short stub" until the bib probe was told expect_short=True). 400 keeps the guard
# against a genuinely lazy model while leaving a faithful, terse conversion alone.
MIN_CHARS_PER_PAGE_PAPER = 400

# A regex that matches nothing (a negative lookahead on the empty string always fails).
# See --content-boundary-re: papers have no lab/exercise sections worth isolating, and
# forcing a chunk break at "Appendix" only manufactures a seam.
CONTENT_BOUNDARY_NEVER = r"(?!)"


# ================================= reports ===================================

@dataclass
class ChapterReport:
    chapter: str                 # e.g. "05"
    status: str                  # 'ok' | 'skipped' | 'failed'
    mode: str = "-"              # 'whole' | 'chunk'
    n_chunks: int = 0
    cost_usd: Optional[float] = None
    truncated: bool = False
    open_at_end: list[str] = field(default_factory=list)
    stray_ends: list[str] = field(default_factory=list)  # \end{} closing nothing
    short: bool = False          # output suspiciously short → likely lazy/incomplete
    out_path: Optional[str] = None
    error: Optional[str] = None


# ============================== input discovery ==============================

def _strip_frontmatter(raw: str) -> str:
    """Drop a leading YAML frontmatter block so a SKILL.md works both as an injected
    system prompt and as a discoverable Claude Code skill."""
    lines = raw.splitlines()
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                return "\n".join(lines[i + 1:]).strip()
    return raw.strip()


def load_spec(path_or_none: Optional[str]) -> tuple[str, str]:
    """Return (general_spec_text, spec_path) — the book-AGNOSTIC contract. The
    book-specific overlay (if any) is composed on top via load_book_overlay /
    compose_spec; keeping them separate is what makes the general SKILL reusable."""
    candidates = [path_or_none] if path_or_none else SPEC_CANDIDATES
    for c in candidates:
        if c and Path(c).exists():
            return _strip_frontmatter(Path(c).read_text(encoding="utf-8")), c
    raise SystemExit(
        "No conversion spec found. Looked for: "
        + ", ".join(x for x in candidates if x)
        + ". Pass one with --spec."
    )


# Where a per-book overlay (`SKILL.<prefix>.md`) is looked for, first match wins.
OVERLAY_DIRS = (".", "src", ".claude/skills/texify-math-pdf")


def load_book_overlay(prefix: str, extra_dirs=()) -> tuple[Optional[str], Optional[str]]:
    """Find the book-specific overlay `SKILL.<prefix>.md` and return (text, path),
    or (None, None) if the book has none. The overlay carries everything that is
    NOT reusable across books — the exact environment list, numbering scheme,
    exercise/figure conventions, margin glosses, whether code is runnable — so the
    general SKILL stays book-agnostic."""
    for d in list(extra_dirs) + list(OVERLAY_DIRS):
        p = Path(d) / f"SKILL.{prefix}.md"
        if p.exists():
            return _strip_frontmatter(p.read_text(encoding="utf-8")), str(p)
    return None, None


def compose_spec(general: str, overlay: Optional[str]) -> str:
    """General contract + book overlay. The overlay already carries its own
    `# BOOK-SPECIFIC OVERLAY …` heading and is appended verbatim; it is authoritative
    wherever it differs (the general contract tells the model so)."""
    if not overlay:
        return general
    return general.rstrip() + "\n\n" + overlay.strip() + "\n"


def discover_paper_prefix(src: Path, override: Optional[str]) -> str:
    """The paper prefix: `--paper white` wins; else the lone PDF in src/.

    Anything ending `_NN` is one of OUR temp slices or a figures PDF, not the source, so it is
    excluded. Keeping the src/ directory to exactly one PDF is the intended workflow."""
    if override:
        return override
    pdfs = [p for p in src.glob("*.pdf") if not re.fullmatch(r".+_\d\d", p.stem)]
    if len(pdfs) == 1:
        return pdfs[0].stem
    raise SystemExit(
        f"can't identify the paper PDF in {src}/ "
        f"(candidates: {[p.name for p in pdfs] or 'none'}); pass --paper <prefix>.")


def _nn(pdf: Path) -> str:
    return pdf.stem.rsplit("_", 1)[1]


def parse_spans(s: str) -> list[tuple[int, int]]:
    """'0-34,35-49,50-55' -> [(0,34),(35,49),(50,55)] (0-based inclusive page spans)."""
    out = []
    for tok in s.split(","):
        tok = tok.strip()
        if not tok:
            continue
        a, b = tok.split("-")
        out.append((int(a), int(b)))
    return out


# ============================== core conversion ==============================

def convert_chunked(backend: Backend, pdf: Path, spec_text: str, task_base: str,
                    chunk_dir: Path, *, keep_chunks: bool, plan_kw: dict,
                    unconverted_dir: Path,
                    specs: Optional[list[ChunkSpec]] = None,
                    first_chunk_task_suffix: Optional[str] = None) -> tuple[str, dict]:
    """Content-aware chunked conversion with cross-chunk continuity.

    `specs` (optional) supplies a pre-built ChunkSpec list — e.g. the hand-chosen page
    spans from --spans — bypassing the planner; otherwise chunks are planned
    from the outline. `first_chunk_task_suffix` (optional) is appended to the FIRST
    chunk's task prompt (e.g. a "this PDF continues a chapter already in progress"
    note for a mid-chapter span).

    A chunk that ALL backends content-block is not fatal: its chunk PDF is saved to
    `unconverted_dir` and a `% UNCONVERTED` marker (page range + that PDF's path) is
    written into the body where it belongs, so the gap is explicit and recoverable;
    conversion continues with the next chunk.

    Returns (latex, info). `info` carries n_chunks, summed cost, the open-env stack
    at the very end (should be empty), whether any chunk truncated, and `unfinished`
    (the list of content-blocked chunks).
    """
    # Pre-built specs (e.g. the hand-chosen page spans from --spans) bypass the
    # planner; otherwise plan content-aware chunks from the outline.
    if specs is None:
        specs = plan_chunks(str(pdf), **plan_kw)
    log.info("[%s] chunk plan: %d chunk(s) — %s", pdf.stem, len(specs),
             " ".join(f"pp{s.page_start+1}-{s.page_end+1}" for s in specs))

    pieces: list[str] = []
    carry_open: list[str] = []      # env stack carried across chunk seams (handoff)
    prev_tail = ""                  # trailing LaTeX fed to the continuity handoff
    total_cost = 0.0
    any_trunc = False
    unfinished: list[dict] = []     # chunks ALL backends content-blocked

    try:
        for spec in specs:
            chunk_pdf = materialize_chunk(str(pdf), spec, str(chunk_dir))
            # `clean_boundary` means the chunk ends at a SECTION boundary — which says
            # nothing about ENVIRONMENTS. A section commonly starts partway down a page, so
            # a page-aligned split there still cuts the previous section's last proof in
            # half; the model then invents an `\end{proof}` at the page edge, reports
            # nothing open, and the handoff tells the next chunk to start fresh — corrupting
            # both sides of the seam. SEAM_CAUTION is self-guarding ("IF the final page cuts
            # off mid-environment..."), so give it to EVERY non-final chunk, not just the
            # ones the outline calls ragged. The final chunk keeps the old rule: nothing
            # continues past it, so the caution is a no-op there.
            needs_caution = (not spec.clean_boundary) or (spec.index != specs[-1].index)
            task = f"{task_base}\n\n{SEAM_CAUTION}" if needs_caution else task_base
            if first_chunk_task_suffix and spec.index == specs[0].index:
                task = f"{task}\n\n{first_chunk_task_suffix}"

            try:
                handoff = build_context_handoff(carry_open, prev_tail)
                res = backend.convert(chunk_pdf, spec_text, task,
                                      context_handoff=handoff)
            except BlockedByPolicyError as e:
                # Every backend refused this chunk. Keep its PDF (so it survives the
                # chunk_dir cleanup) and leave a precise, recoverable gap marker in
                # the body instead of aborting the chapter. Continuity is unchanged,
                # so the next chunk still resumes from the last good output.
                unconverted_dir.mkdir(parents=True, exist_ok=True)
                saved = unconverted_dir / f"{pdf.stem}_p{spec.page_start}-{spec.page_end}.pdf"
                try:
                    shutil.copy2(chunk_pdf, saved)
                except OSError:
                    saved = Path(chunk_pdf)
                pieces.append(tc.unconverted_chunk_marker(
                    spec.page_start + 1, spec.page_end + 1, pdf.name, saved, e))
                unfinished.append({"chunk": spec.index,
                                   "pages": [spec.page_start, spec.page_end],
                                   "pdf": str(saved)})
                log.error("[%s] chunk #%d (pp%d-%d) UNCONVERTED — all backends "
                          "blocked; saved %s, marked in body.", pdf.name, spec.index,
                          spec.page_start, spec.page_end, saved)
                continue

            body = strip_model_preamble(res.text, spec.index == specs[0].index)
            pieces.append(body)
            carry_open = scan_open_environments(body, initial_stack=carry_open)
            prev_tail = body[-HANDOFF_TAIL_CHARS:]
            if res.cost_usd:
                total_cost += res.cost_usd
            any_trunc = any_trunc or res.truncated

            is_last = spec.index == specs[-1].index
            if res.truncated and not is_last:
                log.warning("[%s] chunk #%d reports truncation mid-chapter; "
                            "the seam handoff will try to recover, but review it.",
                            pdf.name, spec.index)
            log.info("[%s] chunk %d/%d pp%d-%d done — %s, %d ch%s, open=%s",
                     pdf.stem, spec.index + 1, len(specs),
                     spec.page_start + 1, spec.page_end + 1, spec.source, len(body),
                     f", ${res.cost_usd:.3f}" if res.cost_usd else "", carry_open)
    finally:
        if not keep_chunks:
            shutil.rmtree(chunk_dir, ignore_errors=True)

    latex = "\n".join(pieces)
    if carry_open:
        log.error("[%s] FINISHED WITH UNBALANCED ENVIRONMENTS: %s — inspect the "
                  "output; a seam was likely mis-stitched.", pdf.name, carry_open)
    return latex, {"n_chunks": len(specs), "cost": total_cost or None,
                   "open_end": carry_open, "truncated": any_trunc,
                   "unfinished": unfinished}


def convert_chapter(backend: Backend, pdf: Path, spec_text: str, *,
                    out_dir: Path, work_dir: Path, force: bool,
                    keep_chunks: bool, plan_kw: dict,
                    specs: Optional[list[ChunkSpec]] = None,
                    first_chunk_task_suffix: Optional[str] = None) -> ChapterReport:
    nn = _nn(pdf)
    out_tex = out_dir / f"{pdf.stem}.tex"
    rep = ChapterReport(chapter=nn, status="ok", out_path=str(out_tex))

    if out_tex.exists() and not force:
        log.info("[%s] %s exists; skipping (use --force to overwrite).",
                 pdf.name, out_tex.name)
        rep.status = "skipped"
        return rep

    task_base = DEFAULT_TASK_PROMPT
    text: Optional[str] = None

    try:
        # Content-aware chunking is the only mode. A paper normally coalesces to ONE
        # chunk (so this is a de-facto whole-document call with no seam); a long one
        # is split at section boundaries.
        chunk_dir = work_dir / pdf.stem
        unconverted_dir = tc.work_dir(out_dir, "unconverted", pdf.stem)
        text, info = convert_chunked(backend, pdf, spec_text, task_base,
                                     chunk_dir, keep_chunks=keep_chunks,
                                     plan_kw=plan_kw, unconverted_dir=unconverted_dir,
                                     specs=specs,
                                     first_chunk_task_suffix=first_chunk_task_suffix)
        rep.mode = "chunk"
        rep.n_chunks = info["n_chunks"]
        rep.cost_usd = info["cost"]
        rep.truncated = info["truncated"]
        rep.open_at_end = info["open_end"]
        if info["unfinished"]:
            rep.status = "partial"
            rng = ", ".join(f"pp{u['pages'][0] + 1}-{u['pages'][1] + 1}"
                            for u in info["unfinished"])
            rep.error = (f"{len(info['unfinished'])} chunk(s) content-blocked on "
                         f"all backends ({rng}); chunk PDFs saved in "
                         f"{unconverted_dir.name}/ and marked '% UNCONVERTED' in "
                         f"{out_tex.name}")

        # The SKILL figure template is `<book>_<NN>_figs.pdf` — BOTH parts are literal
        # placeholders the model often copies verbatim instead of filling in. Substitute
        # both so \includegraphics resolves; leaving `<NN>` behind yields a build-time
        # "Unable to load picture or PDF file 'kirsch_<NN>_figs.pdf'".
        text = text.replace("<book>", pdf.stem.rsplit("_", 1)[0]).replace("<NN>", nn)

        # An \end{} that closes nothing. open_at_end can't see this — it tolerates a
        # stray \end because a continuation CHUNK legitimately closes what the previous
        # one opened — but on the ASSEMBLED chapter it means the body won't compile.
        rep.stray_ends = scan_unmatched_ends(text)
        if rep.stray_ends:
            log.error("[%s] %d stray \\end{} closing nothing: %s — the body will NOT "
                      "compile; inspect it.", pdf.name, len(rep.stray_ends),
                      ", ".join(rep.stray_ends))

        # Guard against silent "lazy" completions (e.g. thinking=low): the model stops
        # early with finish=STOP, which the truncation checks DON'T catch. A faithful
        # conversion of a math paper runs ~2.5KB of LaTeX per source page (white.pdf:
        # 20.5k chars over 8 pages), so MIN_CHARS_PER_PAGE_PAPER leaves real output
        # alone while still catching a stub.
        try:
            npages = pdf_page_count(str(pdf))
        except Exception:
            npages = 0
        if npages and len(text) < MIN_CHARS_PER_PAGE_PAPER * npages:
            rep.short = True
            log.warning("[%s] output suspiciously SHORT: %d chars for %d pages "
                        "(~%d/pg; complete is >~2000/pg) — likely incomplete, RE-RUN.",
                        pdf.name, len(text), npages, len(text) // max(npages, 1))

        out_dir.mkdir(parents=True, exist_ok=True)
        out_tex.write_text(text, encoding="utf-8")
        log.info("[%s] wrote %s (%d chars).", pdf.name, out_tex.name, len(text))
    except BlockedByPolicyError as e:
        # distinct, expected outcome — recorded & reported, never retried blindly
        rep.status = "blocked"
        rep.error = str(e)
        log.error("[%s] BLOCKED by content policy: %s", pdf.name, e)
    except BackendError as e:
        rep.status = "failed"
        rep.error = str(e)
        log.error("[%s] FAILED: %s", pdf.name, e)
    return rep


# ============================== bib + master =================================


# ------------------------- book-level chapter probe --------------------------


def select_divisions(bm: BookMap, selection: Optional[str]) -> list[Division]:
    """Pick chapters/appendices from the map by `--chapters` ('all', a list '05,06', or
    a range '01-09'), preserving map order."""
    if selection in (None, "all"):
        return list(bm.chapters)
    want: set[str] = set()
    for tok in str(selection).split(","):
        tok = tok.strip()
        if not tok or tok == "none":
            continue
        if "-" in tok:
            a, b = tok.split("-", 1)
            want.update(f"{k:02d}" for k in range(int(a), int(b) + 1))
        else:
            want.add(f"{int(tok):02d}")
    return [d for d in bm.chapters if d.nn in want]


def _slug(s: str) -> str:
    s = re.sub(r"[^A-Za-z0-9]+", "_", (s or "").strip().lower()).strip("_")
    return s or "ref"


_BIB_FIELD_ORDER = ["author", "editor", "title", "booktitle", "journal",
                    "volume", "number", "pages", "year", "publisher",
                    "institution", "doi", "url", "note"]


def _format_bibentry(entrytype: str, key: str, fields: dict) -> str:
    lines = [f"@{(entrytype or 'misc').strip()}{{{key},"]
    present = [(f, str(fields[f]).strip()) for f in _BIB_FIELD_ORDER
               if f in fields and str(fields[f]).strip()]
    present += [(f, str(v).strip()) for f, v in fields.items()
                if f not in _BIB_FIELD_ORDER and str(v).strip()]
    for f, v in present:
        lines.append(f"  {f} = {{{v}}},")
    if lines[-1].endswith(","):
        lines[-1] = lines[-1][:-1]
    lines.append("}")
    return "\n".join(lines)


def _uniquify(records: list[tuple[str, dict]]) -> list[dict]:
    """records: (source_id, raw_entry). Assign globally-unique cite keys.

    Identical works (same entrytype+author+year+title) collapse to ONE key even
    across sources — so the same paper cited in two chapters' per-chapter ref
    lists shares a key. Genuinely different works that collide on a base key are
    suffixed _b, _c, … Each returned record keeps its source so the per-chapter
    token→key map stays correct.
    """
    sig_to_key: dict[tuple, str] = {}
    key_to_sig: dict[str, tuple] = {}
    out: list[dict] = []
    for source_id, e in records:
        f = e.get("fields", {}) or {}
        s = (str(e.get("entrytype", "")), str(f.get("author", "")),
             str(f.get("year", "")), str(f.get("title", "")))
        if s in sig_to_key:
            final = sig_to_key[s]
        else:
            base = _slug(e.get("key") or f"{f.get('author', '')}_{f.get('year', '')}")
            final, n = base, ord("a")
            while final in key_to_sig and key_to_sig[final] != s:
                final = f"{base}_{chr(n)}"
                n += 1
            sig_to_key[s] = final
            key_to_sig[final] = s
        out.append({"source": source_id, "key": final,
                    "srcnum": e.get("srcnum"), "label": e.get("label"),
                    "entrytype": e.get("entrytype", "misc"), "fields": f})
    return out


def _parse_bib_fields(body: str) -> dict:
    """Parse a BibTeX entry body ('field = {value}, field = "value", …') into a dict.
    Brace/quote-balanced and resumes AFTER each value, so an `=` inside a value (e.g. a
    URL) is never mistaken for a field separator."""
    fields: dict = {}
    i, n = 0, len(body)
    name_re = re.compile(r"(\w+)\s*=\s*")
    while i < n:
        m = name_re.search(body, i)
        if not m:
            break
        name, v = m.group(1).lower(), m.end()
        if v >= n:
            break
        ch = body[v]
        if ch == "{":
            depth, k = 1, v + 1
            while k < n and depth:
                depth += (body[k] == "{") - (body[k] == "}")
                k += 1
            val, i = body[v + 1:k - 1], k
        elif ch == '"':
            k = v + 1
            while k < n and body[k] != '"':
                k += 1
            val, i = body[v + 1:k], k + 1
        else:                                    # bare value: number / single token
            k = v
            while k < n and body[k] not in ",\n":
                k += 1
            val, i = body[v:k], k
        fields[name] = " ".join(val.split())     # normalize whitespace
    return fields


def _author_year_label(fields: dict) -> Optional[str]:
    """'Surname (YEAR)' / 'A and B (YEAR)' / 'A et al. (YEAR)' from author+year, or None."""
    au, yr = fields.get("author") or fields.get("editor"), fields.get("year")
    if not au or not yr:
        return None

    def surname(a: str) -> str:
        a = a.strip()
        return (a.split(",")[0] if "," in a else (a.split()[-1] if a.split() else a)).strip()

    people = [p for p in re.split(r"\s+and\s+", au) if p.strip()]
    if not people:
        return None
    if len(people) == 1:
        who = surname(people[0])
    elif len(people) == 2:
        who = f"{surname(people[0])} and {surname(people[1])}"
    else:
        who = f"{surname(people[0])} et al."
    return f"{who} ({yr})"


def _parse_bibtex(text: str) -> tuple[str, list[dict]]:
    """Parse model-emitted BibTeX into (style, entries). Each entry is the dict shape the
    rest of the bib pipeline expects: {key, entrytype, srcnum, label, fields}. `srcnum`
    is the 1-based ORDER for a numeric list (= in-text [n]), else None; `label` is the
    author-year form. Brace-balanced over each @entry, so nested braces are safe."""
    raw = strip_code_fences(text)
    sm = re.search(r"%+\s*style\s*:\s*([\w-]+)", raw, re.I)
    style = (sm.group(1).lower() if sm else "unknown")
    numeric = style.startswith("num")
    entries: list[dict] = []
    for m in re.finditer(r"@(\w+)\s*\{\s*([^,\s]+)\s*,", raw):
        et = m.group(1).lower()
        if et in ("comment", "string", "preamble"):
            continue
        bstart, depth, j = m.end(), 1, m.end()
        while j < len(raw) and depth:
            depth += (raw[j] == "{") - (raw[j] == "}")
            j += 1
        fields = _parse_bib_fields(raw[bstart:j - 1])
        entries.append({"key": m.group(2).strip(), "entrytype": et, "fields": fields})
    for idx, e in enumerate(entries, 1):
        e["srcnum"] = idx if numeric else None
        e["label"] = _author_year_label(e["fields"])
    return style, entries


def generate_bib(backend: Backend, book_ref: Optional[Path],
                 per_chapter: dict[str, Path], out_bib: Path,
                 citemap: Path, force: bool) -> Optional[dict]:
    """Probe the reference list(s), write <book>.bib AND <book>.citemap.json, and
    return the citation index. The .bib and the index are serialized from the SAME
    structured extraction, so their keys are identical by construction.
    """
    sidecar = citemap  # citemap -> work dir (.texify_work); .bib stays in out_dir
    if out_bib.exists() and sidecar.exists() and not force:
        log.info("%s + %s exist; skipping bib (use --force).",
                 out_bib.name, sidecar.name)
        return load_citation(sidecar)

    tagged: list[tuple[str, Path]]
    if book_ref:
        tagged, mode = [("book", book_ref)], "book"
    elif per_chapter:
        tagged = [(nn, per_chapter[nn]) for nn in sorted(per_chapter)]
        mode = "per_chapter"
        log.info("No book-level references; probing %d per-chapter ref file(s).",
                 len(tagged))
    else:
        log.warning("No references PDF found; skipping %s "
                    "(chapters will cite best-effort).", out_bib.name)
        return None

    records: list[tuple[str, dict]] = []
    style: dict[str, str] = {}
    for source_id, ref in tagged:
        log.info("Probing references in %s ...", ref.name)
        try:
            # expect_short=True is LOAD-BEARING. A reference list legitimately returns a
            # small body -- a paper with 3 entries yields ~650 chars of BibTeX -- and the
            # fallback backend's stub floor (MIN_CHARS_PER_PAGE, 800/page) would otherwise
            # reject every engine's perfectly good output as a "short stub" and report
            # "no backend completed". The book pipeline never hit this because a textbook's
            # bibliography runs to pages.
            res = backend.convert(str(ref), BIB_PROBE_SYSTEM_PROMPT,
                                  BIB_PROBE_TASK_PROMPT, expect_short=True)
        except BackendError as e:
            log.error("Citation probe failed for %s: %s", ref.name, e)
            continue
        if res.truncated:
            log.warning("Citation probe of %s may be truncated; verify the entry "
                        "count against the PDF.", ref.name)
        src_style, ents = _parse_bibtex(res.text)
        ents = [e for e in ents if e.get("key")]
        if not ents:                              # nothing parsed → save raw to diagnose
            raw = out_bib.with_name(f"{out_bib.stem}.{source_id}.rawprobe.txt")
            try:
                raw.write_text(res.text or "", encoding="utf-8")
            except OSError:
                raw = None
            log.error("No BibTeX entries parsed from %s%s", ref.name,
                      f"; raw output saved to {raw.name} for diagnosis" if raw else "")
            continue
        style[source_id] = src_style
        records.extend((source_id, e) for e in ents)
        log.info("  %s: style=%s, %d entries.", ref.name, src_style, len(ents))

    if not records:
        log.warning("No citation entries extracted; skipping %s.", out_bib.name)
        return None

    final = _uniquify(records)

    # --- .bib: one entry per unique key (first occurrence wins) ----------------
    seen: set[str] = set()
    entries_bib: list[str] = []
    for r in final:
        if r["key"] in seen:
            continue
        seen.add(r["key"])
        entries_bib.append(_format_bibentry(r["entrytype"], r["key"], r["fields"]))
    out_bib.write_text("\n\n".join(entries_bib) + "\n", encoding="utf-8")
    log.info("Wrote %s (%d unique entries).", out_bib.name, len(entries_bib))

    # --- citation index grouped by source -------------------------------------
    by_source: dict[str, list[dict]] = {}
    for r in final:
        by_source.setdefault(r["source"], []).append(
            {"key": r["key"], "srcnum": r["srcnum"], "label": r["label"]})
    citation = {"schema": "texify-citemap/1", "mode": mode, "style": style,
                "sources": {sid: {"rows": rows} for sid, rows in by_source.items()}}
    sidecar.write_text(json.dumps(citation, indent=2, ensure_ascii=False),
                       encoding="utf-8")
    log.info("Wrote %s.", sidecar.name)
    return citation


def load_citation(sidecar: Path) -> Optional[dict]:
    """Reload a citation index written by a previous --bib run."""
    try:
        data = json.loads(sidecar.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except Exception as e:  # noqa: BLE001
        log.warning("Could not read %s: %s", sidecar.name, e)
        return None
    if str(data.get("schema", "")).startswith("texify-citemap"):
        return data
    log.warning("%s has an unexpected schema; ignoring it.", sidecar.name)
    return None


def citation_block_for(citation: Optional[dict], nn: str) -> str:
    """Render the CITATION INDEX block to append to a chapter's system prompt.

    book mode → the one global index for every chapter; per_chapter mode → only
    chapter `nn`'s rows (so each chapter resolves its own [n] numbering). Returns
    "" when there is nothing to inject (chapters then cite best-effort per SKILL).
    """
    if not citation:
        return ""
    if citation.get("mode") == "book":
        rows = citation.get("sources", {}).get("book", {}).get("rows", [])
    else:
        rows = citation.get("sources", {}).get(nn, {}).get("rows", [])
    rows = [r for r in rows if r.get("key")]
    if not rows:
        return ""
    out = [
        "",
        "## CITATION INDEX (authoritative — use these keys for \\cite{})",
        "Map each in-text citation in the body to exactly one row below, by its "
        "bracket number or its author-year. Use ONLY these keys; never invent a "
        "key. If a citation has no matching row, emit "
        "\\cite{MISSING:<short description>} and a % TODO comment.",
        "",
        "| in-text citation | cite key |",
        "|---|---|",
    ]
    for r in rows:
        toks = []
        if r.get("srcnum") is not None:
            toks.append(f"[{r['srcnum']}]")
        if r.get("label"):
            toks.append(str(r["label"]))
        tok = " / ".join(toks) if toks else "(see reference list)"
        out.append(f"| {tok} | {r['key']} |")
    out.append("")
    return "\n".join(out)


def build_master(prefix: str, out_dir: Path, preamble_path: Path,
                 bibstyle: str = "plainnat", body_files: Optional[list[str]] = None,
                 with_bib: bool = True) -> None:
    """Compose <prefix>.tex: the committed preamble INLINED, then an \\input of the
    per-paper patch assets/preamble.<prefix>.tex, then the body, then the bibliography.

    `body_files` OVERRIDES the default glob of <prefix>_NN.tex, for a source whose printed
    order is not the order the deliverable wants. This one interleaves its questions with
    its solutions, so the file the master must \\input is the MERGED srm_body.tex — and the
    per-division srm_02/srm_03.tex it was built from, which are still on disk and still
    match the glob, must NOT also be input or every item would appear twice (once in place,
    once again in source order) in a document that still compiles cleanly.

    `with_bib=False` omits the bibliography. A source with no reference list has no .bib to
    point at, and \\bibliography{<prefix>} on a missing file is a HARD LaTeX error, not a
    warning — so this is not cosmetic. See --no-bib."""
    if not preamble_path.exists():
        raise SystemExit(
            f"Missing {preamble_path}. The master preamble is committed (not "
            "scraped). Restore assets/preamble.tex before building the master."
        )
    if body_files:
        bodies = [Path(b) for b in body_files]
        missing = [str(b) for b in bodies if not (out_dir / b.name).exists()
                   and not b.exists()]
        if missing:
            raise SystemExit(f"--body names files that do not exist: {', '.join(missing)}")
    else:
        bodies = sorted(out_dir.glob(f"{prefix}_[0-9][0-9].tex"), key=lambda p: p.stem)
        if not bodies:
            log.warning("No %s_NN.tex in %s; master will have no body inputs.",
                        prefix, out_dir)
    preamble = preamble_path.read_text(encoding="utf-8").rstrip()
    body = "\n".join(f"\\input{{{p.stem}}}" for p in bodies)
    paper_pre = preamble_path.with_name(f"preamble.{prefix}.tex")
    paper_input = f"\\input{{{paper_pre.as_posix()}}}\n" if paper_pre.exists() else ""
    # plainnat: numeric [n], bibliography sorted ALPHABETICALLY by author. That
    # reproduces the source's own numbers only when the source's list is itself
    # alphabetical (the common case in mathematics journals). If the source
    # numbers its references in CITATION order instead, pass --bibstyle unsrtnat;
    # if the source's order is arbitrary, no style reproduces it and you must
    # check the printed numbers by hand.
    bib = (f"\\bibliographystyle{{{bibstyle}}}\n\\bibliography{{{prefix}}}\n"
           if with_bib else "")
    master = (
        f"{preamble}\n\n"
        f"{paper_input}"
        f"\\begin{{document}}\n\n"
        f"{body}\n\n"
        f"{bib}"
        f"\\end{{document}}\n"
    )
    master_path = out_dir / f"{prefix}.tex"
    master_path.write_text(master, encoding="utf-8")
    log.info("Wrote master %s (%d body input(s), bib=%s).",
             master_path.name, len(bodies), bibstyle if with_bib else "none")


# ================================== main =====================================

def parse_args(argv=None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Texify a mathematics JOURNAL ARTICLE into master-embeddable LaTeX.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        # No prefix abbreviation. Several book-pipeline flags were removed here, and with
        # abbreviation ON argparse silently resolves a removed flag to a surviving one that
        # merely starts the same way: `--mode whole` (the old chunking switch) became
        # `--model whole`, quietly pinning the backend to a model called "whole". A removed
        # flag must fail loudly.
        allow_abbrev=False,
    )
    ap.add_argument("--backend", choices=["mistral", "claude", "gemini", "fallback"],
                    default="fallback",
                    help="fallback (default & norm): Claude Opus 4.7 (high effort) first, "
                    "then Mistral (OCR + reasoning; free/prepaid but slow), then Gemini 3.1 "
                    "Pro (pay-per-token). An engine is only abandoned after split-retry has "
                    "re-tried the chunk on smaller page ranges, so a stub does NOT switch "
                    "engines on the spot. Force a single engine with "
                    "'claude'/'mistral'/'gemini'.")
    ap.add_argument("--src", default="src", help="folder holding the PDFs")
    ap.add_argument("--out", default=".", help="where .tex outputs are written "
                    "(the master \\inputs them from here)")
    ap.add_argument("--paper", "--book", dest="book", default=None,
                    help="paper prefix, e.g. 'white' (auto-detected from src/<prefix>.pdf "
                    "if it is the only PDF there)")
    ap.add_argument("--divisions", "--chapters", dest="chapters", default=None,
                    help="convert these divisions from the map: 'all', or a list '01'. A "
                    "paper has exactly one, so '--chapters 01' (or 'all'). Omit to NOT "
                    "convert (e.g. for --bib only).")
    ap.add_argument("--spec", default=None,
                    help="conversion contract; default searches "
                    f"{SPEC_CANDIDATES}")
    ap.add_argument("--model", default=None, help="override the backend model")
    ap.add_argument("--spans", default=None,
                    help="convert the selected division in EXPLICIT, hand-chosen 0-based "
                    "inclusive page spans instead of content-aware chunks — e.g. '0-4,5-8'. "
                    "The escape hatch when one passage keeps getting content-blocked: split "
                    "it off so the rest converts. span 0 is a clean start, later spans get "
                    "the seam caution.")
    ap.add_argument("--continues", action="store_true",
                    help="with --spans: treat the FIRST span as a mid-document continuation "
                    "(no title block; begin at the first heading shown)")
    ap.add_argument("--force", action="store_true",
                    help="re-convert / re-bib even if the output already exists")
    ap.add_argument("--keep-temp", action="store_true",
                    help="keep the temporary <name>_NN.pdf / <name>_ref.pdf slices derived "
                    "from the map (default: delete them after use)")
    ap.add_argument("--bib", action="store_true",
                    help="(re)generate <paper>.bib + .texify_work/<paper>.citemap.json from "
                    "the map's reference span. Run this BEFORE converting: the citemap is "
                    "injected into the conversion prompt as the authoritative CITATION INDEX.")
    ap.add_argument("--master", action="store_true", help="(re)build <paper>.tex")
    ap.add_argument("--body", default=None,
                    help="with --master: comma-separated body .tex file(s) to \\input, "
                    "INSTEAD of every <paper>_NN.tex on disk. For a source whose deliverable "
                    "reorders its divisions — this one interleaves questions with solutions "
                    "into srm_body.tex — the per-division files must stay on disk (they are "
                    "the merge's input and the re-conversion unit) but must not ALSO be "
                    "input, or every item is typeset twice in a document that still compiles.")
    ap.add_argument("--no-bib", dest="with_bib", action="store_false", default=True,
                    help="with --master: omit \\bibliographystyle/\\bibliography. Required "
                    "for a source with no reference list: \\bibliography on a missing .bib "
                    "is a hard LaTeX error.")
    ap.add_argument("--bibstyle", default="plainnat",
                    help="bibliography style for the master. plainnat: numeric [n], sorted "
                    "ALPHABETICALLY — reproduces the source's numbers when the source's list "
                    "is alphabetical too (usual in maths journals). unsrtnat: numbered in "
                    "CITATION order. Check the printed numbers against the source.")
    ap.add_argument("--preamble", default="assets/preamble.tex",
                    help="committed master header (inlined into the master; the per-paper "
                    "patch assets/preamble.<paper>.tex is \\input after it)")
    ap.add_argument("--work", default=".texify_work", help="scratch dir for chunk PDFs")
    ap.add_argument("--keep-chunks", action="store_true",
                    help="keep per-chunk PDFs in the work dir (debugging)")
    # mistral-only (the fallback BACKUP, tried last)
    ap.add_argument("--mistral-ocr-model", default=MISTRAL_OCR_MODEL,
                    help="mistral: the OCR model (stage 1, billed per page)")
    ap.add_argument("--mistral-model", default=MISTRAL_TEXT_MODEL,
                    help="mistral: the text model that shapes OCR Markdown into LaTeX "
                    "(stage 2), under --backend mistral AND for the fallback backup hop. "
                    "Under --backend mistral the generic --model overrides it.")
    ap.add_argument("--mistral-effort", default=MISTRAL_REASONING_EFFORT,
                    help="mistral: stage-2 reasoning_effort. The default model accepts only "
                    "'high' or 'none'. Pass '' (empty) for a model with NO `reasoning` "
                    "capability, e.g. --mistral-model mistral-large-latest --mistral-effort ''")
    ap.add_argument("--mistral-max-tokens", type=int, default=MISTRAL_MAX_TOKENS,
                    help="mistral: stage-2 output ceiling")
    ap.add_argument("--no-ocr-cache", action="store_true",
                    help="mistral: re-OCR every chunk even if a cached transcription "
                    "exists (the cache is keyed on the chunk PDF's content hash)")
    # claude-only (also the fallback PRIMARY)
    ap.add_argument("--stream", action="store_true",
                    help="claude: stream-json for exact truncation detection")
    ap.add_argument("--claude-bin", default="claude", help="claude executable")
    ap.add_argument("--effort", default="high",
                    help="claude reasoning effort: low/medium/high/xhigh/max. "
                    "PINNED to high — do NOT raise it. The two conversion failures ever "
                    "observed (opus-4-8 @ max in plg/experiments/exp2; opus-4-7 @ xhigh on "
                    "ross_dp ch.I) both sit at the TOP of the effort scale and both silently "
                    "DROP whole sections. See the CLAUDE_MODEL comment in texify_backends.py.")
    # gemini-only (the fallback SECONDARY)
    ap.add_argument("--temperature", type=float, default=0.1,
                    help="sampling temp (gemini and mistral stage-2)")
    ap.add_argument("--thinking", default="high",
                    help="gemini thinking level: high (default & norm — deepest) / "
                    "default (model decides) / low. WARNING: 'low' makes the model "
                    "lazy-stop on big chapters (short stubs that pass as ok).")
    # chunker passthrough. The coalescing targets (chars/soft-pages) are settled to the
    # Read tool's clean single-pass size and no longer exposed as flags; only the safety
    # ceilings, window knobs, and the per-book boundary vocabulary remain tunable.
    ap.add_argument("--max-chunk-pages", type=int, default=MAX_CHUNK_PAGES,
                    help="hard page CEILING for any chunk (default 20, the Read tool's "
                    "per-request cap); a unit past this is sub-split or windowed.")
    ap.add_argument("--window-pages", type=int, default=WINDOW_PAGES)
    ap.add_argument("--window-overlap", type=int, default=WINDOW_OVERLAP)
    # DEFAULT IS "NEVER": a paper is short enough to convert whole, and forcing a
    # standalone chunk at every "Appendix" heading (the book default) buys nothing and
    # costs a seam. On white.pdf it split the 8-page article in two at the Appendix,
    # putting a chunk boundary through the page that also carries section 4. Pass a real
    # regex only for a LONG paper whose supplementary material must be cut off.
    ap.add_argument("--content-boundary-re", default=CONTENT_BOUNDARY_NEVER,
                    help="regex (case-insensitive) for section titles that must each get "
                    "their own chunk. Defaults to a never-matching pattern, so a paper "
                    "coalesces into as few chunks as fit.")
    ap.add_argument("--min-chars-per-page", type=int, default=MIN_CHARS_PER_PAGE_PAPER,
                    help="a body shorter than this*pages is treated as a soft stub (the "
                    "engine re-tries the chunk in halves, then the next engine gets it). "
                    "The book default of 800 is tuned for dense textbook pages and gives "
                    "FALSE stubs on a journal article, whose pages carry less running text.")
    # split-retry (fallback backend)
    ap.add_argument("--no-split-retry", action="store_true",
                    help="on a stub/block, switch engines IMMEDIATELY instead of first "
                    "re-trying the chunk on smaller page ranges with the same engine")
    ap.add_argument("--split-max-depth", type=int, default=SPLIT_MAX_DEPTH,
                    help="how many times split-retry may halve a chunk before giving up on "
                    "that engine (4 reaches single pages from a 20pp chunk)")
    # misc
    ap.add_argument("--dry-run", action="store_true",
                    help="show inputs + chunk plan, convert nothing")
    ap.add_argument("-v", "--verbose", action="store_true")
    return ap.parse_args(argv)


def _mistral_kwargs(args, *, model: Optional[str]) -> dict:
    """Shared construction for the standalone and the fallback-primary Mistral backend.
    The OCR cache lives under --work so it is swept with the rest of the scratch state,
    and survives a re-run: only the LaTeX shaping is re-paid when the contract changes."""
    return {
        "model": model or MISTRAL_TEXT_MODEL,
        "ocr_model": args.mistral_ocr_model,
        "temperature": args.temperature,
        "reasoning_effort": args.mistral_effort,
        "max_tokens": args.mistral_max_tokens,
        "cache_dir": None if args.no_ocr_cache else Path(args.work) / "ocr_cache",
    }


def _wrap_split(engine: Backend, args) -> Backend:
    """Split-retry applies in EVERY mode, not just fallback: halving a chunk on a stub is
    about giving the engine a fair second chance, not about choosing engines. On a single
    engine the final `BlockedByPolicyError` becomes an `% UNCONVERTED` marker + saved chunk
    PDF, which is strictly more honest than silently writing the stub to disk."""
    if args.no_split_retry:
        return engine
    return SplitRetryBackend(engine,
                             min_chars_per_page=getattr(args, "min_chars_per_page", None) or 0,
                             max_depth=args.split_max_depth)


def make_backend(args) -> Backend:
    if args.backend == "mistral":
        # --model wins (it's the generic override); otherwise honour --mistral-model, which
        # defaults to MISTRAL_TEXT_MODEL — so both flags name the stage-2 model here.
        return _wrap_split(get_backend(
            "mistral", **_mistral_kwargs(args, model=args.model or args.mistral_model)), args)
    if args.backend == "claude":
        return _wrap_split(get_backend("claude", model=args.model,
                                       use_stream_json=args.stream,
                                       claude_bin=args.claude_bin, effort=args.effort), args)
    if args.backend == "gemini":
        return _wrap_split(get_backend("gemini", model=args.model,
                                       temperature=args.temperature,
                                       thinking_level=args.thinking), args)
    # fallback (norm): Claude (effort=max) does the BULK of the work; Mistral, then Gemini,
    # are tried ONLY after an engine has ALREADY failed on the chunk AND on its halves.
    #
    # Two decisions are encoded here.
    #   1. ORDER: claude -> mistral -> gemini. Mistral is the free/prepaid hop, so it comes
    #      before pay-per-token Gemini; it is slow, which only matters for the handful of
    #      chunks that ever reach it.
    #   2. SPLIT BEFORE SWITCH: each engine is wrapped in SplitRetryBackend, so a stub or a
    #      block makes THIS engine re-try the chunk in halves (down to single pages) before
    #      the chunk is handed to a different engine. A stub is usually provoked by a few
    #      dense pages, not by the whole chunk; halving isolates them and keeps the rest on
    #      the primary. --no-split-retry restores the old switch-immediately behaviour.
    #
    # --model pins the CLAUDE primary (e.g. claude-opus-4-7); the mistral/gemini hops keep
    # their own defaults (a claude id is meaningless to them), and --mistral-model is the
    # flag that names Mistral's stage-2 model.
    claude = get_backend("claude", model=args.model, use_stream_json=args.stream,
                         claude_bin=args.claude_bin, effort=args.effort)
    mistral = get_backend("mistral", **_mistral_kwargs(args, model=args.mistral_model))
    gemini = get_backend("gemini", temperature=args.temperature,
                         thinking_level=args.thinking)
    mc = getattr(args, "min_chars_per_page", None) or 0
    engines = [_wrap_split(e, args) for e in (claude, mistral, gemini)]

    log.info("backend=fallback: %s (effort=%s) -> %s (ocr=%s, effort=%s) -> %s "
             "(thinking=%s)%s", claude.model, args.effort, mistral.model,
             args.mistral_ocr_model, args.mistral_effort, gemini.model, args.thinking,
             "" if args.no_split_retry else
             f" | split-retry on each engine (max_depth={args.split_max_depth})")
    return FallbackBackend(engines, **({"min_chars_per_page": mc} if mc else {}))


# Claude session-limit detection lives in texify_common. A paper is a single call, so
# there is nothing to sleep through (the book pipeline's --until-done resume loop is
# gone); the limit is just reported and turned into a distinct exit code.
LIMIT_RE = tc.LIMIT_RE


def main(argv=None) -> int:
    args = parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)-7s %(message)s",
        datefmt="%H:%M:%S",
    )

    src = Path(args.src)
    out_dir = Path(args.out)
    work_dir = Path(args.work)
    if not src.is_dir():
        raise SystemExit(f"--src {src} is not a directory.")

    prefix = discover_paper_prefix(src, args.book)
    book_pdf = src / f"{prefix}.pdf"
    work_dir.mkdir(parents=True, exist_ok=True)
    map_path = work_dir / f"{prefix}.map.yaml"  # control files live in the work dir

    # Run log lives next to the control files (.texify_work/) — easy to find and grep
    # after the fact — in addition to stderr. Appends across runs; the "book=… " line
    # logged below marks each run's start.
    _fh = logging.FileHandler(work_dir / f"{prefix}.convert.log")
    _fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)-7s %(message)s", "%H:%M:%S"))
    logging.getLogger().addHandler(_fh)

    # Spec + backend are built lazily: master/standalone assembly is pure file-stitching
    # (no engine), and an embedded-outline probe is free, so don't force a logged-in CLI
    # or API key unless a step actually needs one.
    _cache: dict = {}

    def spec_text() -> str:
        if "spec" not in _cache:
            general, sp = load_spec(args.spec)
            overlay, op = load_book_overlay(prefix, extra_dirs=[args.out, args.src])
            _cache["spec"] = compose_spec(general, overlay)
            log.info("Using conversion spec: %s (%d chars)%s.", sp, len(_cache["spec"]),
                     f" + book overlay {op}" if op else " (no book overlay)")
        return _cache["spec"]

    def backend() -> Backend:
        if "backend" not in _cache:
            _cache["backend"] = make_backend(args)
        return _cache["backend"]

    # ---- the map drives bib + conversion ------------------------------------
    # The map is HAND-WRITTEN for a paper. The book pipeline built it with an LLM
    # `--probe`, which cannot work here: it requires >= 2 top-level divisions and a
    # paper has one, so it either aborted or promoted the paper's own sections to
    # divisions -- which strands the equation counter (numbered WITHIN sections) at
    # every bogus boundary. Probing is gone; write .texify_work/<paper>.map.yaml by
    # hand. It is ~25 lines and you only do it once.
    bm: Optional[BookMap] = None
    want_convert = args.chapters not in (None, "none", "")
    if (args.bib or want_convert) and bm is None:
        if not map_path.exists():
            raise SystemExit(
                f"no {map_path.name}: write the map by hand (see README -- one division "
                "spanning the article, plus the reference span).")
        bm = load_map(map_path)

    sel = select_divisions(bm, args.chapters) if (bm and want_convert) else []
    division_nums = [d.nn for d in sel]
    if args.spans and len(sel) != 1:
        raise SystemExit("--spans converts ONE division at a time in explicit page spans: "
                         "select exactly one via --chapters NN (got: %s)."
                         % (",".join(division_nums) or "none"))
    if args.continues and not args.spans:
        raise SystemExit("--continues only applies with --spans.")
    plan_kw = dict(max_chunk_chars=MAX_CHUNK_CHARS,
                   soft_max_pages=SOFT_MAX_PAGES,
                   max_chunk_pages=args.max_chunk_pages,
                   window_pages=args.window_pages,
                   window_overlap=args.window_overlap,
                   content_boundary_re=args.content_boundary_re)
    if sel:
        log.info("paper=%s  divisions=%s  backend=%s", prefix,
                 ",".join(division_nums), args.backend)

    # ---- dry-run: per-chapter chunk plan straight from the map (no spend) ----
    if args.dry_run:
        if sel:
            print("\n=== chunk plan (%s) ===" %
                  ("explicit --spans" if args.spans else "content-aware, from the map"))
            for d in sel:
                tmp = derive_chapter_pdf(book_pdf, d, work_dir, prefix)
                try:
                    if args.spans:
                        specs = [ChunkSpec(index=i, page_start=lo, page_end=hi,
                                           title=f"span {lo}-{hi}", source="manual",
                                           clean_boundary=(i == 0))
                                 for i, (lo, hi) in enumerate(parse_spans(args.spans))]
                    else:
                        specs = plan_chunks(str(tmp), outline_entries=to_chunk_outline(d),
                                            **plan_kw)
                finally:
                    if not args.keep_temp:
                        tmp.unlink(missing_ok=True)
                clean = sum(s.clean_boundary for s in specs)
                print(f"  {prefix}_{d.nn} ({d.kind}, {d.n_pages}pp): {len(specs)} chunk(s),"
                      f" {clean} clean / {len(specs) - clean} seam")
                for s in specs:
                    print(f"      #{s.index:02d} p{s.page_start}-{s.page_end} "
                          f"({s.source}) {s.title[:34]}")
        return 0

    if not (args.bib or want_convert or args.master):
        raise SystemExit("Nothing to do: pass --bib, --chapters 01, or --master.")

    reports: list[ChapterReport] = []

    # ---- 2. BIB: harvest the map's reference spans -> one master <name>.bib --
    # The derived ref slices are temporary; generate_bib detects each list's citation
    # style and freezes the keys into <name>.citemap.json so every chapter cites them.
    citation: Optional[dict] = None
    if args.bib:
        if not bm.references:
            log.warning("--bib: the map records no reference spans; nothing to extract.")
        book_ref = None
        per_chapter: dict[str, Path] = {}
        derived: list[Path] = []
        for r in bm.references:
            rp = derive_reference_pdf(book_pdf, r, work_dir, prefix)
            derived.append(rp)
            if r.scope == "book":
                book_ref = rp
            elif r.chapter:
                per_chapter[r.chapter] = rp
        try:
            if book_ref or per_chapter:
                citation = generate_bib(backend(), book_ref, per_chapter,
                                        out_dir / f"{prefix}.bib",
                                        work_dir / f"{prefix}.citemap.json", args.force)
        finally:
            if not args.keep_temp:
                for rp in derived:
                    rp.unlink(missing_ok=True)
    else:
        sidecar = work_dir / f"{prefix}.citemap.json"
        if sidecar.exists():
            citation = load_citation(sidecar)
            if citation:
                log.info("Loaded citation index %s; chapters will cite against it.",
                         sidecar.name)

    # ---- 3. CONVERT the article body from the map ---------------------------
    # Content-aware chunked from the map's sections; Claude-first. The body is a temp
    # slice derived from src/<name>.pdf, deleted after use. The system prompt carries
    # the frozen CITATION INDEX. A paper normally plans as ONE chunk (confirm with
    # --dry-run), so there is no seam and no handoff.
    if sel:
        st, be = spec_text(), backend()
        reports = []
        t0 = time.time()
        for d in sel:
            tmp = derive_chapter_pdf(book_pdf, d, work_dir, prefix)
            cspec = st + citation_block_for(citation, d.nn)
            # --spans: convert in explicit, hand-chosen page spans instead of
            # content-aware chunks. span 0 is a clean start; later spans get the
            # seam caution. Useful when one passage keeps getting refused.
            manual_specs = None
            if args.spans:
                manual_specs = [
                    ChunkSpec(index=i, page_start=lo, page_end=hi,
                              title=f"span {lo}-{hi}", source="manual",
                              clean_boundary=(i == 0))
                    for i, (lo, hi) in enumerate(parse_spans(args.spans))]
            try:
                rep = convert_chapter(
                    be, tmp, cspec, out_dir=out_dir, work_dir=work_dir,
                    force=args.force, keep_chunks=args.keep_chunks,
                    plan_kw={**plan_kw, "outline_entries": to_chunk_outline(d)},
                    specs=manual_specs,
                    first_chunk_task_suffix=(CONT_NOTE if args.continues else None))
            finally:
                if not args.keep_temp:
                    tmp.unlink(missing_ok=True)
            reports.append(rep)
        log.info("Convert pass: %d division(s) attempted in %.1fs.",
                 len(reports), time.time() - t0)

    # --- master ---------------------------------------------------------------
    if args.master:
        build_master(prefix, out_dir, Path(args.preamble), bibstyle=args.bibstyle,
                     body_files=[b.strip() for b in args.body.split(",") if b.strip()]
                     if args.body else None,
                     with_bib=args.with_bib)

    # --- summary --------------------------------------------------------------
    if reports:
        print("\n=== summary ===")
        print(f"{'ch':>3}  {'status':<8} {'mode':<6} {'chunks':>6} "
              f"{'cost$':>8}  {'trunc':<5} {'open_at_end':<14} stray_end")
        for r in sorted(reports, key=lambda x: x.chapter):
            cost = f"{r.cost_usd:.3f}" if r.cost_usd is not None else "n/a"
            openv = ",".join(r.open_at_end) if r.open_at_end else "-"
            stray = ",".join(r.stray_ends) if r.stray_ends else "-"
            line = (f"{r.chapter:>3}  {r.status:<8} {r.mode:<6} {r.n_chunks:>6} "
                    f"{cost:>8}  {str(r.truncated):<5} {openv:<14} {stray}")
            print(line)
            if r.error:
                print(f"       error: {r.error}")
        n_fail = sum(r.status == "failed" for r in reports)
        n_blocked = sum(r.status == "blocked" for r in reports)
        n_partial = sum(r.status == "partial" for r in reports)
        n_ok = sum(r.status == "ok" for r in reports)
        n_warn = sum(bool(r.open_at_end) or bool(r.stray_ends) or r.truncated or r.short
                     for r in reports if r.status == "ok")
        unbal = [r.chapter for r in sorted(reports, key=lambda x: x.chapter)
                 if r.stray_ends]
        if unbal:
            print(f"UNBALANCED (stray \\end{{}} — will NOT compile): {', '.join(unbal)}")
        if args.backend in ("gemini", "fallback"):
            print("note: Gemini reports no $ cost; track tokens in Google billing.")
        if args.backend in ("mistral", "fallback"):
            print("note: Mistral cost is ESTIMATED (OCR per page + stage-2 tokens); "
                  "a cached OCR pass bills $0. Mistral's console is authoritative.")
        if n_warn:
            print(f"warning: {n_warn} chapter(s) flagged truncated/short/unbalanced — review them.")
        short_chs = [r.chapter for r in sorted(reports, key=lambda x: x.chapter) if r.short]
        if short_chs:
            print(f"SHORT/incomplete (likely lazy stop — re-run): {', '.join(short_chs)}")
        if n_blocked:
            chs = ", ".join(r.chapter for r in sorted(reports, key=lambda x: x.chapter)
                            if r.status == "blocked")
            print(f"blocked: {n_blocked} division(s) refused by content-filter policy "
                  f"(verbatim copyrighted text): {chs}")
            print("         Not a code error. All three engines refused; re-attempt later, "
                  "or use --spans to isolate the offending pages so the rest converts.")
        if n_partial:
            chs = ", ".join(r.chapter for r in sorted(reports, key=lambda x: x.chapter)
                            if r.status == "partial")
            print(f"partial: {n_partial} division(s) have content-blocked chunk(s) — "
                  f"the rest converted; gaps saved as PDFs in <paper>_NN_unconverted/ "
                  f"and marked '% UNCONVERTED' in the source: {chs}")
        total_cost = sum(r.cost_usd for r in reports if r.cost_usd)
        if total_cost:
            print(f"est. cost this run: ${total_cost:.2f} (rate estimate — "
                  f"verify against provider billing).")
        print(f"totals: {n_ok} ok, {n_partial} partial, {n_blocked} blocked, "
              f"{n_fail} failed (of {len(reports)}).")
        n_limit = sum(bool(r.status == "failed" and r.error and LIMIT_RE.search(r.error))
                      for r in reports)
        return 42 if n_limit else (1 if n_fail else 0)   # 42 = stopped on a session limit
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
