#!/usr/bin/env python3
r"""
texify_qa_merge.py — pair each question with its own solution.

    python3 texify_qa_merge.py                       # -> srm_body.tex, interleaved
    python3 texify_qa_merge.py --order original      # -> srm_body.tex, as the source prints it

WHY THIS IS A SCRIPT AND NOT A PROMPT
-------------------------------------
The deliverable interleaves the source's two halves — question 33, then solution 33, then
question 34 — and the source prints them 55 pages apart. A converting model cannot do that:
a chunk is a contiguous page span, so no single call ever sees both halves of one item.

It also should not have to. Pairing 75 items by their printed number is DETERMINISTIC: given
that the page says "33." on one side and "33." on the other, the only possible correct output
is those two blocks adjacent. That is exactly the kind of step the texify playbook says
belongs in code — permanent, testable, and not re-rolled on every re-conversion — rather than
in the conversion contract, where it would be a coin flip each time.

WHAT IT REFUSES TO DO
---------------------
Every failure below is FATAL, because each one is a defect the merge would otherwise bury in
a document that still compiles and still looks finished:

  * a number on one side with no partner on the other  -> a question printed with someone
    else's solution under it, or none at all;
  * a duplicated number                                -> one item typeset twice;
  * a number outside 1..N, or a gap in 1..N            -> a dropped or invented item;
  * an unclosed \begin{question} / \begin{solution}    -> the rest of the file swallowed into
    one block, which brace-balances and compiles.

`--order original` writes the same items back in the source's own order, questions then
solutions, keeping the \srmpart half-titles that the interleaved order drops. It exists so
the conversion can be diffed against the source as printed.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# A comment can carry anything, including a \begin{question} in an example or a "% SIC" note
# about one. Blank the comments before scanning so no check acts on text that never renders.
# (An escaped \% is not a comment; the lookbehind keeps it.)
_COMMENT_RE = re.compile(r"(?<!\\)%[^\n]*")

_OPEN = {
    "question": re.compile(r"\\begin\{question\}\{(\d+)\}"),
    "solution": re.compile(r"\\begin\{solution\}\{(\d+)\}\{([A-E]?)\}"),
}
_PART_RE = re.compile(r"^[ \t]*\\srmpart\{[^}]*\}[ \t]*\n?", re.M)


def _mask_comments(text: str) -> str:
    """Comments replaced by spaces of the SAME LENGTH, so every offset still indexes the
    original text and a block can be sliced out of it verbatim."""
    return _COMMENT_RE.sub(lambda m: " " * len(m.group(0)), text)


def parse_blocks(text: str, env: str) -> dict[int, str]:
    """{number: the block's full source, \\begin through \\end inclusive}.

    `question` and `solution` never nest — one is a whole item — so the first \\end{env} after
    a \\begin{env} is that block's own. A MISSING \\end is the case worth being careful about:
    scanning to the next \\begin instead would silently absorb every following item into this
    one, and the result would balance, compile, and print. So the \\end must be there."""
    masked = _mask_comments(text)
    end = re.compile(rf"\\end\{{{env}\}}")
    out: dict[int, str] = {}
    for m in _OPEN[env].finditer(masked):
        n = int(m.group(1))
        e = end.search(masked, m.end())
        if not e:
            raise SystemExit(f"FATAL: \\begin{{{env}}}{{{n}}} is never closed.")
        nxt = _OPEN[env].search(masked, m.end())
        if nxt and nxt.start() < e.start():
            raise SystemExit(
                f"FATAL: \\begin{{{env}}}{{{n}}} is followed by "
                f"\\begin{{{env}}}{{{nxt.group(1)}}} before any \\end{{{env}}} — "
                f"the first one was never closed.")
        if n in out:
            raise SystemExit(f"FATAL: {env} {n} appears twice.")
        out[n] = text[m.start():e.end()]
    return out


def _key_of(block: str) -> str:
    m = _OPEN["solution"].search(_mask_comments(block))
    return m.group(2) if m else ""


def _is_deleted(block: str) -> bool:
    """True when the block's body is the single macro \\deleted and nothing else.

    The four withdrawn numbers print DELETED on BOTH sides of the source. Interleaved, that
    would set the word twice under one number — so the solution half is dropped. The test is
    on the body, not on a hard-coded list of numbers, because the list is the source's to
    change: the next revision may withdraw a fifth."""
    body = _mask_comments(block)
    body = re.sub(r"^\\begin\{\w+\}(\{[^}]*\})*", "", body.strip())
    body = re.sub(r"\\end\{\w+\}$", "", body.strip())
    return body.strip() == r"\deleted"


def merge(front: str, questions: dict[int, str], solutions: dict[int, str],
          order: str) -> str:
    qs, ss = set(questions), set(solutions)
    if qs != ss:
        raise SystemExit(
            f"FATAL: questions and solutions do not pair.\n"
            f"  questions with no solution: {sorted(qs - ss) or 'none'}\n"
            f"  solutions with no question: {sorted(ss - qs) or 'none'}")
    lo, hi = min(qs), max(qs)
    gaps = sorted(set(range(lo, hi + 1)) - qs)
    if lo != 1 or gaps:
        raise SystemExit(f"FATAL: numbering is not 1..{hi} without gaps "
                         f"(starts at {lo}; missing {gaps or 'none'}).")

    parts = [front.rstrip(), ""]
    if order == "original":
        parts += ["% ---- questions, in the source's own order ----", ""]
        parts += [questions[n] for n in sorted(qs)]
        parts += ["", "% ---- solutions, in the source's own order ----", ""]
        parts += [solutions[n] for n in sorted(ss)]
    else:
        parts += ["% ---- each question immediately followed by its own solution ----",
                  "% Assembled by texify_qa_merge.py from srm_02.tex + srm_03.tex; do not",
                  "% hand-edit this file — edit those, or SKILL.srm.md, and re-merge.", ""]
        for n in sorted(qs):
            parts.append(questions[n])
            if not _is_deleted(solutions[n]):
                parts.append(solutions[n])
            parts.append("")
    return "\n".join(parts).rstrip() + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--front", default="srm_01.tex", help="the front-matter division")
    ap.add_argument("--questions", default="srm_02.tex")
    ap.add_argument("--solutions", default="srm_03.tex")
    ap.add_argument("--out", default="srm_body.tex")
    ap.add_argument("--order", choices=["interleaved", "original"], default="interleaved",
                    help="interleaved (default): question N then solution N, and the "
                         "\\srmpart half-titles are dropped. original: the source's own "
                         "order, half-titles kept.")
    args = ap.parse_args(argv)

    for f in (args.front, args.questions, args.solutions):
        if not Path(f).exists():
            raise SystemExit(f"FATAL: {f} does not exist — convert that division first.")

    front = Path(args.front).read_text(encoding="utf-8")
    qtext = Path(args.questions).read_text(encoding="utf-8")
    stext = Path(args.solutions).read_text(encoding="utf-8")

    questions = parse_blocks(qtext, "question")
    solutions = parse_blocks(stext, "solution")

    if args.order == "interleaved":
        # The half-titles live OUTSIDE the item blocks, so dropping them is a whole-file edit,
        # not something parse_blocks can do. In interleaved order a heading reading "QUESTIONS"
        # over a stream that also carries every solution would be a plain lie.
        qtext, stext = _PART_RE.sub("", qtext), _PART_RE.sub("", stext)

    out = merge(front, questions, solutions, args.order)
    Path(args.out).write_text(out, encoding="utf-8")

    keys = {n: _key_of(b) for n, b in solutions.items()}
    nodel = sum(1 for b in solutions.values() if _is_deleted(b))
    print(f"{len(questions)} questions + {len(solutions)} solutions -> {args.out} "
          f"({args.order})")
    print(f"  {nodel} withdrawn (solution half dropped): "
          f"{sorted(n for n, b in solutions.items() if _is_deleted(b))}")
    print(f"  {sum(1 for k in keys.values() if k)} keyed, "
          f"{sorted(n for n, k in keys.items() if not k)} unkeyed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
