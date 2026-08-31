# PAPER-SPECIFIC OVERLAY — srm structural registry (HAND-VERIFIED against the source)

Society of Actuaries, *Exam SRM — Statistics for Risk Modeling: Sample Questions and
Solutions*, February 2026 revision. 75 pages.

Every fact below was read off the **page images** (all 75 rendered at 150 dpi; the `φ` on p56
and the suspected typos re-cropped at 340–600 dpi). This source is **born-digital** (Word →
Acrobat PDFMaker), so its text layer is honest about characters — but it is produced by
Word's equation editor and is **useless about structure**: it breaks one displayed formula
into a dozen spans in the wrong reading order, emits `…` and `⋯` as private-use glyphs of the
"MT Extra" font, and renders `μ` as U+00B5 MICRO SIGN. **Read the page.**

## ⚠ THIS IS NOT A PAPER AND NOT A BOOK — it is a question sheet

There is **no prose narrative** here at all. The source is a flat numbered list: 75
multiple-choice questions, then 75 solutions. Accordingly:

- **NEVER emit `\chapter`.** The master is `article`-class; `\chapter` is undefined and would
  be a hard compile error.
- **NEVER emit `\section`, `\subsection`, `\section*` or any other heading.** There are no
  headings in this source below the two centred half-titles, and those have their own macro
  (`\srmpart`, below). In particular the map's bracketed section titles — `[Q33]`, `[S51]` —
  are **chunking hints for the machinery, not headings**: they mark pages whose top starts a
  fresh item so a chunk boundary never falls inside one. They must not appear in the output
  in any form.
- **NEVER emit a numbered `equation`, `align`, `\label{eq:…}` or `\eqref`.** Not one display
  in this source carries a number. Every display is unnumbered: `\[ … \]`, or `align*` when
  it has several aligned lines.
- **There is no `theorem`, `lemma`, `proposition`, `corollary`, `definition`, `example`,
  `remark` or `proof`** anywhere, and no `figure`/`table` FLOAT (see §Figures and §Tables).
- **There is no bibliography and no `\cite`.** See §Citations.

## The four environments — this is the whole structure

`assets/preamble.srm.tex` defines them. Nothing else is available and nothing else is needed.

| element | what it wraps | emit |
|---|---|---|
| a question | one numbered question, stem through choices | `\begin{question}{33}` … `\end{question}` |
| a solution | one numbered solution, key through working | `\begin{solution}{33}{E}` … `\end{solution}` |
| the choices | the five lines "(A)"…"(E)" | `\begin{choices}\item …\end{choices}` |
| a statement list | the lines "I." "II." "III." (["IV."]) | `\begin{statements}\item …\end{statements}` |
| a "given" list | the lines "i)" "ii)" "iii)" "iv)" | `\begin{given}\item …\end{given}` |

**The number is a mandatory argument, taken from the page.** `\begin{question}{33}` prints
"**33.**". Do **not** type the number into the body as well, and do **not** rely on it
auto-incrementing — it does not.

`\begin{solution}{N}{K}` takes the number **and the key letter**. `K` is the single letter
after "Key:" on the page. **Emit the head from the argument only** — do not also transcribe
the words "Key: E" into the body, or they print twice.

### The canonical shape of a question

Question 3 (p3), complete, as the pattern to follow:

```latex
\begin{question}{3}
You are given:
\begin{given}
\item The random walk model
\[ y_t = y_0 + c_1 + c_2 + \cdots + c_t \]
where $c_t,\, t = 0,1,2,\ldots,T$ denote observations from a white noise process.
\item The following nine observed values of $c_t$:
\begin{center}
\begin{tabular}{|c|c|c|c|c|c|c|c|c|c|}
\hline
$t$   & 11 & 12 & 13 & 14 & 15 & 16 & 17 & 18 & 19 \\ \hline
$c_t$ & 2  & 3  & 5  & 3  & 4  & 2  & 4  & 1  & 2  \\ \hline
\end{tabular}
\end{center}
\item The average value of $c_1, c_2, \ldots, c_{10}$ is 2.
\item The 9 step ahead forecast of $y_{19}$, $\hat{y}_{19}$, is estimated based on the
observed value of $y_{10}$.
\end{given}

Calculate the forecast error, $y_{19} - \hat{y}_{19}$.

\begin{choices}
\item 1
\item 2
\item 3
\item 8
\item 18
\end{choices}
\end{question}
```

Note what is *not* there: no heading, no number typed in the body, no `\label` (the
environment writes it), no float, no caption.

### The canonical shape of a solution

```latex
\begin{solution}{4}{B}
$c_t = y_t - y_{t-1}$ and hence $c_1, c_2, \ldots c_{10} = 2,3,5,3,5,2,4,1,2,3.$

The mean of the $c$ values is 3, the variance is $(1+0+4+0+4+1+1+4+1+0)/9 = 16/9$. The
standard deviation is 4/3. The standard error of the forecast is $(4/3)\sqrt{9} = 4$.
\end{solution}
```

## The registry: 75 questions, 75 solutions, 4 of them withdrawn

**Emit exactly 75 `question` environments and exactly 75 `solution` environments**, numbered
1 … 75 with no gap and no repeat, in printed order.

**Questions 17, 28, 47 and 65 were withdrawn** (the p1 log: *"August 2023 update: … Questions
17, 28, 47, and 65 were deleted (no longer on the syllabus)"*). The source still prints each
number, followed by the bare word DELETED and nothing else — no stem, no choices. Emit:

```latex
\begin{question}{17}
\deleted
\end{question}
```

and, on the solutions side, `\begin{solution}{17}{}` with the same one-macro body. `\deleted`
prints DELETED; **do not type the word**, and do not invent a stem or choices for these four.

### Answer keys — the second argument of every `solution`

Take the letter from the page. All 71 live ones, for checking your own reading:

```
 1 E   2 C   3 D   4 B   5 E   6 E   7 —   8 D   9 E  10 C  11 E  12 E  13 E  14 B  15 D
16 D  17 —  18 B  19 E  20 C  21 C  22 A  23 C  24 C  25 C  26 A  27 C  28 —  29 E  30 D
31 D  32 E  33 E  34 B  35 B  36 D  37 B  38 D  39 E  40 C  41 B  42 E  43 D  44 C  45 C
46 D  47 —  48 B  49 C  50 B  51 C  52 D  53 A  54 C  55 B  56 B  57 A  58 C  59 C  60 C
61 D  62 A  63 D  64 E  65 —  66 D  67 D  68 E  69 C  70 C  71 C  72 C  73 B  74 C  75 D
```

**⚠ Solution 7 has NO key line** (p58). It opens straight into "The intent is to model a
binary outcome…". Emit `\begin{solution}{7}{}` — an **empty** second argument. Do not work
out what the key should have been and do not write one in.

**The three odd spellings are NORMALISED, not reproduced.** The source prints "Key: E" 68
times, but "Key E" once (solution 13, no colon) and "Key:D" twice (solutions 66 and 75, no
space). The head is re-typeset from the letter, so all three come out "Key: X". This is the
**one** deliberate departure from reproduce-what-is-printed in this conversion, and it is
confined to a structural label the environment sets. Everything else on the page — including
every typo in §Errata — is reproduced exactly.

## Answer choices: always five, always (A)–(E)

**Every one of the 71 live questions has exactly five choices, lettered (A) through (E).**
There is no exception in the whole source. The `choices` environment supplies the letters
from `\Alph*`, so:

- emit exactly five `\item`s per question — a dropped one silently re-letters every choice
  after it, and the answer key then points at the wrong text;
- do **not** type "(A)" into the item text;
- do **not** reorder them.

A choice may itself contain a display, a table or a picture — question 48's five choices are
each a *picture* (see §Figures), and question 66's are each a five-line block. Set those as
ordinary item content; `\item` takes anything.

Where the source's own choice text quotes the letters — "(E) The correct answer is not given
by (A), (B), (C), or (D)." — those are **literal text inside the item**, never `\ref`.

## Statement lists and "given" lists

- `statements` prints "I.", "II.", "III." — and "IV." where the source has four (questions
  **5**, **6** and **74** only). Roman numerals with a following **full stop**.
- `given` prints "i)", "ii)", "iii)", "iv)" — lower-case roman with a **closing paren only**,
  no opening paren and no full stop. That is how the source sets its "You are given:" items
  (questions 3, 4, 54, 62 and the two halves of 57).
- Where the source uses a **bullet** instead (questions 19, 23, 27, 68, 69), use `itemize`.
- Where it uses a hanging label the lists cannot give — "Split 1:" / "Split 2:" (question 9),
  "Model L:" / "Model M:" (question 38), "X:" / "Y:" / "Z:" (question 51), "I:" / "II:" /
  "III:" (question 33) — set those as ordinary paragraphs or a `description`, not by forcing
  them into `statements`.

## Figures — 17 of them, already cropped; place them by KEY

The figures are **already extracted** by `texify_figs_srm.py` into `assets/figs/`. Place one
with **`\srmfig{<key>}`** and nothing else:

```latex
\srmfig{q35}
```

**Do NOT** emit `\begin{figure}`, `\includegraphics`, `\caption`, `\label{fig:…}`, or the
pipeline's usual `<book>_<NN>_figs.pdf` + `page=<k>` template. This source captions nothing —
a figure is simply artwork sitting between two paragraphs of a question — so a float with an
invented caption would put text on the page that the source does not have, and a float would
also let LaTeX move the picture away from the sentence that says "the following scree plot".
`\srmfig` sets it in place, centred, at natural size (shrunk to the measure if wider).

**The complete inventory. A question not listed here has no figure.**

| key | question | page | what it is | where it goes |
|---|---|---|---|---|
| `q26a` | 26 | 19 | the two-rectangle space | after the "I." label |
| `q26b` | 26 | 19 | the curved boundary | after the "II." label |
| `q26c` | 26 | 19 | the diagonal boundary | after the "III." label |
| `q33` | 33 | 23 | auto-claim regression tree | after the stem, before "Consider three autos" |
| `q35` | 35 | 25 | scree plot | after "Consider the following scree plot." |
| `q39` | 39 | 29 | scatter plot | after the stem |
| `q48` | 48 | 35 | the tree | after the stem, before "Determine which of the following plots" |
| `q48a` | 48 | 35 | choice (A)'s plot | **inside** choices `\item` 1 |
| `q48b` | 48 | 35 | choice (B)'s plot | **inside** choices `\item` 2 |
| `q48c` | 48 | 35 | choice (C)'s plot | **inside** choices `\item` 3 |
| `q48d` | 48 | 35 | choice (D)'s plot | **inside** choices `\item` 4 |
| `q48e` | 48 | 35 | choice (E)'s plot | **inside** choices `\item` 5 |
| `q51` | 51 | 37 | duck-weight regression tree | after the stem, before "You predict the weight" |
| `q57` | 57 | 42 | the T1–T4 regression tree | after the "ii)" item's text |
| `q63` | 63 | 47 | car-seat regression tree | after the stem, before the Variable/Observed Value table |
| `q66` | 66 | 49 | the R1–R5 regression tree | after the stem |
| `q73` | 73 | 55 | MSE-vs-tree-size line chart | after "The graph provides the Mean Squared Error…" |

⚠ **Question 26's three panels are the three roman items, and question 48's five are the five
choices.** On p19 the labels "I.", "II." and "III." sit outside the pictures; keep them as the
`statements` labels and put the picture in the item. On p35 the labels "(A)"–"(E)" likewise
sit outside; they are the `choices` letters and the picture is the item's body — the item text
is **the picture and nothing else**.

⚠ **Do not transcribe a figure's contents into text.** The node values of a regression tree,
the axis ticks of a scree plot and the shaded regions of question 26 are in the picture. A
"helpful" table of them is content the source does not have.

## Tables — a plain `tabular`, never a float

There are **19** tables: **18 in the questions** — one each on pp. 3, 4, 10, 13, 20, 27, 33,
34, 39, 40, 42, 43, 44, 47, 51, 52, 53, 54 (questions 3, 4, 11, 15, 27, 37, 45, 46, 54, 55,
57, 58, 59, 63, 68, 69, 70, 72) — and **1 in the solutions**, in solution 15 on p60.

Every one is a Word table with **visible rules on all four sides and between every cell**, so
reproduce them with `|` column separators and `\hline` on every row — not `booktabs`, which
would drop the vertical rules the source draws. Centre them in a `center` block.
**No `\begin{table}`, no `\caption`, no `\label{tab:…}`**: the source captions and numbers
none of them, and a float would move it away from its question.

Header cells are set **bold** in questions 27 and 63 and **roman** everywhere else; follow the
page. Where a header is mathematics — `$t$`, `$c_t$`, `$y_t$`, `$\hat{s}^{(1)}_t$`, `$R$`,
`$X$`, `$Y$`, `$Z$` — set it in math mode.

## Front matter (p1) — reproduce it, all of it

Page 1 is its own division. It carries, centred: "SOCIETY OF ACTUARIES", then two bold lines,
then a left-aligned paragraph and **18 dated update lines**, then the copyright line.
Reproduce the whole page — the log is the source's own record of which questions were added,
modified and deleted, and it is why four numbers print DELETED.

```latex
\begin{center}
  {SOCIETY OF ACTUARIES\par}
  \vspace{1.2em}
  {\bfseries EXAM SRM - STATISTICS FOR RISK MODELING\par}
  \vspace{1.2em}
  {\bfseries EXAM SRM SAMPLE QUESTIONS AND SOLUTIONS\par}
\end{center}
\vspace{1em}

These questions and solutions are representative of the types of questions that might be
asked of candidates sitting for Exam SRM. …
```

then the log lines as ordinary paragraphs, one per line, in printed order, ending with
"Copyright 2026 by the Society of Actuaries". Note the printed hyphen (not an en dash) in
"EXAM SRM - STATISTICS FOR RISK MODELING", and that the LAST FIVE log lines end **without** a
full stop (the August 2023, July 2024, February 2025, July 2025 and February 2026 entries) —
reproduce that.

The **folio** at the foot of every page is publisher furniture: skip it, on all 75 pages.

## The two half-titles

p2 prints a centred bold **QUESTIONS** and p57 a centred bold **SOLUTIONS**. Emit each, once,
at the very top of its division, as:

```latex
\srmpart{QUESTIONS}
```

Nothing else in the source is a heading. (`texify_qa_merge.py` keeps or drops these depending
on the output order; that is not your concern — emit them where the page shows them.)

## Which division you are converting, and what a continuation chunk means here

The source is converted in three divisions and nine chunks. Tell them apart from the pages
you are given:

- **the title page** → the front matter (§Front matter). One chunk, one page.
- **pages carrying numbered items with (A)–(E) choices** → the questions. Six chunks.
- **pages carrying "Key:" lines and worked arithmetic** → the solutions. Two chunks.

**⚠ EVERY CHUNK BEGINS WITH A FRESH NUMBERED ITEM.** The map places its chunk boundaries at
pages whose top starts a new question or a new solution, precisely so that no chunk ever
opens in the middle of one. So when the task says *"this PDF continues a previous chunk"*:

- there is **no open environment** to close and none to continue — begin with
  `\begin{question}{N}` (or `\begin{solution}{N}{K}`) for the number at the top of your first
  page, and nothing before it;
- **do not re-emit the previous chunk's last item.** The number at the top of your first page
  is the first one you convert;
- **do not emit `\srmpart`.** The half-title is printed on p2 and p57 only; if you cannot see
  it on your own pages, it is not yours to emit.

The one page in the whole source that does not start an item is **p50**, where question 66's
choices (D) and (E) run over from p49 — and the map keeps both pages inside one chunk, so you
will always be given them together.

## Mathematics and notation

- **Every variable is italic math**: `$y_t$`, `$c_t$`, `$\beta_0$`, `$R^2$`, `$X_1$`,
  `$p$`-value, `$n = 100$`. The source's equation editor occasionally sets one **upright** by
  accident — the `z` in `π(z)` in question 42(C) is the clearest case, where the very next
  choice sets the same letter italic. That is a Word artifact, not notation: **set it italic.**
- **Inequalities are `\leqslant` / `\geqslant`**, never `\leq` `\geq` `\le` `\ge`. This is the
  house rule from the general contract and it binds here even though the source prints the
  upright ≤ ≥.
- **Expectation and variance use the house macros — in ALL FIVE places, no exceptions.** The
  preamble patch points `\expc` and `\var` at the source's own italic `E` and `Var`, so they
  print exactly what the page prints; the macro is what keeps the notation uniform. **Never
  `\mathbb{E}`, never `\mathrm{Var}`, and above all never a bare italic `E(\cdot)` or
  `Var(\cdot)`** — a bare `E(` renders identically and is therefore invisible on the page, so
  nothing but a scan of the source can catch it. It has been got wrong exactly once, on the
  first of the five:

  | where | the page prints | emit |
  |---|---|---|
  | **Q13, statement III** (p11) | `E(y|x)` | `$\expc(y \mid x)$` |
  | **Q21, the "where" display** (p16) | `E(c_t) = μ_c` and `Var(c_t) = σ_c²` | `\expc(c_t)`, `\var(c_t)` |
  | **Q58, the model display** (p43) | `Var(ε_t) = σ²` | `\var(\varepsilon_t)` |
  | **S21, I** (p62) | `E(y_t) = y_0 + tμ_c` | `\expc(y_t)` |
  | **S21, II** (p62) | `Var(y_t) = tσ_c² = 0` | `\var(y_t)` |

  Three in the questions, two in the solutions, and that is the complete list. Nothing else in
  the source is a probability operator — there is no `\prb`, no `\cov`, no `\cor`, no
  indicator.
- **A CATEGORY VALUE IS NOT A VARIABLE: set it upright.** Question 57 and its solution use
  three categorical predictors whose *values* are single letters — `X` takes M or F, `Y` takes
  A, B, C or D — and the source sets the variable italic and the value **roman**, in the table
  and in the prose alike. So `$X = \mathrm{F}$`, `$Y = \mathrm{A}$ or `$\mathrm{B}$`, and the
  table cells carry plain `M`, `F`, `A`, `D` with no math mode at all. Writing `$Y = A$ or $B$`
  italicises the values and makes them read as two more variables. The same holds for the end
  nodes `T1`–`T4`, which are node *names*: `MR(T1)`, upright.
- **Greek, exactly as the source uses it:** `\beta` (regression coefficients, by far the
  commonest), `\varepsilon` (the error term — the source's glyph is the rounded ε, so
  `\varepsilon`, **not** `\epsilon`), `\sigma` (`\sigma_c^2`, `\sigma^2`, `\hat{\sigma}^2`),
  `\mu` (`\mu_c`, `\mu`), `\lambda` (the shrinkage parameter of questions 68/69 and the
  Tweedie mass of 75), `\alpha` (the pruning parameter of question 25 and the significance
  level of 54), `\pi` (the logit/probit function of question 42), `\Phi` (the standard normal
  CDF, same question), `\phi` (question 75's dispersion parameter — the **loopy** phi,
  confirmed at 600 dpi; **not** `\varphi`).
- **Hats and bars**: `\hat{y}_{19}`, `\hat{f}(x_i)`, `\hat{s}^{(1)}_t`, `\hat{\sigma}^2`,
  `\hat{\beta}`, `\bar{y}`, `\bar{e}`.
- **⚠ AN INDEXED VARIABLE IS ALWAYS SUBSCRIPTED: `$X_1$`, never `$X1$`.** The source is
  inconsistent about this and you must not follow it. It sets true subscripts `X₁`, `X₂` in
  question 66 and solution 66, but full-size baseline digits in **question 59**'s table header
  and **solution 59**'s prose (`X1`, `X2` — an equation object with the digit at 12pt, not
  8pt), and in **question 70** it does not open an equation object at all and simply types
  `X1, X2, X3, X4, X5, and X6` in the roman body font. All of these name the same kind of
  object — the *i*-th predictor — so all of them are `$X_1$`, `$X_2$`, … Emitting `$X1$`
  where the page happens to show one and `$X_1$` two questions later makes the document
  disagree with itself about its own notation.

  This is the SECOND and last documented departure from reproduce-what-is-printed here (the
  first is the "Key:" spelling). It is confined to the arrangement of a digit that carries no
  content, and it is asserted by `verify.py`, which fails on any unsubscripted `X` + digit.

  **The exception is `T1`–`T4` in question 57 and solution 57**, which are NODE NAMES, not
  indexed variables — the tree's end nodes are called T1, T2, T3, T4. Leave those exactly as
  printed, upright and unsubscripted, as `MR(T1)`.
- **The two ellipses.** `\ldots` on the baseline in a list of terms — `$t = 0,1,2,\ldots,T$`,
  `$c_1, c_2, \ldots, c_{10}$` — and `\cdots` raised in a sum: `$y_0 + c_1 + c_2 + \cdots +
  c_t$`. The text layer renders both as private-use glyphs of the "MT Extra" font
  (`U+F04B` = `\ldots`, `U+F04C` = `\cdots`); go by the image, where the distinction is plain.
- **A leading `–` before a number is a MINUS SIGN**, not an en dash. The source uses U+2013 and
  U+2212 interchangeably for it ("–45,765,767.76", "–0.549", "= –10.01"): emit `$-45{,}765{,}767.76$`
  in math, or `$-0.549$` in a table cell. A dash *between* two numbers ("Questions 29-32",
  "a 0-10 scale", "items A-D") is a printed hyphen — keep it as `-`.
- **Thousands separators are printed commas** — 183,663.30 / 1,836.42 / 45,765,767.76 — and
  must survive: in math mode write `183{,}663.30` so the comma does not pick up list spacing.
- **`<` and `>` MUST be in math mode**, always, even in the middle of a sentence. In text mode
  the default font maps them to `¡` and `¿` — a wrong glyph that compiles silently and looks
  like nothing anyone typed. So "for large sample sizes ($n > 7$)" and "the estimated slope is
  $-1.03$", never a bare `n > 7`. The same goes for `|` (write `\mid` or `\vert` inside math,
  as in `$\{X \mid X_1 \leqslant 5\}$`) and for a literal `%`, `&`, `_`, `#` or `$` in prose,
  which must be escaped.
- **`ln`, `exp`, `log`, `lim`** are operators: `\ln`, `\exp`, `\log`, `\lim_{n \to \infty}`.
  Question 49's two limits set `n \to \infty` **under** the operator, as LaTeX does by default
  in a display — keep them in `\[ … \]`, not inline.
- **A wide display that the source wraps onto two lines is still ONE formula.** Solution 58
  sets $b_1$ with a numerator broken over two lines and $s^2$ likewise; reproduce the break
  with an `array` inside the numerator (`\dfrac{\begin{array}{c} … \\ … \end{array}}{…}`) so
  it fits the measure, exactly as the page does. Do **not** split it into two displays and do
  **not** run it off the right margin.

## Citations — there are none

This source has **no reference list**. It names its textbooks in running prose, with the title
in italics and the page as ordinary words:

- "See Page 242 of *Regression Modeling with Actuarial and Financial Applications*." (sol 31)
- "See Section 8.1 of *An Introduction to Statistical Learning*." (sol 29)
- "(See Section 10.3 of *An Introduction to Statistical Learning*.)" (sol 32)
- "See formula (7.8) in the Frees text." (sol 38) — and "page 243 in the Frees text"
- "see page 307 of Frees" (sol 42); "See Page 348 of Frees." (sol 52); "Page 254 of Frees"
  (sol 64); "Per Frees (page 197)" (sol 71)
- "(see Page 63 of James, et al.)" (sol 53)
- "per equation (10.12) in the first edition of *ISLR*" (sol 59)

**Every one of these is TEXT.** Emit the title in `\textit{…}` where the page italicises it
and the rest as ordinary words. **Never `\cite`, never `\ref`, never `\eqref`** — the numbers
in "formula (7.8)", "Section 8.1", "equation (10.12)", "Page 242" belong to *other books*, so
a `\ref` to them would dangle. There is no `.bib` in this repo and the master emits no
bibliography.

## ⚠ Errata: 20 printed slips, every one reproduced as printed

The general contract's `% SIC` rule governs. Reproduce what the page shows and put a `% SIC:`
comment immediately above it saying what the source has and what was meant. **Do not silently
repair any of these** — a silent correction is invisible to the next reader.

**⚠ A `% SIC:` note belongs ONLY above a slip you are actually reproducing, on the item that
carries it.** Do not annotate an item to say an erratum does *not* apply to it, and do not
leave any other commentary, reasoning or note-to-self in the output. The list below is
indexed by item number: item 37 of the QUESTIONS and item 37 of the SOLUTIONS are different
things, and only the latter has a slip. (A first conversion left
`% SIC: source prints "of" for "or" in Sol 37 II; not applicable here — this is Q37.` sitting
inside question 37. It renders as nothing, which is exactly why it survives every check.)

### In the questions

1. **Q2, choice (D): `I, II and II`** (p2) — the third numeral is a **II**, not III. Every
   other question's analogous choice reads "I, II, and III".
   `% SIC: source prints "I, II and II"; means "I, II and III".`
2. **Q16, choice (E): `None of (A), (B), (C), or (D) meet the meet the stated criterion.`**
   (p14) — "the meet the" is genuinely doubled.
3. **Q30, stem: `is/are true with respect the loadings`** (p21) — "to" is missing.
4. **Q31, stem ends without a full stop**: "…can be represented as a random walk" (p22).
   Every other stem ends with one.
5. **Q45, stem ends without punctuation**: "…resulting in the following estimated
   coefficients" (p33), immediately followed by the table.
6. **Q64, stem: `Determine which or the following is always true.`** (p48) — "or" for "of".
7. **Q66, stem: an unclosed parenthesis** (p49) — "You are given the following regression tree
   (where the inequality represents the values in the left-hand branch of a split." There is
   no closing `)`.
8. **Q66, choice (E), Region 1: a missing closing brace** (p50) — `{X| X_1 \leqslant 5, X_2
   \leqslant 40` where every other region closes with `}`.
9. **Q66, choice (E), Region 3: the `>` is set at SUBSCRIPT SIZE** (p50), so the line prints as
   though it read `X_{1 >} 5`. The characters are `X_1 > 5`; only the size is wrong, and it is
   a Word artifact. Emit `$\{X | X_1 > 5,\ X_2 \leqslant 60\}$` with
   `% SIC: source sets the ">" at subscript size (Word artifact); the relation is X_1 > 5.`
10. **Q73, the lead-in ends with a comma**: "Determine the tree size of the optimal pruned
    tree," (p55).

### In the solutions

11. **Sol 21, II: `does not depend in t`** (p62) — "in" for "on".
12. **Sol 26: `Each step must divide the one the existing regions into two parts`** (p63) —
    "the one the" is garbled; it means "one of the existing regions".
13. **Sol 27: `Only variables with a p-value greater than 0.05 should be considered.`** (p64)
    — reads oddly (it means *considered for removal*) but it is a complete, printed sentence.
    **Leave it exactly as printed and do not add a `% SIC`** — it is not a typo, and marking
    it as one would be a judgement the page does not support.
14. **Sol 37, II: `The presence of absence of scaling`** (p66) — "of" for "or".
15. **Sol 51: `Prediction = 1.25.`** (p69) — the unit "kg" is missing; the same paragraph's
    other two predictions print "0.90 kg" and "0.80 kg".
16. **Sol 61, III: `will select a number less than equal to that selected by AIC`** (p72) —
    "or" is missing.
17. **Sol 62: `produces and interval of –1.03  ± 2(0.06)`** (p72) — "and" for "an". Note also
    the doubled space before the `±`, which is not worth reproducing.
18. **Sol 66: `X_1 must be .> 10`, twice** (p73) — a stray full stop before the `>`, on the
    Region 4 line and again on the Region 5 line. The stop is text and the relation is
    mathematics, so emit them as such:

    ```latex
    % SIC: source prints a stray "." before the ">", on this line and the next.
    To be in Region 4, $X_1$ must be .$> 10$ and $X_2$ must be $\leqslant 60$.
    ```

    The first line of the same solution ("This eliminates answer C") also ends **without** a
    full stop while the second ("This also eliminates answer C.") has one.
19. **Sol 69: `The initial fitted values are all zero They are updated by adding`** (p74) —
    the full stop after "zero" is missing.
20. **Sol 70: `[183,663.30 + 2(1)(89.45755]/100`** (p74) — an opening `(` closed by a `]`.
    The same slip repeats in Model II (`2(2)(89.45755]`) and Model III (`2(6)(89.45755]`).
    Reproduce all three brackets as printed.

Also note, and do **not** tidy: solutions 32 and 33 are printed with **no blank line between
them** (p65); solution 39 labels its choices "(A) is false" while solution 56 labels the same
thing "A is false"; solution 12 uses "A is false" and solution 16 uses "(A) For $K$-means".
Follow each page.

## Counts to check your own work against

State these to yourself before you finish a chunk:

- **75 questions**, numbered 1–75, no gaps, no repeats.
- **75 solutions**, likewise.
- **4 DELETED** on each side: 17, 28, 47, 65.
- **71 × 5 = 355 answer choices**, five per live question, always (A)–(E).
- **17 `\srmfig` calls**, on questions 26 (×3), 33, 35, 39, 48 (×6), 51, 57, 63, 66, 73.
- **19 tables** — 18 in the questions, 1 in the solutions (solution 15).
- **1 solution with an empty key argument** (solution 7); 70 with a letter.
- **0 occurrences** of `\chapter`, `\section`, `\cite`, `\ref`, `\eqref`, `\label{eq:`,
  `\begin{figure}`, `\begin{table}`, `\caption`, `\includegraphics`, `\begin{equation}`.
