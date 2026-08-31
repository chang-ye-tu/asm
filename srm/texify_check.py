#!/usr/bin/env python3
r"""texify_check.py — post-conversion checks for a converted paper body. Four subcommands,
one tool, because they are the same job (does this body hold up?) at four price points:

  flag    STATIC contract-rule flagger (regex only). Residual spots where a SKILL rule looks
          un-applied, with line numbers.        exit 0 clean / 1 flags / 2 usage
  verify  FAITHFULNESS screen (pdftotext, no API). Per-source-page content-word overlap
          between the source PDF and the converted prose.
  xref    WIRE literal cross-references ("Theorem 3.1" -> "Theorem~\ref{thm:3.1}").
          Dry-run by default; --apply rewrites in place (original -> .texify_work/backups/).
  cite    REPAIR fabricated \cite keys against the frozen citemap. Dry-run by default.

Usage:
  python3 texify_check.py flag   white_01.tex
  python3 texify_check.py verify src/white.pdf white_01.tex
  python3 texify_check.py xref   white_01.tex [--apply] [--types thm,sec]
  python3 texify_check.py cite   white_01.tex [--apply] [--map extra.json]

WHY THESE ARE ONE TOOL. They were three (texify_qa / texify_xref / texify_citefix) and had
drifted apart in two ways that this merge fixes by construction:

  * The cross-reference vocabulary was written out TWICE. The flagger warned about `Part` and
    `Appendix`, which the wirer had no rule for and could never wire — so those flags could
    never be cleared — while the wirer wired `Equation`, which the flagger never warned about,
    so a bare "Equation 3.1" sailed through. Both now read the SAME `REFTYPES` table below.
  * Only the flagger stripped LaTeX comments. The wirer would happily rewrite a `\ref` inside a
    `% commented-out` line, and the cite-fixer would remap a `\cite` in one. All four now share
    `_strip_comments`.

NOTE what is deliberately NOT wired: `Chapter`, `Part`, `Appendix`. The master is `article`
class, so no such label can exist. A source that mentions "Chapter 7" is referring to a
CHAPTER OF A WORK IT CITES ("as in Ross [2], Chapter 7"), which the contract says must stay
literal text beside the \cite. Flagging those produced permanent, unfixable false positives.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import texify_common as tc


# ============================ the ONE cross-ref vocabulary ====================
# (keyword pattern (singular|plural), \label prefix, ref macro). The flagger derives its
# XREF regex from this, and the wirer wires exactly these — so they cannot disagree.
REFTYPES = [
    (r"Sections?|Subsections?", "sec",  "ref"),
    (r"Definitions?",           "def",  "ref"),
    (r"Theorems?",              "thm",  "ref"),
    (r"Lemmas?",                "lem",  "ref"),
    (r"Propositions?",          "prp",  "ref"),
    (r"Corollar(?:y|ies)",      "cor",  "ref"),
    (r"Examples?",              "ex",   "ref"),
    (r"Remarks?",               "rem",  "ref"),
    (r"Figures?",               "fig",  "ref"),
    (r"Tables?",                "tab",  "ref"),
    (r"Equations?",             "eq",   "eqref"),
]

# A reference number: 3, 3.1, 3.7.5, A.2 — an optional appendix letter, then dot-joined
# integers. Requires a digit, so it never swallows an English word.
_NUM = r"(?:[A-Z]\.)?\d+(?:\.\d+)*"
_PART = r"(?:\([a-zA-Z]+\))?"            # sub-part like (c) / (ii), kept outside \ref
TOKEN_RE = re.compile(rf"({_NUM})({_PART})")
_KEYWORDS = "|".join(k for k, _, _ in REFTYPES)

_COMMENT_RE = re.compile(r"(?<!\\)%.*$", re.M)


def _strip_comments(text: str) -> str:
    """Drop LaTeX comments. They do not render, so no check should act on them — and two of
    these checks used to REWRITE them."""
    return _COMMENT_RE.sub("", text)


# ============================== flag (static rules) ===========================
# Everything reported is a FLAG for review (may include false positives), never an auto-fix:
# a wrong silent rewrite is worse than a flagged false positive.
_CHECKS = [
    # literal cross-ref mentions not wrapped in \ref, INCLUDING letter/appendix numbers
    # ("Section A.2") — a letter-prefixed number is still a cross-reference. Derived from
    # REFTYPES, so `flag` only ever reports something `xref` can actually wire.
    ("XREF",  re.compile(rf"\b(?:{_KEYWORDS})[~ ]+[A-Z]?\.?\d")),
    ("EULER", re.compile(r"(?<![\\A-Za-z}])e\^")),        # bare italic e^ -> \e^
    ("OPS",   re.compile(                                  # glyphs that must be \prb/\expc/\indc
        r"\\mathbb\{[PEI1]\}|\\mathds\{1\}|\\mathbbm\{1\}|\\mathbf\{1\}|\\Pr\b")),
    ("INEQ",  re.compile(r"\\le\b|\\ge\b|\\leq(?!slant)|\\geq(?!slant)")),
    ("BODY",  re.compile(                                  # body-only / no-markdown violations
        r"\\documentclass|\\usepackage|\\begin\{document\}|\\end\{document\}"
        r"|\\chapter\b|\\setcounter|```")),
]
_ORDER = ["XREF", "EULER", "OPS", "INEQ", "BODY", "ERR"]


def _flag_scan(path):
    out = []
    try:
        lines = Path(path).read_text(encoding="utf-8").splitlines()
    except OSError as e:
        return [("ERR", 0, str(e))]
    for i, ln in enumerate(lines, 1):
        code = _strip_comments(ln)
        for tag, rx in _CHECKS:
            for m in rx.finditer(code):
                snip = code[max(0, m.start() - 18):m.start() + 32].strip()
                out.append((tag, i, snip))
    return out


def _flag_main(files) -> int:
    if not files:
        print("usage: python3 texify_check.py flag FILE [FILE ...]")
        return 2
    total = 0
    for f in files:
        iss = _flag_scan(f)
        total += len(iss)
        if not iss:
            print(f"## {f}  — clean")
            continue
        print(f"\n## {f}  — {len(iss)} flag(s)")
        by = {}
        for tag, ln, snip in iss:
            by.setdefault(tag, []).append((ln, snip))
        for tag in _ORDER:
            if tag in by:
                print(f"  [{tag}] {len(by[tag])}")
                for ln, snip in by[tag][:12]:
                    print(f"      L{ln}: …{snip}…")
                if len(by[tag]) > 12:
                    print(f"      … +{len(by[tag]) - 12} more")
    print(f"\nTOTAL: {total} flag(s) across {len(files)} file(s)")
    return 1 if total else 0


# ============================ verify (faithfulness) ==========================
# Size and \begin/\end balance say nothing about whether the LaTeX reproduces the source. This
# measures that locally and for free, by CONTENT-WORD UNIGRAM overlap per source page.
#
# NOT proof of correctness — math, tables and figures do not extract as prose, so even perfect
# output will not hit 100% and a dense page can dip. Read it as: consistent high coverage =
# plausibly faithful; a cliff to ~0 over several pages = real missing content. On white.pdf the
# body scores 92.9%, and the ONLY low page is the reference list, which lives in the .bib by
# design. Confirm any flag by eyeballing the page.
MIN_WORD_LEN = 7    # a "content word": long enough to be topical, not a stop-word
LOW = 0.5           # per-page coverage below this is flagged for inspection


def _content_words(s: str, min_len: int = MIN_WORD_LEN) -> list[str]:
    # A LIST, not a set: coverage is TOKEN-weighted, so a word the source repeats ten times
    # and the body drops costs ten hits, not one. Do not "simplify" this to a set.
    return [w for w in re.findall(r"[a-z]+", (s or "").lower()) if len(w) >= min_len]


def _strip_latex(t: str) -> str:
    t = _strip_comments(t)

    # ESCAPED SPECIALS FIRST — load-bearing, and not obvious. `\$` is a literal dollar sign,
    # not a math delimiter. The inline-math rule below is a naive `\$[^$]*\$` pair-matcher, so
    # a single `\$` makes the file's $-count odd and DESYNCHRONISES every pair after it: the
    # regex then strips the PROSE between the maths instead of the maths. That silently cost
    # one chapter two thirds of its text and 23 coverage points, on a body that was perfect.
    t = re.sub(r"\\[$&%#_{}]", " ", t)

    # `\\[2pt]` is a line break with optional spacing, NOT display math — but it contains the
    # characters `\[`, so the `\[..\]` rule below would match it and eat everything up to the
    # next real `\]`.
    t = re.sub(r"\\\\\[[^\]]*\]", " ", t)

    t = re.sub(r"\\\[.*?\\\]", " ", t, flags=re.S)          # display math \[..\]
    t = re.sub(r"\$\$.*?\$\$", " ", t, flags=re.S)          # display math $$..$$
    t = re.sub(r"\$[^$]*\$", " ", t)                        # inline math
    t = re.sub(r"\\begin\{[^}]*\}|\\end\{[^}]*\}", " ", t)  # env delimiters
    t = re.sub(r"\\[a-zA-Z@]+\*?", " ", t)                  # control sequences
    t = re.sub(r"[{}\\&~^_#]", " ", t)                      # specials
    return t


def _source_pages(pdf_path: str) -> list[str]:
    """Source text per page via `pdftotext -layout` (cleaner than pypdf here: ~10pts higher
    content-word recall on math-dense pages). Pages split on form-feed."""
    r = subprocess.run(["pdftotext", "-layout", pdf_path, "-"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print(f"pdftotext failed on {pdf_path}: {r.stderr[:200]}", file=sys.stderr)
        raise SystemExit(2)
    return r.stdout.split("\f")


def verify(pdf_path: str, tex_path: str, low: float = LOW, min_len: int = MIN_WORD_LEN):
    """Return (overall_token_coverage, gap_page_indices, rows). `rows` is one
    (page0, coverage_or_None, n_content_words) per source page. Importable."""
    tex_set = set(_content_words(_strip_latex(Path(tex_path).read_text(
        encoding="utf-8", errors="ignore")), min_len))
    rows, tot, hit = [], 0, 0
    for i, pgtext in enumerate(_source_pages(pdf_path)):
        pw = _content_words(pgtext, min_len)
        if not pw:                       # e.g. the empty tail after the final form-feed
            rows.append((i, None, 0))
            continue
        c = sum(1 for w in pw if w in tex_set)
        rows.append((i, c / len(pw), len(pw)))
        tot += len(pw)
        hit += c
    overall = hit / tot if tot else 0.0
    gap_pages = [i for i, cov, _ in rows if cov is not None and cov < low]
    return overall, gap_pages, rows


def _verify_main(pdf, tex) -> int:
    overall, gaps, rows = verify(pdf, tex)
    name = Path(tex).name
    npages = sum(1 for _, c, _ in rows if c is not None)   # real pages, not the empty tail
    print(f"{name:<16} content-word coverage: {overall:6.1%}   "
          f"low-coverage pages (<{LOW:.0%}): {len(gaps)}/{npages}")
    if gaps:
        # collapse consecutive gap pages into ranges, to spot a dropped region
        runs, s = [], None
        for i in range(len(rows)):
            cov = rows[i][1]
            isgap = cov is not None and cov < LOW
            if isgap and s is None:
                s = rows[i][0]
            if (not isgap or i == len(rows) - 1) and s is not None:
                e = rows[i][0] if isgap else rows[i - 1][0]
                runs.append((s, e))
                s = None
        print("   gap ranges (0-based pdf pages): " +
              ", ".join(f"{a}-{b}" if a != b else f"{a}" for a, b in runs))
    return 0


# ============================== xref (wire refs) =============================

def _label_set(prefix: str, corpus: str) -> set[str]:
    return set(re.findall(rf"\\label\{{{prefix}:([^}}]+)\}}", corpus))


def _span_re(keyword: str) -> re.Pattern:
    # "<Word>" + first number + any comma/and-separated continuation numbers; longer
    # separators first so a whole list is consumed in one span.
    return re.compile(
        rf"\b(?:{keyword})(?:~|\s)+{_NUM}{_PART}"
        rf"(?:(?:\s*,\s+and\s+|\s+and\s+|\s*,\s*)(?:~|\s)*{_NUM}{_PART})*")


def _wire_text(text, labels_by_prefix, missing, enabled):
    for keyword, prefix, macro in REFTYPES:
        if prefix not in enabled:
            continue
        labels = labels_by_prefix[prefix]

        def wire_span(m, _labels=labels, _prefix=prefix, _macro=macro):
            def wire_tok(tm):
                num, part = tm.group(1), tm.group(2) or ""
                if num in _labels:
                    return f"\\{_macro}{{{_prefix}:{num}}}{part}"
                missing[_prefix].add(num)
                return tm.group(0)
            return TOKEN_RE.sub(wire_tok, m.group(0))

        text = _span_re(keyword).sub(wire_span, text)
    return text


def _xref_main(args) -> int:
    files = sorted(Path(f) for f in args.files)
    enabled = ({t.strip() for t in args.types.split(",")} if args.types
               else {p for _, p, _ in REFTYPES})
    corpus = "\n".join(_strip_comments(p.read_text(encoding="utf-8")) for p in files)
    labels_by_prefix = {p: _label_set(p, corpus) for _, p, _ in REFTYPES}
    n_labels = sum(len(s) for s in labels_by_prefix.values())

    total, missing = 0, defaultdict(set)
    for p in files:
        src = p.read_text(encoding="utf-8")
        # Wire the CODE only; a \ref inside a % comment does not render and must not be
        # rewritten. Comments are spliced back untouched.
        out = _sub_outside_comments(
            src, lambda code: _wire_text(code, labels_by_prefix, missing, enabled))
        wired = sum(out.count(f"\\{m}{{{pre}:") - src.count(f"\\{m}{{{pre}:")
                    for _, pre, m in REFTYPES)
        total += wired
        if wired:
            if args.apply:
                tc.backup_write(p, out)
            print(f"  {p.name}: +{wired} ref(s) {'wired' if args.apply else 'would wire'}")
    print(f"TOTAL: {total} literal refs {'wired' if args.apply else 'would be wired'} "
          f"against {n_labels} labels across {len(enabled)} type(s).")
    if any(missing.values()):
        print("UNWIRED (target has NO \\label — relabel/re-convert):")
        for _, prefix, _ in REFTYPES:
            ks = sorted(missing.get(prefix, ()))
            if ks:
                shown = ", ".join(ks[:20]) + (f" … (+{len(ks) - 20})" if len(ks) > 20 else "")
                print(f"  {prefix}: {shown}")
    return 0


def _sub_outside_comments(text: str, fn) -> str:
    """Apply `fn` to every stretch of CODE, leaving % comments byte-for-byte intact."""
    out, pos = [], 0
    for m in _COMMENT_RE.finditer(text):
        out.append(fn(text[pos:m.start()]))
        out.append(m.group(0))
        pos = m.end()
    out.append(fn(text[pos:]))
    return "".join(out)


# ============================== cite (repair keys) ===========================
# The conversion can INVENT a citation key instead of taking one from the CITATION INDEX. An
# invented key is not in <paper>.bib, so it renders "[?]". This maps each fabricated key onto
# the right frozen key via the citemap, on three tiers of confidence — and REPORTS anything
# ambiguous rather than guessing, because a wrong cite is worse than a visible "[?]".
CITE_RE = re.compile(r"\\(cite[tp]?\*?|citeauthor|citeyear)(\[[^\]]*\])?\{([^}]+)\}")

# Words that are never a surname. Kept deliberately GENERIC: this list used to carry the
# vocabulary of a specific textbook corpus ("learning", "prediction", "games", "theory",
# "algorithms", "pattern"), which would have eaten real surnames on any other source.
STOP = {"ref", "missing", "online", "the", "and", "of", "a", "an", "etal"}


def _parse_label(lab: str):
    """('Nash and Gittins (1977)') -> ({'nash','gittins'}, '1977'). The bib stage can emit a
    null label for an entry it could not summarise — treat that as "no info", never crash."""
    lab = lab or ""
    y = re.search(r"\((\d{4})", lab)
    year = y.group(1) if y else None
    names = lab[:lab.find("(")] if "(" in lab else lab
    names = names.replace(" and ", ",").replace(" et al.", "").replace("&", ",")
    # normalise each surname: drop spaces/hyphens/dots so compound names align
    # ("de Farias" -> defarias, "Mas-Colell" -> mascolell).
    sn = {re.sub(r"[\s\-.]", "", n).lower() for n in names.split(",") if n.strip()}
    return {s for s in sn if s}, year


def _load_citemap(path: Path):
    sources = json.load(open(path))["sources"]
    rows = (sources.get("book") or next(iter(sources.values())))["rows"]
    cm = []
    for r in rows:
        sn, yr = _parse_label(r.get("label") or "")
        cm.append({"key": r["key"], "src": str(r["srcnum"]), "sn": sn,
                   "yr": yr, "label": r.get("label") or ""})
    return cm


def _bib_keys(path: Path):
    return set(re.findall(r"@\w+\{([^,]+),", path.read_text(encoding="utf-8")))


def _parse_key(k: str):
    """Derive (surnames, year, srcnum-hint) from a fabricated key."""
    is_missing = k.startswith("MISSING:")
    k2 = k[8:] if is_missing else k
    year = None
    m = re.search(r"(?:19|20)\d{2}", k2)
    if m:
        year = m.group(0)
    else:                                   # CamelCaseYY / trailing 2-digit year
        m2 = re.search(r"(?<!\d)(\d{2})(?!\d)$", k2.strip())
        if m2:
            yy = int(m2.group(1))
            year = str(1900 + yy if yy > 30 else 2000 + yy)
    src = None                              # [n] hint: 1-3 digits that are not the year
    for num in re.findall(r"\d{1,3}", k2):
        if year and num in year:
            continue
        if 1 <= int(num) <= 400:
            src = num
            break
    if is_missing:
        sn = {re.sub(r"[\-.]", "", t).lower() for t in k2.split()
              if t[:1].isupper() and len(re.sub(r"[\-.]", "", t)) > 2}
    else:
        toks = re.findall(r"[A-Z][a-z]+|[a-z]{3,}", k2)
        sn = {t.lower().replace("-", "") for t in toks
              if t.lower() not in STOP and len(t) > 2}
    return {s for s in sn if not s.isdigit() and s not in STOP}, year, src


def _match(k, cm, bysrc):
    sn, yr, src = _parse_key(k)
    if not sn and not src:
        return None, "no-signal", []
    # 1. srcnum — the [n] is authoritative; require only loose author corroboration.
    if src and src in bysrc:
        rsn = bysrc[src]["sn"]
        if (not sn) or (sn & rsn) or any(a in b or b in a for a in sn for b in rsn):
            return bysrc[src]["key"], "srcnum", [bysrc[src]]
    # EXACT author-set equality only — looser overlap mis-maps prolific authors.
    strong = [c for c in cm if sn and sn == c["sn"]]
    sy = [c for c in strong if yr and c["yr"] == yr]           # 2. author + year unique
    if len({c["key"] for c in sy}) == 1:
        return sy[0]["key"], "auth+yr", sy
    if len({c["key"] for c in strong}) == 1:                    # 3. author unique
        c = strong[0]
        if (not yr) or (not c["yr"]) or abs(int(yr) - int(c["yr"])) <= 3:
            return c["key"], "auth-uniq", strong
        return None, "ambig", strong
    return None, ("ambig" if strong else "none"), strong


def _cite_main(args) -> int:
    files = [Path(f) for f in args.files]
    prefix = args.paper or files[0].stem.rsplit("_", 1)[0]
    cm = _load_citemap(Path(args.citemap or f".texify_work/{prefix}.citemap.json"))
    bib = _bib_keys(Path(args.bib or f"{prefix}.bib"))
    bysrc = {c["src"]: c for c in cm}
    valid = bib | {c["key"] for c in cm}
    overrides = json.load(open(args.map)) if args.map else {}

    used = {}
    for f in files:                       # code only: a \cite in a % comment is not a citation
        for mobj in CITE_RE.finditer(_strip_comments(f.read_text(encoding="utf-8"))):
            for key in (x.strip() for x in mobj.group(3).split(",")):
                if key and key not in valid:
                    used[key] = used.get(key, 0) + 1

    mapping, ambig, none = {}, {}, {}
    for k in sorted(used):
        if k in overrides:
            mapping[k] = (overrides[k], "manual")
            continue
        tgt, conf, cands = _match(k, cm, bysrc)
        if tgt:
            mapping[k] = (tgt, conf)
        elif conf == "ambig":
            ambig[k] = sorted({c["key"] for c in cands})
        else:
            none[k] = True

    print(f"=== cite ({prefix}): {len(used)} fabricated cite key(s) over {len(files)} file(s) ===")
    print(f"  HIGH-confidence maps: {len(mapping)}   ambiguous: {len(ambig)}   "
          f"no-candidate: {len(none)}")
    for k, (t, c) in sorted(mapping.items()):
        print(f"  {k:42s} -> {t:34s} [{c}]  (x{used[k]})")
    if ambig:
        print("--- AMBIGUOUS (manual: pick one via --map) ---")
        for k, cs in sorted(ambig.items()):
            print(f"  {k:42s} ?? {cs[:6]}")
    if none:
        print("--- NO CANDIDATE (manual) ---")
        for k in sorted(none):
            print(f"  {k}  (x{used[k]})")

    if args.apply and mapping:
        for f in files:
            txt = f.read_text(encoding="utf-8")
            out = _sub_outside_comments(txt, lambda code: CITE_RE.sub(
                lambda m: "\\{}{}{{{}}}".format(
                    m.group(1), m.group(2) or "",
                    ", ".join(mapping[x.strip()][0] if x.strip() in mapping else x.strip()
                              for x in m.group(3).split(","))), code))
            if out != txt:
                tc.backup_write(f, out)
                print(f"  applied -> {f.name}")
        print(f"APPLIED {len(mapping)} key remap(s). Ambiguous/none left untouched.")
    elif not args.apply:
        print("\n(dry-run; pass --apply to write HIGH-confidence maps)")
    return 0


# ================================== main =====================================

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Post-conversion checks for a converted paper body.",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="mode", required=True)

    p_flag = sub.add_parser("flag", help="static contract-rule flagger (cheap)")
    p_flag.add_argument("files", nargs="+", help="converted .tex bodies")

    p_ver = sub.add_parser("verify", help="content-word coverage vs the source PDF")
    p_ver.add_argument("pdf", help="source PDF")
    p_ver.add_argument("tex", help="converted .tex body")

    p_x = sub.add_parser("xref", help="wire literal cross-refs -> \\ref/\\eqref")
    p_x.add_argument("files", nargs="+")
    p_x.add_argument("--apply", action="store_true", help="rewrite in place (default: dry-run)")
    p_x.add_argument("--types", default=None,
                     help="comma list of prefixes to wire (default: all), e.g. thm,sec")

    p_c = sub.add_parser("cite", help="repair fabricated \\cite keys via the citemap")
    p_c.add_argument("files", nargs="+")
    p_c.add_argument("--paper", default=None, help="paper prefix (auto from the first file)")
    p_c.add_argument("--citemap", default=None)
    p_c.add_argument("--bib", default=None)
    p_c.add_argument("--map", default=None, help="JSON of manual {oldkey: newkey} overrides")
    p_c.add_argument("--apply", action="store_true")

    args = ap.parse_args(argv)
    if args.mode == "flag":
        return _flag_main(args.files)
    if args.mode == "verify":
        return _verify_main(args.pdf, args.tex)
    if args.mode == "xref":
        return _xref_main(args)
    return _cite_main(args)


if __name__ == "__main__":
    raise SystemExit(main())
