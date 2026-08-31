# ASM lecture notes — conventions, sources, and gotchas

Authoritative handoff for anyone (human or model) continuing these notes.
Read this before editing any `.Rnw`.

**A revision pass is outstanding.** All fourteen units are written and built, and the
instructor has ordered a line-by-line revision: strip non-load-bearing remarks and lead-ins,
remove every forward citation, and greatly expand the exercises. The work order, the
measured inventory, the decision rules and a per-unit checklist are in
[`REVISION.md`](REVISION.md). Do that before adding anything new.

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

Derived from `mva/note/clm.tex`, not from FREES/ISLR prose.

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
  "we now show", "in this section").

Test for a sentence: if it is not a definition, theorem, proof, or one terse factual
remark, delete it.

**Cover page:** one vertically centred line, `\fontsize{26}{32}`, nothing else — no
subtitle, rule, course name, or reading list.

## 3. The verification principle

> Add **as many comparisons as possible** between the manual formula and what the package
> produces.

Every unit has a §Computation section mirroring its theory sections, printing the
*difference* rather than asserting agreement. Where several routes to one quantity exist,
compute all of them (Unit 3 gets the joint *F* four ways; Unit 2 gets *R*²=*r*² four ways;
Unit 4 gets Cook's D two ways and WLS three ways).

**Never state a numerical claim you have not run.** Several prose claims were wrong on
first draft and only the printed output caught them (§6).

## 4. Course structure (locked)

14 teaching weeks × 3 × 50 min = 42 periods; midterm week 9, final week 16.
Linear models are developed for general *k*; *k*=1 appears as corollaries, **never** as its
own unit.

| Wk | Unit | Topic tag |
|---:|------|-----------|
| 1 | U01 Statistical Learning (incl. bootstrap) | T1×3 |
| 2 | U02 Multiple Regression I: Matrix Theory (+ *k*=1) | T2×3 |
| 3 | U03 Multiple Regression II: Inference & Interpretation | T2×3 |
| 4 | U04 Regression Diagnostics | T2×3 |
| 5 | U05 Variable Selection & Dimension Reduction | T2×2 + T5×1 |
| 6 | U06 Shrinkage, High Dimensions, KNN | T2×3 |
| 7 | U07 GLM I: categorical responses (FREES 11) | T2×3 |
| 8 | U08 GLM II: counts & exponential family (FREES 12–13) | T2×3 |
| 9 | **期中考** (U01–08) | |
| 10 | U09 Modeling Trends (FREES 7, 8.1) | T3×3 |
| 11 | U10 Autoregression & Forecasting (FREES 8.2–8.4, 9) + trees intro | T3×2 + T4×1 |
| 12 | U11 Decision Trees | T4×3 |
| 13 | U12 Ensembles | T4×3 |
| 14 | U13 Unsupervised Learning | T5×3 |
| 15 | U14 Convex Optimization, SVM, Neural Networks | beyond-syllabus ×3 |
| 16 | **期末考** (U09–14) | |

Period totals: T1 3 · T2 20 · T3 5 · T4 7 · T5 4 · beyond 3 = 42.
T4 (16.7%) and T5 (9.5%) sit **below** their SOA bands; this was a deliberate trade,
paid to trees, to fund Unit 14. Recorded in the README appendix, not hidden.

Framing: a graduate course with SRM as one input. The README leads with the course's own
structure; SRM tables are an appendix showing chapter-by-chapter coverage.

## 5. Sources (all texified and local)

| Source | Path | What it gives |
|---|---|---|
| ISLR | `research/llm_proj/books/islr/islr_NN.Rnw` | required reading |
| FREES | `research/llm_proj/books/frees/frees_NN.tex` | required reading |
| CLM / MC / MLM / GCI | `lectures/mva/note/*.tex` | U02–03 theorems and proofs; MC = matrix differentials |
| BDA units 1–7 | `lectures/bda/note/unitNN.Rnw` | u02 ridge/lasso → U06 · u03 logistic/ROC → U07 · u04 bias-var/CV → U01 · u05 trees → U11–12 · **u06 convex/SVM/NN (115 pp) → U14** · u07 PCA/clustering → U13 |
| EconometricsWithR | `research/llm_proj/books/EconometricsWithR/abridged/abridged.Rnw` | robust SEs, LPM/probit/logit, AR(1)/unit roots/ADF. Same `.Rnw` format and notation. `abridged_zh.Rnw` is a full Chinese translation. `data/` has 7 real datasets incl. `us_macro_quarterly.xlsx` |
| ptpr (Devroye–Györfi–Lugosi) | `research/llm_proj/books/ptpr/ptpr_NN.tex` | Bayes optimality (ch 2, used in U01); VC theory, trees, NN, deleted estimates |
| Baldi, *Probability* | `research/llm_proj/books/baldi_p/baldi_p_03.tex` | **Convergence chapter**: Lévy continuity, Portmanteau, Slutsky, delta method |
| Kallenberg, *FMP* | `research/llm_proj/books/kallenberg_fmp/kallenberg_fmp_06.tex` | **Lindeberg–Feller** (thm 6.13) + product-comparison and Taylor lemmas |
| Abadir & Magnus, *Matrix Algebra* | `books/ma/ma_02,07,13.tex` | matrices, eigenvalues and factorisations, matrix calculus |
| Knapp, *Basic Real Analysis* | `books/knapp_real_b/knapp_real_b_01–02.tex` | one-variable calculus, metric spaces, Bolzano–Weierstrass, Heine–Borel |
| Knapp, *Advanced Real Analysis* | `books/knapp_real_a/` | functional analysis, probability foundations |
| Boyd & Vandenberghe | `books/boyd/boyd_02,03,05.tex` | convex sets, convex functions, **Duality** (§5.3.2 = the Slater proof) |
| Bertsekas, *Convex Analysis* | `books/bertsekas_cv/cv_chap*.tex` | alternative convex-duality development |
| SOA sample questions | `lectures/asm/srm/srm_body.tex` | 71 live questions, each followed by its solution |
| SOA syllabus | `lectures/asm/syllabus/2026-09-exam-srm-syllabus.pdf` | topic weights, reading list |

Datasets: prefer `ISLR2::Boston` (always present). FREES's own datasets are **not** on disk;
quote FREES's typeset tables instead, or simulate from a known truth.

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

## 7. Files

```
asm/README.md                  course page: syllabus, 16-week schedule, SRM appendix
asm/note/asm_preamble.tex      17pt 16:9, tcolorbox theorem boxes, minted, xeCJK, macros
asm/note/asm_knitr_setup.R     minted/Verbatim hooks, output.lines, options(width = 62)
asm/note/build.py              UNITS + NOTES; --quiet --pkg-check
asm/note/REVISION.md           outstanding revision work order + per-unit checklist
asm/note/unit01–14.Rnw         built
asm/note/prereq.Rnw            Mathematical Prerequisites (the core source), built
asm/exam/1151/                 empty — exams not yet written
asm/srm/                       SOA question bank (texify project)
```

Build: `cd note && python build.py [03|prereq|…]`. One PDF per document; the
student edition was removed on the instructor's instruction.
Needs `Rscript`, `xelatex`, `bibtex`, `pygmentize`. All R packages are installed.

## 8. State and what is left

**Built and verified** — unit01 43 pp · unit02 59 · unit03 35 · unit04 47 · unit05 29 ·
unit06 77 · unit07 68 · unit08 71 · unit09 52 · unit10 91 · unit11 63 ·
unit12 46 · unit13 42 · unit14 41 · prereq 109; all 0 errors,
0 undefined references. **One PDF per document**: the student edition, its `--student` flag and the
`\studentedition` toggle were removed on the instructor's instruction.

**Added to `prereq.Rnw` for Unit 2** (§P.18, immediately after the definition of the
three laws): the corollary *the square of a $t_\nu$ is $F_{1,\nu}$*, with a three-line
proof from the definitions. Unit 2 used this identity twice (Example 2.2 and the $k=1$
remark) and the only proof of anything like it in the course was Unit 3's `cor:t2F`, i.e.
forward. Note the two are different statements: the prerequisites' is about the *laws*,
Unit 3's is about the general-$F$ *statistic* collapsing to $t^2$ when $q=1$.

**Added to `prereq.Rnw` for Unit 6** (§P.3, Convexity and Separation): *coercive
minimisation* (continuous + coercive attains its infimum; strictly convex ⇒ unique) and the
*directional characterisation of a convex minimum* (`f'(x;v) ⩾ 0` for every `v`). The second
is what lets Unit 6 derive the lasso stationarity conditions without introducing
subdifferentials, and the lasso/ridge constrained-versus-penalised equivalence reuses the
existing Slater strong-duality theorem verbatim.

**Added to `prereq.Rnw` for Unit 7.** §P.24 gained a CLT for *bounded* independent
summands with *unequal* variances (Corollary "Bounded summands with unequal variances"),
which the binary-regression score needs and the existing weighted-sums corollary, with its
common-variance hypothesis, does not cover. Part IV gained a whole section, **Maximum
Likelihood**: score identities via differentiation under the integral, then a *concave*
maximum likelihood theorem (existence, consistency, asymptotic normality, and the χ² limit
of 2{ℓ(θ̂)−ℓ(θ₀)}) for independent non-identically distributed observations, with Wald and
likelihood ratio corollaries. Concavity is what makes the proof short: the curvature floor
plus |U| = O_p(√n) puts the maximiser inside any ball, so consistency needs no uniform law
of large numbers and no subdifferentials. Units 7 and 8 both rest on it; Unit 7 verifies its
three hypotheses for logistic regression in one page.

**Added to `prereq.Rnw` for Unit 8.** §P.24 gained a **Lyapunov** CLT (bounded
(2+δ)-moments, unequal variances), because a Poisson score `Σx_i(y_i−μ_i)` is unbounded and
Unit 7's bounded-summand corollary does not reach it. The maximum-likelihood theorem was
**generalised to the sandwich form**: the limiting curvature `G` and the limiting score
variance `F` are now separate hypotheses, the conclusion is
`√n(θ̂−θ₀) → N(0, G⁻¹FG⁻¹)`, and the χ² statements for `2{ℓ(θ̂)−ℓ(θ₀)}`, Wald and the
likelihood ratio are stated under the extra hypothesis `F = G`, the information equality.
That is exactly what quasi-Poisson needs: only the *mean* is correctly specified, `F = φG`,
and the sandwich collapses to `φG⁻¹`. Unit 7 was updated to note that `F = G` holds there.

**Unit 9 needed nothing new in `prereq.Rnw`.** Everything it proves is elementary algebra
or a direct application of results already there: the closed-form
`var(β̂₁) = 12σ²/{T(T²−1)}`, the random-walk moments, `var(ȳ) = σ²(T+1)(2T+1)/(6T)`,
the discrete orthogonality of harmonics from a geometric sum, and the exact
`DW = 2(1−r₁) − (e₁²+e_T²)/Σe²`. The one place where a limit theorem would be needed, the
95% calibration of the ±2/√T correlogram band, is **not** claimed: the unit proves
`var(r̃_k) = 1/(T−k)`, notes that Chebyshev gives only 1/4, and measures the coverage by
simulation (95.6% and 95.8%). **Unit 10 closes that gap**: §2.3 derives
`√T(r₁,…,r_K)' ⇒ N(0, I_K)` from the new prerequisites section below, so the band is a
95.45% band, and Unit 9's two simulated numbers are explained rather than merely reported.
Unit 9's own text was left as it stands.

**Added to `prereq.Rnw` for Unit 10** (§P.24d, *Dependent Summands*, between
Lindeberg–Feller and the delta method). The dependence wall that Unit 9 hit is now down.
The section proves, in order: the variance of a stationary average and the resulting
*L*² weak law (`γ(k)→0 ⇒ ȳ→μ`, no independence needed); an **approximation lemma**
(if `S_n^{(p)} ⇒ Z_p` for each *p*, `Z_p ⇒ Z`, and `lim_p limsup_n P{|S_n−S_n^{(p)}|>ε}=0`,
then `S_n ⇒ Z`), proved from Lévy continuity; *m*-dependence and a **CLT for stationary
*m*-dependent sequences** by big-block/small-block, the big blocks being genuinely i.i.d.
so Lindeberg–Lévy applies unchanged; and finally a **CLT for autoregressive scores**,
`n^{-1/2} Σ u_{t-1}ε_t ⇒ N(0, τ²Γ)` for `u_t = Σ_j a_j ε_{t-j}` with `Σ|a_j|² < ∞`.
§P.27 gained a numerical check of the last one: the variance is exact at every *n*, the
*m*-dependent truncation error matches `τ⁴Σ_{j⩾m}a_j²`, and skewness and kurtosis approach
0 and 3 at the *n*^(−1/2) rate but slowly (kurtosis still 4.76 at *n* = 50).

**This replaces the martingale CLT that the Unit 9 handoff planned.** The martingale route
needs conditioning on infinite σ-fields, hence the grouping lemma for independence, hence
a π–λ argument that `prereq.Rnw` does not have and that the motto would require proving.
The *m*-dependent approximation reaches every application the course has (AR(1) least
squares with `a_j = β₁^j`; the correlogram and Ljung–Box with `a_j = 1{j = k−1}`) using
only finite independence, Fubini and the existing Lindeberg–Lévy corollary. Martingale
differences still appear, but as an *L*²-orthogonality statement about a "past space"
`L_t` (the closure in *L*² of square-integrable functions of finitely many `ε_u`, `u ≤ t`),
which needs no σ-fields at all. **If a later unit needs a genuine martingale CLT, add it;
do not assume this section already is one.**

**What Unit 10 deliberately does not prove**, and says so in the text:
the `χ²_{K−p−q}` limit of a portmanteau statistic on *fitted* residuals (measured by
simulation instead: mean *Q* at *K*−1 with one fitted coefficient, at *K*−4 with four);
the limiting law of the Dickey–Fuller `t` statistic (a Brownian functional; the unit
*does* prove the rate is *T* not √*T*, and that `T^{-1}Σy_{t-1}ε_t ⇒ (σ²/2)(χ²₁−1)`, which
is enough to show the limit is not normal, then simulates the critical values); and the
asymptotics of GARCH estimation (the likelihood is not concave, so §P.ML does not apply).

**Two defects in already-built units were found by gotcha 37 and repaired.** The scan for
`## Error` in the built `.tex` files, run retroactively over every unit, hit two:

* `unit04` §4.6.4: `Xh` and `V_hc1` were never defined, so all five chunks of the weighted
  least squares comparison errored and the PDF printed `object 'Xh' not found` where the
  three-way agreement should have been. Fixed by adding `Xh <- cbind(1, xh)` and
  `V_hc1 <- vcovHC(mh, type = "HC1")`. With the numbers finally printing, the exercise's
  claim that the ordering is "WLS smallest, then HC1 and OLS" turned out to be wrong: HC1
  is larger than OLS on the slope and *smaller* on the intercept. Reworded.
* `unit05` §5.5.2: the chunk indexed the data frame by `names(coef(rs, j))`, which are
  `regsubsets`'s dummy-column names (`DivisionW`) and not columns of `d`, so it errored.
  Worse, **the pitfall's claim was false**: with the ISLR §6.1.3 form
  `C_p = {RSS + 2(d+1)σ̂²}/n`, substituting the candidate's own `σ̂²` gives
  `(RSS_d/n)(n+d+1)/(n−d−1)`, which still penalises size and on `Hitters` picks the same
  model (10) as the correct version. The degeneracy belongs to the **standardised** form
  `C_p = RSS_d/σ̂² − n + 2(d+1)`, where the substitution gives exactly `d+1`, a function of
  size alone that always picks the smallest model. Rewritten with that algebra, verified to
  2.8e−14, and the ISLR form's non-collapse stated explicitly.

**Both had been reported as built and verified.** The lesson is gotcha 37: a green build
means LaTeX compiled, not that the R ran.

**Units 13 and 14 needed nothing new in `prereq.Rnw`.** Unit 13 uses the SVD (§P.10) for
Eckart--Young, the spectral theorem and its Rayleigh corollary for the variance
characterisation Unit 5 already proved, Jensen for the impurity-style arguments, and Unit
10's analysis-of-variance identity for the within/between decomposition. Unit 14 is the
payoff of §§P.3--P.3b: the SVM dual, strong duality under affine constraints, and
complementary slackness are all direct applications, and coercive minimisation gives
existence of the optimal hyperplane. Backpropagation is §P.11's chain rule.

**Unit 12 needed nothing new in `prereq.Rnw`.** The variance-of-an-average theorem is one
line of algebra; the majority-vote bound is Chebyshev; the boosting operator uses the
spectral theorem and Taylor, both already there. Unit 1's out-of-bag fraction proposition is
cited by name, and its closing remark was corrected from "(Unit 11)" to "(Unit 12)", bagging
having moved.

**Unit 11 needed nothing new in `prereq.Rnw`.** Everything it proves is elementary: the
value function of cost-complexity pruning is a minimum of finitely many affine functions,
hence concave and piecewise linear; the impurity results are Jensen on the simplex; the
staircase bound is Jensen on `u ↦ u³`; and the two-class Gini identity and the categorical
ordering theorem both reduce to Unit 10's analysis-of-variance identity.

**The pruning theorem is proved by dynamic programming, not by the pruning lattice.**
`bda/note/unit05.Rnw` §5.2.3 proves the same theorem through modularity of `R_α` on the
lattice of pruned subtrees; both proofs are correct. Unit 11 uses the recursion
`m_α(t) = min{R(t)+α, m_α(t_L)+m_α(t_R)}` instead, from which `h_t(α) = m_α(t_L)+m_α(t_R)
− R(t) − α` has every slope ⩾ 1, so it is strictly increasing and has a unique zero `α_t`.
That is shorter, needs no lattice theory, gives nesting by induction on height in three
lines, and **is the algorithm the packages run**, so §4.1 can recompute `prune.tree`'s `k`
from it to 1e−11. Do not replace it with the lattice argument.

**Outstanding before anything new: the revision pass of `REVISION.md`.** 204 remarks to
triage, 76 in-unit forward `\ref`s and 25 forward `Unit M` mentions to remove, and 154
exercises to expand to roughly 20–26 per unit. **Unit 1's twelve forward `Unit M` mentions
are exempt by instructor decision** and stay as they are; everything else goes. `remark` is `\newtheorem*`, so deleting
remarks shifts no numbering and breaks no `\ref`; only units 02, 12 and 14 use
`\ref{ex:...}` at all. Do not delete or merge `\subsection`s, which would move `sec:N.x`
labels (gotcha 12).

**To write** — the two exams; problem sets (`qa_mid`, `qa_final`);
an SRM question→unit map. **All fourteen units are now written and built.**

**Deliberately not yet in `prereq.Rnw`.** Determinants (only the trace is used so far) and
the Moore–Penrose inverse (the rank-deficient case is currently handled by noting that R
reports `NA`). Add them from `books/ma/` when the multivariate-normal density, the GLM
likelihood, or the singular design case first needs them.

**Known duplication.** Units 01–02 still prove in place four results that now also live in
`prereq.Rnw`: Sherman–Morrison (U01), matrix differentiation, trace = rank, and the
multivariate-normal/χ² results (U02). The intended end state is that the units cite them by
name and the proofs live only in the prerequisites. Not yet done.

**Exam format (decided, not yet built):** `exam` class with `\printanswers` toggle,
Chinese header in the style of `mva/exam/1142/mid-1142.tex`; Part I ≈ 15 SOA-style
five-choice questions (60 marks), Part II 3–4 written derivation/interpretation problems
(40 marks).
