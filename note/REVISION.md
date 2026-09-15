# ASM lecture notes — work order for the SRM/PA rebuild

Read `CONVENTIONS.md` first: it holds the motto, the house style, the verification
principle, the source inventory and the gotchas, all of which still bind. This file is the
current work order and the per-unit procedure. Everything earlier than the 2026-09-15
redesign has been removed from it; the pre-rebuild sources are in git at `84b0283` and the
first-principles Unit 1 is kept as `superseded/unit01-first-principles.Rnw`.

---

## 1. Purpose and status

The course prepares students for SOA Exam SRM and Exam PA. Each unit is to **cover the
exam's required reading** (the FREES and ISLR sections listed in §3), developed by reading
those sections in full and rewriting their content into coherent blocks **as rigorous
accounts of what the two books hand-wave**, with exercises drawn from FREES and ISLR and
every SOA sample question mapped to the unit, all with detailed solutions.

* **Unit 1 is rebuilt on this design and is the template** (`unit01.Rnw`, 108 pp, 60 chunks,
  8 proofs, 25 exercises, 0 errors). Its text reproduces FREES's chapter 1 examples from the
  book's data and script (Galton's table, the Massachusetts bodily injury claims to the
  digits of FREES Table 1.2, the chi-square transforms with the script's seed) and its
  exercises include all seven of FREES chapter 1.
* **Unit 2 is rebuilt** (`unit02.Rnw`, 168 pp, 84 chunks, 31 proofs, 45 exercises: all
  22 of FREES chapter 2, FREES 3.1–3.6 as far as §3.1–3.3 allow, 11 of ISLR §3.7, the six
  SOA questions). Its mathematics follows the instructor's CLM note
  (`~/usr/work/lectures/mva/note/clm.tex`), cited as CLM §n in the reading boxes; the
  instructor said Units 2 and 3 may lean on it closely. The pre-rebuild version is
  `superseded/unit02-first-principles.Rnw`.
* **Units 3–14 are still the old first-principles versions.** They build clean and are to
  be rebuilt in order, one unit per pass, starting with Unit 3 (FREES §3.4–3.5, §6.1;
  ISLR §3.3–3.4; SOA 13, 27, 49, 56, 62, 71; CLM §7–9).
* `prereq.Rnw` remains the single source of background results and stays in the reading
  path.

## 2. Rules (all current; fixed by the instructor)

1. **The motto holds: every result is proved.** Background results are cited by name from
   `prereq.Rnw`; anything a unit needs that is not there is added there with a proof.
2. **Proofs are complete.** No intermediate step is omitted. A proof with more than one
   idea is laid out in numbered steps (the LOOCV-shortcut proof in Unit 1 runs a page and
   is the model).
3. **Every block names its source.** A remark, definition or example that condenses a
   passage of ISLR or FREES carries the passage in its title:
   `\begin{remark}[Two drawbacks; ISLR §5.1.1]`. The blocks are the author's condensation,
   never verbatim quotation; the tag makes that checkable.
4. **Scope is the syllabus reading list** (§3). Material outside both reading lists is
   kept but carries "(beyond the syllabus)" in its title and a reading box saying so:
   the bootstrap, robust standard errors, Unit 14. Nothing is deleted on that ground.
5. **Exercises.** Every FREES and ISLR exercise of the unit's sections that is solvable
   with the material covered so far, titled by source (`[ISLR §5.4, exercise 8]`,
   `[FREES exercise 3.2]`), with full solutions and live R chunks; plus **every SOA sample
   question mapped to the unit**, computational and descriptive alike, as the exam's own
   verifiers, each option derived from the unit's propositions and **never an answer key**.
   FREES's data files and chapter scripts are on disk (§4), so its data-based exercises are
   in scope, and the unit's text reproduces the book's own in-chapter computations from the
   script alongside the ISLR lab. `ISLR2`'s data sets are all installed.
6. **House style** (`CONVENTIONS.md` §2): definition, proposition/lemma with proof, terse
   factual remark, example, reading box; concise language, no previews, no forward
   references of any kind, no em-dashes, no motivation prose. **No lead-ins, no
   non-load-bearing sentences, no fillers, ever** (the instructor's words, repeated on
   2026-09-15 after the template): a sentence that is not a definition, a result, a proof
   step, or a reading of a printed number is deleted.
7. **Verification** (`CONVENTIONS.md` §3): every number in prose comes from a chunk that
   prints it, the R sections reproduce the ISLR labs' numbers exactly, and R stays because
   PA is R-based.
8. **One unit at a time**, finished, built and checked before the next.

## 3. The syllabus and the unit map

`syllabus/2026-09-exam-srm-syllabus.pdf` (SRM) and `syllabus/2026-10-exam-pa-syllabus.pdf`
(PA). SRM: 35 multiple-choice questions; R output may be shown for interpretation. PA:
project-based, assumes SRM, adds data exploration, feature engineering and the R workflow
of its e-learning modules; R is no longer available at the exam. PA covers the same
reading except FREES 7–9.

| Unit | ISLR (2nd ed.) | FREES | SRM topic |
|---|---|---|---|
| 1 Statistical learning | 2.1–2.3, 5.1, 5.3.1–5.3.3 (5.2, 5.3.4 beyond) | 1 (background) | 1 |
| 2 Regression I: matrix theory, $k=1$ | 3.1–3.2 | 2.1–2.8, 3.1–3.3 | 2 |
| 3 Regression II: inference, interpretation | 3.3–3.4 | 3.4–3.5, 6.1 | 2 |
| 4 Diagnostics | 3.3.3 | 5.1, 5.3–5.5, 5.7 (robust SE beyond) | 2 |
| 5 Selection and dimension reduction | 6.1, 6.3, 12.2 | 5.2, 5.6, 6.2–6.3 | 2, 5 |
| 6 Shrinkage, high dimensions, KNN | 6.2, 6.4–6.5, 3.5–3.6 | | 2 |
| 7 GLM I: categorical responses | | 11.1–11.6 | 2 |
| 8 GLM II: counts, exponential family | | 12.1–12.4, 13.1–13.6 | 2 |
| 9 Trends | | 7.1–7.6, 8.1 | 3 |
| 10 Autoregression, forecasting; trees intro | 8.1.1 | 8.2–8.4, 9.1–9.5 (8.5–8.6 beyond) | 3, 4 |
| 11 Decision trees | 8.1, 8.3.1–8.3.2 | | 4 |
| 12 Ensembles | 8.2, 8.3.3–8.3.4 | | 4 |
| 13 Unsupervised learning | 12.1–12.2, 12.4–12.5 | | 5 |
| 14 Convex optimisation, SVM, neural networks | beyond the syllabus | | |

Excluded by the syllabus: ISLR 5.3.4, 8.2.4, 8.2.5, 8.3.5, 12.5.2. The syllabus fixes
AIC and BIC to the ISLR §6.1.3 forms $(\mathrm{RSS}+2d\hat\sigma^2)/n$ and
$(\mathrm{RSS}+\ln(n)\,d\hat\sigma^2)/n$ for ordinary linear models.

**Schedule.** Fourteen units, one per weekly meeting of 130–140 minutes (the instructor:
14, not 13; the first meeting of the semester carried no lecture). The `\periodmark`s still
say "period $k$ of 3" and are left as they are.

## 4. Sources on disk

* ISLR: `~/usr/work/research/llm_proj/books/islr/islr_NN.Rnw`; exercises are the last
  `\section{Exercises}` of each chapter, Conceptual then Applied, labelled `exer:N.M.k`.
* FREES: `~/usr/work/research/llm_proj/books/frees/frees_NN.tex`; exercises are the
  chapter's `\section{Exercises}`, labelled `exer:N.k`; `\dataset{...}` marks the ones
  that need its data files.
* SOA sample questions: `srm/srm_body.tex`, `\begin{question}{N}` followed by
  `\begin{solution}{N}{LETTER}`; questions 17, 28, 47 and 65 are deleted from the syllabus
  and must not be used.
* FREES data and scripts, downloaded 2026-09-15 from the "Data & Scripts" link in
  `README.md` (`instruction.bus.wisc.edu/jfrees/jfreesbooks/Regression Modeling/BookWebDec2010/`):
  `note/data/frees/csv/*.csv` (41 data sets), `note/data/frees/scripts/ChapNRCode.txt`
  (the in-chapter R code, chapters 1–8, 10–13, 16, 19, 20, plus `Divorce.csv` and
  `HealthExpendEvent.csv`), `note/data/frees/doc/DataDescriptions.pdf` (+ `.txt`) and the
  2019 errata. Chunks read them as `read.csv("data/frees/csv/X.csv")`; knitr runs in
  `note/`. Known deviations from the book: `AutoBI` was withdrawn at the survey conductor's
  request and `AUTOBIsim` is the simulated substitute; `NAICExpense` has 384 companies, not
  the 500 of the text; `MassBodilyInjury.csv` has a trailing space in a header, so
  `names(x) <- trimws(names(x))`. The scripts use Rcmdr's `numSummary`, `Hist` and
  `qq.plot`; use base R.
* Background proofs: `note/prereq.Rnw` (single source), and the texified books it was
  built from (`CONVENTIONS.md` §5).

## 5. Per-unit procedure

1. Read the unit's syllabus sections in full (§3), both books, their exercise sets, and
   FREES's chapter script, whose in-chapter computations the text reproduces from the data.
   For the regression units read the matching sections of the CLM note as well, and take
   the proofs from it where it has them.
2. Write the unit: sections mirror the syllabus material, each opening with a reading box
   naming the sections and the SRM learning outcome; blocks per rule 6, proofs per rules
   1–2, tags per rule 3; an R section reproducing the relevant ISLR lab; an exercise
   section per rule 5, off-syllabus items marked per rule 4.
3. Run the reference scan below, then `python build.py NN`. Never run two builds at once.
4. After the build, read the printed output: `grep -c -E '^## Error( in|:)' unitNN.tex`
   must be 0, every prose claim must match what printed, and every figure description must
   match the rendered figure (convert `figs/unitNN-*.pdf` with `pdftoppm -r 70 -png` and
   look). Do not edit the `.Rnw` while a build runs.
5. Tick the checklist and record anything learned as a gotcha in `CONVENTIONS.md` §6.

Reference scan (forward references of every kind, and cross-document `\ref`s, which print
as undefined):

```bash
cd note && python3 - <<'PY'
import re, pathlib
u = "unit02"
s = pathlib.Path(u + ".Rnw").read_text()
for pat in ('sec:', 'thm:', 'lem:', 'cor:', 'prop:', 'def:', 'ex:', 'eq:'):
    lb = {m.group(1): m.start() for m in re.finditer(r'\\label\{(' + pat + r'[^}]*)\}', s)}
    fwd = [m.group(1) for m in re.finditer(r'\\(?:ref|eqref)\{(' + pat + r'[^}]*)\}', s)
           if m.group(1) in lb and m.start() < lb[m.group(1)]]
    und = sorted({m.group(1) for m in re.finditer(r'\\(?:ref|eqref)\{(' + pat + r'[^}]*)\}', s)
                  if m.group(1) not in lb})
    if fwd or und: print(pat, "forward:", fwd, " undefined:", und)
print("em-dashes:", s.count('---'))
PY
```

`note/prose.py unitNN.Rnw` lists every unnumbered paragraph and remark with its line
number, for triaging lead-ins.

## 6. SOA sample questions by unit

All questions mapped to a unit are used (rule 5). Assignments marked ✓ were verified
against the question text; the rest are a keyword first pass to be checked when the unit
is rebuilt.

| unit | questions |
|------|-----------|
| 01 | 12 ✓, 50 ✓ |
| 02 | 11 ✓, 18 ✓, 23 ✓, 24 ✓, 44 ✓, 53 ✓ |
| 03 | 13 ✓, 27 ✓, 49 ✓, 56 ✓, 62 ✓, 71 ✓ |
| 04 | 2, 36, 42, 14 ✓ (response transformation for variance) |
| 05 | 5, 6, 8, 10, 30, 35, 37, 54 ✓ (sequential removal), 61 ✓ (AIC/BIC), 70 ✓ (AIC from RSS) |
| 06 | 68, 69, 75 |
| 07 | 3, 4, 22, 34, 38, 41, 52, 55, 72, 19 ✓ (likelihood ratio; or 08), 67 ✓ (logistic LRT) |
| 08 | 7, 20, 45 ✓ (GLM, log link) |
| 09 | 21, 31, 46 |
| 10 | 64, 58 ✓ (AR(1) conditional least squares) |
| 11 | 9, 25, 26, 29, 33, 48, 51, 57, 63, 66, 73 |
| 12 | 39, 74 |
| 13 | 1, 15, 16, 32, 40, 43, 59, 60 |

## 7. Checklist

| unit | read sources | written | built clean | output read | pages |
|------|:---:|:---:|:---:|:---:|---:|
| 01 | ✓ | ✓ | ✓ | ✓ | 108 |
| 02 | ✓ | ✓ | ✓ | ✓ | 168 |
| 03 | | | | | |
| 04 | | | | | |
| 05 | | | | | |
| 06 | | | | | |
| 07 | | | | | |
| 08 | | | | | |
| 09 | | | | | |
| 10 | | | | | |
| 11 | | | | | |
| 12 | | | | | |
| 13 | | | | | |
| 14 | | | | | |
