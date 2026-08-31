#!/usr/bin/env python3
"""Build ASM (精算統計模型) lecture units to PDF.

Each unit goes through knit -> xelatex -> (bibtex if needed) -> xelatex until
cross-references converge (at most four XeLaTeX passes).

Usage:
    python build.py                       # build all 14 units + appendix notes
    python build.py 03 07 11              # build only unit03, unit07, unit11
    python build.py unit03 unit07         # full names also accepted
    python build.py --quiet               # suppress per-step progress
    python build.py --skip-pkg-check      # skip the R-package availability probe
    python build.py --pkg-check           # only run the probe, don't build
    python build.py --allow-missing        # development only: skip unwritten units

Required CLI tools (must be on PATH):
    Rscript, xelatex, bibtex, pygmentize   (pygmentize is minted's backend)
Optional:
    pdfinfo                                (used only to report page counts)

The 17pt/16:9 units are readable both projected and printed, so there is a
single PDF per unit rather than a note/slide pair.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

UNITS  = [f"unit{i:02d}" for i in range(1, 15)]
# Appendix notes: same build, named rather than numbered. They are reference
# material several units cite, not teaching weeks, so they sit outside UNITS.
NOTES  = ["prereq"]
DOCS   = UNITS + NOTES
UNITS_WITH_BIB = set()          # populated as units acquire \cite calls
ROOT = Path(__file__).parent.resolve()
MAX_XELATEX_PASSES = 4

# R packages loaded by chunks that actually execute during the build.
# Missing any of these aborts the build.
R_PACKAGES_REQUIRED = [
    "AER", "boot", "broom", "car", "class", "cluster", "dplyr", "e1071",
    "FNN", "forecast",
    "gbm", "ggplot2", "glmnet", "ISLR2", "knitr", "leaps", "lmtest",
    "MASS", "nnet", "pls", "pscl", "randomForest", "rpart", "rpart.plot",
    "quadprog", "sandwich", "statmod", "tree", "tseries", "tweedie", "xfun",
]

# Mentioned only in prose or in eval=FALSE chunks. Absence does NOT break the
# build; --pkg-check warns but does not abort.
#   rugarch : an alternative GARCH fitter to unit10's tseries::garch
#   VGAM    : ordinal & nominal alternatives  (unit07, FREES 11.5-11.6)
# tseries moved to REQUIRED: unit10 runs adf.test and garch in live chunks.
R_PACKAGES_OPTIONAL = [
    "corrplot", "GGally", "rugarch", "VGAM",
]


def normalize_unit(arg: str) -> str:
    """Accept '3', '03', 'unit3', 'unit03', or an appendix-note name."""
    s = arg.lower()
    if s in NOTES:
        return s
    if s.startswith("unit"):
        s = s[4:]
    try:
        return f"unit{int(s):02d}"
    except ValueError:
        raise SystemExit(f"ERROR: cannot parse document identifier: {arg!r}")


def run(cmd: list, cwd: Path) -> tuple:
    """Run cmd in cwd. Return (returncode, captured_stdout_stderr_text)."""
    try:
        proc = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, check=False
        )
    except FileNotFoundError as e:
        return 127, str(e)
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def check_tool(name: str) -> None:
    if shutil.which(name) is None:
        sys.exit(f"ERROR: {name!r} not found on PATH.")


# Every probe result line is tagged with this. Loading a namespace can print
# to stderr no matter how quietly it is asked to (quantmod, for one, announces
# "Registered S3 method overwritten by 'quantmod'" on attach), and run() merges
# stderr into stdout. Without a sentinel those lines parse as package names and
# the probe reports nonsense like a missing package called
# "method            from".
_PROBE_TAG = "__ASM_MISSING__"


def _probe_packages(pkgs: list) -> list:
    """Return the subset of pkgs not installed (per requireNamespace)."""
    pkg_vec = ", ".join(f'"{p}"' for p in pkgs)
    rscript = (
        f"pkgs <- c({pkg_vec}); "
        "ok <- vapply(pkgs, function(p) suppressMessages(suppressWarnings("
        "requireNamespace(p, quietly = TRUE))), logical(1)); "
        f"for (p in pkgs[!ok]) cat('{_PROBE_TAG}', p, '\\n', sep='')"
    )
    rc, out = run(["Rscript", "-e", rscript], cwd=ROOT)
    if rc != 0:
        sys.exit(f"ERROR: R package probe failed (rc={rc}):\n{out}")
    return [line.strip()[len(_PROBE_TAG):]
            for line in out.splitlines() if line.strip().startswith(_PROBE_TAG)]


def check_r_packages() -> None:
    """Probe REQUIRED (abort if missing) then OPTIONAL (warn only)."""
    missing_req = _probe_packages(R_PACKAGES_REQUIRED)
    missing_opt = _probe_packages(R_PACKAGES_OPTIONAL)

    if missing_opt:
        print("WARNING: optional R package(s) not installed. The build still "
              "succeeds; the eval=FALSE chunks that use them simply cannot be "
              "run interactively by the student:", file=sys.stderr)
        for p in missing_opt:
            print(f"  - {p}", file=sys.stderr)
        quoted = ", ".join(f'"{p}"' for p in missing_opt)
        print(f"  Install (optional):\n    Rscript -e "
              f"'install.packages(c({quoted}))'\n", file=sys.stderr)

    if not missing_req:
        return
    print("ERROR: missing required R package(s):", file=sys.stderr)
    for p in missing_req:
        print(f"  - {p}", file=sys.stderr)
    quoted = ", ".join(f'"{p}"' for p in missing_req)
    print(
        f"\nInstall with:\n  Rscript -e 'install.packages(c({quoted}))'",
        file=sys.stderr,
    )
    sys.exit(1)


def get_pages(pdf: Path):
    """Return page count via pdfinfo if available, else None."""
    if shutil.which("pdfinfo") is None or not pdf.exists():
        return None
    rc, out = run(["pdfinfo", str(pdf)], cwd=pdf.parent)
    if rc != 0:
        return None
    for line in out.splitlines():
        if line.startswith("Pages:"):
            try:
                return int(line.split()[1])
            except (IndexError, ValueError):
                return None
    return None


def count_pattern(log: Path, pattern: str) -> int:
    if not log.exists():
        return 0
    pat = re.compile(pattern)
    n = 0
    with log.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            if pat.search(line):
                n += 1
    return n


def latex_requests_rerun(log: Path) -> bool:
    """Whether the latest XeLaTeX log explicitly asks for another pass."""
    return count_pattern(
        log,
        r"(?i)(Rerun to get (?:cross-references|citations) (?:right|correct)|"
        r"(?:Label|Citation)\(s\) may have changed|"
        r"rerunfilecheck Warning: File .* has changed|"
        r"longtable Warning: Table widths have changed)",
    ) > 0


def show_log_tail(log: Path, n: int = 40) -> None:
    if not log.exists():
        return
    with log.open(encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
    print(f"--- last {min(n, len(lines))} lines of {log.name} ---", file=sys.stderr)
    for line in lines[-n:]:
        print(line.rstrip(), file=sys.stderr)


def build_unit(unit: str, quiet: bool) -> dict:
    rnw = ROOT / f"{unit}.Rnw"
    tex = ROOT / f"{unit}.tex"
    pdf = ROOT / f"{unit}.pdf"
    log = ROOT / f"{unit}.log"
    has_bib = unit in UNITS_WITH_BIB

    if not rnw.exists():
        return {"unit": unit, "ok": False, "step": "missing"}

    if not quiet:
        print(f"=== {unit} ===")

    def step(label: str, cmd: list) -> int:
        if not quiet:
            print(f"  {label} ... ", end="", flush=True)
        rc, out = run(cmd, cwd=ROOT)
        if rc != 0:
            if not quiet:
                print("FAILED")
            else:
                print(f"{unit}: {label} FAILED", file=sys.stderr)
            if out.strip():
                print(out[-3000:], file=sys.stderr)
            return rc
        if not quiet:
            print("ok")
        return rc

    # 1. knit
    rc = step("knit", ["Rscript", "-e", f"knitr::knit('{rnw.name}', quiet=TRUE)"])
    if rc != 0:
        return {"unit": unit, "ok": False, "step": "knit"}

    latex_cmd = ["xelatex", "-shell-escape", "-interaction=nonstopmode", tex.name]
    rc = step("xelatex (1)", latex_cmd)
    if rc != 0:
        return {"unit": unit, "ok": False, "step": "xelatex-1"}

    # A bibliography requires two successful XeLaTeX passes after BibTeX.
    if has_bib:
        rc = step("bibtex", ["bibtex", unit])
        if rc != 0:
            return {"unit": unit, "ok": False, "step": "bibtex"}

    minimum_passes = 3 if has_bib else 2
    pass_no = 1
    for pass_no in range(2, MAX_XELATEX_PASSES + 1):
        rc = step(f"xelatex ({pass_no})", latex_cmd)
        if rc != 0:
            return {"unit": unit, "ok": False, "step": f"xelatex-{pass_no}"}
        if pass_no >= minimum_passes and not latex_requests_rerun(log):
            break

    errors = count_pattern(log, r"^!|^Error:")
    undef  = count_pattern(log, r"Reference .* undefined|Citation .* undefined")
    overfull = count_pattern(log, r"Overfull \\[hv]box")
    underfull = count_pattern(log, r"Underfull \\[hv]box")
    rerun  = latex_requests_rerun(log)
    pages  = get_pages(pdf)
    ok     = pdf.exists() and errors == 0 and undef == 0 and overfull == 0 and not rerun

    if not ok and not quiet:
        show_log_tail(log)

    return {
        "unit": unit, "ok": ok, "errors": errors, "undef": undef,
        "overfull": overfull, "underfull": underfull,
        "rerun": rerun, "passes": pass_no, "pages": pages,
    }


def main(argv: list) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__.split("\n", 1)[0],
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("\n", 1)[1],
    )
    parser.add_argument(
        "units", nargs="*",
        help="Documents to build (e.g. 03 07 unit11 asymp). Default: all.",
    )
    parser.add_argument(
        "-q", "--quiet", action="store_true",
        help="Suppress per-step progress; only print the summary table.",
    )
    parser.add_argument(
        "--skip-pkg-check", action="store_true",
        help="Skip the R-package availability probe.",
    )
    parser.add_argument(
        "--pkg-check", action="store_true",
        help="Run only the R-package probe and exit (no build).",
    )
    parser.add_argument(
        "--allow-missing", action="store_true",
        help="Development only: skip requested documents whose .Rnw is absent.",
    )
    args = parser.parse_args(argv)

    check_tool("Rscript")
    if not args.skip_pkg_check or args.pkg_check:
        check_r_packages()
    if args.pkg_check:
        print("All required R packages are available.")
        return 0
    for tool in ("xelatex", "bibtex", "pygmentize"):
        check_tool(tool)

    targets = [normalize_unit(u) for u in args.units] if args.units else list(DOCS)
    bad = [u for u in targets if u not in DOCS]
    if bad:
        sys.exit(f"ERROR: unknown document(s): {bad}. Valid: {DOCS}")

    present = [u for u in targets if (ROOT / f"{u}.Rnw").exists()]
    absent  = [u for u in targets if u not in present]
    if absent and not args.allow_missing:
        print(f"ERROR: missing source document(s): {', '.join(absent)}", file=sys.stderr)
        return 1
    if absent:
        print(f"(allow-missing: skipping {', '.join(absent)})", file=sys.stderr)
    if not present:
        print("ERROR: no source documents to build.", file=sys.stderr)
        return 1

    results = [build_unit(u, args.quiet) for u in present]

    print("\n" + "=" * 82)
    print(f"{'Unit':<8} {'Status':<8} {'Pages':<7} {'Passes':<7} "
          f"{'Errors':<8} {'Undef':<6} {'Over':<5} {'Under':<6} {'Rerun':<6}")
    print("-" * 82)
    for r in results:
        status = "[OK]" if r["ok"] else "[FAIL]"
        pages  = "?" if r.get("pages") is None else str(r["pages"])
        errs   = "?" if r.get("errors") is None else str(r["errors"])
        undef  = "?" if r.get("undef")  is None else str(r["undef"])
        over   = "?" if r.get("overfull")  is None else str(r["overfull"])
        under  = "?" if r.get("underfull") is None else str(r["underfull"])
        passes = "?" if r.get("passes") is None else str(r["passes"])
        rerun  = "?" if r.get("rerun")  is None else ("yes" if r["rerun"] else "no")
        print(f"{r['unit']:<8} {status:<8} {pages:<7} {passes:<7} "
              f"{errs:<8} {undef:<6} {over:<5} {under:<6} {rerun:<6}")

    failed = [r for r in results if not r["ok"]]
    if failed:
        print(f"\n{len(failed)} of {len(results)} unit(s) failed.")
        return 1
    print(f"\nAll {len(results)} unit(s) built.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
