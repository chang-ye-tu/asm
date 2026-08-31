"""
texify_backends.py
==================

A unified conversion backend for the *texify* pipeline.

The job of this module is to be the single seam between "I have one PDF chunk
and a spec, give me LaTeX" and the very different engines that can do that
work:

  * MistralBackend    -> Mistral OCR + chat      (pay-per-token + per-page OCR;
                                                   the DEFAULT primary here)
  * GeminiBackend     -> Google GenAI File API  (pay-per-token, high concurrency)
  * ClaudeCliBackend  -> `claude -p` headless    (prepaid via the monthly Agent
                                                   SDK credit, low concurrency)

Everything above this module (the chunker, the orchestrator, the master-tex
builder) talks to a `Backend` and never branches on which engine is in use.

------------------------------------------------------------------------------
Design notes worth knowing before reading the code
------------------------------------------------------------------------------

1.  SYNCHRONOUS ON PURPOSE.  `convert()` blocks.  Concurrency across chapters is
    the orchestrator's responsibility (a thread pool / asyncio.to_thread), not
    the adapter's.  This keeps the adapter trivially testable and keeps the
    "how many things run at once" policy in one place.

2.  THE PDF IS WIRED IN BY THE BACKEND, NOT THE CALLER.  The caller passes a
    `pdf_path` plus a *semantic* `task_prompt` ("convert this to LaTeX, body
    only, no fences").  Gemini uploads the file; Claude is told to `Read` the
    local path; Mistral OCRs it and feeds the transcription to a text model.
    The caller's task_prompt is identical for every backend.
    (Claude Code's Read tool ingests PDFs visually; for PDFs over ~10 pages it
    needs an explicit page range, which this backend injects automatically.)

3.  CONTINUITY IS ONE MECHANISM: a TEXT HANDOFF.  The *chunker* formats the prior
    chunk's open-environment stack + trailing LaTeX and passes it as
    `context_handoff`, which each backend appends to the task prompt.  It is
    engine-independent, so ANY backend can convert ANY chunk — essential for the
    fallback path, where a single chunk may switch engines mid-chapter.

4.  TRUNCATION.  Silent mid-proof truncation is the scariest failure mode, so
    every result carries a `truncated` flag AND the computed `open_environments`
    stack.  Reliability differs by engine:
      - Gemini:  `truncated` is exact (finish_reason == MAX_TOKENS).
      - Mistral: `truncated` is exact (finish_reason == "length").
      - Claude:  exact only in stream-json mode (stop_reason == "max_tokens");
        in the default json mode it is a weak heuristic.
    Because of that asymmetry, the ORCHESTRATOR should treat a *whole-chapter*
    convert that returns a non-empty `open_environments` as truncation
    regardless of the flag, and re-run that chapter through the chunker.  For
    intermediate chunks an open environment is normal (it continues next chunk),
    so there the `truncated` flag (not the stack) is the signal.

5.  MISTRAL IS TWO STAGES, NOT ONE.  `mistral-ocr-latest` is an OCR model, not a
    chat model: it transcribes a PDF to per-page Markdown-with-LaTeX-math and
    cannot be asked to obey the conversion contract.  So MistralBackend runs
    OCR -> Markdown, then hands that transcription to a Mistral *text* model
    together with the same system prompt every other backend gets.  Two useful
    consequences:
      - The OCR pass is CACHED on the chunk PDF's content hash, so re-running a
        chapter after editing the SKILL contract re-shapes the LaTeX without
        paying for OCR again.
      - OCR sees the page, so the text model never has to; that is why this
        backend works on scanned/DRM'd PDFs where text extraction returns junk.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import shutil
import subprocess
import tempfile
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

log = logging.getLogger("texify.backends")

# --- Optional heavy deps are imported lazily so this module loads anywhere ----
try:
    from google import genai
    from google.genai import types as genai_types
    from google.genai.errors import APIError as GenAIAPIError
    _HAS_GENAI = True
except Exception:  # pragma: no cover - exercised only where the SDK is absent
    _HAS_GENAI = False

# The Mistral SDK moved the client between majors: `mistralai.Mistral` on 1.x,
# `mistralai.client.Mistral` on 2.x (where the top level became a namespace
# package). Accept either so the pipeline isn't pinned to one SDK generation.
try:
    from mistralai import Mistral as _MistralClient          # SDK 1.x
except Exception:
    try:
        from mistralai.client import Mistral as _MistralClient   # SDK 2.x
    except Exception:
        _MistralClient = None
_HAS_MISTRAL = _MistralClient is not None

# SDKError carries .status_code / .body, which is how we tell a retryable 429/5xx
# from a hard 400. Its module moved with the client, so probe both.
try:
    from mistralai.client.errors.sdkerror import SDKError as MistralSDKError  # 2.x
except Exception:
    try:
        from mistralai.models import SDKError as MistralSDKError             # 1.x
    except Exception:
        MistralSDKError = None

try:
    from pypdf import PdfReader
    _HAS_PYPDF = True
except Exception:
    _HAS_PYPDF = False


# =============================== configuration ================================

# NOTE: this string is whatever your script used; confirm it against Google's
# current model list, as preview names rotate.
GEMINI_MODEL = "gemini-3.1-pro-preview"
# Thinking level for Gemini 3.x. "default" (model decides) is the safe choice —
# it reliably transcribes the FULL chapter. WARNING: "low" is NOT economical in
# practice: on big chapters the model lazy-stops early (finish=STOP, not
# truncation), emitting a short stub that silently passes as "ok". Use "low" only
# for small chapters you'll eyeball. Override per run with --thinking.
GEMINI_THINKING_LEVEL = "default"

# Approximate $ per 1M tokens (input, output) for a ROUGH cost estimate in the
# summary; thinking tokens bill at the OUTPUT rate. Chosen by model family at
# construction — Pro is ~5-8x pricier than Flash, so using one rate for both (the
# old bug) over/under-reports badly. ESTIMATES ONLY; provider billing is the
# authoritative figure.
GEMINI_PRICES = {           # (input, output) $/Mtok
    "pro":   (2.00, 12.00),
    "flash": (0.30,  2.50),
}


def _gemini_price(model: str) -> tuple[float, float]:
    return GEMINI_PRICES["flash"] if "flash" in (model or "").lower() \
        else GEMINI_PRICES["pro"]

# PINNED: claude-opus-4-7, and the orchestrator pins --effort to high. DO NOT RAISE THE EFFORT.
#
# What the evidence actually says. plg/experiments/exp2 swept opus-4.6 / 4.7 / 4.8 x
# {max, high, medium, low} on two real 9-page conversion chunks. It RECORDED the outputs and
# scored nothing; the comparison below is a structure count done afterwards over those files:
#
#   * 11 of the 12 combos are STRUCTURALLY IDENTICAL and balanced — same section count, same
#     theorem-likes, same proofs, same labels.
#   * claude-opus-4-8 @ max ALONE drops content. Specimen 1 came back with 1 section instead of
#     2, 3 theorem-likes instead of 5, 2 proofs instead of 3 — plus a stray \end{align*} and
#     \end{proof}, so it would not even compile. Specimen 2: 4 sections instead of 5.
#
# So the finding is NEGATIVE — "not 4.8 @ max". It does not crown a winner: `high` is chosen
# from inside the verified-safe band, not because it beat the other ten.
#
# `xhigh` was NEVER in that sweep, and it is NOT safe: on ross_dp ch. I it dropped two whole
# sections and left a stray \end{align} — the same signature as 4.8 @ max. Both observed
# failures sit at the TOP of the effort scale. Do not go above `high`.
#
# The failure is SILENT, which is why this is pinned in code rather than left to a flag: a
# compressed body can still be balanced, and looks_truncated() still returns False, so
# open_at_end / stray_end / trunc can all pass it clean. Only a structure count against a peer
# run gives it away.
CLAUDE_MODEL = "claude-opus-4-7"

# ------------------------------ Mistral ------------------------------------
# Stage 1: the OCR model. `-latest` currently resolves to OCR 4. It has the `ocr`
# capability and NO `completion_chat`, so it can only transcribe — it can never be
# asked to obey the conversion contract. That is stage 2's job.
MISTRAL_OCR_MODEL = "mistral-ocr-latest"

# Stage 2: the text model that shapes OCR Markdown into contract-conformant LaTeX.
#
# `mistral-medium-latest` (Medium 3.5, 262k ctx) is the default because it is the only
# Mistral text model with the `reasoning` capability, and reasoning is what keeps
# \begin/\end balanced across a 20-page chunk. Measured on kirsch ch.3: SIX runs on the
# cheaper `mistral-large-latest` (no reasoning) each left the body unbalanced and
# uncompilable; medium+high was clean on both chunks. See the README.
#
# The price is real — reasoning tokens bill at the OUTPUT rate, so a chunk costs ~16x
# large's and takes ~5x the wall clock, and the token burn trips Mistral's per-minute
# rate limit (handled by the 429 backoff below).
#
# To trade correctness for cost, drop to large AND clear the effort flag, since large
# 400s on reasoning_effort (`_chat` drops it and retries once, then remembers):
#     --mistral-model mistral-large-latest --mistral-effort ''
MISTRAL_TEXT_MODEL = "mistral-medium-latest"

# Reasoning effort for the stage-2 model. `mistral-medium-latest` accepts ONLY "high" or
# "none". None/"" omits the parameter entirely, which is required for models without the
# `reasoning` capability (e.g. mistral-large-latest).
MISTRAL_REASONING_EFFORT: Optional[str] = "high"

# Output ceiling for stage 2. A dense 20-page chunk runs ~2.5 KB of LaTeX per page
# (~17k tokens); this leaves headroom without capping a legitimately long chapter.
MISTRAL_MAX_TOKENS = 65536

# Approximate $ per 1M tokens (input, output), by model family, for the summary's
# cost estimate. ESTIMATES ONLY; Mistral's billing console is authoritative.
# Source: mistral.ai/pricing/api (checked 2026-07).
MISTRAL_PRICES = {              # (input, output) $/Mtok
    "mistral-large":    (0.50, 1.50),
    "mistral-medium":   (1.50, 7.50),
    "magistral-medium": (2.00, 5.00),
    "mistral-small":    (0.15, 0.60),
}
# OCR bills per PAGE, not per token: OCR 4 is $4 / 1000 pages. A cache hit costs $0.
MISTRAL_OCR_PRICE_PER_PAGE = 0.004


def _mistral_price(model: str) -> tuple[float, float]:
    m = (model or "").lower()
    for family, rate in MISTRAL_PRICES.items():
        if m.startswith(family):
            return rate
    return MISTRAL_PRICES["mistral-large"]


# Where OCR transcriptions are memoized, keyed by the chunk PDF's content hash.
# Chunk slices are byte-deterministic given the same source + page span, so this
# survives across runs: editing the SKILL contract and re-converting costs $0 of OCR.
MISTRAL_OCR_CACHE_DIR = Path(".texify_work") / "ocr_cache"

# Stage 2 input ceiling (chars). Large 3's window is 262k tokens ~= 1M chars, but a
# transcription anywhere near that means the chunker failed to bound the chunk. This
# is the tripwire, not a target.
MISTRAL_MAX_DOC_CHARS = 700_000

# When a *probe* (expect_short) legitimately spans a whole book, only each page's
# HEAD is needed — chapter/section headings sit at the top of the page — so pages are
# truncated to this many chars rather than blowing the window.
MISTRAL_PROBE_PAGE_HEAD_CHARS = 900

# Claude Code's Read tool reads PDFs <= this many pages whole; beyond it, the
# tool requires an explicit page range, which we supply in the prompt.
READ_WHOLE_PDF_PAGE_LIMIT = 10

# ...and it accepts at most this many pages PER Read request. A chunk wider than this
# must be read in several calls; we enumerate the ranges so no page is silently
# skipped. The chunker caps chunks at this size (MAX_CHUNK_PAGES), so the multi-range
# path is a backstop for hand-built/over-budget chunks.
READ_REQUEST_PAGE_LIMIT = 20

# Per-call wall-clock ceilings (seconds).  A dense math chapter can run minutes.
GEMINI_UPLOAD_TIMEOUT = 600
CLAUDE_CALL_TIMEOUT = 1800
MISTRAL_OCR_TIMEOUT = 900
# Stage 2 is the slow one, and the default model REASONS: a 9-page chunk took ~12 min, so a
# full 20-page chunk can run past the 30 min the other engines are given. Budget an hour.
MISTRAL_CHAT_TIMEOUT = 3600

# Retry policy (transient API / process failures only).
MAX_RETRIES = 4
BACKOFF_BASE = 5  # seconds; wait = BACKOFF_BASE * 2**attempt

# Mistral rate-limits on a tokens-per-MINUTE bucket, so a 429 needs minutes to clear, not
# the seconds BACKOFF_BASE gives a 5xx. Used only when the server sends no `Retry-After`.
# 60/120/240/480 -> ~15 min of patience before a chapter is called failed.
MISTRAL_RATE_LIMIT_BACKOFF = 60


# ================================= results ====================================

@dataclass
class ConversionResult:
    """Everything the orchestrator needs from one conversion call."""
    text: str
    backend: str
    model: str
    truncated: bool
    open_environments: list[str] = field(default_factory=list)
    cost_usd: Optional[float] = None       # Claude reports it; Gemini does not
    usage: Optional[dict] = None
    pdf_path: Optional[str] = None


class BackendError(RuntimeError):
    """Raised when a conversion fails unrecoverably (after retries)."""


class BlockedByPolicyError(BackendError):
    """The model REFUSED to emit the output because a provider content-filter /
    safety policy blocked it (e.g. verbatim reproduction of a copyrighted book).

    This is a distinct, NON-retryable, expected outcome — not a transient failure
    and not a code bug. The orchestrator records and reports it separately so the
    run reflects what was blocked instead of pretending it crashed.
    """


# Phrases a provider returns when output is suppressed by a content/safety filter.
_POLICY_BLOCK_RE = re.compile(
    r"output blocked|content[\s-]*filter|content[\s-]*polic|safety[\s-]*polic|"
    r"blocked by .*polic|refus|copyright|cannot reproduce|can't reproduce|"
    r"prohibited_content|content_policy|blocklist",
    re.I,
)


def is_policy_block(message: str) -> bool:
    """True if an error/result message looks like a content-filter / policy block."""
    return bool(message and _POLICY_BLOCK_RE.search(message))


# ============================== shared helpers ================================

_ENV_RE = re.compile(r"\\(begin|end)\s*\{([^}]*)\}")


def strip_code_fences(text: str) -> str:
    """Defensively remove a leading ```latex / trailing ``` even though the spec
    forbids them; models add them anyway often enough to matter."""
    t = text.strip()
    if t.startswith("```"):
        # drop first fence line
        nl = t.find("\n")
        if nl != -1:
            t = t[nl + 1:]
    if t.rstrip().endswith("```"):
        t = t.rstrip()[: t.rstrip().rfind("```")]
    return t.strip()


def strip_model_preamble(text: str, is_first_chunk: bool) -> str:
    """Drop a conversational preamble emitted before the LaTeX body.

    Models sometimes prepend prose ("Here is the converted LaTeX body:", "I have
    what I need ...") despite the spec forbidding it. For a chapter-opening chunk
    the real body always starts at a structural anchor: a line beginning with a
    backslash command or a percent comment. Everything before the FIRST such line
    is chatter and is dropped. Continuation chunks (is_first_chunk=False) may
    legitimately begin mid-prose or mid-math, so they are returned unchanged.
    """
    if not is_first_chunk:
        return text
    anchor = chr(92)  # backslash: the start of a LaTeX command
    lines = text.splitlines()
    for i, ln in enumerate(lines):
        s = ln.lstrip()
        if s.startswith(anchor) or s.startswith("%"):
            return text if i == 0 else "\n".join(lines[i:])
    return text  # no anchor found -> do not risk dropping everything


def scan_open_environments(text: str,
                           initial_stack: Optional[list[str]] = None) -> list[str]:
    """Return the LaTeX environments still open at the end of `text`.

    `initial_stack` seeds environments left open by a previous chunk, so this is
    reusable both for whole-chapter validation (initial_stack=None -> result
    should be []) and for chunk handoff (seed with the prior chunk's stack).

    Tolerant by design: an `\\end{x}` with no matching `\\begin{x}` in the
    current text closes something from the seed/earlier chunk, which is the
    normal shape of a continuation chunk, so it is not treated as an error.
    """
    stack: list[str] = list(initial_stack or [])
    for kind, name in _ENV_RE.findall(text):
        name = name.strip()
        if kind == "begin":
            stack.append(name)
        else:  # end
            if stack and stack[-1] == name:
                stack.pop()
            elif name in stack:
                # mismatched nesting; remove the nearest matching open env
                for i in range(len(stack) - 1, -1, -1):
                    if stack[i] == name:
                        del stack[i]
                        break
            # else: closes a pre-seed env we don't track -> ignore
    return stack


def scan_unmatched_ends(text: str) -> list[str]:
    """Return the `\\end{x}` in `text` that close nothing — the MIRROR of
    scan_open_environments, and NOT a substitute for it.

    scan_open_environments deliberately ignores an unmatched `\\end`, because a
    continuation chunk legitimately closes an environment its predecessor opened. That
    tolerance is right per-chunk and WRONG for an assembled chapter, where nothing
    precedes the text: there, a stray `\\end` is an unambiguous defect that leaves the
    body uncompilable while `open_environments` still comes back empty. Call this on the
    finished chapter only.
    """
    stack: list[str] = []
    stray: list[str] = []
    for kind, name in _ENV_RE.findall(text):
        name = name.strip()
        if kind == "begin":
            stack.append(name)
        elif stack and stack[-1] == name:
            stack.pop()
        elif name in stack:
            for i in range(len(stack) - 1, -1, -1):
                if stack[i] == name:
                    del stack[i]
                    break
        else:
            stray.append(name)
    return stray


def looks_truncated(text: str) -> bool:
    """Weak, HIGH-PRECISION truncation heuristic for engines that don't report a
    stop reason.  Only flags cases that are almost certainly cut off, to avoid
    false-positiving on legitimate mid-chunk boundaries.  The orchestrator's
    open-environment check is the real safety net for whole-chapter calls."""
    t = text.rstrip()
    if not t:
        return True
    if t.endswith("\\"):           # dangling control-sequence start
        return True
    if re.search(r"\\[a-zA-Z]+$", t) and not t.endswith(("\\\\",)):
        # ends on a bare command name with no argument/space — usually mid-token
        return True
    return False


def pdf_page_count(pdf_path: str) -> Optional[int]:
    """Page count via pypdf, or None if pypdf is unavailable / the file is bad."""
    if not _HAS_PYPDF:
        log.warning("pypdf not installed; cannot determine page count for %s", pdf_path)
        return None
    try:
        return len(PdfReader(pdf_path).pages)
    except Exception as e:  # corrupt / encrypted / missing
        log.warning("could not read page count for %s: %s", pdf_path, e)
        return None


# =============================== base class ===================================

class Backend(ABC):
    name: str = "base"

    def __init__(self, model: str):
        self.model = model

    @abstractmethod
    def convert(self,
                pdf_path: str,
                system_prompt: str,
                task_prompt: str,
                *,
                context_handoff: Optional[str] = None,
                expect_short: bool = False) -> ConversionResult:
        """`expect_short`: this call legitimately returns a SMALL body (a structure
        probe emits only a section/chapter list, not chapter-length LaTeX), so the
        FallbackBackend must NOT treat it as a soft-stub non-completion. Plain
        single-engine backends ignore it (they have no short-output floor)."""
        ...

    # small shared retry wrapper for the callables that may hit transient errors
    def _with_retry(self, fn, *, retryable):
        last = None
        for attempt in range(MAX_RETRIES):
            try:
                return fn()
            except retryable as e:  # type: ignore[misc]
                last = e
                wait = BACKOFF_BASE * (2 ** attempt)
                log.warning("[%s] transient error (%s); retry %d/%d in %ds",
                            self.name, e, attempt + 1, MAX_RETRIES, wait)
                time.sleep(wait)
        raise BackendError(f"[{self.name}] exhausted retries: {last}")


# ============================== Gemini backend ================================

class GeminiBackend(Backend):
    name = "gemini"

    def __init__(self, model: str = GEMINI_MODEL, *,
                 api_key: Optional[str] = None, temperature: float = 0.1,
                 thinking_level: Optional[str] = GEMINI_THINKING_LEVEL):
        if not _HAS_GENAI:
            raise BackendError(
                "google-genai is not installed. `pip install google-genai "
                "--break-system-packages` to use the Gemini backend."
            )
        super().__init__(model)
        self.client = genai.Client(api_key=api_key or os.environ.get("GEMINI_API_KEY"))
        self.temperature = temperature
        self.thinking_level = thinking_level
        self.price_in, self.price_out = _gemini_price(model)

    def convert(self, pdf_path, system_prompt, task_prompt, *,
                context_handoff=None, expect_short=False) -> ConversionResult:
        user = task_prompt  # expect_short: n/a here (no short-output floor on a single engine)
        if context_handoff:
            user = f"{task_prompt}\n\n{context_handoff}"

        uploaded = self._upload_and_wait(pdf_path)
        try:
            # thinking control: a digit string -> a fixed thinking_budget (tokens),
            # which BOUNDS reasoning (prevents both lazy under-thinking and the
            # runaway over-thinking that truncates output); "low"/"high" -> level;
            # "default" -> let the model decide.
            thinking_cfg = None
            tl = (self.thinking_level or "").strip().lower()
            if tl and tl != "default":
                try:
                    if tl.lstrip("-").isdigit():
                        thinking_cfg = genai_types.ThinkingConfig(thinking_budget=int(tl))
                    else:
                        thinking_cfg = genai_types.ThinkingConfig(thinking_level=tl)
                except Exception as e:  # SDK shape mismatch — fall back to default
                    log.warning("[gemini] thinking=%r not accepted (%s); "
                                "using model default", self.thinking_level, e)
            cfg = genai_types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=self.temperature,
                thinking_config=thinking_cfg,
            )
            resp = self._with_retry(
                lambda: self.client.models.generate_content(
                    model=self.model, contents=[uploaded, user], config=cfg),
                retryable=(GenAIAPIError, Exception),
            )
        finally:
            try:
                self.client.files.delete(name=uploaded.name)
            except Exception:
                log.debug("[gemini] could not delete uploaded file %s", uploaded.name)

        # finish_reason gives us an EXACT truncation signal
        fr_name = "UNKNOWN"
        if getattr(resp, "candidates", None):
            fr = getattr(resp.candidates[0], "finish_reason", None)
            fr_name = getattr(fr, "name", str(fr)) if fr is not None else "UNKNOWN"

        try:
            raw = resp.text or ""
        except Exception:
            raw = ""
        # RECITATION is Gemini's verbatim-copyright block; the rest are safety
        # filters — all are content-policy blocks, not transient failures.
        if not raw and fr_name in ("SAFETY", "RECITATION", "PROHIBITED_CONTENT",
                                   "BLOCKLIST", "SPII"):
            raise BlockedByPolicyError(
                f"[gemini] content policy block (finish_reason={fr_name})")

        text = strip_code_fences(raw)
        usage = None
        if getattr(resp, "usage_metadata", None):
            um = resp.usage_metadata
            usage = {
                "prompt_tokens": getattr(um, "prompt_token_count", None),
                "thoughts_tokens": getattr(um, "thoughts_token_count", None),
                "output_tokens": getattr(um, "candidates_token_count", None),
                "total_tokens": getattr(um, "total_token_count", None),
            }
            # cost visibility: thinking tokens bill at the output rate, so surface
            # them separately — they're the silent driver of Gemini spend.
            log.info("[gemini] tokens: prompt=%s thoughts=%s output=%s total=%s "
                     "(thinking_level=%s, finish=%s)",
                     usage["prompt_tokens"], usage["thoughts_tokens"],
                     usage["output_tokens"], usage["total_tokens"],
                     self.thinking_level, fr_name)

        # rough cost estimate ($): prompt at input rate; output + thinking at the
        # (higher) output rate. Estimate only — Google billing is authoritative.
        cost = None
        if usage:
            cost = round(
                (usage["prompt_tokens"] or 0) / 1e6 * self.price_in
                + ((usage["output_tokens"] or 0) + (usage["thoughts_tokens"] or 0))
                / 1e6 * self.price_out, 4)

        return ConversionResult(
            text=text,
            backend=self.name,
            model=self.model,
            truncated=(fr_name == "MAX_TOKENS"),
            open_environments=scan_open_environments(text),
            cost_usd=cost,           # estimated from usage × configured rates
            usage=usage,
            pdf_path=pdf_path,
        )

    def _upload_and_wait(self, pdf_path: str):
        log.info("[gemini] uploading %s", pdf_path)
        f = self.client.files.upload(file=pdf_path)
        waited = 0
        while f.state.name == "PROCESSING":
            if waited >= GEMINI_UPLOAD_TIMEOUT:
                raise BackendError(f"[gemini] upload stuck PROCESSING: {pdf_path}")
            time.sleep(5)
            waited += 5
            f = self.client.files.get(name=f.name)
        if f.state.name == "FAILED":
            raise BackendError(f"[gemini] file processing FAILED: {pdf_path}")
        return f


# ============================ Claude -p backend ===============================

class ClaudeCliBackend(Backend):
    name = "claude"

    def __init__(self, model: str = CLAUDE_MODEL, *,
                 claude_bin: str = "claude",
                 use_stream_json: bool = False,
                 effort: Optional[str] = None,
                 extra_args: Optional[list[str]] = None):
        """
        effort: Claude Code reasoning-effort level passed as `--effort` (low /
            medium / high / xhigh / max). For adaptive-reasoning models (Opus 4.8),
            this — NOT MAX_THINKING_TOKENS, which they ignore — controls the thinking
            budget; `max` is the deepest. None omits the flag (model default).

        use_stream_json: if True, parse stream-json events to read the true
            stop_reason (exact truncation detection) at the cost of more fragile
            parsing.  Default False uses --output-format json (clean result +
            total_cost_usd) with the heuristic truncation flag.

        NOTE on auth: do NOT add `--bare` via extra_args if you rely on your
            subscription, because bare mode skips OAuth/keychain and expects an
            API key.  For clean subscription runs, invoke from a directory with
            no stray CLAUDE.md / MCP config instead.
        """
        resolved = shutil.which(claude_bin)
        if not resolved:
            raise BackendError(
                f"`{claude_bin}` not found on PATH. Install Claude Code and log in."
            )
        super().__init__(model)
        self.claude_bin = resolved
        self.use_stream_json = use_stream_json
        self.effort = effort
        self.extra_args = list(extra_args or [])

    def convert(self, pdf_path, system_prompt, task_prompt, *,
                context_handoff=None, expect_short=False) -> ConversionResult:
        abs_pdf = str(Path(pdf_path).resolve())  # expect_short: n/a (no floor on single engine)

        # Build the read instruction; >10pp PDFs need an explicit page range, and the
        # Read tool takes at most READ_REQUEST_PAGE_LIMIT pages per call, so a bigger
        # chunk must be paged through in several calls (else only the first window is
        # ever seen).
        n = pdf_page_count(abs_pdf)
        page_note = ""
        if n and n > READ_WHOLE_PDF_PAGE_LIMIT:
            if n <= READ_REQUEST_PAGE_LIMIT:
                page_note = (f' This document has {n} pages; read them by passing the '
                             f'page range "1-{n}" to the Read tool.')
            else:
                ranges = [f'"{s + 1}-{min(s + READ_REQUEST_PAGE_LIMIT, n)}"'
                          for s in range(0, n, READ_REQUEST_PAGE_LIMIT)]
                page_note = (f' This document has {n} pages, more than the Read tool '
                             f'accepts per call. Make SEPARATE Read calls for EACH of '
                             f'these page ranges so you see every page: '
                             f'{", ".join(ranges)}.')

        prompt = f'Read the PDF at "{abs_pdf}".{page_note} {task_prompt}'
        if context_handoff:  # cross-chunk continuity: prior open-env stack + tail LaTeX
            prompt = f"{prompt}\n\n{context_handoff}"

        # The spec can be large; pass it as a file to dodge ARG_MAX limits.
        sys_fd, sys_path = tempfile.mkstemp(suffix=".txt", prefix="texify_sys_")
        try:
            with os.fdopen(sys_fd, "w", encoding="utf-8") as fh:
                fh.write(system_prompt)

            cmd = [
                self.claude_bin, "-p", prompt,
                "--append-system-prompt-file", sys_path,
                "--allowedTools", "Read",
                "--permission-mode", "dontAsk",
                "--model", self.model,
            ]
            if self.effort:
                cmd += ["--effort", self.effort]
            if self.use_stream_json:
                cmd += ["--output-format", "stream-json", "--verbose"]
            else:
                cmd += ["--output-format", "json"]
            cmd += self.extra_args

            data = self._with_retry(
                lambda: self._run(cmd),
                retryable=(subprocess.TimeoutExpired, _RetryableClaude),
            )
        finally:
            try:
                os.remove(sys_path)
            except OSError:
                pass

        if data.get("is_error"):
            msg = data.get("text") or data.get("subtype") or "unknown error"
            if is_policy_block(msg):
                raise BlockedByPolicyError(f"[claude] content policy block: {msg}")
            raise BackendError(f"[claude] run failed: {msg}")

        text = strip_code_fences(data.get("text", ""))

        # Truncation: exact via stream stop_reason; heuristic otherwise.
        stop_reason = data.get("stop_reason")
        truncated = (
            stop_reason == "max_tokens"
            or data.get("hit_max_output", False)
            or data.get("subtype") == "error_max_turns"
            or (stop_reason is None and looks_truncated(text))
        )

        return ConversionResult(
            text=text,
            backend=self.name,
            model=self.model,
            truncated=truncated,
            open_environments=scan_open_environments(text),
            cost_usd=data.get("cost_usd"),
            usage=data.get("usage"),
            pdf_path=pdf_path,
        )

    # -- subprocess plumbing ---------------------------------------------------

    def _run(self, cmd: list[str]) -> dict:
        log.debug("[claude] %s (model=%s)", "stream-json" if self.use_stream_json
                  else "json", self.model)
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              timeout=CLAUDE_CALL_TIMEOUT)
        if proc.returncode != 0:
            # `claude -p` often exits non-zero with the real reason on STDOUT
            # (a json result whose is_error/result carries the message, e.g. an
            # API content-filter block), leaving STDERR empty. Surface whichever
            # we can find so the failure isn't logged as a bare "exited 1:".
            detail = (proc.stderr or "").strip()
            if not detail and proc.stdout:
                try:
                    d = json.loads(proc.stdout)
                    detail = str(d.get("result") or d.get("subtype")
                                 or d.get("error") or "").strip()
                except json.JSONDecodeError:
                    detail = proc.stdout.strip()[:500]
            # a content-filter / policy block is a distinct, non-retryable outcome
            if is_policy_block(detail):
                raise BlockedByPolicyError(f"[claude] content policy block: {detail[:500]}")
            # crude classification: overload / rate-limit / 5xx are retryable
            if re.search(r"overload|rate.?limit|429|50\d|timeout", detail, re.I):
                raise _RetryableClaude(detail[:300])
            raise BackendError(f"[claude] exited {proc.returncode}: {detail[:500]}")
        return (self._parse_stream(proc.stdout) if self.use_stream_json
                else self._parse_json(proc.stdout))

    @staticmethod
    def _parse_json(stdout: str) -> dict:
        try:
            d = json.loads(stdout)
        except json.JSONDecodeError as e:
            raise BackendError(f"[claude] could not parse json output: {e}")
        return {
            "text": d.get("result", ""),
            "cost_usd": d.get("total_cost_usd"),
            "usage": d.get("usage"),
            "is_error": d.get("is_error", False),
            "subtype": d.get("subtype"),
            "stop_reason": None,  # not exposed in json mode
        }

    @staticmethod
    def _parse_stream(stdout: str) -> dict:
        out: dict = {"text": "", "cost_usd": None,
                     "usage": None, "is_error": False, "subtype": None,
                     "stop_reason": None, "hit_max_output": False}
        for line in stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            t = ev.get("type")
            if t == "assistant":
                sr = (ev.get("message") or {}).get("stop_reason")
                if sr:
                    out["stop_reason"] = sr
            elif t == "result":
                out["text"] = ev.get("result", "")
                out["cost_usd"] = ev.get("total_cost_usd")
                out["usage"] = ev.get("usage")
                out["is_error"] = ev.get("is_error", False)
                out["subtype"] = ev.get("subtype")
            elif t == "system" and ev.get("subtype") == "api_retry":
                if ev.get("error") == "max_output_tokens":
                    out["hit_max_output"] = True
        return out


class _RetryableClaude(RuntimeError):
    """Internal marker for transient `claude -p` failures worth retrying."""


# ============================== Mistral backend ===============================

# What stage 2 must know about the shape of what stage 1 hands it. These are
# artifacts of the OCR REPRESENTATION, not of the book, which is exactly why they
# belong to the backend and not to the (engine-independent) SKILL contract.
MISTRAL_OCR_NOTES = (
    "SOURCE FORM. Below is a faithful OCR transcription of the PDF pages — Markdown "
    "with LaTeX mathematics — not the PDF itself. Convert ALL of it under the system "
    "contract, reading these OCR conventions correctly:\n"
    "  - `<!-- page N -->` marks where a page begins. It is a PAGE MARKER, NOT content: "
    "never emit it, and never let it interrupt a sentence, proof, equation or environment "
    "that runs across the page break — stitch such a construct back together.\n"
    "  - Running heads and page numbers are already stripped. If a stray folio or running "
    "title survives inside the text, drop it.\n"
    "  - `$$ ... \\tag{1.42} $$` is how OCR renders a NUMBERED display equation. Emit it as "
    "`\\begin{equation}\\label{eq:1.42} ... \\end{equation}` — the tag is the number the book "
    "prints, so it becomes the \\label key. NEVER emit a literal `\\tag`. An UNtagged "
    "`$$ ... $$` is an unnumbered display: emit `\\[ ... \\]`.\n"
    "  - An in-text reference to a numbered equation, e.g. `(1.42)`, becomes `\\eqref{eq:1.42}`.\n"
    "  - A bolded run-in head like `**Lemma 1.14**` or `**Theorem 2.3**` is one of the book's "
    "theorem-like environments. Emit the environment the contract names for it, with the "
    "printed number as its \\label key — never `\\textbf{...}`.\n"
    "  - A `Proof:` paragraph is a proof: emit `\\begin{proof} ... \\end{proof}`. The OCR's "
    "QED box (`$\\square$` / `$\\blacksquare$`) is the proof's TERMINATOR — REPLACE it with "
    "`\\end{proof}`, which draws the box for you. NEVER emit `\\qed`, `\\qedsymbol`, "
    "`$\\square$` or `$\\blacksquare$`: those print a box WITHOUT closing the environment, "
    "leaving it open. If OCR lost the box, close the proof after its last sentence, "
    "immediately before the next heading or theorem-like environment. A proof runs through "
    "display equations and across page markers, so a display ending is NOT the end of the "
    "proof — but every proof you open MUST be closed by `\\end{proof}`.\n"
    "  - A QED box with NO `\\begin{proof}` of yours before it means this chunk OPENED inside "
    "a proof that a previous chunk began. The continuity note above tells you what is still "
    "open: emit the remaining text and then `\\end{proof}`, and do NOT open a new proof.\n"
    "  - ENVIRONMENT BALANCE IS NON-NEGOTIABLE: every `\\begin{X}` gets exactly one matching "
    "`\\end{X}`, and environments close in reverse order of opening. OCR runs a theorem's "
    "statement straight into the `Proof:` that follows, which invites four specific errors — "
    "commit none: (a) the statement ENDS where `Proof:` begins, so emit `\\end{theorem}` "
    "there, then open `\\begin{proof}`; (b) never close an environment with a different "
    "environment's `\\end`; (c) never emit `\\end{X}` twice for one `\\begin{X}`, nor an "
    "`\\end{X}` for an `\\begin{X}` you did not open; (d) never let a theorem or proof run "
    "unclosed into the next section. Before you emit the final character, re-scan your own "
    "output and confirm the `\\begin`/`\\end` stack is empty.\n"
    "  - `<!-- footnote -->` introduces a footnote lifted from the bottom of that page. Its "
    "marker (e.g. `$^3$`) matches a superscript in that page's body text: re-attach it there "
    "as `\\footnote{...}` and do not emit the marker or the standalone line.\n"
    "  - `![img-0.jpeg](img-0.jpeg)` is a figure image. Emit the contract's figure template "
    "with its \\includegraphics path written LITERALLY as `<book>_<NN>_figs.pdf` — keep both "
    "placeholders exactly; the orchestrator substitutes the real book prefix and chapter "
    "number. Never guess a filename. Number the `page=` keys by figure order.\n"
    "  - NO Markdown may survive into the output: `#` headings become \\section/\\subsection, "
    "`**bold**` becomes the right environment or \\textbf, `|pipe tables|` become tabular.\n"
    "  - OCR can misread a symbol. Where the mathematics makes a reading plainly wrong "
    "(a stray `1` for `l`, `\\varepsilon` for `\\in`), emit the mathematically correct symbol."
)

# `extract_footer` lifts the bottom-of-page block out of the body. That block is a folio
# ("136"), a running footer ("Chapter 5  Maxwell's equations"), or a FOOTNOTE — and a
# footnote is real content whose silent deletion would be a fidelity bug, so it has to be
# put back. Discriminate in that order:
#   1. digits/punctuation only          -> folio, drop
#   2. leading superscript/symbol marker -> footnote, keep ("$^3$ Note that ...")
#   3. 8+ words                          -> unmarked prose, keep (long footnote)
#   otherwise                            -> running footer, drop
_FOLIO_RE = re.compile(r"^[\s\d.,;:\-–—|]*$")
_FOOTNOTE_MARKER_RE = re.compile(
    r"^\s*(?:\$[^$]{0,12}\^[^$]{0,12}\$|\^\{?\d+\}?|\[\d+\]|[*†‡§¶])")


def _footer_is_content(footer: Optional[str]) -> bool:
    if not footer:
        return False
    f = footer.strip()
    if _FOLIO_RE.match(f):
        return False
    if _FOOTNOTE_MARKER_RE.match(f):
        return True
    return len(re.findall(r"[A-Za-z]{2,}", f)) >= 8


# An in-band refusal ("I cannot reproduce this copyrighted text") arrives as a normal
# 200 with prose instead of LaTeX. High-precision test: short, essentially no LaTeX, not
# machine output, and it talks like a refusal. A real body is thousands of chars of
# backslashes, so it cannot trip this; that asymmetry is what makes the check safe.
#
# The leading-character guard matters more than it looks. `is_policy_block` fires on the
# bare word "copyright", so WITHOUT it a structure probe returning
#   {"sections": [{"title": "Copyright and Permissions"}]}
# or a short BibTeX entry titled "On Copyright" would be reported as a content block. The
# caller ALSO skips this check for `expect_short` calls (probes), which is the other half
# of the guard.
_MACHINE_OUTPUT_START = "@{%\\["   # BibTeX / JSON / LaTeX comment / LaTeX command / array


def _looks_like_inband_refusal(text: str) -> bool:
    t = (text or "").strip()
    if not t or len(t) > 1000 or "\\begin{" in t:
        return False
    if t[0] in _MACHINE_OUTPUT_START:
        return False
    return t.count("\\") <= 4 and is_policy_block(t)


class MistralBackend(Backend):
    """Mistral OCR (stage 1) + a Mistral text model (stage 2).

    Stage 1 (`mistral-ocr-latest`) transcribes the PDF to per-page Markdown with LaTeX
    math, stripping running heads. It bills per PAGE and is memoized on the PDF's
    content hash, so the expensive part is paid once per chunk, ever.

    Stage 2 (`mistral-large-latest` by default) receives the SAME system prompt every
    other backend gets — the composed SKILL contract — plus the transcription, and
    emits the LaTeX body. Because stage 2 never sees the PDF, `MISTRAL_OCR_NOTES` tells
    it how to read stage 1's conventions (`\\tag{}`, `**Lemma 1.4**`, page markers).

    `self.model` is the STAGE-2 model, because that is the one the orchestrator reports
    and `--model` overrides; the OCR model is a separate, rarely-touched knob.
    """
    name = "mistral"

    def __init__(self, model: str = MISTRAL_TEXT_MODEL, *,
                 api_key: Optional[str] = None,
                 ocr_model: str = MISTRAL_OCR_MODEL,
                 temperature: float = 0.1,
                 reasoning_effort: Optional[str] = MISTRAL_REASONING_EFFORT,
                 max_tokens: int = MISTRAL_MAX_TOKENS,
                 cache_dir: Optional[Path] = MISTRAL_OCR_CACHE_DIR,
                 max_doc_chars: int = MISTRAL_MAX_DOC_CHARS):
        if not _HAS_MISTRAL:
            raise BackendError(
                "mistralai is not installed. `pip install mistralai "
                "--break-system-packages` to use the Mistral backend."
            )
        key = api_key or os.environ.get("MISTRAL_API_KEY")
        if not key:
            raise BackendError("MISTRAL_API_KEY is not set; export it to use --backend mistral.")
        super().__init__(model)
        self.client = _MistralClient(api_key=key)
        self.ocr_model = ocr_model
        self.temperature = temperature
        self.reasoning_effort = reasoning_effort
        self.max_tokens = max_tokens
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self.max_doc_chars = max_doc_chars
        self.price_in, self.price_out = _mistral_price(model)

    # -- public API ------------------------------------------------------------

    def convert(self, pdf_path, system_prompt, task_prompt, *,
                context_handoff=None, expect_short=False) -> ConversionResult:
        pages, billed_pages = self._ocr(pdf_path)

        doc = self._render(pages)
        if len(doc) > self.max_doc_chars:
            if expect_short:
                # A book-wide probe wants headings, which live at the top of each page.
                doc = self._render(pages, head=MISTRAL_PROBE_PAGE_HEAD_CHARS)
                log.info("[mistral] probe over %d pages: truncated to %d chars/page "
                         "(%d chars total) to fit the context window.",
                         len(pages), MISTRAL_PROBE_PAGE_HEAD_CHARS, len(doc))
            else:
                log.warning("[mistral] transcription is %d chars for %d pages — at or over "
                            "the %d-char ceiling. The chunker should have bounded this; "
                            "output may truncate.", len(doc), len(pages), self.max_doc_chars)

        parts = [task_prompt, MISTRAL_OCR_NOTES]
        if context_handoff:   # cross-chunk continuity: prior open-env stack + tail LaTeX
            parts.append(context_handoff)
        parts.append(f"<document>\n{doc}\n</document>")
        user = "\n\n".join(parts)

        resp = self._retry(lambda: self._chat(system_prompt, user))

        if not getattr(resp, "choices", None):
            raise BackendError("[mistral] chat returned no choices")
        choice = resp.choices[0]
        finish = str(getattr(choice, "finish_reason", "") or "")
        raw = choice.message.content
        if not isinstance(raw, str):
            # A reasoning model returns content CHUNKS, mixing TextChunk (.text) with
            # ThinkChunk (.thinking). Select TextChunk explicitly: relying on `.text`
            # being absent from ThinkChunk would silently splice chain-of-thought into
            # the LaTeX body the day the SDK renames that field.
            raw = "".join(c.text for c in (raw or [])
                          if getattr(c, "type", None) == "text" and hasattr(c, "text"))

        if finish in ("content_filter", "error"):
            raise BlockedByPolicyError(
                f"[mistral] content policy block (finish_reason={finish})")

        text = strip_code_fences(raw)
        # A probe legitimately returns short, non-LaTeX output (JSON, BibTeX), so the
        # refusal heuristic must not run on it — see _looks_like_inband_refusal.
        if not expect_short and _looks_like_inband_refusal(text):
            raise BlockedByPolicyError(
                f"[mistral] in-band refusal ({len(text)} chars, no LaTeX): {text[:200]!r}")

        usage = None
        cost = billed_pages * MISTRAL_OCR_PRICE_PER_PAGE
        um = getattr(resp, "usage", None)
        if um:
            usage = {
                "prompt_tokens": getattr(um, "prompt_tokens", None),
                "output_tokens": getattr(um, "completion_tokens", None),
                "total_tokens": getattr(um, "total_tokens", None),
                "ocr_pages_billed": billed_pages,
            }
            cost += ((usage["prompt_tokens"] or 0) / 1e6 * self.price_in
                     + (usage["output_tokens"] or 0) / 1e6 * self.price_out)
            log.info("[mistral] tokens: prompt=%s output=%s | ocr_pages_billed=%d "
                     "(finish=%s, effort=%s)", usage["prompt_tokens"],
                     usage["output_tokens"], billed_pages, finish, self.reasoning_effort)

        return ConversionResult(
            text=text,
            backend=self.name,
            model=self.model,
            truncated=(finish == "length"),   # exact, unlike Claude's json mode
            open_environments=scan_open_environments(text),
            cost_usd=round(cost, 4) if cost else None,
            usage=usage,
            pdf_path=pdf_path,
        )

    # -- stage 1: OCR ----------------------------------------------------------

    def _ocr(self, pdf_path: str) -> tuple[list[dict], int]:
        """Transcribe every page of `pdf_path`. Returns (pages, billed_pages); a cache
        hit bills 0 pages, which is what makes re-conversion after a contract edit free."""
        raw = Path(pdf_path).read_bytes()
        cache = None
        if self.cache_dir:
            digest = hashlib.sha256(raw).hexdigest()[:32]
            cache = self.cache_dir / f"{digest}.{self.ocr_model}.json"
            if cache.exists():
                try:
                    pages = json.loads(cache.read_text(encoding="utf-8"))["pages"]
                    log.info("[mistral] OCR cache hit for %s (%d pages, $0).",
                             Path(pdf_path).name, len(pages))
                    return pages, 0
                except Exception:  # noqa: BLE001 — stale/corrupt cache -> re-OCR
                    log.debug("[mistral] unusable OCR cache %s; re-OCRing.", cache.name)

        log.info("[mistral] OCR %s via %s ...", Path(pdf_path).name, self.ocr_model)
        # Every leg goes through _classify: an unwrapped SDKError would escape the
        # pipeline's BackendError handling entirely and abort the whole run on a 429.
        up = self._retry(lambda: self._upload(pdf_path, raw))
        try:
            url = self._retry(lambda: self._signed_url(up.id))
            resp = self._retry(lambda: self._ocr_call(url))
        finally:
            try:
                self.client.files.delete(file_id=up.id)
            except Exception:  # noqa: BLE001
                log.debug("[mistral] could not delete uploaded file %s", up.id)

        pages = []
        for p in resp.pages:
            md = p.markdown or ""
            # extract_footer pulls the page footer out of the body. That is right for a
            # folio and WRONG for a footnote, so content-bearing footers are re-attached
            # (flagged so stage 2 can turn them back into \footnote at their marker).
            if _footer_is_content(getattr(p, "footer", None)):
                md = f"{md}\n\n<!-- footnote -->\n{p.footer.strip()}"
            pages.append({"index": p.index, "markdown": md})

        billed = len(pages)
        ui = getattr(resp, "usage_info", None)
        if ui and getattr(ui, "pages_processed", None):
            billed = ui.pages_processed

        if cache:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            cache.write_text(json.dumps({"schema": "texify-ocr/1",
                                         "ocr_model": self.ocr_model,
                                         "source": Path(pdf_path).name,
                                         "pages": pages}, ensure_ascii=False),
                             encoding="utf-8")
        chars = sum(len(p["markdown"]) for p in pages)
        log.info("[mistral] OCR %s -> %d pages, %d chars (~%d/pp), %d page(s) billed.",
                 Path(pdf_path).name, len(pages), chars,
                 chars // max(len(pages), 1), billed)
        return pages, billed

    def _upload(self, pdf_path: str, raw: bytes):
        try:
            return self.client.files.upload(
                file={"file_name": Path(pdf_path).name, "content": raw}, purpose="ocr")
        except Exception as e:  # noqa: BLE001
            raise self._classify(e, "upload") from e

    def _signed_url(self, file_id: str) -> str:
        try:
            return self.client.files.get_signed_url(file_id=file_id, expiry=1).url
        except Exception as e:  # noqa: BLE001
            raise self._classify(e, "signed_url") from e

    def _ocr_call(self, signed_url: str):
        try:
            return self.client.ocr.process(
                model=self.ocr_model,
                document={"type": "document_url", "document_url": signed_url},
                extract_header=True,     # running heads are noise; drop them
                extract_footer=True,     # folios are noise — footnotes are re-attached above
                include_image_base64=False,
                timeout_ms=MISTRAL_OCR_TIMEOUT * 1000,
            )
        except Exception as e:  # noqa: BLE001
            raise self._classify(e, "ocr") from e

    # -- stage 2: chat ---------------------------------------------------------

    def _chat(self, system_prompt: str, user: str):
        kw = dict(
            model=self.model,
            messages=[{"role": "system", "content": system_prompt},
                      {"role": "user", "content": user}],
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            timeout_ms=MISTRAL_CHAT_TIMEOUT * 1000,
        )
        if self.reasoning_effort:
            kw["reasoning_effort"] = self.reasoning_effort
        try:
            return self.client.chat.complete(**kw)
        except Exception as e:  # noqa: BLE001
            # Models without the `reasoning` capability 400 on reasoning_effort, and the
            # ones that have it accept only a subset of levels. Either way the request is
            # otherwise fine: drop the arg, remember, and retry once.
            if kw.get("reasoning_effort") and "reasoning_effort" in str(e):
                log.warning("[mistral] %s rejected reasoning_effort=%r (%s); retrying "
                            "without it.", self.model, self.reasoning_effort,
                            str(e)[:120])
                self.reasoning_effort = None
                kw.pop("reasoning_effort")
                try:
                    return self.client.chat.complete(**kw)
                except Exception as e2:  # noqa: BLE001
                    raise self._classify(e2, "chat") from e2
            raise self._classify(e, "chat") from e

    # -- shared plumbing -------------------------------------------------------

    @staticmethod
    def _render(pages: list[dict], head: Optional[int] = None) -> str:
        """Per-page Markdown joined with explicit page markers, so stage 2 can tell a
        page break from a paragraph break and stitch across it."""
        out = []
        for i, p in enumerate(pages):
            md = p["markdown"]
            if head is not None and len(md) > head:
                md = md[:head] + "\n… [page truncated for probe]"
            out.append(f"<!-- page {i + 1} -->\n{md}")
        return "\n\n".join(out)

    def _retry(self, fn):
        """Mistral-specific retry. The base `_with_retry` backs off 5/10/20/40s, which is
        right for a 5xx blip and FAR too short for a 429: Mistral rate-limits on a
        tokens-per-minute bucket, and one reasoning-model call can spend ~56k tokens, so
        the bucket needs minutes to refill, not seconds. Honour `Retry-After` when the
        server sends it; otherwise back off from a much larger base for rate limits only.
        """
        last: Optional[_RetryableMistral] = None
        for attempt in range(MAX_RETRIES):
            try:
                return fn()
            except _RetryableMistral as e:
                last = e
                if e.retry_after:
                    wait = e.retry_after
                else:
                    base = (MISTRAL_RATE_LIMIT_BACKOFF if e.rate_limited
                            else BACKOFF_BASE)
                    wait = base * (2 ** attempt)
                log.warning("[mistral] %s (%s); retry %d/%d in %ds",
                            "RATE LIMITED" if e.rate_limited else "transient error",
                            e, attempt + 1, MAX_RETRIES, wait)
                time.sleep(wait)
        raise BackendError(f"[mistral] exhausted retries: {last}")

    @staticmethod
    def _classify(e: Exception, stage: str) -> Exception:
        """Map an SDK exception onto the pipeline's three-way outcome: retry, policy
        block, or hard failure. Getting this wrong is expensive in both directions — a
        retried policy block wastes four backoffs, a non-retried 429 fails a chapter."""
        status = getattr(e, "status_code", None)
        body = str(getattr(e, "body", "") or "")
        msg = f"{e}"[:500]
        if status == 429 or re.search(r"rate.?limit", body or msg, re.I):
            return _RetryableMistral(f"[mistral/{stage}] {msg}", rate_limited=True,
                                     retry_after=_retry_after_seconds(e))
        if status in (408, 409, 500, 502, 503, 504) or \
                re.search(r"timeout|timed out|connection|temporarily unavailable",
                          msg, re.I):
            return _RetryableMistral(f"[mistral/{stage}] {msg}")
        # A guardrail rejection is a 400 whose body talks about policy, not parameters.
        if status in (400, 403, 422) and is_policy_block(body or msg):
            return BlockedByPolicyError(f"[mistral/{stage}] content policy block: {msg}")
        if isinstance(e, (BackendError, BlockedByPolicyError)):
            return e
        return BackendError(f"[mistral/{stage}] {msg}")


def _retry_after_seconds(e: Exception) -> Optional[int]:
    """The server's own `Retry-After`, if it sent one — always better than our guess."""
    resp = getattr(e, "raw_response", None)
    try:
        v = resp.headers.get("retry-after") if resp is not None else None
        return max(1, min(int(float(v)), 900)) if v else None
    except (TypeError, ValueError, AttributeError):
        return None


class _RetryableMistral(RuntimeError):
    """Internal marker for transient Mistral API failures worth retrying."""

    def __init__(self, msg: str, *, rate_limited: bool = False,
                 retry_after: Optional[int] = None):
        super().__init__(msg)
        self.rate_limited = rate_limited
        self.retry_after = retry_after


# ============================== fallback backend ==============================

# Per-chunk output below this many chars-per-page is treated as a non-completion
# (lazy stub or in-band "soft" refusal) and triggers the fallback, just like a hard
# block. Faithful conversion runs ~2000+ chars/pp; a stub/refusal is a few hundred
# (a 18pp chunk that came back as 5 KB == 279/pp). Generous floor — well under any
# real chunk (even a knitr lab, output omitted, runs ~1900/pp), well over a stub.
MIN_CHARS_PER_PAGE = 800


# ========================== split-retry (same engine) =========================

# How deep the halving may go: 20pp -> 10 -> 5 -> 3 -> 2 -> 1. Four levels reaches single
# pages from any chunk the chunker will build, and bounds the worst case at 2**4 calls.
SPLIT_MAX_DEPTH = 4

# Trailing LaTeX handed from one half to the next, mirroring the orchestrator's chunk seam.
SPLIT_HANDOFF_TAIL_CHARS = 800

# Appended to every half except the last, so the model does not invent an `\end` for an
# environment whose content continues onto a page it cannot see. The orchestrator imports
# this same constant for its own chunk seams — one definition, one wording.
SEAM_CAUTION = (
    "PAGINATION: if the final page here cuts off mid-sentence or mid-environment, "
    "stop exactly at the cutoff. Do NOT invent an \\end{...} to close an "
    "environment whose content clearly continues onto a page outside this chunk."
)


class SplitRetryBackend(Backend):
    """Wrap ONE engine so a non-completion is retried on SMALLER PAGE RANGES of the same
    chunk **before** the caller gives up on that engine.

    A stub or refusal is usually provoked by a few dense pages, not by the whole chunk. So
    when the engine fails to complete a multi-page PDF, halve it and re-ask the SAME
    engine on each half, recursing until the pages that actually fail are isolated. That
    beats handing the whole chunk to a different engine on the first stumble: the primary
    converts the pages it can, engines are not mixed mid-chunk for no reason, and only the
    genuinely stubborn pages ever change engine.

    Only when a SINGLE page still fails (or `SPLIT_MAX_DEPTH` is hit) does this raise
    `BlockedByPolicyError` — which is exactly what makes `FallbackBackend` advance. The two
    compose: split within an engine first, switch engines last.

    Deliberately all-or-nothing per chunk: if one half still fails at single-page
    granularity, the whole chunk (including the half this engine DID convert) goes to the
    next engine. Stitching two engines inside one chunk would mix notation habits mid-proof
    for the sake of saving one call. NOTE: the book pipeline had a `texify_refine` pass that
    # recovered a blocked chunk PAGE BY PAGE afterwards; it is gone, so a chunk all three
    # engines refuse leaves a `% UNCONVERTED` marker and you fill it with --spans or by hand
    granularity, after the fact and under human eyes.

    A structure probe (`expect_short`) is never split: it legitimately returns a tiny body,
    and halving it would just produce two partial outlines.
    """

    def __init__(self, inner: Backend, *,
                 min_chars_per_page: int = 0,
                 max_depth: int = SPLIT_MAX_DEPTH):
        if not _HAS_PYPDF:
            raise BackendError("pypdf is required for split-retry; `pip install pypdf`.")
        super().__init__(inner.model)
        self.inner = inner
        self.name = inner.name          # logs read as the engine, not the wrapper
        self.min_cpp = min_chars_per_page or MIN_CHARS_PER_PAGE
        self.max_depth = max_depth

    def convert(self, pdf_path, system_prompt, task_prompt, *,
                context_handoff=None, expect_short=False) -> ConversionResult:
        return self._convert(pdf_path, system_prompt, task_prompt,
                             context_handoff, expect_short, depth=0)

    # -- internals -------------------------------------------------------------

    def _convert(self, pdf, sysp, task, handoff, expect_short, depth) -> ConversionResult:
        n = pdf_page_count(pdf) or 1
        try:
            res = self.inner.convert(pdf, sysp, task,
                                     context_handoff=handoff, expect_short=expect_short)
            if expect_short or len(res.text or "") >= self.min_cpp * n:
                return res
            reason = (f"non-completion: {len(res.text or '')} chars for {n}pp "
                      f"(< {self.min_cpp}/pp floor)")
        except BlockedByPolicyError as e:
            reason = f"content block: {e}"

        if expect_short or n <= 1 or depth >= self.max_depth:
            raise BlockedByPolicyError(
                f"[{self.name}] {reason}; cannot split further "
                f"(pages={n}, depth={depth})")

        log.warning("[%s] %s — splitting %dpp in half and retrying the SAME engine "
                    "(depth %d) BEFORE any fallback.", self.name, reason, n, depth + 1)
        return self._split_and_convert(pdf, sysp, task, handoff, n, depth)

    def _split_and_convert(self, pdf, sysp, task, handoff, n, depth) -> ConversionResult:
        mid = n // 2
        spans = [(0, mid - 1), (mid, n - 1)]
        tmpdir = tempfile.mkdtemp(prefix="texify_split_")
        pieces: list[str] = []
        cost = 0.0
        trunc = False
        # Seeded empty: the OUTER open-env stack rides in on `handoff`, which the first
        # half receives verbatim. scan_open_environments tolerates an `\end` closing
        # something from before the seed, so a half that closes an outer env is fine.
        carry: list[str] = []
        cur_handoff = handoff
        try:
            for i, (a, b) in enumerate(spans):
                part = self._slice(pdf, a, b, tmpdir, i)
                t = task if i == len(spans) - 1 else f"{task}\n\n{SEAM_CAUTION}"
                res = self._convert(part, sysp, t, cur_handoff, False, depth + 1)
                pieces.append(res.text)
                cost += res.cost_usd or 0.0
                trunc = trunc or res.truncated
                carry = scan_open_environments(res.text, initial_stack=carry)
                cur_handoff = _split_handoff(carry, res.text[-SPLIT_HANDOFF_TAIL_CHARS:])
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

        text = "\n".join(pieces)
        log.info("[%s] split-retry recovered %dpp as %d part(s), %d chars.",
                 self.name, n, len(spans), len(text))
        return ConversionResult(
            text=text, backend=self.name, model=self.model, truncated=trunc,
            open_environments=scan_open_environments(text),
            cost_usd=cost or None, usage=None, pdf_path=pdf,
        )

    @staticmethod
    def _slice(pdf: str, a: int, b: int, outdir: str, idx: int) -> str:
        from pypdf import PdfWriter
        reader = PdfReader(pdf)
        w = PdfWriter()
        for p in range(a, b + 1):
            w.add_page(reader.pages[p])
        out = str(Path(outdir) / f"part{idx}_p{a}-{b}.pdf")
        with open(out, "wb") as fh:
            w.write(fh)
        return out


def _split_handoff(open_envs: list[str], tail: str) -> str:
    """The chunker owns the seam wording; reuse it so a split seam and a chunk seam say
    exactly the same thing. Imported lazily — texify_chunker imports no engine, so there
    is no cycle, and this module still loads if the chunker is absent."""
    try:
        from texify_chunker import build_context_handoff
        return build_context_handoff(open_envs, tail)
    except Exception:  # pragma: no cover - chunker absent in a bare smoke test
        return ""


class FallbackBackend(Backend):
    """Try several backends IN ORDER, advancing to the next when the current one
    fails to *complete* the conversion — either a hard `BlockedByPolicyError`, OR a
    SOFT non-completion: an in-band refusal / lazy stub that comes back as a
    suspiciously short body (see `MIN_CHARS_PER_PAGE`). Both matter, because a model
    asked to reproduce copyrighted text may refuse SOFTLY (a short "I can't…" or a
    summary) without tripping the API content-filter — that wouldn't raise, so a
    block-only fallback would silently accept the stub.

    The norm is Claude Opus 4.7 (high effort) first, then Mistral, then Gemini 3.1 Pro —
    different engines refuse different passages. A transient / non-policy *exception* is
    NOT a reason to switch engines, so it propagates unchanged. If EVERY backend fails to
    complete, raise `BlockedByPolicyError` (the orchestrator then records the chunk as
    unconverted).

    Each entry is normally a `SplitRetryBackend`, so an engine only counts as "failed to
    complete" AFTER it has re-tried the chunk on smaller page ranges. Switching engines is
    therefore the last resort, not the first response to a stub: a stub usually comes from
    a few dense pages, and halving isolates them without changing engine at all.

    Continuity is the text handoff so ANY backend can convert ANY chunk: one that
    falls through to the secondary still receives the same open-environment +
    trailing-LaTeX context as the primary would have.
    """
    name = "fallback"

    def __init__(self, backends: list[Backend],
                 min_chars_per_page: int = MIN_CHARS_PER_PAGE):
        if not backends:
            raise ValueError("FallbackBackend needs at least one backend")
        self.backends = backends
        self.min_cpp = min_chars_per_page
        super().__init__(backends[0].model)

    def convert(self, pdf_path, system_prompt, task_prompt, *,
                context_handoff=None, expect_short=False) -> ConversionResult:
        npages = pdf_page_count(pdf_path) or 0
        # The short-output floor detects soft stubs in a CONVERSION; a structure probe
        # (expect_short) legitimately returns a tiny list, so disable the floor for it.
        floor = 0 if expect_short else self.min_cpp * npages
        last: Optional[BlockedByPolicyError] = None
        for i, b in enumerate(self.backends):
            more = i + 1 < len(self.backends)
            try:
                res = b.convert(pdf_path, system_prompt, task_prompt,
                                context_handoff=context_handoff, expect_short=expect_short)
            except BlockedByPolicyError as e:
                last = e
                # NOT necessarily a policy refusal. SplitRetryBackend raises this SAME exception
                # when the output merely fell under the --min-chars-per-page floor and the chunk
                # cannot be split further — so a short-but-CORRECT answer (a one-entry reference
                # list; a "Notes and References" page whose numbered list must NOT be transcribed)
                # is reported as three engines "blocking" it, and the chunk is written off as
                # UNCONVERTED. Nothing was blocked. Name the real cause, or the next reader goes
                # hunting a guardrail that never fired.
                kind = ("short output, under the --min-chars-per-page floor — NOT a policy "
                        "refusal; lower the floor" if "non-completion" in str(e)
                        else "hard content-block")
                log.warning("[fallback] %s: %s; %s", b.name, kind,
                            "trying next backend" if more else "no backend left")
                continue
            ntext = len(res.text or "")
            if floor and ntext < floor:
                # SOFT non-completion: short stub / in-band refusal. Treat like a block.
                last = BlockedByPolicyError(
                    f"[{b.name}] non-completion: {ntext} chars for {npages}pp "
                    f"(< {self.min_cpp}/pp floor) — likely a stub or soft refusal")
                log.warning("[fallback] %s; %s", last,
                            "trying next backend" if more else "no backend left")
                continue
            if i:
                log.info("[fallback] %s completed it after %d fallback(s).", b.name, i)
            return res
        raise BlockedByPolicyError(
            f"[fallback] no backend completed ({', '.join(b.name for b in self.backends)}); "
            f"last: {last}")


# ================================= factory ====================================

def get_backend(name: str, *, model: Optional[str] = None, **kwargs) -> Backend:
    name = name.lower()
    if name == "mistral":
        return MistralBackend(model or MISTRAL_TEXT_MODEL, **kwargs)
    if name == "gemini":
        return GeminiBackend(model or GEMINI_MODEL, **kwargs)
    if name == "claude":
        return ClaudeCliBackend(model or CLAUDE_MODEL, **kwargs)
    raise ValueError(
        f"unknown backend {name!r} (expected 'mistral', 'gemini' or 'claude')")


# The task prompt is identical for both engines; the backend wires in the PDF.
DEFAULT_TASK_PROMPT = (
    "Convert this PDF to LaTeX following the system instructions exactly. "
    "Output ONLY pure LaTeX body content. Do NOT include \\documentclass, "
    "\\usepackage, \\begin{document}, or \\end{document}, and do NOT wrap the "
    "output in markdown code fences. Do NOT preface the output with any "
    "explanation, plan, acknowledgement, or commentary: the VERY FIRST character "
    "of your response must be a backslash or a percent sign (%)."
)


# ============================ manual smoke test ===============================

if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")
    ap = argparse.ArgumentParser(description="Convert one PDF with one backend.")
    ap.add_argument("--backend", choices=["mistral", "gemini", "claude"], required=True)
    ap.add_argument("--pdf", required=True)
    ap.add_argument("--prompt", required=True, help="path to the spec (prompt.txt)")
    ap.add_argument("--model", default=None)
    ap.add_argument("--out", default=None, help="write LaTeX here instead of stdout")
    ap.add_argument("--stream", action="store_true",
                    help="claude only: stream-json for exact truncation detection")
    ap.add_argument("--no-ocr-cache", action="store_true",
                    help="mistral only: re-OCR even if a cached transcription exists")
    args = ap.parse_args()

    spec = Path(args.prompt).read_text(encoding="utf-8")
    kw = {}
    if args.backend == "claude":
        kw = {"use_stream_json": args.stream}
    elif args.backend == "mistral" and args.no_ocr_cache:
        kw = {"cache_dir": None}
    backend = get_backend(args.backend, model=args.model, **kw)

    res = backend.convert(args.pdf, spec, DEFAULT_TASK_PROMPT)

    log.info("done: %d chars | truncated=%s | open_env=%s | cost=%s",
             len(res.text), res.truncated, res.open_environments, res.cost_usd)
    if args.out:
        Path(args.out).write_text(res.text, encoding="utf-8")
        log.info("wrote %s", args.out)
    else:
        print(res.text)
