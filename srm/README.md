# texify — SOA Exam SRM sample questions → interleaved LaTeX

Converts the Society of Actuaries' sample-question sheet into LaTeX in which **each question
is immediately followed by its own solution**, which is not how the source prints it.

> Society of Actuaries, *Exam SRM — Statistics for Risk Modeling: Sample Questions and
> Solutions*, February 2026 revision. — `src/srm.pdf`, 75 pages.
>
> p1 front matter · p2–p56 questions 1–75 · p57–p75 solutions 1–75.

Outputs: **`srm_01.tex`** (front matter), **`srm_02.tex`** (the questions),
**`srm_03.tex`** (the solutions), **`srm_body.tex`** (the merged, interleaved body),
**`srm.tex`** (the master) and `srm.pdf`.

> **Model/effort are PINNED: `claude-opus-4-7` @ `high`. Do not raise the effort.** Both
> conversion failures ever observed on this pipeline sat at the *top* of the effort scale
> (`4.8@max`, `4.7@xhigh`) and both silently DROPPED whole sections. The failure is silent — a
> compressed body can still be brace-balanced and pass every structural check.

## Quickstart

```bash
python3 texify_figs_srm.py --check                    # 1. crop the 17 figures (once)
python3 texify_orchestrate.py --paper srm --divisions all \
        --max-chunk-pages 10 --window-overlap 0       # 2. convert (9 chunks, ~20 min)
python3 texify_qa_merge.py                            # 3. pair each Q with its own solution
python3 texify_orchestrate.py --paper srm --master \
        --body srm_body.tex --no-bib                  # 4. assemble srm.tex
latexmk -pdf srm.tex                                  # 5. plain pdflatex
./verify.py                                           # 6. the regression gate (free)
```

`--dry-run` prints the chunk plan and spends nothing; you want **9 chunks, 9 clean / 0 seam**.

To redo ONE division after an overlay change — the normal loop — delete its `.tex` and re-run
with `--divisions 03` alone. Never pass `--force`: it would re-convert the divisions you were
happy with, and a re-conversion is a coin flip that can only lose.

**`--bib` is never run.** This source has no reference list — see "No bibliography" below.

Prerequisites: `pip install pypdf pyyaml pymupdf`, plus Claude Code on PATH and logged in.

## Repository layout

```
├── texify_orchestrate.py    # the CLI you run
├── texify_backends.py       # Claude / Mistral / Gemini behind one interface
├── texify_chunker.py        # chunk planning
├── texify_bookmap.py        # the map schema + PDF slicing (read-only)
├── texify_common.py         # work-dir layout, backup_write, session-limit detection
├── texify_check.py          # post-conversion checks: flag / verify / xref / cite
├── texify_figcrop.py        # the book-agnostic half of the figure extractor (from books/islr)
├── texify_figs_srm.py       # NEW — this source's 17-figure inventory and cropper
├── texify_qa_merge.py       # NEW — pairs question N with solution N
├── verify.py                # the regression gate; ./verify.py --selftest proves it can fail
├── SKILL.srm.md             # the per-source overlay — authoritative where it differs
├── .claude/skills/texify-math-pdf/SKILL.md   # the GENERAL conversion contract
├── assets/
│   ├── preamble.tex         # committed master header (article class)
│   ├── preamble.srm.tex     # per-source patch: the four environments
│   └── figs/srm_q*.pdf      # the 17 cropped figures
├── src/srm.pdf              # the one input
└── .texify_work/
    ├── srm.map.yaml         # THE control file: page spans + chunking hints. Hand-written.
    ├── smoke.tex            # the preamble smoke test
    ├── mathdiff.py          # diff the MATHEMATICS of two conversions — the check a gate can't do
    └── run1/                # the first conversion, kept to diff the second against
```

Five files are **hand-written** and are the whole customization surface:
`.texify_work/srm.map.yaml`, `assets/preamble.srm.tex`, `SKILL.srm.md`, `verify.py`, and the
`FIGURES` inventory at the top of `texify_figs_srm.py`.

## The point of the exercise: interleaving

The source prints all 75 questions, then all 75 solutions, 55 pages apart. The deliverable
puts each solution under its own question.

**A converting model cannot do that** — a chunk is a contiguous page span, so no single call
ever sees both halves of one item. **And it should not have to.** Pairing 75 items by their
printed number is deterministic: given that the page says "33." on one side and "33." on the
other, the only possible correct output is those two blocks adjacent. That is the texify
playbook's own test for what belongs in code rather than in a prompt, so it lives in
`texify_qa_merge.py`, where it is permanent and testable, instead of being re-rolled on every
re-conversion.

So the questions and the solutions are converted as **separate divisions** (`srm_02`,
`srm_03`), each item delimited and carrying its printed number:

```latex
\begin{question}{33} … \end{question}          % in srm_02.tex
\begin{solution}{33}{E} … \end{solution}       % in srm_03.tex
```

and the merge writes `srm_body.tex`. `--order original` writes the same items back in the
source's own order, so the conversion can be diffed against the source as printed.

**The four withdrawn numbers print DELETED on both sides**, so interleaved they would set the
word twice under one number; the merge drops the solution half. It decides that on the block's
body being exactly `\deleted`, not on a hard-coded list — the list is the source's to change.

## Numbering and the four environments

All of it in `assets/preamble.srm.tex`. There are no sections, no theorems and no numbered
equations in this source; there are four environments and that is the whole structure.

| object | printed | mechanism |
|---|---|---|
| a question | `33.` hanging at the left margin | `question` env, number as a mandatory argument |
| a solution | `Solution.  Key: E`, run in | `solution` env, number + key letter |
| the choices | `(A)` … `(E)` | `choices` (enumitem, `\Alph*`) |
| a statement list | `I.` `II.` `III.` (`IV.`) | `statements` (enumitem, `\Roman*.`) |
| a "given" list | `i)` `ii)` `iii)` `iv)` | `given` (enumitem, `\roman*)`) |

Four of those decisions are traps, and each fails *silently*:

- **The number is an argument, not an auto-increment.** 1–75 looks contiguous but is not:
  17, 28, 47 and 65 were withdrawn in August 2023 and the source still prints them. An
  auto-incrementing counter would renumber the 71 live questions the moment the merge dropped
  a deleted one — and the numbers would still run 1..71 without a gap, so nothing downstream
  would notice.
- **The counter is still stepped, via `\refstepcounter`,** so `\label` records what LaTeX
  actually set. That is what lets `verify.py` read `\newlabel{q:33}{{33}…}` back out of the
  `.aux` and assert the printed number equals the number the page shows.
- **The solution's head must not be a list label.** The obvious `\item[\textbf{Solution.}]`
  puts the word in a `\labelwidth`-wide box, and LaTeX right-aligns a label there and lets an
  oversize one hang out to the **left** — so every solution head printed further left than the
  question number above it, with the visual hierarchy exactly inverted.
- **`\makeatletter` is load-bearing.** An `\input`ed `.tex` is not a `.sty`: `@` keeps catcode
  12 there, so the private `\srm@…` names die with *"Missing `\begin{document}`"*, an error
  that names neither the macro nor the file. This is what the first smoke run found.

**Smoke-test the preamble before spending anything**: `.texify_work/smoke.tex` exercises every
decision above; compile it and read `smoke.aux` back to see what each `\label` resolved to.

## Figures: 17, cropped by key, not by division

`texify_figs_srm.py` crops them out of the born-digital source into
`assets/figs/srm_<key>.pdf`, and the body places one with **`\srmfig{q35}`**.

This is deliberately **not** the pipeline's usual `<book>_<NN>_figs.pdf` + `page=<k>`
convention. That indexes a figure by its position within a division's figure file, which here
would make question 48's answer-choice picture "page 8 of `srm_02_figs.pdf`" — a number whose
meaning changes silently the moment a division boundary moves. A key naming the question
cannot drift. There are also no floats and no captions: this source captions nothing, so a
`figure` environment would need an invented caption *and* would let LaTeX move the picture
away from the sentence that says "the following scree plot".

Sixteen of the seventeen are embedded rasters, so their extent is exactly
`page.get_image_rects(xref)` — no union to build, no caption to pull back off. All sixteen
were checked for intruding glyphs and all are clean. **The one vector figure is `q57`, and it
shares p42 with a table**: of that page's 280 drawings, 142 are the data table's cell rules
and 138 are the regression tree, so the inventory addresses it by a y-band rather than by the
page.

⚠ **The bug worth knowing about.** p35 sets question 48's five answer-choice pictures two-up,
and the two panels of a row are not laid out to the same baseline: choice (C) starts at
y=455.8 and choice (D), to its *right*, at y=454.1. Sorting the rasters on `(y0, x0)` — the
obvious reading order — therefore put **(D) before (C)**, by 1.7pt. Nothing downstream could
see it: both crops were written, both were the right size, the count was 17, `edge_ink` was
clean, and the built PDF showed a perfectly good picture under each of (C) and (D). They were
just the wrong way round. `_image_rects` now buckets into rows first.

`--check` runs `edge_ink`, the cheapest honest check there is: a crop that shaved an axis
label still writes its file and still passes every count, but it cannot keep its ink off the
outermost pixel row.

## No bibliography

This source cites its textbooks in running prose — "See Page 242 of *Regression Modeling with
Actuarial and Financial Applications*", "see page 307 of Frees", "Section 8.1 of *An
Introduction to Statistical Learning*" — and carries no reference list anywhere. So:

- the map's `references:` is empty and **`--bib` is never run**;
- the overlay forbids `\cite`, and `verify.py` fails on one;
- the master is built with **`--no-bib`**. This is not cosmetic: `\bibliography{srm}` on a
  missing `.bib` is a hard LaTeX error, not a warning.

Every "Page 242", "formula (7.8)", "Section 8.1" belongs to *another book*, so it stays
literal text — a `\ref` to it would dangle.

## ⚠ 20 printed slips, every one reproduced as printed

The contract says *never improve the source*, so the body reproduces what the page shows and
carries a `% SIC:` comment above each. All twenty were confirmed on the page images, the
doubtful ones re-cropped at 340 dpi. The full list with page numbers is in `SKILL.srm.md`;
the shape of them:

- **word-level typos** — "I, II and II" for III (Q2), "meet the meet the" (Q16), "with respect
  the loadings" (Q30), "which or the following" (Q64), "does not depend in *t*" (S21), "the
  one the existing regions" (S26), "presence of absence" (S37), "less than equal to" (S61),
  "produces and interval" (S62), "all zero They" (S69);
- **broken delimiters** — an unclosed `(` in Q66's stem, a missing `}` in Q66(E) Region 1, and
  `2(1)(89.45755]` in S70 (three times over);
- **stray or missing punctuation** — `.>` for `>` twice in S66, a trailing comma in Q73's
  lead-in, missing full stops in Q31, Q45 and S69;
- **a size slip** — Q66(E) Region 3 sets its `>` at subscript size, so the line prints as
  though it read `X_{1>}5`. The characters are right; only the size is wrong.

`verify.py` checks each of these **in both directions**: the erratum must still be there, and
the *repaired* form must not be — a silent correction is the fidelity bug the contract forbids
and it is invisible to every structural check.

**Two things are deliberately NOT reproduced**, both confined to typography that carries no
content, both recorded here, in the overlay and in `verify.py`:

1. **The answer-key label.** The source spells it three ways — "Key: E" 68 times, "Key E" once
   (solution 13) and "Key:D" twice (solutions 66, 75). The head is re-typeset from the key
   letter, so all three come out "Key: X".
2. **The subscript on an indexed variable.** The source sets true subscripts `X₁`, `X₂` in
   question 66, full-size baseline digits in question 59's table and solution 59's prose, and
   in question 70 does not open an equation object at all — it just types `X1, X2, X3, X4, X5,
   and X6` in the roman body font. All name the same kind of object, so all become `$X_1$`.
   Following the source here would make the document disagree with itself about its own
   notation two questions apart. (`T1`–`T4` in question 57 are node *names*, not indexed
   variables, and are left exactly as printed.)

## Converter defects found by re-running, and now fixed in the overlay

The body in this repo was produced by the pipeline **unaided** — nothing in `srm_02.tex` or
`srm_03.tex` is hand-patched. Getting there took three runs — the questions twice, the
solutions three times — and each round-trip turned a defect into an overlay rule. That loop is the method: *convert → read the output against the
page → if the model got it wrong, fix the **contract**, not the output → re-convert.* A rule in
the overlay holds for every future run; an edit to the `.tex` is lost the next time anyone
passes `--force`.

Four defects, none of which any structural check could see:

1. **A bare `E(y \mid x)` in question 13**, where the source's other four expectation and
   variance operators correctly came out `\expc`/`\var`. It renders as an ordinary italic
   `E` — *identical* to the macro on the page — so only a scan of the source can find it.
   `\mathbb{E}` and `\Pr` were already forbidden; the plainest spelling of all was not. The
   overlay now tables all five occurrences by page, and `verify.py` forbids a bare `E(`/`Var(`.
2. **`$Y = A$ or $B$` in solution 57** — the *values* of a categorical predictor set italic,
   as though they were two more variables. The source sets the variable italic and the value
   roman, in the table and in the prose alike. The overlay now says so, and names the other
   letters it applies to (`M`/`F` for `X`, the node names `T1`–`T4`).
3. **`$X1$` in solution 59 against `$X_1$` in question 59** — the same variable, set two ways
   in one document. Two runs disagreed here, which is what the math-diff below is for; going
   back to the source at 400 dpi showed why. The source is itself inconsistent: it sets true
   subscripts `X₁`, `X₂` in question 66, full-size baseline digits in question 59, and in
   question 70 does not open an equation object at all. So this one is not "the converter got
   it wrong" but "the page cannot be followed literally without the output contradicting
   itself", and it is settled by a documented normalisation — everything is `$X_1$` — rather
   than by keeping whichever spelling a given run happened to emit.
4. **A stray `% SIC` note inside question 37** reading *"source prints 'of' for 'or' in Sol 37
   II; not applicable here — this is Q37."* — the converter reasoning aloud in the output. It
   renders as nothing, which is exactly why it survives every check. The overlay now says a
   `% SIC:` note belongs only above a slip actually being reproduced, and that item 37 of the
   questions and item 37 of the solutions are different things.

**Then diff the two conversions' mathematics.** `.texify_work/mathdiff.py` tokenises every
formula in every item of both runs and compares them; a disagreement is a place where at least
one of the two read the page wrong. Across 356 formulas in the questions and 172 in the
solutions it reported 28 disagreements between the first two runs, 27 of them merely of
spelling (`\e^z` vs `\e^{z}`,
`\hat{s}_t^{(1)}` vs `\hat{s}^{(1)}_t`, `\neq` vs `\ne`, a number set in text mode by one
run and in math by the other) — **and one of reading**: `$X1$` against `$X_1$` in solution 59,
which sent me back to the source at 400 dpi and produced defect 3. Re-run after the fix, the
last two conversions of the solutions disagree on nothing but math-mode grouping. That is the check
`verify.py` structurally cannot do: a misread *symbol* is as countable and as compilable as
the right one, so no count and no compile can see it.

## Expected QA output

**`./verify.py` is the regression gate — run it after any change.** It costs nothing and
asserts what was read off the printed pages by hand:

```
616/616 checks passed          # 462 on the text and the tables, 154 on the .aux and the build
```

- 75 questions and 75 solutions, numbered 1–75, no gaps, no repeats, none swallowing another;
- 17, 28, 47, 65 withdrawn on both sides, body exactly `\deleted`;
- all 71 answer keys, and solution 7's **empty** key;
- 355 answer choices — five per live question, always (A)–(E);
- 17 `\srmfig` calls on the 11 questions that have artwork, and every file present;
- 19 tables (18 in the questions, 1 in solution 15) — **and every number in every one of them
  checked against the source's own cells**, which is the only check that can see a transposed
  digit: turn question 54's 15,286.6 into 15,268.6 and the body still balances, the tabular
  still has the right shape, the count is still 19, and the PDF still looks perfect;
- the 20 errata still present *and* their repaired forms still absent;
- no `\chapter`, `\section`, `\cite`, `\eqref`, `\begin{equation}`, float, `\caption`,
  `\leq`/`\geq`, `\mathbb{E}`, a bare `E(`/`Var(`, or an unsubscripted `X1`;
- **`srm_body.tex` interleaved**: the exact sequence q1, s1, q2, s2, …, q17 (no s17), …;
- **the `.aux` readback** — every `\label{q:N}` and `\label{s:N}` resolved to N.

**`./verify.py --selftest` proves the gate can fail.** It builds a synthetic body from the
ground truth (tabulars filled from the source's own cells), watches it pass — 438 checks, 0
failures — then applies 16 mutations: a dropped question, a duplicated one, a changed key, a
key given to solution 7, a dropped answer choice, a swapped figure key, a figure on a question
that has none, a lost table, a transposed digit inside a table, a silently repaired erratum, a
missing `% SIC`, a forbidden `\section`, a `\leq`, a stem on a withdrawn number, a body left
in source order, and an unclosed `\end{solution}`. **16/16 caught.**

The one that mattered: an unclosed `\end{solution}` was **MISSED** by the first version of the
gate. Remove one and every later `\begin` still finds *an* `\end` — the next block's — so the
scan still returns 75 blocks with the right numbers and the right keys, and the only trace is
that block 1 now contains block 2 entirely. The document brace-balances, compiles, and prints
solution 2 inside solution 1's list. `_env_problems` now walks the stream in order.

The other screens, if you want them separately:

```bash
python3 texify_check.py flag   srm_02.tex srm_03.tex     # clean but for 2 known XREFs
python3 texify_check.py verify src/srm.pdf srm_body.tex # 100.0%, 0/75 low-coverage pages
```

The coverage figure is worth noting: **100.0% content-word coverage with no low-coverage page
anywhere in the 75**. The comparable figure on a math-dense scanned paper was 92.9%; a
born-digital source with an honest text layer should do better, and it does.

⚠ **`flag` reports XREF false positives here, and they are correct output.** Its rule warns
about a literal "Section 8.1" or "Table 2" that should have been a `\ref` — but every such
mention in this source names a division of *another book* ("See Section 8.1 of *An
Introduction to Statistical Learning*", "See formula (7.8) in the Frees text"). Those must
stay literal text; a `\ref` to them would dangle. `verify.py` is the check that binds.

Read `trunc` / `open_at_end` / `stray_end` in the run summary, not just `status`. They are
different failures: `open_at_end` means a `\begin{X}` was never closed; **`stray_end` means an
`\end{X}` closes nothing and the body will NOT compile.**

## What changed from the paper pipeline

This is a fork of `llm_proj/papers/white` (a 9-page journal article). Three changes to the
machinery, all in `texify_orchestrate.py`, and all because a question sheet is not a paper:

1. **`build_master --body`** — overrides the default glob of `srm_NN.tex`. The master must
   `\input` the *merged* `srm_body.tex`; the per-division files stay on disk (they are the
   merge's input and the re-conversion unit) but must not **also** be input, or every item is
   typeset twice — once in place, once again in source order — in a document that still
   compiles cleanly.
2. **`build_master --no-bib`** — omits the bibliography for a source that has no reference
   list. `\bibliography` on a missing `.bib` is a hard error.
3. Nothing else. The chunker, the backends and the checks are unmodified.

The map does one thing the paper map never needed: its `sections` are **chunking hints, not
headings**. This source has no headings, so each entry marks a page whose *top* starts a fresh
item, and the chunker (which coalesces adjacent entries up to 10 pages) then always cuts
between items. p50 deliberately has **no** entry — it is the one page in the source that does
not start a new item, because question 66's choices (D) and (E) run over from p49.

## Troubleshooting

- **`\bibliography` error / "I couldn't open database file srm.bib"** — the master was built
  without `--no-bib`.
- **Every item typeset twice** — the master was built without `--body srm_body.tex`, so the
  glob picked up `srm_02.tex` and `srm_03.tex` as well as the merged body.
- **"Missing `\begin{document}`" from the preamble patch** — an `\input`ed `.tex` is not a
  `.sty`; `\makeatletter` is missing.
- **`¡` or `¿` where the source prints `<` or `>`** — a bare `<`/`>` in text mode. They must
  be in math mode, always.
- **The merge says "questions and solutions do not pair"** — one side lost or gained an item.
  Delete that division's `.tex` and re-convert it **without** `--force` (which would re-roll
  the other divisions too).
- **A chunk is content-blocked on all three engines** — its PDF is saved under
  `.texify_work/unconverted/` and a `% UNCONVERTED` marker is left in the body. Use `--spans`
  to isolate the offending pages so the rest converts.

The committed `srm/.gitignore` excludes disposable `.texify_work` output while explicitly
retaining the hand-written map, smoke/math-diff tools, and the two reference-conversion
`.tex` sets.  Do not replace it with a blanket `.texify_work/` rule.
