#!/usr/bin/env python3
"""
texify_common.py — shared helpers for the texify pipeline.

Three things, defined once so orchestrate / qa / xref / citefix agree:

  * INTERMEDIATE-FILE LAYOUT — every transient artifact lives under <out>/.texify_work/, so the
    project root holds only deliverables (the body, the master, the pdf, the bib, src, assets).
  * backup_write — edit a file in place, stashing the original once under .texify_work/backups/.
  * LIMIT_RE — recognise a Claude session-limit message so the run can report it distinctly
    (exit 42) rather than as a generic failure.

No project deps: import this from anywhere without an import cycle.
"""
from __future__ import annotations

import logging
import re
import shutil
from pathlib import Path

log = logging.getLogger("texify.common")

# ============================ intermediate-file layout =======================
WORK = ".texify_work"


def work_dir(out_dir, *sub: str) -> Path:
    """Return (and create) <out_dir>/.texify_work[/sub...]."""
    d = Path(out_dir) / WORK
    for s in sub:
        d = d / s
    d.mkdir(parents=True, exist_ok=True)
    return d


def backup_write(path: Path, new_text: str, out_dir=None) -> Path:
    """Write `new_text` to `path`, first copying the original (once) to
    .texify_work/backups/<name>.bak. Returns the file written."""
    path = Path(path)
    base = out_dir if out_dir is not None else path.parent
    if path.exists():
        bak = work_dir(base, "backups") / (path.name + ".bak")
        if not bak.exists():
            shutil.copy2(path, bak)
    path.write_text(new_text, encoding="utf-8")
    return path


# ============================== session limit ================================
# Reported, not slept through. The book pipeline's --until-done resume loop (and the
# seconds_until_reset clock math it needed) is gone: a paper is a single call, so there is
# nothing to resume — you just re-run it after the reset.
LIMIT_RE = re.compile(r"session limit|hit your[^.]*limit|resets?\s+\d", re.I)


# ============================ UNCONVERTED marker =============================
# A chunk that ALL backends content-block becomes a recoverable in-body marker; its PDF slice is
# saved under .texify_work/unconverted/ so the gap is explicit and can be filled by hand or with
# --spans. (The book pipeline also had a single-PAGE marker + regexes to find and re-splice both,
# for texify_refine's page-at-a-time recovery pass; refine is gone, and nothing reads the markers
# back, so the marker is now write-only and the regexes are deleted.)
def unconverted_chunk_marker(p1: int, p2: int, src_name: str, saved: Path, reason: str) -> str:
    """Marker for a whole blocked chunk (1-based inclusive pages p1..p2 of src_name)."""
    return (
        f"\n% ===== UNCONVERTED CHUNK: pages {p1}-{p2} of {src_name} — all backends "
        f"content-blocked.\n"
        f"% Convert this PDF by hand (or re-run with --spans to isolate it) and paste the "
        f"body here:\n"
        f"%   {saved}\n% reason: {reason}\n% =====\n")
