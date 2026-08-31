#!/usr/bin/env python3
r"""
mathdiff.py — diff the MATHEMATICS of two independent conversions of the same source.

    python3 .texify_work/mathdiff.py runA/srm_02.tex srm_02.tex --env question
    python3 .texify_work/mathdiff.py runA/srm_03.tex srm_03.tex --env solution

WHY THIS EXISTS
---------------
verify.py only tests what someone thought to test. A MISREAD SYMBOL is as countable and as
compilable as the right one: swap a subscript, drop a prime, read `1` where the page prints
`i`, and every count still tallies, the body still balances, the PDF still looks right. The
only check that covers that class is a diff of two conversions' mathematics against each
other — where a disagreement is a place at least one of them read the page wrong.

⚠ NORMALISE BY TOKENISING, NOT BY DELETING WHITESPACE. `\overline h` and `\overline{h}` are
the same formula; collapsing spaces makes the first one token and fills the report with noise
that hides the one line where the readings genuinely disagree. So: split into control
sequences, braces and single characters, drop the pure-spacing tokens, and fold the handful of
spellings that are interchangeable in output (`\frac`/`\dfrac`, `\times`/`\cdot` never — that
one changes the glyph, so it stays a difference).

Silence is the good outcome. Anything it prints wants both readings checked against the page.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_COMMENT_RE = re.compile(r"(?<!\\)%[^\n]*")
_OPEN = {
    "question": re.compile(r"\\begin\{question\}\{(\d+)\}"),
    "solution": re.compile(r"\\begin\{solution\}\{(\d+)\}\{[A-E]?\}"),
}

# Every way this source's bodies enter mathematics.
_MATH_RE = re.compile(
    r"\\\[(.*?)\\\]"                       # display
    r"|\\begin\{align\*\}(.*?)\\end\{align\*\}"
    r"|(?<!\\)\$(.+?)(?<!\\)\$",           # inline
    re.S)

# Tokens that carry no meaning for the READING of a formula, only its setting.
_DROP = {
    r"\,", r"\;", r"\:", r"\!", r"\quad", r"\qquad", r"\ ", r"\>",
    r"\left", r"\right", r"\big", r"\Big", r"\bigg", r"\Bigg",
    r"\displaystyle", r"\textstyle", r"\limits", r"\nolimits", r"\notag",
    r"&", r"\\",
}
# Spellings that render identically. \frac vs \dfrac differs only in size; \ldots vs \dots
# resolve to the same glyph in text. Anything that changes a GLYPH is not folded.
_FOLD = {r"\dfrac": r"\frac", r"\tfrac": r"\frac", r"\dots": r"\ldots",
         r"\mathrm": r"\text", r"\textrm": r"\text"}

_TOKEN_RE = re.compile(r"\\[A-Za-z]+|\\.|\s+|.")


def _mask(t: str) -> str:
    return _COMMENT_RE.sub("", t)


def blocks(text: str, env: str) -> dict[int, str]:
    end = re.compile(rf"\\end\{{{env}\}}")
    masked, out = _mask(text), {}
    for m in _OPEN[env].finditer(masked):
        e = end.search(masked, m.end())
        if e:
            out[int(m.group(1))] = masked[m.start():e.end()]
    return out


def tokens(formula: str) -> list[str]:
    out = []
    for t in _TOKEN_RE.findall(formula):
        if t.isspace():
            continue
        t = _FOLD.get(t, t)
        if t in _DROP:
            continue
        out.append(t)
    return out


def formulas(block: str) -> list[list[str]]:
    out = []
    for m in _MATH_RE.finditer(block):
        body = next(g for g in m.groups() if g is not None)
        tk = tokens(body)
        if tk:
            out.append(tk)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--env", choices=["question", "solution"], required=True)
    args = ap.parse_args(argv)

    A = blocks(Path(args.a).read_text(encoding="utf-8"), args.env)
    B = blocks(Path(args.b).read_text(encoding="utf-8"), args.env)
    if set(A) != set(B):
        print(f"item sets differ: only in A {sorted(set(A)-set(B))}, "
              f"only in B {sorted(set(B)-set(A))}")

    diffs = 0
    for n in sorted(set(A) & set(B)):
        fa, fb = formulas(A[n]), formulas(B[n])
        if len(fa) != len(fb):
            print(f"{args.env} {n}: {len(fa)} formulas in A, {len(fb)} in B")
            diffs += 1
            continue
        for i, (x, y) in enumerate(zip(fa, fb)):
            if x != y:
                print(f"{args.env} {n}, formula {i + 1}:")
                print(f"   A: {' '.join(x)}")
                print(f"   B: {' '.join(y)}")
                diffs += 1
    total = sum(len(formulas(v)) for v in A.values())
    print(f"\n{total} formulas compared across {len(A)} items; {diffs} disagreement(s).")
    return 1 if diffs else 0


if __name__ == "__main__":
    sys.exit(main())
