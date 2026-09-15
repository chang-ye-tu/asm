# ASM lecture notes — conventions, sources, and gotchas

Authoritative handoff for anyone (human or model) continuing these notes. Read this before
editing any `.Rnw`, then read `REVISION.md`, the current work order.

**State (2026-09-15).** The course prepares students for SOA Exam SRM and Exam PA. Each
unit covers the exam's required FREES/ISLR sections, rewritten as rigorous accounts of what
those books hand-wave, with exercises from those texts and the mapped SOA sample questions.
§1's motto holds and `prereq.Rnw` remains the single source of background results. FREES's
data files and chapter scripts are on disk under `note/data/frees/`, so the book's examples
are reproduced from its data and all its exercises are in scope. Unit 1 is rebuilt on this
design as the template; Units 2–14 are the pre-rebuild versions and are rebuilt next, in
order. The rules fixed on the template, the syllabus map, the SOA map and the per-unit
procedure are in `REVISION.md`.

---

## 1. The motto

> **No unproved result.** Everything is derived from first principles.

What may be assumed, and nothing else:

* measure-theoretic probability — the integral and its convergence theorems
  (monotone, dominated, Fubini–Tonelli);
* linear algebra and multivariate calculus.

**`prereq.Rnw` — *Mathematical Prerequisites* — is the single core source.** It assumes
**no real-analysis background**: it starts from the completeness axiom. Four parts:
I Analysis (sup/inf, Bolzano–Weierstrass, Heine–Borel, Rolle and the MVT, differentiation
under the integral sign, semi-continuity, Taylor, convexity and separation, **and convex
programming — Lagrangian duality, weak duality, Slater, KKT**);
II Linear Algebra (rank–nullity, **trace**, projection, **spectral theorem**, positive
definiteness and symmetric square roots, idempotents with tr = rank, Schur complement,
Sherman–Morrison, **SVD**, **operator norm and condition number**, matrix differentiation
with the chain rule); III Measure-Theoretic Probability (inequalities,
Borel–Cantelli, conditional expectation as an *L*² projection, the multivariate normal,
χ²/*t*/*F*, modes of convergence, characteristic functions, Lévy continuity, Portmanteau,
CMT, Slutsky, Lindeberg–Feller, **dependent summands: the stationary *L*² weak law,
*m*-dependence, and a CLT for autoregressive scores**, delta method); IV the results the
units actually cite.

**Do not cite any of this as "standard".** If a unit needs a result that is not there,
**add it to `prereq.Rnw` with a proof** — the document is meant to grow as the units do —
rather than asserting it in the unit or inventing a second appendix.

## 2. House style

The style is that of `mva/note/clm.tex`. The content of a unit is the syllabus sections of
FREES and ISLR (`REVISION.md` §3), condensed into the blocks below, never their prose.

**Allowed:** definition · theorem/lemma/proposition/corollary · proof · *short factual*
remark · `reading` box (one line, the required sections) · `derivation` box (mathematics
only) · `\periodmark` at the two 50-minute breaks.

**Forbidden — removed on the instructor's instruction:**

* motivation boxes, `suppremark` commentary boxes, "why this matters" asides
  (`motivation`/`suppremark`/`srmbox` are deliberately **absent** from `asm_preamble.tex`);
* section or unit **summaries**, and result→R-function summary tables;
* meta-commentary about the document itself ("each subsection reproduces…", "differences
  are printed rather than asserted…");
* forward-reference previews ("§5.4 exhibits the two curves", "Unit 7 returns to this");
* sentences restating what a printed number already shows;
* rhetorical framing ("this is the whole subject in one line");
* exercise **tiers** (no "Tier A / B / C" — one flat list);
* SRM-alignment sections;
* answer keys when an SOA sample question is used (present the problem and solution,
  never "(Key: C)").

* **em-dashes** (`---`). Not a style preference: rewrite the sentence. Use a colon for an
  explanation, a comma pair for an aside, a semicolon for a contrast, parentheses for a
  gloss, or split into two sentences. `grep -c -- '---' *.Rnw` must return 0 everywhere. The rule governs the
  typeset notes; this markdown file is not typeset and is exempt;
* lead-ins that announce what the next passage will do ("it is derived here in full",
  "we now show", "the methods below", "in this section"), and any sentence that carries no
  load. The instructor's words, twice: **no lead-ins, no non-load-bearing sentences, no
  fillers, ever.**

**Required tags (fixed on the Unit 1 template).**

* A remark, definition or example that condenses a passage of ISLR or FREES carries the
  passage in its title: `\begin{remark}[Two drawbacks; ISLR §5.1.1]`. The block is the
  author's condensation, never a quotation; the tag makes that checkable.
* A section or exercise outside the SRM/PA reading lists carries "(beyond the syllabus)"
  in its title and a reading box saying so. Nothing is deleted on that ground.
* Exercises are titled by source: `[ISLR §5.4, exercise 8]`, `[FREES exercise 3.2]`,
  `[SOA sample question 12]`.
* Proofs are complete: no intermediate step omitted; numbered steps when a proof has more
  than one idea.

Test for a sentence: if it is not a definition, theorem, proof, or one terse factual
remark, delete it.

**Cover page:** one vertically centred line, `\fontsize{26}{32}`, nothing else — no
subtitle, rule, course name, or reading list.

## 3. The verification principle

> Add **as many comparisons as possible** between the manual formula and what the package
> produces.

Every unit reproduces the ISLR lab of its sections with the lab's numbers, and FREES's
in-chapter examples from the book's data and script to the digits of the book's tables,
and prints the *difference* between the manual formula and the package output rather than
asserting agreement. Where several routes to one quantity exist, compute all
of them (the pre-rebuild Unit 3 gets the joint *F* four ways; Unit 2 gets *R*²=*r*² four
ways; Unit 4 gets Cook's D two ways and WLS three ways). R stays because PA is R-based.

**Never state a numerical claim you have not run.** Several prose claims were wrong on
first draft and only the printed output caught them (§6).

## 4. Course structure

Fourteen units, one per weekly meeting of 130–140 minutes, in the order below; the order
is the reading order and later units cite earlier ones by name. The `\periodmark`s still
say "period $k$ of 3" and stay until the instructor says otherwise. `README.md`'s schedule
table lists the date and the unit's contents in English, with no week or assigned-reading
column (instructor, 2026-09-15). Linear models are developed for general *k*; *k*=1
appears as corollaries, never as its own unit.

| Unit | Topic | SRM topic |
|------|-------|-----------|
| U01 | Statistical learning; resampling (bootstrap beyond the syllabus) | 1 |
| U02 | Multiple regression I: matrix theory (+ *k*=1) | 2 |
| U03 | Multiple regression II: inference and interpretation | 2 |
| U04 | Regression diagnostics (robust SEs beyond the syllabus) | 2 |
| U05 | Variable selection and dimension reduction | 2, 5 |
| U06 | Shrinkage, high dimensions, KNN | 2 |
| U07 | GLM I: categorical responses (FREES 11) | 2 |
| U08 | GLM II: counts and the exponential family (FREES 12–13) | 2 |
| U09 | Modeling trends (FREES 7, 8.1) | 3 |
| U10 | Autoregression and forecasting (FREES 8.2–8.4, 9); trees intro | 3, 4 |
| U11 | Decision trees | 4 |
| U12 | Ensembles | 4 |
| U13 | Unsupervised learning | 5 |
| U14 | Convex optimisation, SVM, neural networks | beyond the syllabus |

## 5. Sources (all texified and local)

| Source | Path | What it gives |
|---|---|---|
| ISLR | `research/llm_proj/books/islr/islr_NN.Rnw` | required reading |
| ISLR data not in `ISLR2` | `lectures/asm/note/data/islr/Advertising.csv` | the `Advertising` data of ISLR chapters 2–3, from statlearning.com |
| FREES | `research/llm_proj/books/frees/frees_NN.tex` | required reading |
| FREES data and scripts | `lectures/asm/note/data/frees/{csv,scripts,doc}/` | the 41 data sets, the in-chapter R code by chapter, the data descriptions and errata (`REVISION.md` §4 for the deviations from the book) |
| CLM / MC / MLM / GCI | `lectures/mva/note/*.tex` | proof sources for regression theory (prereq and the pre-rebuild U02–03); MC = matrix differentials |
| BDA units 1–7 | `lectures/bda/note/unitNN.Rnw` | proof sources: u02 ridge/lasso (U06) · u03 logistic/ROC (U07) · u04 bias-var/CV (U01) · u05 trees (U11–12) · u06 convex/SVM/NN (U14) · u07 PCA/clustering (U13); the pre-rebuild bodies came from these |
| EconometricsWithR | `research/llm_proj/books/EconometricsWithR/abridged/abridged.Rnw` | robust SEs, LPM/probit/logit, AR(1)/unit roots/ADF. Same `.Rnw` format and notation. `abridged_zh.Rnw` is a full Chinese translation. `data/` has 7 real datasets incl. `us_macro_quarterly.xlsx` |
| ptpr (Devroye–Györfi–Lugosi) | `research/llm_proj/books/ptpr/ptpr_NN.tex` | Bayes optimality (ch 2, used in U01); VC theory, trees, NN, deleted estimates |
| Baldi, *Probability* | `research/llm_proj/books/baldi_p/baldi_p_03.tex` | **Convergence chapter**: Lévy continuity, Portmanteau, Slutsky, delta method |
| Kallenberg, *FMP* | `research/llm_proj/books/kallenberg_fmp/kallenberg_fmp_06.tex` | **Lindeberg–Feller** (thm 6.13) + product-comparison and Taylor lemmas |
| Abadir & Magnus, *Matrix Algebra* | `books/ma/ma_02,07,13.tex` | matrices, eigenvalues and factorisations, matrix calculus |
| Knapp, *Basic Real Analysis* | `books/knapp_real_b/knapp_real_b_01–02.tex` | one-variable calculus, metric spaces, Bolzano–Weierstrass, Heine–Borel |
| Knapp, *Advanced Real Analysis* | `books/knapp_real_a/` | functional analysis, probability foundations |
| Boyd & Vandenberghe | `books/boyd/boyd_02,03,05.tex` | convex sets, convex functions, **Duality** (§5.3.2 = the Slater proof) |
| Bertsekas, *Convex Analysis* | `books/bertsekas_cv/cv_chap*.tex` | alternative convex-duality development |
| SOA sample questions | `lectures/asm/srm/srm_body.tex` | 71 live questions (17, 28, 47, 65 deleted from the syllabus), `\begin{question}{N}` then `\begin{solution}{N}{LETTER}`; mapped to units in `REVISION.md` §6 |
| SOA SRM syllabus | `lectures/asm/syllabus/2026-09-exam-srm-syllabus.pdf` | topic weights, reading list (the scope of every unit) |
| SOA PA syllabus | `lectures/asm/syllabus/2026-10-exam-pa-syllabus.pdf` | assumes SRM minus FREES 7–9; R workflow, data exploration, feature engineering; no R at the exam |

Datasets: every `ISLR2` data set is installed (`Auto`, `Boston`, `Carseats`, `College`,
`Default`, `Hitters`, `Portfolio`, …), and every FREES data set is a CSV under
`note/data/frees/csv/`, read with a path relative to `note/`.

## 6. Gotchas — every one of these cost a build failure or a wrong number

### LaTeX / build

1. **`\Atarget` must not appear in an `enumitem` `label=` key.** hyperref re-expands labels
   inside an `\edef`; the build dies with one "Undefined control sequence \x" per item and
   points at `\begin{enumerate}`. Put the anchor in the item **body**.
2. **Macros are discovered missing at build time.** Already added: `\bW \bZ \bOmega
   \bgamma \balpha \bg \convd \convp`, for Unit 6 `\sign \CV \bd \bq`, for
   Unit 7 `\sd \bF \bG \bK \btheta \bpi \calI`, and for Unit 10 / the new
   prerequisites section `\bGam \calL`, for Unit 11 `\calS \calT \bp`, and for
   Unit 12 `\bff \calO \calE`. **`\bxi` does not exist** (write `\boldsymbol{\xi}`), and
   `\bb` is β, so a neural network's offset vector must NOT be `\bb_1`; Unit 14 uses
   `\bc_1`. Check before writing new
   mathematics. **`\bI` is the identity matrix**, so the Fisher information is `\calI`
   (renamed in `prereq.Rnw` too); `\be` is the error vector, so a basis vector must be
   written `\mathbf{e}_j`.
3. `build.py` counts `^!` and `^Error:` in the log; a build reporting pages but non-zero
   Errors is a **failure**, not a warning.
4. **Floats do not float in the 16:9 format.** Every figure in Unit 6 marked `[!ht]` was
   deferred to the end of the document: a page is a slide, and the tcolorbox stream leaves
   no room for a float to land. `float` is now loaded in `asm_preamble.tex` and figures use
   `\begin{figure}[H]` with the chunk **inside** the float, so caption and graphic stay
   together. (Unit 2 sidesteps the problem differently, by emitting the plot inline and
   floating a caption-only `figure`.)
5. **`\be` is the error vector `\boldsymbol{\varepsilon}`, not a basis vector.**
   `\bv=\pm\be_j` typeset as ±ε_j and read as nonsense. Write `\mathbf{e}_j`.
   Likewise `\inf_\bb` fails ("Missing { inserted"); braces are needed around any
   multi-token subscript, `\inf_{\bb}`.
6. **Never run two `build.py` invocations at once.** Concurrent xelatex runs collide over
   minted's temp files and the whole document falls back to unhighlighted verbatim, with
   one `! Package minted Error` per chunk (23 of them on unit06) and a spurious `[FAIL]`.
   Nothing is wrong with the source; rebuild alone.
7. **A long `\fancyhead[L]` collides with `\leftmark`.** Unit 8's first header, "GLM II:
   Counts and the Exponential Family", ran straight into "§4 Computation: Formulas Against
   Package Output" with no gap. The right header is set by the longest section title, so
   the left one has to stay near Unit 7's length (about 36 characters). Shortened to
   "GLM II: Counts".
8. **`\texttt{pkg::object}` does not break.** One such token in a paragraph produced a
   42pt overfull hbox in Unit 8. Write "\texttt{bioChemists} from \texttt{pscl}" instead
   of "\texttt{pscl::bioChemists}" in running prose.

### Cross-references — broken twice, so read this

9. **Never hardcode a theorem number inside an R chunk comment.** It is verbatim, so LaTeX
   cannot check it, and it goes stale silently. Nine such comments were wrong
   (`# Theorem 3.4` for a theorem that was 3.5, etc.). Use word descriptions
   (`# tr(H) = k+1`) and put live `\ref`s in the surrounding prose.
10. **`\ref` does not cross documents.** Unit 7's draft cited the conditions of the
   prerequisites' maximum-likelihood theorem as `\ref{L1}`--`\ref{L3}`; those labels live
   in `prereq.tex`, so the build printed `??` and reported four undefined references. Name
   the conditions in words instead ("the curvature condition"). This is the mechanical half
   of the rule below.
11. **Never cite another document by number.** Cross-unit and unit→appendix references must
   be **named**: "the residual-variance theorem of Unit 2", "the Frisch–Waugh–Lovell
   theorem of Unit 3", "the Lindeberg–Feller theorem of Appendix A". Numeric citations into
   `prereq` were wrong on all four attempts (A.19/A.24/A.26/A.30 vs the true A.20/A.22/
   A.24/A.26).
12. **Renumbering a unit** shifts (a) counter prefixes, (b) `sec:N.x` labels, (c) the
   `figs/unitNN-` path, (d) the header, (e) the titlepage, (f) cross-unit `Unit N §M.x`
   section refs. The header uses `Unit\ N` (backslash-space) and escapes a `Unit (\d+)`
   regex; the **titlepage uses a real space and does not** — a blanket remap applied after
   fixing the titlepage will map it twice. Verify header against titlepage in the built PDF.

### R / statistics

13. **`lmtest::bptest` defaults to Koenker's studentized statistic**, not the original
   Breusch–Pagan of FREES §5.7.1. FREES's five steps reproduce `bptest(m, studentize =
   FALSE)` **only** when step (ii) scales by σ̃² = SSE/*n* (the restricted MLE), not
   *s*² = SSE/(*n*−*k*−1); using *s*² inflates *LM* by {*n*/(*n*−*k*−1)}². The two variants
   differed by 1.8× on the course example. Derived in full in Unit 4.
14. **The R package probe merges stderr.** `requireNamespace` can trigger a package's
   startup banner (quantmod's "Registered S3 method overwritten"), which then parses as a
   missing package name. `build.py` tags result lines with `__ASM_MISSING__`; keep that.
15. **Check every numerical claim against the printed output.** Caught this way:
    an algebraically wrong identity check that printed 27.5 beside siblings at 1e−12;
    a claim that KNN test error "never falls below the Bayes error" when three rows did
    (Monte-Carlo noise — fixed with an exact *L*\* and an `mc_se` column); a `max|z|²/n`
    printed as if visibly "→0" when on a fixed sample it is 1.267 and shows nothing.
16. **An unexpected number may be a finding, not a bug.** Bootstrap SEs came out 1.8× the
    formula SEs on `Boston` — that is evidence against constant variance, and it is taught.
17. **`glmnet`'s λ is not the textbook λ, and the conversion differs at the two ends of
    the family.** Writing the criteria as ‖Y−Xβ‖²+λ‖β‖₁ and ‖Y−Xβ‖²+λ|β|², the reported
    constant maps as **λ = 2n·λ_glmnet for the lasso** but **λ = n·λ_glmnet / sd_n(y) for
    ridge**, where sd_n uses divisor *n*. (glmnet standardises the gaussian response
    internally and reports λ already multiplied by sd_n(y); that factor cancels for the
    ℓ¹ penalty and does not for the ℓ² one.) Verified on `Hitters` and `Boston`, glmnet
    4.1.10. The naive λ = n·λ_glmnet is wrong by 380 on coefficients of size 425.
    The version-proof move, and the one Unit 6 §4.4 teaches, is to **recover λ from the
    stationarity conditions**: `x_j'(y − Xb̂)/b̂_j` must be constant in *j*.
18. **`cv.glmnet` does not fit the folds on the full-data λ grid.** In
    `glmnet:::cv.glmnet.raw` the fold loop runs *before* `lambda <- glmnet.object$lambda`,
    so each fold is called with `lambda = NULL` and builds its own path; `buildPredmat`
    then interpolates onto the full-data grid. Passing the shared grid to the fold fits
    reproduces `cvm` only to ~0.2% and selects a different `lambda.min`. Fitting each fold
    on its own path and interpolating reproduces `cvm` and `cvsd` to 1e−11. `cvsd` is
    `sqrt(weighted.mean((fold_means − cvm)², w = fold_sizes)/(V−1))`.
19. **`MASS::lm.ridge` uses the textbook parametrisation** with divisor-*n* standardisation,
    so it, not `glmnet`, is the clean package check for the ridge closed form: agreement
    1e−13.
20. **`glmnet` needs a path and a tight `thresh` before its `df` can be trusted.** Refitting
    at single λ values on a *k*>*n* design reported active sets of 57 with n=50; one path
    fit at `thresh = 1e-14` gives the correct maximum of 49 = rank of the centred design.
21. **`glm`'s default `epsilon = 1e-8` is not tight enough to check the score equations.**
    On `Default` the score at the reported estimate was 1.1e−2 (the `income` column runs to
    7e4). `control = glm.control(epsilon = 1e-14)` brings it to 1.6e−8 and makes the manual
    standard errors agree with `summary()` to 9e−10.
22. **`MASS::polr` uses the opposite sign convention to FREES.** FREES writes
    logit P(y ≤ j) = α_j + x′β; `polr` fits logit P(y ≤ j) = ζ_j − x′γ, so γ = −β while
    ζ_j = α_j. Same fitted probabilities, same log-likelihood, opposite signs on every
    slope. Unit 7 §4.7 prints both rows.
23. **`polr` and `multinom` are not nested**, so the difference of their log-likelihoods is
    not a likelihood ratio statistic and must not be referred to χ². Compare them by AIC,
    and test proportional odds instead through the *c*−1 dichotomised logistic regressions,
    which do share a slope vector under the model.
24. **Separation is silent.** `glm` returns a coefficient with a much larger standard error,
    a z statistic near zero, deviance ≈ 0 and fitted probabilities at 0 and 1, plus a
    warning that is easy to miss. The MLE does not exist; the fit is an artefact of the
    iteration limit.
25. **Deviance residuals need `pmax(d, 0)` inside the square root.** Terms that should be
    exactly zero come out at −1e−16 and `sqrt` returns `NaN`, silently poisoning the sum.
26. **`sandwich::vcovHC` on a `glm` warns when a hat value is near 1** and can be singular.
    On `Bikeshare` the manual sandwich
    `(X'WX)^{-1} (X'diag((y−μ̂)²)X) (X'WX)^{-1}` matches `HC0` to 5e−15 and does not warn;
    compute it directly.
27. **`quasipoisson` changes nothing but the standard errors.** The coefficients are
    bit-identical to `poisson` and every SE is exactly √φ̂ times as large. If the sandwich
    ratios are *not* all equal to √φ̂ (0.16 to 7.07 on `Bikeshare`), the quasi-Poisson
    variance assumption is itself wrong.
28. **The Poisson deviance is not χ²_{n−p} when the means are small.** With a *correct*
    intercept-only Poisson and n=2000, the mean deviance is 1683 at μ=0.3 and 2003 at
    μ=50. The approximation improves as each μ_i grows, not as n grows, so
    "deviance ≈ df" is not a fit test for sparse counts. Use the Pearson statistic for the
    dispersion and deviance *differences* for nested comparisons.
29. **A 2×2 `par(mfrow)` figure does not fit the 16:9 page at the default margins.** At
    `out.width = 0.78\linewidth` a 6.4×4.1in device becomes ~122mm tall against ~126mm of
    text height, so the caption spills off the page and the lower row's titles collide with
    the upper row's x-labels. Keep 2×2 panels at `fig.height` ≈ 3.3 with
    `mar = c(2.6, 3.4, 1.8, 0.6)`, `mgp = c(1.9, 0.6, 0)` and no x-label on the top row.
30. **`predict(fit, newdata = ...)` needs the regressor to be a plain named column.**
    `lm(y ~ I(1:T))` cannot be given new data: the `newdata` column name never matches and
    R silently reuses the fitted values, then `lines()` fails on a length mismatch. Create
    the time variable first, `tv <- 1:T; lm(y ~ tv)`.
31. **`pacf` is not a lagged regression.** `stats::pacf` solves the *sample* Yule--Walker
    equations, forming every inner product from all *T* observations; regressing `y_t` on
    `y_{t-1},…,y_{t-k}` uses only the *T*−*k* complete cases. On `LakeHuron` they differ at
    lag 2 by 0.267 against 0.238. The gap is an end effect of exact order 1/*T* (gap × *T*
    is 0.92, 0.88, 0.87 at *T* = 50, 200, 800). Unit 10 §1.3 states the Yule--Walker system
    and §5.1 reproduces `pacf` from it to machine precision. **Do not claim the two agree.**
32. **`arima(..., method = "CSS")` equals `lm` on the lag, the default does not.** Unit 10
    checks conditional least squares four ways: closed form, `lm`, `arima` with `CSS`, and
    *r*₁. The default `method = "CSS-ML"` maximises the exact likelihood and gives a
    different number (0.838 against 0.836 on `LakeHuron`).
33. **`tseries::garch` drops the first observation from the likelihood.** A manual
    `optim` on the conditional Gaussian likelihood summing from *t* = 1 reports a
    log-likelihood 3.2 higher than the package on 1859 DAX returns and looks like a better
    optimum; summing from *t* = 2 instead reproduces the package to 3e−5, and the
    coefficients to 8e−5. Match the conditioning convention before concluding anything.
34. **The GARCH likelihood is not concave and `optim` reports success anyway.** Of three
    starting values on the DAX returns, two converge (exit code 0) to a degenerate point
    with α̂ at machine zero, δ̂ = 1 and a log-likelihood about 95 lower. Always start from
    several places and print the log-likelihood. Unit 10 §6.5 teaches this.
35. **`tseries::adf.test` always fits a trend** and uses *k* = trunc{(*n*−1)^(1/3)} lagged
    differences, so it spends most of its degrees of freedom on nuisance terms. Its power
    against a true *AR*(1) with β₁ = 0.836 at *T* = 98 is 25%: `LakeHuron` is not rejected
    (*p* = 0.25) even though it is stationary. Report that as low power, measured, not as
    evidence of a unit root. Its internal critical-value table at *T* = 250 is
    −3.99/−3.43/−3.13, which Unit 10 §5.5 reproduces by simulation to 0.02.
48. **`prcomp` and `eigen` may or may not agree in sign, so compare absolute values.** On
    `USArrests` they happen to agree; permuting the rows flips `prcomp`'s first column.
    Nothing in the theory determines the sign (Unit 13 Prop 13.6), so any prose claim that
    survives a sign flip is safe and any that does not is wrong.
49. **`cutree(h = ...)` refuses to cut a centroid-linkage tree**, with "the 'height'
    component of 'tree' is not sorted (increasingly)". That is the inversion of Unit 13
    Thm 13.15 showing up as an error, and the unit uses `tryCatch` to print it as evidence
    rather than letting it fail the chunk. `cutree(k = ...)` still works, since it reads the
    merge order and not the heights.
50. **Counting the linear pieces of a rectified network must not straddle a breakpoint.**
    Evaluating slopes on a grid that includes points either side of a kink produces spurious
    intermediate slopes: a 6-unit network reported 12 distinct slopes where the theorem
    allows 7. Evaluate at the midpoints between consecutive breakpoints.
51. **`solve.QP` fails on some permutations of the same SVM dual** ("constraints are
    inconsistent"), so it cannot be used to demonstrate that a convex problem has one answer.
    Unit 14 §4.5 uses the unconstrained hinge form instead and minimises it with `optim` from
    ten random starts: relative spread 9e-4 (the optimiser's tolerance on a non-differentiable
    objective) against 5.3 for `nnet`.
52. **`e1071::svm` orders the factor levels its own way**, so its (w, b) is the *negative* of
    the textbook one and the SUMS are what vanish, to about 1e-4 (libsvm's own tolerance),
    not the differences. The hyperplane is identical.
53. **`nnet`'s offsets and a hand-written backprop must agree on layout.** Unit 14's first
    `grad` returned `X'D1` where `D1'X` was required, a transposition that leaves the
    parameter vector's *length* right and every value wrong (largest gap 0.03 against
    7e-11 after the fix). **Always check a hand-derived gradient against central
    differences**; nothing in a training loop reveals it.
43. **ρ and σ² in the bagging formula are variances over the draw of the TRAINING SET,
    not over the trees inside one forest.** Conditionally on the data the members of a
    forest are independent (bootstrap and mtry are i.i.d. draws), so a single forest
    estimates ρ = 0. Unit 12 §4.1 and §4.3 therefore simulate 150 independent training
    sets. `predict(rf, newdata, predict.all = TRUE)$individual` gives the per-tree
    predictions that make the estimate possible.
44. **The sample version of the averaging identity is exact.** For any M×B matrix,
    var(row means) = mean(s²_b)/B + {(B−1)/B}·mean(off-diagonal covariances) is algebra,
    so the check lands at 1e−16. Estimating ρ as a *correlation* and multiplying by the
    *average* variance is NOT the same thing and leaves a systematic 5% gap; use the
    covariances.
45. **`gbm` needs `bag.fraction = 1`** to switch off stochastic gradient boosting, or two
    runs on the same data differ and the λB comparison is noise.
46. **The λB ≈ constant result is a property of the problem, and the grid must contain the
    optimum.** On an exclusive-or truth with `n.trees = 4000` the minimum was censored at
    the boundary for the two smaller shrinkages and λB came out 40/80/102.5, which looks
    like a refutation and is an artefact. On a smooth-plus-interaction truth the optima are
    interior at B = 1700/800/300 and λB = 17/16/15. Always print `best_B` and check it is
    not the last grid point.
47. **A single bagged forest at small B is too variable to show monotonicity in B.** One
    realisation on `Boston`-sized data gave 0.945, 0.528, 1.046 at B = 5, 25, 100. Average
    over ten forests before claiming the curve decreases.
37. **An R error inside a chunk does NOT fail the build.** `build.py` counts `^!` and
    `^Error:` in the **LaTeX** log. knitr catches an R error, prints it as chunk output, and
    LaTeX typesets it happily, so the summary table says `[OK]` while the PDF contains
    `## Error in prune.tree(): can not prune singlenode tree`. This happened on unit11's
    first build. **After every build, extract the `Verbatim` blocks from the `.tex` and read
    them** (the same pass that checks the numerical claims, §3). Grep for `## Error` at
    minimum.
38. **`cv.tree` does not do balanced K-fold cross-validation.** Its folds come from
    `sample(K, n, replace = TRUE)`, so sizes are multinomial: 38 to 60 for n = 506, K = 10.
    It also prunes each fold's tree at the **full-data** `k` sequence, so the `size` it
    reports is the full-data leaf count and the fold actually scored may have a different
    one (8,7,5,4,4,4,2,1 against 8,7,6,5,4,3,2,1 on one Boston fold). Read the size axis of
    a `cv.tree` plot as a label, not as what was measured.
39. **`rpart`'s `cp` is α divided by the root's cost**; multiplying back reproduces `tree`'s
    `k`. The two agree only as far as they make the same splits: on `Boston` the first three
    thresholds match to five figures (19339.6, 7311.9, 3061.0) and the fourth does not,
    because `tree` stops on `mindev`/`minsize` and `rpart` on `minsplit`/`minbucket`, so the
    trees being pruned differ.
40. **`prune.tree(t, best = J)` returns the nearest size the sequence contains, not J**, and
    it errors outright on a single-node tree. `cv.tree` inherits that error whenever a
    fold's tree has one node, so a permissive-growing experiment must guard the call.
41. **Growing criterion and pruning criterion select different trees, by a lot.** On
    `Carseats`, `cv.tree(FUN = prune.misclass)` chose 7 to 27 leaves depending on the seed
    while `cv.tree` (deviance) chose 2 to 3 on the same tree. Deviance is a log likelihood
    and punishes a confident wrong leaf without limit; the error count does not. Prune on
    the loss the model will be judged by, and report which was used.
42. **`tree`'s classification deviance is exactly `2 Σ_t n_t H(p_t)`**, twice the
    count-weighted entropy, hence the likelihood ratio statistic of Unit 7 against a
    saturated model. Verified to the printed digits on `Carseats` (170.66).
36. **A 2×2 `acf` panel is swamped by the lag-0 spike.** Both DAX correlograms in Unit 10
    Figure 4 needed `ylim = c(-0.06, 0.20)`; otherwise the structure at lags 1--30, which is
    the whole point of the picture, is a flat line at the bottom. Say in the caption that
    the axis is cropped.
54. **Never edit a `.Rnw` while its build is running.** `knitr::knit` read `unit02.Rnw` at the
    moment a script rewrote it and knitted a truncated file (88 KB instead of 190 KB) with
    no error; the PDF simply ended early. Wait for `[OK]`/`[FAIL]` before touching the source,
    and kill a build with `pkill -f 'python build.py'`, never with a pattern that also
    matches the shell issuing the `pkill`.
55. **`Rscript -e` mangles long scripts.** Past a few thousand characters the argument is
    garbled (spaces become `~+~`) and R hangs waiting on stdin. Put anything longer than a
    few lines in a file under the scratchpad and run `Rscript file.R`.
56. **`grep -c '## Error' unitNN.tex` is fooled by an ANOVA table**, whose `Error` row prints
    as `## Error   630.4 271 ...`. The check that only catches R failures is
    `grep -c -E '^## Error( in|:)' unitNN.tex`.

## 7. Files

```
asm/README.md                  course page (Chinese): schedule and SRM appendix; to be rewritten after the re-plan
asm/syllabus/                  SRM and PA syllabus PDFs
asm/srm/srm_body.tex           SOA sample questions and solutions (texify project)
asm/note/asm_preamble.tex      17pt 16:9, tcolorbox theorem boxes, minted, xeCJK, macros
asm/note/asm_knitr_setup.R     minted/Verbatim hooks, output.lines, options(width = 62)
asm/note/build.py              UNITS + NOTES; --quiet --pkg-check
asm/note/data/frees/           FREES data (csv/), chapter scripts (scripts/), descriptions and errata (doc/)
asm/note/prose.py              lists unnumbered paragraphs and remarks with line numbers
asm/note/REVISION.md           current work order: rules, syllabus map, SOA map, procedure, checklist
asm/note/unit01.Rnw            rebuilt on the SRM/PA design (the template)
asm/note/unit02–14.Rnw         pre-rebuild versions, all built; to be rebuilt in order
asm/note/prereq.Rnw            Mathematical Prerequisites (the single source of background results)
asm/note/superseded/           unit01-first-principles.Rnw, the replaced Unit 1
asm/exam/1151/                 empty; exams not yet written
```

**What the repository carries (instructor, 2026-09-16).** Only the PDFs and the sources that
compile them: in `note/`, the `.Rnw` files, the two headers, `build.py`, `data/`, the two
handoff documents and the PDFs; in `srm/`, `srm.tex`, `srm_*.tex`, `assets/`, `src/srm.pdf`,
`srm.pdf` and the README. Both directories use a whitelist `.gitignore` (`*` then `!`
rules), so a new file type must be added there before it can be committed. The texify
pipeline in `srm/`, `note/superseded/`, `note/prose.py` and every build product stay
local.

Build: `cd note && python build.py [03|prereq|…]`, one document per invocation, never two
at once. One PDF per document; there is no student edition. Needs `Rscript`, `xelatex`,
`bibtex`, `pygmentize`; all R packages are installed. A green `[OK]` means LaTeX
compiled, not that the R ran: `grep -c -E '^## Error( in|:)' unitNN.tex` must be 0 (gotchas 37, 56). The
pre-rebuild sources of every document are in git at `84b0283`.

## 8. State and what is left

**Built.** unit01 (rebuilt, 108 pp, 60 chunks, 8 proofs, 25 exercises) · unit02
(rebuilt, 168 pp, 84 chunks, 31 proofs, 45 exercises) · unit03–14 and prereq
(pre-rebuild, 0 errors, 0 undefined references). Next: rebuild Unit 3 per
`REVISION.md` §5, then Units 4–14 in order.

**What `prereq.Rnw` supplies beyond Parts I–III, and why** (each added for the unit named;
cite by name, never by number):

* §P.3 coercive minimisation (continuous + coercive attains its infimum; strictly convex ⇒
  unique) and the directional characterisation of a convex minimum: the lasso stationarity
  conditions without subdifferentials; the constrained/penalised equivalence of ridge and
  lasso reuses the Slater strong-duality theorem (U06).
* §P.18 the square of a $t_\nu$ is $F_{1,\nu}$, a statement about the laws; Unit 3's
  `cor:nested-F`/$t^2$ statement is about the statistic when $q=1$ (U02).
* §P.24 a CLT for bounded independent summands with unequal variances (U07) and a
  Lyapunov CLT with (2+δ)-moments, since a Poisson score is unbounded (U08).
* §P.24d *Dependent summands*: variance of a stationary average and the *L*² weak law; an
  approximation lemma from Lévy continuity; a CLT for stationary *m*-dependent sequences by
  big/small blocks; a CLT for autoregressive scores $n^{-1/2}\sum u_{t-1}\varepsilon_t$
  with $u_t=\sum_j a_j\varepsilon_{t-j}$ (U10; makes the correlogram band a 95.45% band).
  **It is not a martingale CLT**: martingale differences appear only as *L*²-orthogonality
  to a "past space", with no σ-fields. If a later unit needs a genuine martingale CLT, add
  it.
* Part IV *Maximum Likelihood*: score identities by differentiation under the integral; a
  concave maximum-likelihood theorem (existence, consistency, asymptotic normality) in
  sandwich form $\sqrt n(\hat\theta-\theta_0)\Rightarrow N(0,G^{-1}FG^{-1})$, with the
  χ² limit of $2\{\ell(\hat\theta)-\ell(\theta_0)\}$, Wald and likelihood-ratio
  corollaries under the information equality $F=G$ (U07, U08; quasi-Poisson has $F=\phi G$).
  Concavity is what keeps the proof short (curvature floor + $|U|=O_p(\sqrt n)$; no uniform
  law of large numbers).

**Deliberately not in `prereq.Rnw`.** Determinants (only the trace is used) and the
Moore–Penrose inverse (the rank-deficient case is handled by noting that R reports `NA`).
Add them from `books/ma/` when a unit first needs them.

**Proof choices to keep when rebuilding.** Unit 11 proves the cost-complexity pruning
theorem by dynamic programming ($m_\alpha(t)=\min\{R(t)+\alpha,\,m_\alpha(t_L)+m_\alpha(t_R)\}$,
every slope of $h_t$ at least 1, hence a unique $\alpha_t$ and nesting by induction on
height), which is the algorithm the packages run and lets `prune.tree`'s `k` be recomputed
to 1e−11; do not replace it with the lattice argument of `bda/note/unit05.Rnw`. Unit 10
does not prove, and says so, the $\chi^2_{K-p-q}$ limit of a portmanteau statistic on
fitted residuals (measured by simulation), the limiting law of the Dickey–Fuller $t$ (it
proves the rate is $T$ and that the limit is not normal, then simulates the critical
values), and GARCH asymptotics (the likelihood is not concave).

**Still to write.** The two exams (`exam` class with `\printanswers`, Chinese header as in
`mva/exam/1142/mid-1142.tex`; Part I about 15 SOA-style five-choice questions for 60
marks, Part II 3–4 written derivation/interpretation problems for 40 marks) and the
problem sets (`qa_mid`, `qa_final`), after the units are rebuilt and the schedule
re-planned.
