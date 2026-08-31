#!/usr/bin/env python3
r"""
verify.py — the regression gate for the srm conversion. Run it after ANY change; it costs
nothing (no engine calls).

    ./verify.py                 # text checks + .aux readback + a clean compile
    ./verify.py --no-build      # text checks only (no pdflatex)
    ./verify.py --selftest      # prove every check can fail, then exit

WHAT A GATE IS FOR
------------------
Brace balance, "0 flags", "it compiles" and "open_at_end is empty" say almost nothing about
fidelity: a body can drop a whole question, swap two answer choices, silently repair a printed
typo or put choice (D)'s picture under choice (C) and still pass every one of them. So every
check below is a COUNT OR A FACT PREDICTED FROM THE PRINTED PAGE — read off the 75 rendered
page images by hand, before any conversion existed — because a number predicted from the
source is the only kind of check that can actually fail.

The strongest of them is the .aux readback: every \label must equal the number LaTeX actually
SET for it. That catches a numbering shift from any cause, including ones nobody thought to
test for.

⚠ A CRASH IS NOT A PASS. This exits 1 both when a check fails and when Python raises, so a
harness that counts "FAIL" lines can report a clean baseline while half the checks never ran.
Treat a traceback as a hard stop.

⚠ AND A GATE THAT FAILS WRONGLY IS WORSE THAN NO GATE. Before believing a failure, check the
ground truth below against the page — the same discipline the gate exists to enforce on the
converter.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

PAPER = "srm"
N_ITEMS = 75

# ============================== GROUND TRUTH ==================================
# Read off the page images by hand. Nothing here is derived from the conversion.

# The four numbers withdrawn in August 2023. The source still prints each, followed by the
# bare word DELETED (p14, p21, p35, p48 and again p61, p64, p68, p73).
DELETED = {17, 28, 47, 65}

# The answer key of every live item, from the "Key:" line of its solution. Solution 7 (p58)
# has NO key line at all — it is the empty string, and that is not a gap in this table.
KEYS = {
    1: "E",  2: "C",  3: "D",  4: "B",  5: "E",  6: "E",  7: "",   8: "D",  9: "E", 10: "C",
    11: "E", 12: "E", 13: "E", 14: "B", 15: "D", 16: "D", 18: "B", 19: "E", 20: "C", 21: "C",
    22: "A", 23: "C", 24: "C", 25: "C", 26: "A", 27: "C", 29: "E", 30: "D", 31: "D", 32: "E",
    33: "E", 34: "B", 35: "B", 36: "D", 37: "B", 38: "D", 39: "E", 40: "C", 41: "B", 42: "E",
    43: "D", 44: "C", 45: "C", 46: "D", 48: "B", 49: "C", 50: "B", 51: "C", 52: "D", 53: "A",
    54: "C", 55: "B", 56: "B", 57: "A", 58: "C", 59: "C", 60: "C", 61: "D", 62: "A", 63: "D",
    64: "E", 66: "D", 67: "D", 68: "E", 69: "C", 70: "C", 71: "C", 72: "C", 73: "B", 74: "C",
    75: "D",
}

# Every question that carries artwork, and the figure keys it must place, in order. A
# question not listed here has none. 17 figures on 11 questions.
FIGS = {
    26: ["q26a", "q26b", "q26c"],
    33: ["q33"], 35: ["q35"], 39: ["q39"],
    48: ["q48", "q48a", "q48b", "q48c", "q48d", "q48e"],
    51: ["q51"], 57: ["q57"], 63: ["q63"], 66: ["q66"], 73: ["q73"],
}

# Word tables, counted from the cell-rule bands of the source: 18 in the questions (pp. 3, 4,
# 10, 13, 20, 27, 33, 34, 39, 40, 42, 43, 44, 47, 51, 52, 53, 54) and 1 in the solutions
# (solution 15, p60).
N_TABLES_Q, N_TABLES_S = 18, 1

# The three questions whose statement list runs to IV; every other list stops at III.
FOUR_STATEMENTS = {5, 6, 74}

# Every table, as (side, item, source page, y-band). The bands are the extent of the Word
# cell rules, measured off the source; each of these 19 pages carries exactly one table.
# Used to compare the NUMBERS in the source's own cells against the numbers in the tabular.
TABLE_BANDS = [
    ("q",  3,  3, 208, 267), ("q",  4,  4, 187, 246), ("q", 11, 10, 108, 267),
    ("q", 15, 13, 129, 415), ("q", 27, 20, 214, 338), ("q", 37, 27, 150, 266),
    ("q", 45, 33, 129, 267), ("q", 46, 34, 150, 262), ("q", 54, 39, 129, 309),
    ("q", 55, 40, 129, 186), ("q", 57, 42, 170, 266), ("q", 58, 43, 156, 210),
    ("q", 59, 44, 129, 267), ("q", 63, 47, 354, 436), ("q", 68, 51, 214, 309),
    ("q", 69, 52, 214, 309), ("q", 70, 53, 150, 287), ("q", 72, 54, 317, 434),
    ("s", 15, 60, 398, 684),
]

# Errata that must SURVIVE, as the page prints them. Each is (side, item, label, pattern) and
# is searched INSIDE THAT ITEM'S OWN BLOCK.
#
# ⚠ THE SCOPE IS THE POINT, and it is what the first version of this gate got wrong. Its
# "silently repaired to 'I, II and III'" check scanned the whole questions file — and five
# OTHER questions (31, 34, 38, 60 and 74) print exactly that string as their own choice (D),
# quite correctly. So the gate failed a conversion that had reproduced question 2's typo
# perfectly, complete with its % SIC note. That is the "a gate that fails wrongly is worse
# than no gate" case, and the fix is to scope every erratum to the item the page prints it in.
ERRATA_PRESENT = [
    ("q",  2, "Q2(D) 'I, II and II'",            r"I,\s*II\s+and\s+II(?!I)"),
    ("q", 16, "Q16(E) doubled 'the meet the'",   r"meet\s+the\s+meet\s+the"),
    ("q", 30, "Q30 'with respect the loadings'", r"with\s+respect\s+the\s+loadings"),
    ("q", 64, "Q64 'which or the following'",    r"which\s+or\s+the\s+following"),
    ("q", 73, "Q73 lead-in ends with a comma",   r"optimal\s+pruned\s+tree,"),
    ("q", 31, "Q31 stem ends with no full stop",
     r"represented\s+as\s+a\s+random\s+walk(?!\s*\.)"),
    ("s", 21, "S21(II) 'depend in t'",           r"depend\s+in\s+\$?t"),
    ("s", 26, "S26 'the one the existing regions'", r"the\s+one\s+the\s+existing\s+regions"),
    ("s", 37, "S37(II) 'presence of absence'",   r"presence\s+of\s+absence"),
    ("s", 61, "S61(III) 'less than equal to'",   r"less\s+than\s+equal\s+to"),
    ("s", 62, "S62 'produces and interval'",     r"produces\s+and\s+interval"),
    ("s", 69, "S69 'all zero They'",             r"all\s+zero\s+They"),
    ("s", 70, "S70 '(89.45755]' mismatched bracket", r"89\.45755\s*\]"),
]

# The SILENT REPAIR of each of those is the fidelity bug the contract forbids, and it is
# invisible to every structural check — so look for it directly, in the same scope.
ERRATA_ABSENT = [
    ("q",  2, "Q2(D) repaired to 'I, II and III'",  r"I,\s*II\s+and\s+III"),
    ("q", 16, "Q16(E) de-doubled to 'meet the stated'", r"\(D\)\s+meet\s+the\s+stated"),
    ("q", 30, "Q30 repaired to 'with respect to the loadings'",
     r"with\s+respect\s+to\s+the\s+loadings"),
    ("q", 64, "Q64 repaired to 'which of the following is always true'",
     r"which\s+of\s+the\s+following\s+is\s+always\s+true"),
    ("s", 21, "S21 repaired to 'depend on t'",      r"depend\s+on\s+\$?t"),
    ("s", 37, "S37 repaired to 'presence or absence'", r"presence\s+or\s+absence"),
    ("s", 61, "S61 repaired to 'less than or equal to'", r"less\s+than\s+or\s+equal\s+to"),
    ("s", 62, "S62 repaired to 'produces an interval'", r"produces\s+an\s+interval"),
    ("s", 69, "S69 repaired to 'all zero. They'",   r"all\s+zero\.\s+They"),
]

# Items whose slip is a WRONG or EXTRA character (not merely absent punctuation) and which the
# contract therefore requires to carry a `% SIC:` note inside the item's own block.
SIC_QUESTIONS = {2, 16, 30, 64, 66}
SIC_SOLUTIONS = {21, 26, 37, 61, 62, 66, 69, 70}

# Macros that must not appear anywhere in the body. Each is something this source does not
# have; emitting one means the converter reached for a structure that is not on the page.
FORBIDDEN = [
    r"\\chapter\b", r"\\section\b", r"\\subsection\b", r"\\cite\b", r"\\eqref\b",
    r"\\begin\{equation\}", r"\\begin\{align\}(?!\*)", r"\\begin\{figure\}",
    r"\\begin\{table\}", r"\\caption\b", r"\\includegraphics\b", r"\\label\{eq:",
    r"\\documentclass", r"\\usepackage", r"\\begin\{document\}", r"```",
    r"\\leq\b", r"\\geq\b", r"\\le\b", r"\\ge\b",          # house rule: \leqslant/\geqslant
    r"\\mathbb\{[PE]\}", r"\\Pr\b",                          # house rule: \prb/\expc
    # ⚠ A BARE E( OR Var( IN MATH. This is the one the gate missed on the first real
    # conversion: question 13's statement III came out `$E(y \mid x)$` while the other four
    # occurrences in the source correctly used \expc/\var. \mathbb{E} and \Pr were forbidden
    # but the plainest spelling of all was not, and it renders as a perfectly ordinary italic
    # E — indistinguishable, on the page, from the macro. The negative lookbehind lets
    # \expc/\var/\mathit{E} through and stops at a word character, so "SSE(" and "TRUE(" do
    # not match.
    r"(?<![A-Za-z\\])E\s*\(", r"(?<![A-Za-z\\])Var\s*\(",
    # ⚠ AN UNSUBSCRIPTED INDEXED VARIABLE. The source is inconsistent — true subscripts in
    # question 66, full-size baseline digits in question 59's table, and plain roman "X1, X2,
    # X3" typed into the body font in question 70 — and following it makes the document
    # disagree with itself about its own notation two questions apart. Everything is `X_1`.
    # (T1-T4 in question 57 are node NAMES, not indexed variables, and are left as printed;
    # the class is restricted to X so they pass.)
    r"(?<![A-Za-z\\])X\d",
]

# ============================== plumbing ======================================

_COMMENT_RE = re.compile(r"(?<!\\)%[^\n]*")
_Q_OPEN = re.compile(r"\\begin\{question\}\{(\d+)\}")
_S_OPEN = re.compile(r"\\begin\{solution\}\{(\d+)\}\{([A-E]?)\}")


def _mask(text: str) -> str:
    """Comments blanked to spaces of the same length, so offsets still index the original."""
    return _COMMENT_RE.sub(lambda m: " " * len(m.group(0)), text)


def _blocks(text: str, env: str) -> dict[int, str]:
    open_re = _Q_OPEN if env == "question" else _S_OPEN
    end_re = re.compile(rf"\\end\{{{env}\}}")
    masked, out = _mask(text), {}
    for m in open_re.finditer(masked):
        e = end_re.search(masked, m.end())
        if e:
            out[int(m.group(1))] = text[m.start():e.end()]
    return out


def _env_problems(text: str, env: str) -> list[str]:
    r"""Structural defects in the \begin{env}…\end{env} stream that a per-block dict CANNOT
    see, because building one hides both of them.

    ⚠ THIS EXISTS BECAUSE THE GATE MISSED A DROPPED \end{solution}. Remove one, and every
    later \begin still finds *an* \end — the next block's — so the scan still returns 75
    blocks with the right numbers and the right keys, and the only trace is that block 1 now
    contains block 2 entirely. The document brace-balances, compiles, and prints solution 2
    inside solution 1's list. Nothing else here looks at the stream in order, so nothing else
    can see it.

    A REPEATED NUMBER is the same kind of blind spot from the other side: a dict keyed on the
    number silently keeps the last one, so six duplicated items — the exact defect a 1-page
    window overlap produces — leave the count at 75."""
    masked = _mask(text)
    open_re = _Q_OPEN if env == "question" else _S_OPEN
    end_re = re.compile(rf"\\end\{{{env}\}}")
    opens = list(open_re.finditer(masked))
    ends = list(end_re.finditer(masked))
    out = []
    if len(opens) != len(ends):
        out.append(f"{env}: {len(opens)} \\begin but {len(ends)} \\end")
    seen: dict[int, int] = {}
    for m in opens:
        n = int(m.group(1))
        seen[n] = seen.get(n, 0) + 1
        e = end_re.search(masked, m.end())
        if not e:
            out.append(f"{env} {n}: never closed")
            continue
        nxt = open_re.search(masked, m.end())
        if nxt and nxt.start() < e.start():
            out.append(f"{env} {n}: swallows {env} {nxt.group(1)} — its \\end is missing")
    for n, k in sorted(seen.items()):
        if k > 1:
            out.append(f"{env} {n} appears {k} times")
    return out


def _items_in(block: str, env: str) -> int:
    """How many \\item the FIRST `env` list inside this block has."""
    masked = _mask(block)
    b = re.search(rf"\\begin\{{{env}\}}", masked)
    if not b:
        return 0
    e = re.search(rf"\\end\{{{env}\}}", masked[b.end():])
    if not e:
        return -1
    return len(re.findall(r"\\item\b", masked[b.end():b.end() + e.start()]))


class Report:
    def __init__(self):
        self.fails: list[str] = []
        self.n = 0

    def check(self, ok: bool, msg: str):
        self.n += 1
        if not ok:
            self.fails.append(msg)
        return ok


# ============================== the checks ====================================

def check_text(rep: Report, qtex: str, stex: str, body: str, figdir: Path):
    q, s = _blocks(qtex, "question"), _blocks(stex, "solution")

    # -- the environment stream, walked IN ORDER ------------------------------
    for tex, env in ((qtex, "question"), (stex, "solution")):
        probs = _env_problems(tex, env)
        rep.check(not probs, "; ".join(probs))

    # -- the registry ---------------------------------------------------------
    rep.check(len(q) == N_ITEMS, f"questions: {len(q)} blocks, expected {N_ITEMS}")
    rep.check(len(s) == N_ITEMS, f"solutions: {len(s)} blocks, expected {N_ITEMS}")
    want = set(range(1, N_ITEMS + 1))
    rep.check(set(q) == want, f"question numbers off: missing {sorted(want - set(q))}, "
                              f"extra {sorted(set(q) - want)}")
    rep.check(set(s) == want, f"solution numbers off: missing {sorted(want - set(s))}, "
                              f"extra {sorted(set(s) - want)}")

    # -- the four withdrawn numbers, on both sides ----------------------------
    for n in sorted(DELETED):
        for side, blocks in (("question", q), ("solution", s)):
            b = blocks.get(n, "")
            body_only = re.sub(r"\\(?:begin|end)\{\w+\}(\{[^}]*\})*", "", _mask(b)).strip()
            rep.check(body_only == r"\deleted",
                      f"{side} {n} should be exactly \\deleted, is {body_only[:60]!r}")
    for n in sorted(want - DELETED):
        rep.check(r"\deleted" not in _mask(q.get(n, "")),
                  f"question {n} is not withdrawn but carries \\deleted")

    # -- the answer keys ------------------------------------------------------
    for n, want_key in KEYS.items():
        m = _S_OPEN.search(_mask(s.get(n, "")))
        got = m.group(2) if m else "<no block>"
        rep.check(got == want_key,
                  f"solution {n}: key {got!r}, page says {want_key!r}")
    rep.check(_S_OPEN.search(_mask(s.get(7, ""))) is not None
              and _S_OPEN.search(_mask(s[7])).group(2) == "",
              "solution 7 must have an EMPTY key argument (the page prints no Key line)")

    # -- five choices per live question, none for a withdrawn one -------------
    for n in sorted(want - DELETED):
        rep.check(_items_in(q.get(n, ""), "choices") == 5,
                  f"question {n}: {_items_in(q.get(n, ''), 'choices')} choices, expected 5")
    for n in sorted(DELETED):
        rep.check(r"\begin{choices}" not in _mask(q.get(n, "")),
                  f"question {n} is withdrawn and must have no choices")
    total = sum(_items_in(q.get(n, ""), "choices") for n in want - DELETED)
    rep.check(total == 5 * (N_ITEMS - len(DELETED)),
              f"{total} answer choices in all, expected {5 * (N_ITEMS - len(DELETED))}")

    # -- statement lists: only three questions reach IV -----------------------
    for n in sorted(FOUR_STATEMENTS):
        rep.check(_items_in(q.get(n, ""), "statements") == 4,
                  f"question {n}: statements list has "
                  f"{_items_in(q.get(n, ''), 'statements')} items, page shows 4")
    for n, b in q.items():
        k = _items_in(b, "statements")
        if k and n not in FOUR_STATEMENTS:
            rep.check(k == 3, f"question {n}: statements list has {k} items, page shows 3")

    # -- figures --------------------------------------------------------------
    for n, keys in FIGS.items():
        got = re.findall(r"\\srmfig\{([^}]*)\}", _mask(q.get(n, "")))
        rep.check(got == keys, f"question {n}: figures {got}, page shows {keys}")
    for n, b in q.items():
        if n not in FIGS:
            rep.check(not re.search(r"\\srmfig\b", _mask(b)),
                      f"question {n} has no artwork on the page but places a figure")
    rep.check(not re.search(r"\\srmfig\b", _mask(stex)),
              "the solutions carry no artwork; none must be placed there")
    all_keys = [k for ks in FIGS.values() for k in ks]
    for k in all_keys:
        rep.check((figdir / f"{PAPER}_{k}.pdf").exists(),
                  f"figure file {figdir}/{PAPER}_{k}.pdf is missing "
                  f"(run texify_figs_srm.py)")
    rep.check(len(re.findall(r"\\srmfig\b", _mask(qtex))) == len(all_keys),
              f"{len(re.findall(chr(92) + chr(92) + 'srmfig' + chr(92) + 'b', _mask(qtex)))} "
              f"\\srmfig calls, expected {len(all_keys)}")

    # -- tables ---------------------------------------------------------------
    for label, tex, want_n in (("questions", qtex, N_TABLES_Q), ("solutions", stex, N_TABLES_S)):
        got = len(re.findall(r"\\begin\{tabular\}", _mask(tex)))
        rep.check(got == want_n, f"{label}: {got} tabulars, the pages show {want_n}")

    # -- errata ---------------------------------------------------------------
    for side, item, label, pat in ERRATA_PRESENT:
        block = _mask((q if side == "q" else s).get(item, ""))
        rep.check(re.search(pat, block) is not None,
                  f"erratum LOST — {label} is no longer in item {item} as printed")
    for side, item, label, pat in ERRATA_ABSENT:
        block = _mask((q if side == "q" else s).get(item, ""))
        rep.check(re.search(pat, block) is None, f"SILENT CORRECTION — {label}")
    for n in sorted(SIC_QUESTIONS):
        rep.check("% SIC" in q.get(n, ""), f"question {n} reproduces a printed slip but "
                                           f"carries no '% SIC:' note")
    for n in sorted(SIC_SOLUTIONS):
        rep.check("% SIC" in s.get(n, ""), f"solution {n} reproduces a printed slip but "
                                           f"carries no '% SIC:' note")

    # -- forbidden constructs -------------------------------------------------
    for pat in FORBIDDEN:
        for label, tex in (("questions", qtex), ("solutions", stex)):
            hit = re.search(pat, _mask(tex))
            rep.check(hit is None,
                      f"{label}: forbidden {pat} at ...{_mask(tex)[max(0, hit.start()-40):hit.end()+20]!r}"
                      if hit else "")

    # -- THE DELIVERABLE: every question immediately followed by its solution --
    if body:
        seq = [(m.start(), "q", int(m.group(1))) for m in _Q_OPEN.finditer(_mask(body))]
        seq += [(m.start(), "s", int(m.group(1))) for m in _S_OPEN.finditer(_mask(body))]
        seq.sort()
        want_seq = []
        for n in range(1, N_ITEMS + 1):
            want_seq.append(("q", n))
            if n not in DELETED:            # a withdrawn number prints DELETED once, not twice
                want_seq.append(("s", n))
        got_seq = [(k, n) for _, k, n in seq]
        rep.check(got_seq == want_seq,
                  "srm_body.tex is not interleaved as required. First divergence: "
                  + next((f"position {i}: got {got_seq[i]}, expected {want_seq[i]}"
                          for i in range(min(len(got_seq), len(want_seq)))
                          if got_seq[i] != want_seq[i]),
                         f"length {len(got_seq)} vs {len(want_seq)}"))
        rep.check(r"\srmpart" not in _mask(body),
                  "srm_body.tex keeps a \\srmpart half-title; interleaved order has no halves")


_NUM_RE = re.compile(r"\d[\d,{}\\]*(?:\.\d+)?")


def _magnitudes(text: str) -> list[str]:
    """Every number in `text`, as a bare digit string — no sign, no thousands separator.

    Signs are deliberately dropped. The source prints its negatives four different ways
    ("–45,765,767.76", "− 0.549", "– 0.1" with a space after the dash), so a signed comparison
    reports a difference wherever the dash merely sits apart from its digits, and a check that
    cries wolf on correct output is worse than no check at all. What survives is the digits,
    which is what a transposed or dropped one changes."""
    out = []
    for m in _NUM_RE.finditer(text):
        s = re.sub(r"[,{}\\]", "", m.group(0)).rstrip(".")
        if s:
            out.append(s)
    return sorted(out)


_MULTI_RE = re.compile(r"\\multicolumn\{\d+\}\{[^{}]*\}\{((?:[^{}]|\{[^{}]*\})*)\}")


def _tabular_data(block: str) -> str:
    r"""The DATA of the first tabular in `block` — its cells, with LaTeX's own numbers gone.

    ⚠ A TABULAR CARRIES NUMBERS THAT ARE NOT DATA, and they will be compared against the
    source's cells if you let them: the `5` in `\multicolumn{5}{|c|}{Executive Compensation}`
    spanning question 54's title row, and the column count implicit in `{|l|r|r|r|r|}`. The
    first version of this check reported question 54 as differing from its own page by one
    stray `5` — a gate crying wolf on a perfectly correct table, which is the failure mode
    that gets a gate switched off."""
    m = re.search(r"\\begin\{tabular\}.*?\\end\{tabular\}", block, re.S)
    if not m:
        return ""
    t = m.group(0)
    t = re.sub(r"^\\begin\{tabular\}\s*(\[[^\]]*\])?\s*\{[^{}]*\}", "", t)   # column spec
    t = t.replace(r"\end{tabular}", "")
    t = _MULTI_RE.sub(r"\1", t)                                             # keep the content
    t = re.sub(r"\\cline\{[^{}]*\}|\\hline|\\\\", " ", t)
    return t


def check_tables(rep: Report, qtex: str, stex: str, pdf: Path):
    """The numbers in every tabular, against the numbers in the source's own cells.

    ⚠ THIS IS THE ONLY CHECK THAT CAN SEE A TRANSPOSED DIGIT. Question 54's table alone
    carries 24 numbers of up to seven significant figures; turn 15,286.6 into 15,268.6 and the
    body still balances, the tabular still has the right shape, the count of tables is still
    19, the PDF still looks perfect, and the candidate working the question gets the wrong
    answer. Nothing structural can reach it — only the source can.

    It compares MULTISETS, not positions, so it cannot say *which* cell moved; a transposition
    that swaps two cells' contents within one table is invisible to it. It catches the digit
    itself being wrong, which is the failure that actually happens."""
    try:
        import fitz
    except ImportError:
        rep.check(True, "")
        print("note: PyMuPDF not installed — the table-number check was skipped.")
        return
    if not pdf.exists():
        print(f"note: {pdf} not present — the table-number check was skipped.")
        return
    doc = fitz.open(str(pdf))
    q, s = _blocks(qtex, "question"), _blocks(stex, "solution")
    for side, item, page1, y0, y1 in TABLE_BANDS:
        band = doc[page1 - 1].get_text("text", clip=fitz.Rect(0, y0, 612, y1))
        block = _mask((q if side == "q" else s).get(item, ""))
        want, got = _magnitudes(band), _magnitudes(_tabular_data(block))
        rep.check(want == got,
                  f"{'question' if side == 'q' else 'solution'} {item} (p{page1}): the "
                  f"tabular's numbers differ from the source's cells — "
                  f"only on the page {sorted(set(want) - set(got)) or []}, "
                  f"only in the tex {sorted(set(got) - set(want)) or []}"
                  + (f", counts differ" if set(want) == set(got) else ""))
    doc.close()


def check_build(rep: Report, aux: Path, log: Path):
    """The strongest check there is: what LaTeX ACTUALLY SET for every \\label."""
    if not aux.exists():
        rep.check(False, f"{aux} not written — the build did not finish")
        return
    text = aux.read_text(encoding="utf-8", errors="replace")
    labels = dict(re.findall(r"\\newlabel\{([qs]:\d+)\}\{\{([^}]*)\}", text))
    for n in range(1, N_ITEMS + 1):
        rep.check(labels.get(f"q:{n}") == str(n),
                  f".aux: \\label{{q:{n}}} resolved to {labels.get(f'q:{n}')!r}, not {n!r}")
    for n in range(1, N_ITEMS + 1):
        if n in DELETED:
            rep.check(f"s:{n}" not in labels,
                      f".aux: s:{n} is set, but withdrawn item {n} must print DELETED once")
        else:
            rep.check(labels.get(f"s:{n}") == str(n),
                      f".aux: \\label{{s:{n}}} resolved to {labels.get(f's:{n}')!r}, not {n!r}")
    if log.exists():
        t = log.read_text(encoding="utf-8", errors="replace")
        rep.check("LaTeX Error" not in t, "the build log carries a LaTeX Error")
        rep.check("Undefined control sequence" not in t,
                  "the build log carries an undefined control sequence")
        rep.check("??" not in re.sub(r"\?\?\?+", "", t) or "Reference" not in t,
                  "the build log reports an undefined reference")


# ============================== self-test =====================================
# "Prove each check has teeth: mutate the body and watch it fail." A gate that cannot fail is
# decoration. Each mutation below is a defect this pipeline can actually produce.

def _synth(pdf: Path) -> tuple[str, str, str]:
    """A minimal body built from the GROUND TRUTH alone that must pass every check.

    The tabulars are filled with the numbers read out of the SOURCE's own cells, so the
    table-number check has something real to pass — and something a mutation can break."""
    try:
        import fitz
        doc = fitz.open(str(pdf))
        cells = {(side, n): _magnitudes(
                     doc[pg - 1].get_text("text", clip=fitz.Rect(0, y0, 612, y1)))
                 for side, n, pg, y0, y1 in TABLE_BANDS}
        doc.close()
    except Exception:
        cells = {(side, n): ["0"] for side, n, _pg, _y0, _y1 in TABLE_BANDS}
    tab = {k: "\\begin{tabular}{c}" + " ".join(v) + "\\end{tabular}"
           for k, v in cells.items()}
    qs, ss = [], []
    sic_note = "% SIC: reproduced as printed.\n"
    errata_q = {
        2: "I, II and II", 16: "meet the meet the", 30: "with respect the loadings",
        64: "which or the following", 66: "left-hand branch of a split.",
        73: "optimal pruned tree,\n", 31: "represented as a random walk",
    }
    errata_s = {
        21: "depend in $t$", 26: "the one the existing regions",
        37: "presence of absence", 61: "less than equal to",
        62: "produces and interval", 66: "must be .$> 10$",
        69: "all zero They", 70: "2(1)(89.45755]/100",
    }
    for n in range(1, N_ITEMS + 1):
        if n in DELETED:
            qs.append(f"\\begin{{question}}{{{n}}}\n\\deleted\n\\end{{question}}")
            ss.append(f"\\begin{{solution}}{{{n}}}{{}}\n\\deleted\n\\end{{solution}}")
            continue
        parts = [f"\\begin{{question}}{{{n}}}"]
        if n in SIC_QUESTIONS:
            parts.append(sic_note.rstrip())
        parts.append(errata_q.get(n, f"Stem of question {n}."))
        if n in FOUR_STATEMENTS:
            parts.append("\\begin{statements}\n" + "\\item x\n" * 4 + "\\end{statements}")
        for k in FIGS.get(n, []):
            parts.append(f"\\srmfig{{{k}}}")
        if ("q", n) in tab:
            parts.append(tab[("q", n)])
        parts.append("\\begin{choices}\n" + "\\item x\n" * 5 + "\\end{choices}")
        parts.append("\\end{question}")
        qs.append("\n".join(parts))

        sp = [f"\\begin{{solution}}{{{n}}}{{{KEYS[n]}}}"]
        if n in SIC_SOLUTIONS:
            sp.append(sic_note.rstrip())
        sp.append(errata_s.get(n, f"Working of solution {n}."))
        if ("s", n) in tab:
            sp.append(tab[("s", n)])
        sp.append("\\end{solution}")
        ss.append("\n".join(sp))

    qtex = "\\srmpart{QUESTIONS}\n" + "\n\n".join(qs)
    stex = "\\srmpart{SOLUTIONS}\n" + "\n\n".join(ss)

    qb = _blocks(qtex, "question")
    sb = _blocks(stex, "solution")
    body = "\n\n".join(qb[n] + ("" if n in DELETED else "\n\n" + sb[n])
                       for n in range(1, N_ITEMS + 1))
    return qtex, stex, body


MUTATIONS = [
    ("a question dropped",         lambda q, s, b: (q.replace(_blocks(q, "question")[33], "", 1), s, b)),
    ("a question duplicated",      lambda q, s, b: (q + "\n" + _blocks(q, "question")[33], s, b)),
    ("an answer key changed",      lambda q, s, b: (q, s.replace("{33}{E}", "{33}{A}", 1), b)),
    ("solution 7 given a key",     lambda q, s, b: (q, s.replace("{7}{}", "{7}{D}", 1), b)),
    ("an answer choice dropped",   lambda q, s, b: (q.replace(_blocks(q, "question")[12],
                                                    _blocks(q, "question")[12].replace("\\item x\n", "", 1), 1), s, b)),
    ("a figure key swapped",       lambda q, s, b: (q.replace("\\srmfig{q48c}", "\\srmfig{q48d}", 1), s, b)),
    ("a figure placed on a question that has none",
                                   lambda q, s, b: (q.replace("Stem of question 40.",
                                                    "Stem of question 40.\n\\srmfig{q35}", 1), s, b)),
    ("a table lost",               lambda q, s, b: (re.sub(r"\\begin\{tabular\}.*?\\end\{tabular\}",
                                                    "", q, count=1, flags=re.S), s, b)),
    ("an erratum silently repaired",
                                   lambda q, s, b: (q.replace("I, II and II", "I, II and III", 1), s, b)),
    ("a % SIC note dropped",       lambda q, s, b: (q.replace("% SIC: reproduced as printed.\n", "", 1), s, b)),
    ("a forbidden \\section emitted",
                                   lambda q, s, b: (q + "\n\\section{Questions}", s, b)),
    ("\\leq used instead of \\leqslant",
                                   lambda q, s, b: (q + "\n$x \\leq 1$", s, b)),
    ("a withdrawn number given a stem",
                                   lambda q, s, b: (q.replace("\\begin{question}{17}\n\\deleted",
                                                    "\\begin{question}{17}\nA stem.", 1), s, b)),
    ("the body left in source order (not interleaved)",
                                   lambda q, s, b: (q, s, "\n".join(_blocks(q, "question").values())
                                                    + "\n" + "\n".join(_blocks(s, "solution").values()))),
    ("a solution left unclosed",   lambda q, s, b: (q, s.replace("\\end{solution}", "", 1), b)),
    ("a digit transposed in a table",
                                   lambda q, s, b: (q.replace("15286.6", "15268.6", 1), s, b)),
]


def selftest(figdir: Path, pdf: Path) -> int:
    qtex, stex, body = _synth(pdf)
    base = Report()
    check_text(base, qtex, stex, body, figdir)
    check_tables(base, qtex, stex, pdf)
    print(f"baseline: {base.n} checks, {len(base.fails)} failures")
    for f in base.fails:
        print(f"    BASELINE FAIL  {f}")
    if base.fails:
        print("\nThe synthetic body built from the ground truth does not pass. Either the "
              "ground truth or a check is wrong — fix that before trusting any mutation.")
        return 1

    bad = 0
    for name, mutate in MUTATIONS:
        q2, s2, b2 = mutate(qtex, stex, body)
        rep = Report()
        try:
            check_text(rep, q2, s2, b2, figdir)
            check_tables(rep, q2, s2, pdf)
        except Exception as e:                     # a crash is not a catch
            print(f"  CRASH   {name}: {type(e).__name__}: {e}")
            bad += 1
            continue
        if rep.fails:
            print(f"  caught  {name}  ->  {rep.fails[0][:96]}")
        else:
            print(f"  MISSED  {name}  <- this mutation is invisible to the gate")
            bad += 1
    print(f"\n{len(MUTATIONS) - bad}/{len(MUTATIONS)} mutations caught.")
    return 1 if bad else 0


# ============================== main ==========================================

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--questions", default=f"{PAPER}_02.tex")
    ap.add_argument("--solutions", default=f"{PAPER}_03.tex")
    ap.add_argument("--body", default=f"{PAPER}_body.tex")
    ap.add_argument("--figdir", default="assets/figs")
    ap.add_argument("--src", default="src/srm.pdf",
                    help="the source PDF, for the table-number check")
    ap.add_argument("--no-build", action="store_true", help="skip pdflatex")
    ap.add_argument("--selftest", action="store_true",
                    help="prove every check can fail, then exit")
    args = ap.parse_args(argv)

    figdir = Path(args.figdir)
    if args.selftest:
        return selftest(figdir, Path(args.src))

    missing = [f for f in (args.questions, args.solutions) if not Path(f).exists()]
    if missing:
        print(f"nothing to verify: {', '.join(missing)} not written yet.")
        return 1

    rep = Report()
    qtex = Path(args.questions).read_text(encoding="utf-8")
    stex = Path(args.solutions).read_text(encoding="utf-8")
    body = Path(args.body).read_text(encoding="utf-8") if Path(args.body).exists() else ""
    if not body:
        print(f"note: {args.body} not present — the interleaving check is skipped.")
    check_text(rep, qtex, stex, body, figdir)
    check_tables(rep, qtex, stex, Path(args.src))

    if not args.no_build:
        subprocess.run(["latexmk", "-pdf", "-interaction=nonstopmode",
                        "-halt-on-error", f"{PAPER}.tex"],
                       capture_output=True, text=True)
        check_build(rep, Path(f"{PAPER}.aux"), Path(f"{PAPER}.log"))
        rep.check(Path(f"{PAPER}.pdf").exists(), f"{PAPER}.pdf was not produced")

    for f in rep.fails:
        print(f"FAIL  {f}")
    print(f"\n{rep.n - len(rep.fails)}/{rep.n} checks passed.")
    return 1 if rep.fails else 0


if __name__ == "__main__":
    sys.exit(main())
