# ASM lecture notes — preliminary revision work order

**Read `CONVENTIONS.md` first.** It is the binding handoff: house style, the motto, the
verification principle, the build, and 53 numbered gotchas. This file is a work order for
one specific pass over the fourteen units and does not replace it.

Status at the time of writing: all 14 units and `prereq.Rnw` are written and build with
0 LaTeX errors, 0 undefined references, and no R errors inside chunks.

---

## 1. The instruction

From the instructor, verbatim:

> for each Unit, read line-by-line and 1. Remove all non load-bearing lead-ins and fillers
> (remarks) 2. Remove all forward citations 3. The content of the exercise should not be
> simple repetition of the materials appeared earlier; for the 50 \* 3 minutes the number
> and the depths of the exercises should be largely expanded.

**Read line by line** is part of the instruction. Do not do this with a regular expression
sweep; the counts below are for scheduling, not for scripting the edit.

---

## 2. Inventory (measured 2026-08-21, before any revision)

| unit | remarks | exercises | fwd §-refs | fwd Unit refs | pages |
|------|--------:|----------:|-----------:|--------------:|------:|
| 01 | 19 | 10 | 4 | 12 † | 43 |
| 02 | 24 | 13 | 7 | 12 | 59 |
| 03 | 11 | 10 | 1 | 1 | 35 |
| 04 | 15 | 9 | 7 | 4 | 47 |
| 05 | 7 | 10 | 0 | 0 | 29 |
| 06 | 19 | 13 | 8 | 0 | 77 |
| 07 | 14 | 12 | 6 | 0 | 68 |
| 08 | 11 | 12 | 4 | 0 | 71 |
| 09 | 14 | 11 | 7 | 3 | 52 |
| 10 | 24 | 14 | 7 | 2 | 91 |
| 11 | 15 | 12 | 9 | 3 | 63 |
| 12 | 14 | 10 | 8 | 0 | 46 |
| 13 | 8 | 9 | 4 | 0 | 42 |
| 14 | 9 | 9 | 4 | 0 | 41 |
| **total** | **204** | **154** | **76** | **37** | |

† Unit 1's twelve forward `Unit M` mentions are **exempt by instructor decision**; see §4.
The figure to drive to zero is therefore 76 in-unit forward `\ref`s and 25 forward `Unit M`
mentions in units 2–14.

Exercises currently average about 850 characters including the solution, i.e. they are
short. Regenerate the table at any time with:

```bash
cd note && python3 - <<'PY'
import re, pathlib
for i in range(1, 15):
    u = f"unit{i:02d}"; s = pathlib.Path(u + ".Rnw").read_text()
    lab = {m.group(1): m.start() for m in re.finditer(r'\\label\{(sec:[^}]*)\}', s)}
    fwd = sum(1 for m in re.finditer(r'\\ref\{(sec:[^}]*)\}', s)
              if m.group(1) in lab and m.start() < lab[m.group(1)])
    fwdu = sum(1 for m in re.finditer(r'Unit (\d+)', s) if int(m.group(1)) > i)
    print(u, len(re.findall(r'\\begin\{remark\}', s)),
          len(re.findall(r'\\begin\{exercise\}', s)), fwd, fwdu)
PY
```

**Two facts that make this work safe.** `remark` is declared `\newtheorem*`, so it is
**unnumbered**: deleting remarks shifts no theorem, definition, lemma or corollary number,
and no `\ref` breaks. And only units 02, 12 and 14 contain `\ref{ex:...}` at all (3, 1 and
3 uses), all inside their own exercise sections, so adding exercises is safe too. Do not,
by contrast, delete or merge whole `\subsection`s: that changes `sec:N.x` labels and is
gotcha 12 territory.

---

## 3. Task 1 — remarks, lead-ins, fillers

`CONVENTIONS.md` §2 already says: *allowed* is definition, theorem, proof, **short factual**
remark, `reading` box, `derivation` box; and *the test for a sentence* is that if it is not
a definition, theorem, proof, or one terse factual remark, it goes.

### Keep a remark only if it does one of these

1. states a fact a later proof, definition or computation actually uses;
2. records that a hypothesis is necessary, ideally with the counterexample when it is
   dropped;
3. states what is **not** proved, or the boundary of a result's validity (`CONVENTIONS.md`
   §8 lists these per unit; they are load-bearing and must survive);
4. states an empirical or numerical finding that the unit's Computation section establishes.

### Delete it if it

- restates in words the theorem just proved;
- motivates ("this is why it matters", "the reason we care about");
- previews or narrates the document (also task 2);
- gives study advice or rhetorical framing ("this is the whole subject in one line");
- observes that a printed number is large or small without adding a fact;
- repeats a remark already made in the same subsection. Two surviving adjacent remarks
  should usually become one.

### Also in scope

The **unnumbered prose paragraphs** that open sections and subsections. Several units open
with a scene-setting paragraph ("Unit 11 ended with a measurement…", "There is no
response…"). Apply the same test: if the paragraph does not define something or state a
fact used later, it goes. Where it establishes standing notation, keep the notation and cut
the framing around it.

Expect the remark count to fall substantially. The rule governs, not a quota: a unit that
legitimately keeps most of its remarks is a correct outcome.

---

## 4. Task 2 — forward citations

Two kinds, both to reach zero.

**In-unit** — `\ref{sec:N.x}` appearing textually before `\label{sec:N.x}`. 76 of these.
Overwhelmingly they are theory sections pointing at the Computation or Pitfalls sections
that come later, in the pattern "§10.5.2 measures both".

**Cross-unit** — a mention of `Unit M` inside `unitNN.Rnw` with `M > NN`. 37 of these,
e.g. "which is Unit 10", "that is the whole content of Unit 12", "(Unit 13)".

### Repairs, in order of preference

1. The remark containing it fails task 1 anyway. Delete the remark; nothing else to do.
2. Delete the clause. "The reported standard errors are too small; §10.5.2 measures both"
   becomes "The reported standard errors are too small." **The backward link survives**:
   the Computation section already cites the theory section it verifies, and that is the
   direction that should exist.
3. Convert to a statement of fact with no pointer. "Pruning, which is Unit 11" becomes
   "Growing until each leaf is small overfits, and pruning is the repair" — true, and it
   does not send the reader forward.
4. If the mathematics genuinely depends on a later result, restructure so it does not.
   This should be rare; if it happens, record it.

### What must NOT be removed

- **Backward** references. Unit 12 citing Unit 11, or §12.4 citing §12.1, is correct.
- Cross-unit references remain **named, never numbered** (gotcha 11): "the
  Frisch–Waugh–Lovell theorem of Unit 3", "the prerequisites' central limit theorem for
  autoregressive scores". A cross-document `\ref` is also gotcha 10 and will surface as an
  undefined reference at build time.

### The one exception, decided by the instructor

**Unit 1's forward `Unit M` mentions stay as they are. Do not touch them.**

Unit 1 carries 12 of them, several being course-map scaffolding ("principal components and
clustering (Unit 13) are the unsupervised half"). Removing them would obey the letter of the
instruction and cost Unit 1 its overview of what the course contains. The question was put
to the instructor, who ruled: leave them.

The exception is **scoped to cross-unit forward references in Unit 1 only**. It does not
cover:

* Unit 1's 4 in-unit forward `\ref{sec:1.x}`s, which are the ordinary
  theory-points-at-Computation pattern and are removed like everywhere else;
* forward `Unit M` mentions in any other unit. Units 2, 3, 4, 9, 10 and 11 carry 25
  between them (12, 1, 4, 3, 2, 3) and all 25 go.

### Verification

Re-run the script in §2. Every entry in both forward columns must read 0, with the single
permitted exception of Unit 1's forward-`Unit` column, which stays at 12.

That script only sees `\ref{sec:...}` and `Unit M`. A second scan, run per unit, catches
forward references to theorems, lemmas, equations and exercises, and catches cross-document
`\ref`s (gotcha 10) as *undefined* labels before the build reports them. Both lists must
come back empty:

```bash
cd note && python3 - <<'PY'
import re, pathlib
u = "unit03"                       # the unit being revised
s = pathlib.Path(u + ".Rnw").read_text()
for pat in ('thm:', 'lem:', 'cor:', 'prop:', 'def:', 'ex:', 'eq:'):
    lb = {m.group(1): m.start()
          for m in re.finditer(r'\\label\{(' + pat + r'[^}]*)\}', s)}
    fwd = [m.group(1) for m in re.finditer(r'\\(?:ref|eqref)\{(' + pat + r'[^}]*)\}', s)
           if m.group(1) in lb and m.start() < lb[m.group(1)]]
    und = sorted({m.group(1)
                  for m in re.finditer(r'\\(?:ref|eqref)\{(' + pat + r'[^}]*)\}', s)
                  if m.group(1) not in lb})
    if fwd or und:
        print(pat, "forward:", fwd, " undefined:", und)
PY
```

---

## 5. Task 3 — exercises

The instruction has three parts: **not simple repetition** of earlier material, **more of
them**, and **deeper**, sized against 3 × 50 minutes of teaching per unit.

### Target

Roughly **20–26 exercises per unit**, up from about 11, with solutions substantially longer
than the present ~850 characters. Numbers are a guide; a unit with less material may carry
fewer.

### Three rules added by the instructor after units 1--3 were first revised

1. **Draw exercises from ISLR and FREES.** Their exercise sets are on disk:
   `books/islr/islr_NN.Rnw` §N.4 (Conceptual, then Applied) and
   `books/frees/frees_NN.tex` §N.x. Attribute in the exercise title,
   `\begin{exercise}[ISLR §5.4, exercise 8]` or `\begin{exercise}[FREES exercise 3.2]`.
   FREES's data-based exercises cannot be used (its datasets are not on disk, §5 of
   `CONVENTIONS.md`); its algebraic and small-table ones are the best source of derivation
   drills in the whole reading list. ISLR's Applied exercises port directly, `ISLR2` being
   installed.
2. **No pure-descriptive SOA questions.** A question whose solution is "A is false because
   ..., B is false because ..." with no arithmetic does not go in. Roughly half the bank is
   of that kind; see the CALC/DESC column added to the map below.
3. **Solutions detailed, language concise.** Every computational solution carries a live
   R chunk that prints the numbers rather than a sentence asserting them, and every
   theoretical one carries the derivation in full. The prose around them is cut to the
   statement of what the numbers show: no closing flourishes, no "the lesson is", no
   restating a printed figure.

Chunks inside a `solution` environment work (tcolorbox is `breakable`) and share the
document's R session, so they can reuse objects from the unit's Computation section. Label
them `s<unit>-<name>` to keep them unique. Budget for it: units 1--3 went from about
35 s to about 55--65 s of build time each.

### Composition (a drafting aid, NOT printed structure)

`CONVENTIONS.md` forbids exercise tiers: the printed list stays **flat and unlabelled**.
Use this only to check a set is varied:

- 3–5 that **extend a theorem**: relax a hypothesis and see what survives, prove a corollary
  the text states without proof, work a special case in closed form, or construct a
  counterexample when a hypothesis is dropped.
- 3–5 **numerical** problems with specific given values, the arithmetic worked in the
  solution.
- 2–4 that **connect to an earlier unit**. This is the cheapest source of genuine depth and
  is automatically non-repetitive. Backward only.
- 2–4 **SOA sample questions** (see §6), presented as problem and full derivation. Never
  "(Key: C)" — that is an explicit prohibition in `CONVENTIONS.md` §2.
- 2–3 **computational**, asking the student to reproduce or extend a check from the unit's
  Computation section.
- 1–2 on **what a result does not say**. `CONVENTIONS.md` §8 lists, per unit, exactly what
  was deliberately left unproved; those are ready-made.

### Banned

- An exercise whose solution is "this is §N.x" and no work. The present
  `ex:computational` exercises are close to this and should be rewritten or absorbed.
- An exercise that re-derives, with the same numbers, something the section already
  derived. Change the setting, the hypothesis, or the direction of the question.
- Anything whose solution needs machinery outside `prereq.Rnw` and the earlier units. If a
  good exercise needs a new result, the result goes into `prereq.Rnw` **with a proof**
  (`CONVENTIONS.md` §1), or the exercise goes.

### Non-negotiable

- **Never state a numerical claim you have not run** (`CONVENTIONS.md` §3). Every number in
  a new exercise or solution must be computed. Use a scratch R script; if the number belongs
  in the document, it goes in a chunk.
- No em-dashes: `grep -c -- '---' *.Rnw` must stay 0.
- Solutions must not forward-cite either.

---

## 6. SOA sample questions

`asm/srm/srm_body.tex` holds the live SOA sample questions in
`\begin{question}{N}...\end{question}` followed by `\begin{solution}{N}{LETTER}`. Questions
17, 28, 47 and 65 were **deleted from the syllabus** (see the header notes in that file) and
must not be used.

**Only computational questions may be used** (rule 2 above). A first pass over the 71 live
questions splits them as

* **computational** (the official solution does arithmetic or a derivation):
  1, 3, 4, 11, 15, 18, 19, 21, 22, 23, 24, 30, 33, 35, 44, 45, 46, 48, 51, 55, 57, 58, 59,
  62, 63, 64, 66, 67, 68, 69, 70, 72, 73;
* **applied but table-reading** (a decision rule applied to a printed table; usable if the
  exercise is extended to reproduce the table): 27, 54;
* **pure descriptive**, and therefore excluded: 2, 5, 6, 7, 8, 9, 10, 12, 13, 14, 16, 20,
  25, 26, 29, 31, 32, 34, 36, 37, 38, 39, 40, 41, 42, 43, 49, 50, 52, 53, 56, 60, 61, 71,
  74, 75.

Only the ones bearing on units 1--3 have been checked against the question text; the rest
of the split is a first pass. Note that the exclusion is expensive for the early units:
**Unit 1's entire allocation (12, 50, 61) is descriptive, so Unit 1 now carries no SOA
exercise at all.** That is the correct outcome under rule 2, and its exercises draw on ISLR
instead.

Below is the map from question number to unit. Verify each against the question text before
using it, and correct this table as you go; the README's SRM appendix promises a
question→unit map as a deliverable.

Verified so far (question text read against the unit):

* **Unit 01 → 12, 50** only. **61 is AIC/BIC and belongs to Unit 5, not Unit 1.**
* **Unit 02 → 23, 53** as exercises; 11, 18, 24 and 44 were already worked as *examples* in
  the body of §2.6.3, so the unit uses six in all. **14 (transforming a response to
  stabilise variance) belongs to Unit 4; 58 (AR(1) conditional least squares) to Unit 10;
  70 (AIC from residual sums of squares) to Unit 5.**
* **Unit 03 → 13, 49, 71** as exercises. **45 (GLM with a log link) belongs to Unit 8 (or
  7); 67 (logistic likelihood ratio) to Unit 7.** 56 (statements about prediction) and 62
  (a confidence interval from an estimate and its standard error) are correctly placed in
  Unit 3 but were judged too thin to carry an exercise and were not used.
* Of the five formerly unassigned, all five were read: 11 (SSE arithmetic) → 02;
  19 (likelihood ratio test) → 07 or 08; 27 (drop the predictor with p > 0.05) → 03;
  44 (F for one added regressor from TSS and RSS) → 02, where it is already Example 2.2;
  54 (remove the largest p-value first, one at a time) → 05.

| unit | questions (unverified) |
|------|------------------------|
| 01 | none usable: 12, 50 descriptive; 61 → unit 05 |
| 02 | 11 18 24 44 (body examples), 23 (exercise); 53 descriptive, dropped; 14 → 04, 58 → 10, 70 → 05 |
| 03 | 62, 27 (exercises); 13 49 56 71 descriptive, dropped; 45 → 08, 67 → 07 |
| 04 | 2 36 42; **+14** |
| 05 | 5 6 8 10 30 35 37; **+54, +61, +70** |
| 06 | 68 69 75 |
| 07 | 3 4 22 34 38 41 52 55 72; **+19** (or 08), **+67** |
| 08 | 7 20; **+45** |
| 09 | 21 31 46 |
| 10 | 64; **+58** |
| 11 | 9 25 26 29 33 48 51 57 63 66 73 |
| 12 | 39 74 |
| 13 | 1 15 16 32 40 43 59 60 |
| unassigned | none: all five placed above |

Units 10 and 12 look under-served by this pass. The unassigned five have now been read
and none of them belongs to either, so those two units must be served by re-reading
questions already assigned elsewhere, or they carry no SOA question and their exercise sets
draw on the other categories instead.

---

## 7. Mechanics

```bash
cd note
python build.py 07            # one unit
python build.py               # everything (slow; several minutes)
```

**Never run two `build.py` invocations at once** (gotcha 6).

After **every** build, gotcha 37 applies: a green `[OK]` means LaTeX compiled, not that the
R ran. Extract and read the printed output:

```bash
grep -c '## Error' unit07.tex          # must be 0
python3 -c "
import re, pathlib
t = pathlib.Path('unit07.tex').read_text()
for b in re.findall(r'\\\\begin\{Verbatim\}\[fontsize=\\\\small,frame=leftline,framesep=2mm\]\n(.*?)\\\\end\{Verbatim\}', t, re.S):
    print('====='); print(b.rstrip())
"
```

That scan already found two defects in units 04 and 05 that had been signed off as built.

### Per-unit checklist

Work one unit at a time and finish it before starting the next.

- [ ] read the `.Rnw` line by line
- [ ] task 1: remarks and opening paragraphs triaged
- [ ] task 2: both forward columns at 0
- [ ] task 3: exercises expanded, every number run
- [ ] `grep -c -- '---' unitNN.Rnw` = 0
- [ ] builds with 0 errors, 0 undefined references
- [ ] printed output read, `## Error` count 0
- [ ] page count recorded

| unit | 1 | 2 | 3 | built | pages after |
|------|---|---|---|-------|-------------|
| 01 | ✓ | ✓ | ✓ | ✓ | 75 (was 43) |
| 02 | ✓ | ✓ | ✓ | ✓ | 90 (was 59) |
| 03 | ✓ | ✓ | ✓ | ✓ | 70 (was 35) |
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

### Notes recorded during the pass

* **Unit 1.** No remark failed the §3 test outright, so all 19 survive; eleven were cut back
  to their factual core and every preview clause inside them is gone. The four in-unit
  forward `\ref`s are gone; the twelve forward `Unit M` mentions stay by the §4 exception.
  10 exercises → 25. The KNN table in §1.5.3 gained a `z` column so the remark about
  Monte-Carlo error points at a printed number instead of asserting one.
* **Unit 2.** Repair 4 of §4 was needed once. Unit 2 used $F_{1,\nu}=t_\nu^2$ in Example 2.2
  and in the $k=1$ remark, and the only proof of it in the course was
  `cor:t2F` in **Unit 3**, i.e. forward. A corollary "The square of a $t$ is an $F$" with a
  three-line proof was added to `prereq.Rnw` §P.18 (immediately after the definition of the
  three laws) and Unit 2 now cites it by name. `prereq` rebuilds at 109 pp, 0 errors.
* **Unit 2, second restructuring.** The proof of the overall $F$ test cited
  `Exercise~\ref{ex:HH0}` for the properties of $\bH-\bH_0$, so a theorem depended on an
  exercise stated later. Those properties are now Lemma 2.20 in §2.6.3 with a proof, the
  $F$-test proof cites the lemma, and the exercise was rewritten to *use* it (SSR as a
  squared length, and the invariance of $F$ to the origin and scale of the response).
* **Unit 3.** Repair 4 of §4 was needed a second time, for a different reason. The proof of
  the extra-sum-of-squares corollary ended "it coincides with (3.4), both being the same
  $F$ statistic for the same hypothesis", which is not a proof: having the same law does
  not make two statistics equal. **Proposition 3.4, Restricted least squares**, was added
  before it, deriving the constrained minimiser in closed form and with it the exact
  identity `SSE_R - SSE_U = (Rb-r)'[R(X'X)^{-1}R']^{-1}(Rb-r)`. The corollary's proof is
  now two lines and strictly stronger (the two forms are the same *number*, not two
  statistics with a common law), and the old projection argument was dropped. Verified
  numerically: 4053.2563 both ways on the course example. 11 remarks → 10, 10 exercises →
  23.
* **All forward references of every kind are now zero in units 1, 2 and 3**, not only the
  two kinds the §2 script counts: no forward theorem, lemma, equation or exercise reference
  either. The one exception preserved is Unit 1's twelve `Unit M` mentions.
* **Cross-unit `\ref` is a live trap when writing new exercises** (gotcha 10). Three
  attempts to cite Unit 2's results from a Unit 3 exercise as `\ref{thm:ols-proj}` and the
  like produced undefined references; they are now named in words. Run the second scan in
  §4 before building, not after.

### Rescan against the instructor's three rules (§5)

Exercise counts after the rescan: **01: 26 · 02: 28 · 03: 26** (from 10, 13, 10). Solution
chunks that execute at build time: 17, 14, 16.

* **Removed as pure descriptive:** SOA 12 and 50 from Unit 1, 53 from Unit 2, and 13, 49
  and 71 from Unit 3. Their *mathematics* was kept where it was worth keeping and rewritten
  without the multiple-choice frame: the CI-versus-PI limits of 13 and 49 are now
  Exercise 3.9, deriving `u-t = O(n^{-1/2})` and `w-v → 2 z σ` and the degenerate `s=0`
  case; the omitted-variable consequences of 71 are part (d) of Exercise 3.23.
* **Added from ISLR:** §2.4 ex 7 (KNN by hand), §5.4 ex 1 (minimum-variance portfolio,
  with the bootstrap SE), §5.4 ex 8 (LOOCV over polynomial degree), §5.4 ex 9 (bootstrap on
  `Boston` medv, median and tenth percentile) to Unit 1; §3.7 ex 5 (fitted values as linear
  combinations) and §3.7 ex 11 (the t-statistic is symmetric in x and y) to Unit 2;
  §3.7 ex 3 (GPA/IQ interaction), §3.7 ex 10 (`Carseats` with factors) and §3.7 ex 15
  (`crim`: marginal against partial coefficients) to Unit 3.
* **Added from FREES:** ex 3.1 (reconstruct an ANOVA table from `s_y` and `s`), ex 3.2
  (standard errors, covariance and a linear combination from a printed `(X'X)^{-1}`),
  ex 3.3 (a four-observation design by hand), ex 4.1 (F from R² at two sample sizes),
  ex 2.6 (|r| as the geometric mean of the two slopes) and ex 2.9 (a binary regressor gives
  the two-sample t), all to Unit 2. FREES's chapter 1 and the data-based parts of 2--4 are
  unusable without its datasets.
* **`Portfolio` and `Carseats` are in `ISLR2`** and now execute in unit 01 and unit 03
  chunks; no new package is needed.
* **Two claims failed when the prose was converted to a live chunk**, which is the point of
  the conversion. Unit 2's negative-`adjR2` exercise asserted "negative about half the
  time" from a single draw whose `adjR2` was in fact `+0.056`; it now runs 500 draws and
  reports 51%. Unit 1's boundary bias-variance exercise said "three orders of magnitude",
  which is 730-fold.
* **A printed column that looks like a bug and is not.** In Unit 3's simultaneous-coverage
  exercise the F-region coverage is bit-identical at every predictor correlation, because
  `z2 = rho*z1 + sqrt(1-rho^2)*w` leaves the column space unchanged and the F statistic is a
  function of the projection, not of the basis. The exercise now says so.

### When the pass is finished

- update the page counts in `CONVENTIONS.md` §8;
- record anything learned as a new numbered gotcha in `CONVENTIONS.md` §6;
- if the SOA map was verified, say so here and consider moving it into `README.md`'s SRM
  appendix, which promises it;
- report to the instructor the Unit 1 course-map question from §4 above, and any place
  where removing a forward citation cost something real.
