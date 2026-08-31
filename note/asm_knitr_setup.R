# =============================================================================
#  asm_knitr_setup.R
#  Shared knitr configuration for 精算統計模型 course units.
#  -----------------------------------------------------------------------------
#  Sourced by every unitNN.Rnw inside its <<setup, include=FALSE>>= chunk:
#
#    <<setup, include=FALSE>>=
#    source("asm_knitr_setup.R")
#    knitr::opts_chunk$set(fig.path = "figs/unit03-")
#    @
#
#  render_sweave() replaces knitr's default framed/highlighting wrappers, which
#  conflict with minted's catcode handling (any "#" inside an R comment breaks
#  the build otherwise). Sinput / Soutput are redirected to minted / Verbatim
#  through the hooks below. Carried over from bda/note/bda_knitr_setup.R; the
#  only ASM change is the default figure size, tuned for the wider two-column
#  layouts this course uses for its regression-output pages.
# =============================================================================

library(knitr)

knitr::render_sweave()

knitr::opts_chunk$set(
  fig.path   = "figs/",
  fig.align  = "center",
  fig.width  = 6.4,           # tuned for the 257mm x 144.5mm slide format
  fig.height = 3.0,
  out.width  = "0.78\\linewidth",
  dev        = "cairo_pdf",
  echo       = TRUE,
  message    = FALSE,
  warning    = FALSE,
  prompt     = FALSE,
  comment    = "##"
)

# Source hook: render every chunk through minted, defaulting to language "r"
# when no engine option is supplied. Optional chunk options:
#   linenos        : TRUE/FALSE, override the global linenos setting
#   firstnumber    : integer or "last" (continue numbering from previous block)
#   highlightlines : string such as "{5-7,10}" to shade specific lines
knitr::knit_hooks$set(source = function(x, options) {
  lang <- options$engine
  if (is.null(lang) || lang == "R") lang <- "r"

  mopts <- character()
  if (!is.null(options$linenos)) {
    mopts <- c(mopts, if (isTRUE(options$linenos)) "linenos" else "linenos=false")
  }
  if (!is.null(options$firstnumber)) {
    mopts <- c(mopts, paste0("firstnumber=", options$firstnumber))
  }
  if (!is.null(options$highlightlines)) {
    mopts <- c(mopts, paste0("highlightlines=", options$highlightlines))
  }
  opts_str <- if (length(mopts)) paste0("[", paste(mopts, collapse = ","), "]") else ""

  paste0("\n\\begin{minted}", opts_str, "{", lang, "}\n",
         paste(x, collapse = "\n"),
         "\n\\end{minted}\n")
})

# Output hooks: route stdout, messages, and warnings through fancyvrb's
# Verbatim, which coexists with minted more reliably than knitr's defaults.
knitr::knit_hooks$set(output = function(x, options) {
  paste0("\n\\begin{Verbatim}[fontsize=\\small,frame=leftline,framesep=2mm]\n",
         x,
         "\\end{Verbatim}\n")
})
knitr::knit_hooks$set(message = function(x, options) {
  paste0("\n\\begin{Verbatim}[fontsize=\\small,frame=leftline]\n",
         x, "\\end{Verbatim}\n")
})
knitr::knit_hooks$set(warning = function(x, options) {
  paste0("\n\\begin{Verbatim}[fontsize=\\small,frame=leftline]\n",
         x, "\\end{Verbatim}\n")
})

# Output truncation: `output.lines = N` caps a chunk's printed output at N
# lines. Wraps whatever output hook is installed above, so the Verbatim
# formatting survives.
local({
  default_hook <- knitr::knit_hooks$get("output")
  knitr::knit_hooks$set(output = function(x, options) {
    if (!is.null(n <- options$output.lines)) {
      lines <- xfun::split_lines(x)
      if (length(lines) > n) {
        lines <- c(head(lines, n), "## ... [output truncated]")
      }
      x <- paste(lines, collapse = "\n")
    }
    default_hook(x, options)
  })
})

# Narrow console width: the slide measure holds about 62 monospace columns at
# \small. R's default of 80 would wrap regression output mid-table.
options(width = 62, digits = 4, scipen = 4)
