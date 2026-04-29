"""Gradio demo app for the Business Intelligence AI Assistant."""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Any

import gradio as gr

from app.config import load_settings
from app.llm_client import LLMConnectionError
from app.router import AssistantRouter

RAG_EXAMPLES = [
    "What is payment success rate?",
    "How are failed payments reviewed?",
    "How are high-value clients classified?",
]

SQL_EXAMPLES = [
    "Show total payment amount by provider.",
    "Which month had the highest number of failed payments?",
    "List the top 10 clients by total payment amount.",
]

HYBRID_EXAMPLES = [
    "Using the KPI definition, calculate the payment success rate from the database.",
    "According to the client segmentation rules, how many high-value clients do we have?",
    "Based on the provider failure-rate threshold in the policy, which providers should be reviewed?",
]

EXAMPLE_CHOICES = [
    *[f"RAG - {question}" for question in RAG_EXAMPLES],
    *[f"SQL - {question}" for question in SQL_EXAMPLES],
    *[f"Hybrid - {question}" for question in HYBRID_EXAMPLES],
]

CUSTOM_CSS = """
:root {
  --bi-bg: #070b14;
  --bi-bg-soft: #0b1020;
  --bi-panel: rgba(17, 25, 42, 0.92);
  --bi-panel-soft: rgba(22, 33, 54, 0.86);
  --bi-panel-strong: rgba(10, 16, 28, 0.96);
  --bi-border: rgba(148, 163, 184, 0.18);
  --bi-border-strong: rgba(148, 163, 184, 0.32);
  --bi-muted: #94a3b8;
  --bi-muted-2: #64748b;
  --bi-text: #f8fafc;
  --bi-text-soft: #dbeafe;
  --bi-blue: #3b82f6;
  --bi-blue-strong: #2563eb;
  --bi-cyan: #38bdf8;
  --bi-violet: #8b5cf6;
  --bi-green: #22c55e;
  --bi-code-bg: #0a1020;
  --bi-shadow: 0 24px 80px rgba(0, 0, 0, 0.38);
  --bi-shadow-soft: 0 12px 40px rgba(0, 0, 0, 0.28);
  --bi-radius: 16px;
  --bi-radius-sm: 10px;
}

/* Page background */
html,
body {
  width: 100% !important;
  min-height: 100% !important;
  margin: 0 !important;
  padding: 0 !important;
  color: var(--bi-text) !important;
  background:
    radial-gradient(circle at 18% 8%, rgba(59, 130, 246, 0.20), transparent 28%),
    radial-gradient(circle at 88% 18%, rgba(139, 92, 246, 0.16), transparent 28%),
    radial-gradient(circle at 50% 105%, rgba(56, 189, 248, 0.08), transparent 28%),
    linear-gradient(180deg, #060914 0%, #080d19 42%, #050812 100%) !important;
  background-attachment: fixed !important;
}

/* The app container stays centered, but transparent */
.gradio-container {
  color: var(--bi-text) !important;
  background: transparent !important;
}

.gradio-container {
  max-width: 1520px !important;
  margin: 0 auto !important;
  padding: 0 18px 18px !important;
}

/* Global typography smoothing */
* {
  box-sizing: border-box !important;
}

.gradio-container,
.gradio-container * {
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;
}

/* Hero */
.bi-hero {
  padding: 28px 6px 18px;
}

.bi-hero h1 {
  margin: 0 0 8px;
  font-size: 34px;
  line-height: 1.05;
  letter-spacing: -0.04em;
  font-weight: 800;
  color: var(--bi-text);
  text-shadow: 0 0 28px rgba(59, 130, 246, 0.18);
}

.bi-hero p {
  margin: 0;
  color: var(--bi-muted);
  font-size: 15px;
  line-height: 1.55;
  max-width: 980px;
}

/* Main panels */
.bi-panel {
  position: relative;
  border: 1px solid var(--bi-border) !important;
  border-radius: var(--bi-radius) !important;
  background:
    linear-gradient(180deg, rgba(30, 41, 59, 0.72), rgba(15, 23, 42, 0.90)) !important;
  color: var(--bi-text) !important;
  box-shadow: var(--bi-shadow-soft) !important;
  backdrop-filter: blur(18px);
  overflow: hidden;
}

.bi-panel::before {
  content: "";
  position: absolute;
  inset: 0;
  pointer-events: none;
  border-radius: inherit;
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.08), transparent 32%),
    radial-gradient(circle at top left, rgba(59, 130, 246, 0.14), transparent 38%);
}

/* Gradio blocks inside panels */
.bi-details {
  overflow: visible;
  overflow-x: hidden;
}

.bi-details,
.bi-context,
.bi-chat {
  min-width: 0 !important;
}

.bi-details,
.bi-details > *,
.bi-details .block,
.bi-details .prose,
.bi-details .gradio-accordion,
.bi-details details,
.bi-details summary {
  background: transparent !important;
  color: var(--bi-text) !important;
  border-color: var(--bi-border) !important;
  max-width: 100% !important;
  min-width: 0 !important;
}

/* Details / trace panel */
.bi-details h3 {
  margin-top: 0;
  margin-bottom: 10px;
  font-size: 15px;
  letter-spacing: 0.01em;
  color: var(--bi-text);
}

.bi-details p,
.bi-details li {
  color: var(--bi-text-soft) !important;
}

.bi-details details {
  border-radius: var(--bi-radius-sm) !important;
  overflow: hidden !important;
  background: rgba(15, 23, 42, 0.55) !important;
  border: 1px solid var(--bi-border) !important;
  margin-bottom: 10px !important;
}

.bi-details summary {
  font-weight: 700 !important;
  color: var(--bi-text) !important;
  padding: 10px 12px !important;
  background: rgba(15, 23, 42, 0.68) !important;
}

.bi-meta code {
  white-space: pre-wrap !important;
}

/* Retrieved context */
.bi-context {
  box-sizing: border-box !important;
  width: 100% !important;
  max-width: 100% !important;
  max-height: 380px;
  overflow: auto;
  overflow-x: hidden;
  overflow-wrap: anywhere;
  word-break: normal;
  background:
    linear-gradient(180deg, rgba(8, 13, 25, 0.96), rgba(11, 18, 32, 0.96)) !important;
  color: var(--bi-text) !important;
  padding: 12px 14px !important;
  border-radius: var(--bi-radius-sm) !important;
  border: 1px solid var(--bi-border) !important;
}

/* Context text */
.bi-context,
.bi-context > *,
.bi-context .prose,
.bi-context .markdown,
.bi-context p,
.bi-context li,
.bi-context h1,
.bi-context h2,
.bi-context h3,
.bi-meta,
.bi-meta p,
.bi-meta h3,
.bi-details p,
.bi-details li,
.bi-details h3 {
  color: var(--bi-text) !important;
}

.bi-context h3 {
  font-size: 15px;
  margin: 14px 0 7px;
  color: #e0f2fe !important;
}

.bi-context h1,
.bi-context h2 {
  font-size: 18px !important;
  line-height: 1.2 !important;
  overflow-wrap: anywhere !important;
}

.bi-context p,
.bi-context li {
  font-size: 13px;
  line-height: 1.5;
  color: #cbd5e1 !important;
  max-width: 100% !important;
}

/* Chat */
.bi-chat {
  border-radius: var(--bi-radius) !important;
}

.bi-chat .message,
.bi-chat .message p,
.bi-chat .message li {
  font-size: 15px !important;
  line-height: 1.58 !important;
}

.bi-chat .message {
  border-radius: 14px !important;
}

/* Assistant message premium look */
.bi-chat .message.bot,
.bi-chat .message.assistant {
  background: rgba(15, 23, 42, 0.72) !important;
  border: 1px solid rgba(148, 163, 184, 0.14) !important;
}

/* User message */
.bi-chat .message.user {
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.95), rgba(59, 130, 246, 0.78)) !important;
  color: white !important;
  border: 1px solid rgba(147, 197, 253, 0.26) !important;
}

/* Code blocks */
.bi-chat pre,
.bi-details pre,
.bi-context pre {
  border-radius: var(--bi-radius-sm) !important;
  border: 1px solid rgba(96, 165, 250, 0.20) !important;
  background:
    linear-gradient(180deg, rgba(6, 11, 22, 0.98), rgba(10, 16, 30, 0.98)) !important;
  max-width: 100% !important;
  overflow-x: hidden !important;
  white-space: pre-wrap !important;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.035) !important;
}

.bi-details pre code,
.bi-context pre code,
.bi-chat pre code {
  background: transparent !important;
  color: #dbeafe !important;
  white-space: pre-wrap !important;
  overflow-wrap: anywhere !important;
  font-size: 12.5px !important;
  line-height: 1.5 !important;
}

/* Inline code */
.bi-details p code,
.bi-details li code,
.bi-context p code,
.bi-context li code,
.bi-chat p code,
.bi-chat li code {
  white-space: pre-wrap !important;
  overflow-wrap: anywhere !important;
  background: rgba(15, 23, 42, 0.95) !important;
  color: #bfdbfe !important;
  border: 1px solid rgba(96, 165, 250, 0.20) !important;
  border-radius: 6px !important;
  padding: 2px 5px !important;
}

/* Inputs */
.bi-input textarea,
textarea {
  font-size: 15px !important;
  color: var(--bi-text) !important;
  background: rgba(15, 23, 42, 0.92) !important;
  border: 1px solid var(--bi-border) !important;
  border-radius: 12px !important;
}

.bi-input textarea:focus,
textarea:focus {
  border-color: rgba(96, 165, 250, 0.72) !important;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.18) !important;
}

/* Buttons */
button,
.gr-button {
  border-radius: 12px !important;
  font-weight: 700 !important;
  border: 1px solid rgba(148, 163, 184, 0.18) !important;
  transition: transform 0.14s ease, box-shadow 0.14s ease, border-color 0.14s ease !important;
}

button:hover,
.gr-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 12px 28px rgba(0, 0, 0, 0.24) !important;
  border-color: rgba(96, 165, 250, 0.35) !important;
}

/* Primary button */
button.primary,
.gr-button-primary {
  background:
    linear-gradient(135deg, var(--bi-blue-strong), var(--bi-blue), var(--bi-cyan)) !important;
  color: white !important;
  border: 1px solid rgba(147, 197, 253, 0.32) !important;
}

/* Dropdowns / inputs / forms */
input,
select,
.gr-dropdown,
.gr-textbox,
.gr-form,
.gr-input {
  background: rgba(15, 23, 42, 0.88) !important;
  color: var(--bi-text) !important;
  border-color: var(--bi-border) !important;
  border-radius: 12px !important;
}

/* Labels / badges */
label,
span.label,
.block-label {
  color: #dbeafe !important;
  font-weight: 700 !important;
}

/* Tables if Markdown renders any */
table {
  border-collapse: collapse !important;
  width: 100% !important;
  overflow: hidden !important;
  border-radius: var(--bi-radius-sm) !important;
}

th {
  background: rgba(30, 41, 59, 0.95) !important;
  color: #e0f2fe !important;
}

td,
th {
  border: 1px solid rgba(148, 163, 184, 0.16) !important;
  padding: 8px 10px !important;
}

td {
  color: #e2e8f0 !important;
}

/* Scrollbars */
*::-webkit-scrollbar {
  width: 10px;
  height: 10px;
}

*::-webkit-scrollbar-track {
  background: rgba(15, 23, 42, 0.7);
  border-radius: 999px;
}

*::-webkit-scrollbar-thumb {
  background: linear-gradient(180deg, rgba(59, 130, 246, 0.65), rgba(139, 92, 246, 0.55));
  border-radius: 999px;
  border: 2px solid rgba(15, 23, 42, 0.9);
}

*::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(180deg, rgba(96, 165, 250, 0.8), rgba(167, 139, 250, 0.72));
}

/* Footer */
footer {
  color: var(--bi-muted-2) !important;
}

/* Small screens */
@media (max-width: 900px) {
  .gradio-container {
    padding: 0 12px 14px !important;
  }

  .bi-hero h1 {
    font-size: 27px;
  }

  .bi-hero p {
    font-size: 14px;
  }
}
"""

CUSTOM_CSS += """

/* =========================================================
   Right trace panel cleanup
   ========================================================= */

/* Remove the strong diagonal glow specifically from the trace panel */
.bi-details.bi-panel,
.bi-details .bi-panel {
  background:
    linear-gradient(180deg, rgba(17, 24, 39, 0.96), rgba(8, 13, 25, 0.98)) !important;
  border: 1px solid rgba(148, 163, 184, 0.20) !important;
  box-shadow: 0 18px 55px rgba(0, 0, 0, 0.30) !important;
}

/* Disable the glossy overlay on the right panel */
.bi-details.bi-panel::before,
.bi-details .bi-panel::before {
  display: none !important;
}

/* Make inner blocks inside right panel look less boxed/cut */
.bi-details .block,
.bi-details .form,
.bi-details .gr-form,
.bi-details .gr-box,
.bi-details .prose {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  overflow: visible !important;
}

/* Route metadata text should not be clipped */
.bi-details,
.bi-details * {
  overflow-wrap: anywhere !important;
}

.bi-details p,
.bi-details li,
.bi-details span,
.bi-details div {
  line-height: 1.55 !important;
}

/* Give the route card more breathing room */
.bi-meta {
  padding: 4px 2px 8px !important;
  overflow: visible !important;
}

.bi-meta h3 {
  margin-bottom: 12px !important;
}

.bi-meta p {
  margin: 8px 0 !important;
  color: #dbeafe !important;
}

/* Remove harsh box around reason/route text if Gradio adds one */
.bi-details textarea,
.bi-details input,
.bi-details .output-markdown,
.bi-details .markdown,
.bi-details .prose {
  min-height: auto !important;
  height: auto !important;
  max-height: none !important;
}


/* =========================================================
   Accordion polish
   ========================================================= */

.bi-details details {
  background: rgba(8, 13, 25, 0.74) !important;
  border: 1px solid rgba(148, 163, 184, 0.16) !important;
  border-radius: 12px !important;
  margin: 12px 0 !important;
}

.bi-details summary {
  background: rgba(15, 23, 42, 0.82) !important;
  border-bottom: 1px solid rgba(148, 163, 184, 0.12) !important;
  padding: 11px 13px !important;
  color: #e2e8f0 !important;
}

/* Remove weird bright triangle/edge effects */
.bi-details summary::marker {
  color: #93c5fd !important;
}


/* =========================================================
   Code blocks in right panel
   ========================================================= */

.bi-details pre {
  background: #070b14 !important;
  border: 1px solid rgba(96, 165, 250, 0.18) !important;
  border-radius: 12px !important;
  padding: 12px !important;
  margin: 8px 0 !important;
  box-shadow: none !important;
}

.bi-details pre code {
  color: #dbeafe !important;
  font-size: 12.5px !important;
  line-height: 1.55 !important;
}


/* =========================================================
   Retrieved context card cleanup
   ========================================================= */

.bi-context {
  background: #070b14 !important;
  border: 1px solid rgba(148, 163, 184, 0.18) !important;
  border-radius: 12px !important;
  box-shadow: none !important;
  max-height: 420px !important;
}

/* Avoid huge glowing inner cards in retrieved chunks */
.bi-context .block,
.bi-context .prose,
.bi-context .markdown {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
}


/* =========================================================
   Main chat panel small cleanup
   ========================================================= */

.bi-chat {
  min-height: 520px !important;
}

.bi-chat .message {
  max-width: 100% !important;
}

/* Make bottom controls span nicely */
.bi-input {
  width: 100% !important;
}


/* =========================================================
   Responsive padding
   ========================================================= */

@media (max-width: 1100px) {
  .gradio-container {
    padding: 0 18px 18px !important;
  }
}

@media (max-width: 700px) {
  .gradio-container {
    padding: 0 12px 14px !important;
  }
}
"""

CUSTOM_CSS += """
/* =========================================================
   Width refinement: premium dashboard width, not full stretch
   ========================================================= */

/* Keep page centered and wide, but not ultra-wide */
.gradio-container {
  width: 100% !important;
  max-width: 1500px !important;
  margin: 0 auto !important;
  padding: 0 28px 24px !important;
}

/* Remove previous forced full-width behavior */
.gradio-container > .main,
.gradio-container .main,
.gradio-container .wrap,
.gradio-container .contain {
  max-width: 1500px !important;
  width: 100% !important;
  margin-left: auto !important;
  margin-right: auto !important;
}

/* Keep hero aligned with the app width */
.bi-hero,
.gradio-container > div {
  max-width: 1500px !important;
  margin-left: auto !important;
  margin-right: auto !important;
}

/* Make main chat/result panel less horizontally stretched */
.bi-chat {
  max-width: 100% !important;
}

/* Make long tables/code outputs feel less absurdly wide */
.bi-chat table {
  max-width: 100% !important;
}

.bi-chat .message {
  max-width: 100% !important;
}

/* Slightly reduce visual dominance of the left answer panel */
.bi-panel {
  border-radius: 15px !important;
}

/* On large screens, avoid the left side eating the whole layout */
@media (min-width: 1300px) {
  .gradio-container {
    max-width: 1420px !important;
  }

  .bi-hero,
  .gradio-container > div {
    max-width: 1420px !important;
  }
}

/* On medium screens, still use available space */
@media (max-width: 1100px) {
  .gradio-container {
    max-width: none !important;
    padding: 0 18px 18px !important;
  }
}

/* =========================================================
   Full-width background, keep app width the same
   ========================================================= */

/* Make Gradio wrappers transparent so the body gradient shows through */
gradio-app,
#root,
.app,
.main,
.wrap,
.contain,
.gradio-container,
.gradio-container > .main,
.gradio-container .main,
.gradio-container .wrap,
.gradio-container .contain,
.gradio-container > div {
  background-color: transparent !important;
}

/* Keep the current app/content width */
.gradio-container {
  width: 100% !important;
  max-width: 1420px !important;
  margin: 0 auto !important;
  padding: 0 28px 24px !important;
}

/* Keep hero/content aligned exactly as before */
.bi-hero,
.gradio-container > div {
  max-width: 1420px !important;
  margin-left: auto !important;
  margin-right: auto !important;
}

/* Hide Gradio footer */
footer {
  display: none !important;
  visibility: hidden !important;
  height: 0 !important;
  min-height: 0 !important;
  margin: 0 !important;
  padding: 0 !important;
  overflow: hidden !important;
}
"""

CUSTOM_CSS += """
/* =========================================================
   Quick SQL/code block polish
   ========================================================= */

/* Code blocks: cleaner, darker, less wrapped */
.bi-chat pre,
.bi-details pre,
.bi-context pre {
  background: #050914 !important;
  border: 1px solid rgba(96, 165, 250, 0.22) !important;
  border-radius: 12px !important;
  padding: 14px 16px !important;
  margin: 10px 0 !important;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.04),
    0 10px 30px rgba(0, 0, 0, 0.22) !important;

  /* Important: make SQL look like SQL */
  overflow-x: auto !important;
  overflow-y: auto !important;
  white-space: pre !important;
  max-width: 100% !important;
}

/* Code text */
.bi-chat pre code,
.bi-details pre code,
.bi-context pre code {
  background: transparent !important;
  color: #dbeafe !important;
  font-family:
    "JetBrains Mono",
    "Fira Code",
    "Cascadia Code",
    Consolas,
    monospace !important;
  font-size: 12.5px !important;
  line-height: 1.65 !important;
  white-space: pre !important;
  overflow-wrap: normal !important;
  word-break: normal !important;
}

/* SQL query in the right panel: slightly smaller so it fits better */
.bi-details pre code {
  font-size: 11.5px !important;
  line-height: 1.55 !important;
}

/* Inline code stays readable but compact */
.bi-chat p code,
.bi-chat li code,
.bi-details p code,
.bi-details li code,
.bi-context p code,
.bi-context li code {
  background: rgba(15, 23, 42, 0.95) !important;
  color: #bfdbfe !important;
  border: 1px solid rgba(96, 165, 250, 0.18) !important;
  border-radius: 6px !important;
  padding: 2px 5px !important;
  font-family:
    "JetBrains Mono",
    "Fira Code",
    "Cascadia Code",
    Consolas,
    monospace !important;
  font-size: 0.88em !important;
}

/* Better scrollbar inside code blocks */
.bi-chat pre::-webkit-scrollbar,
.bi-details pre::-webkit-scrollbar,
.bi-context pre::-webkit-scrollbar {
  height: 8px;
}

.bi-chat pre::-webkit-scrollbar-thumb,
.bi-details pre::-webkit-scrollbar-thumb,
.bi-context pre::-webkit-scrollbar-thumb {
  background: rgba(96, 165, 250, 0.45);
  border-radius: 999px;
}

.bi-chat pre::-webkit-scrollbar-track,
.bi-details pre::-webkit-scrollbar-track,
.bi-context pre::-webkit-scrollbar-track {
  background: rgba(15, 23, 42, 0.8);
}
"""

@lru_cache(maxsize=1)
def get_router() -> AssistantRouter:
    """Create and cache the assistant router for the UI process."""
    return AssistantRouter()


def strip_example_prefix(choice: str | None) -> str:
    """Return the question text from a grouped example dropdown value."""
    if not choice:
        return ""
    if " - " not in choice:
        return choice
    return choice.split(" - ", 1)[1]


def format_sources(sources: list[str] | None) -> str:
    """Format source filenames for display."""
    if not sources:
        return "_No document sources for this route._"
    return "\n".join(f"- `{source}`" for source in sources)


def format_sql_query(sql_query: str | None) -> str:
    """Format SQL query metadata for display."""
    if not sql_query:
        return "_No SQL query for this route._"
    return f"```sql\n{sql_query.strip()}\n```"


def normalize_markdown(text: str) -> str:
    """Clean model markdown so it renders better in Gradio."""
    cleaned = text.strip()
    cleaned = cleaned.replace("\\[", "$$").replace("\\]", "$$")
    cleaned = cleaned.replace("\\(", "$").replace("\\)", "$")
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned


def format_retrieved_context(context: list[dict[str, Any]] | None) -> str:
    """Format retrieved document chunks for an expandable details panel."""
    if not context:
        return "_No retrieved document context for this route._"

    sections = []
    for index, chunk in enumerate(context, start=1):
        source = chunk.get("source", "unknown")
        chunk_index = chunk.get("chunk_index", "n/a")
        score = chunk.get("score")
        score_text = f"{score:.3f}" if isinstance(score, float) else "n/a"
        text = normalize_markdown(str(chunk.get("text", "")).strip())
        if len(text) > 900:
            text = f"{text[:900].rstrip()}..."
        sections.append(
            f"### {index}. `{source}`\n\n"
            f"Chunk `{chunk_index}` | score `{score_text}`\n\n{text}"
        )
    return "\n\n".join(sections)


def format_route_metadata(result: dict[str, Any]) -> str:
    """Format route decision metadata for display."""
    route = str(result.get("route", "unknown")).upper()
    reason = str(result.get("route_reason", "No route reason returned."))
    return f"### Route\n\n`{route}`\n\n### Reason\n\n{reason}"


def format_router_response(result: dict[str, Any]) -> tuple[str, str, str, str, str]:
    """Convert a router response into UI display sections."""
    answer = normalize_markdown(str(result.get("answer") or "No answer returned."))
    return (
        answer,
        format_route_metadata(result),
        format_sources(result.get("sources")),
        format_sql_query(result.get("sql_query")),
        format_retrieved_context(result.get("retrieved_context")),
    )


def normalize_chat_history(history: list[Any] | None) -> list[dict[str, str]]:
    """Convert Gradio chat history into message dictionaries."""
    normalized: list[dict[str, str]] = []
    for item in history or []:
        if isinstance(item, dict) and "role" in item and "content" in item:
            normalized.append(
                {"role": str(item["role"]), "content": extract_message_text(item["content"])}
            )
        elif isinstance(item, (list, tuple)) and len(item) >= 2:
            user_message, assistant_message = item[0], item[1]
            if user_message:
                normalized.append({"role": "user", "content": extract_message_text(user_message)})
            if assistant_message:
                normalized.append(
                    {"role": "assistant", "content": extract_message_text(assistant_message)}
                )
    return normalized


def extract_message_text(value: Any) -> str:
    """Extract plain text from Gradio/OpenAI-style message content blocks."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        if "text" in value:
            return extract_message_text(value["text"])
        if "content" in value:
            return extract_message_text(value["content"])
        return " ".join(extract_message_text(part) for part in value.values()).strip()
    if isinstance(value, (list, tuple)):
        parts = [extract_message_text(part) for part in value]
        return "\n".join(part for part in parts if part).strip()
    return str(value)


def answer_user_question(
    question: str,
    history: list[dict[str, str]] | None,
) -> tuple[list[dict[str, str]], str, str, str, str, str]:
    """Answer a user question and return updated chat plus detail panels."""
    history = normalize_chat_history(history)
    clean_question = str(question or "").strip()
    if not clean_question:
        return history, "", "_Ask a question to begin._", "", "", ""

    settings = load_settings()
    try:
        result = get_router().answer_question(clean_question)
        answer, route_md, sources_md, sql_md, context_md = format_router_response(result)
    except LLMConnectionError:
        answer = (
            "I could not reach the local LLM server. Start LM Studio's local server "
            f"and confirm it is reachable at `{settings.llm_base_url}`, then try again."
        )
        route_md = "**Route:** `ERROR`\n\n**Reason:** Local LLM server is not reachable."
        sources_md = "_No sources available._"
        sql_md = "_No SQL query available._"
        context_md = "_No retrieved context available._"
    except Exception as exc:
        answer = (
            "Something went wrong while answering the question. "
            f"Details: {exc}"
        )
        route_md = "**Route:** `ERROR`\n\n**Reason:** The assistant could not complete this request."
        sources_md = "_No sources available._"
        sql_md = "_No SQL query available._"
        context_md = "_No retrieved context available._"

    updated_history = [
        *history,
        {"role": "user", "content": clean_question},
        {"role": "assistant", "content": answer},
    ]
    return updated_history, "", route_md, sources_md, sql_md, context_md


def queue_user_question(
    question: str,
    history: list[dict[str, str]] | None,
) -> tuple[list[dict[str, str]], str, str, str, str, str, str]:
    """Immediately add the user message and a lightweight working state."""
    history = normalize_chat_history(history)
    clean_question = str(question or "").strip()
    if not clean_question:
        return (
            history,
            "",
            "",
            "### Route\n\n_Ask a question to begin._",
            "_Sources will appear here._",
            "_SQL query will appear here when applicable._",
            "_Retrieved document chunks will appear here._",
        )

    pending_history = [
        *history,
        {"role": "user", "content": clean_question},
        {
            "role": "assistant",
            "content": "Working on it...",
        },
    ]
    return (
        pending_history,
        "",
        clean_question,
        "### Route\n\n`PROCESSING`\n\n### Reason\n\nRouting and generating the answer...",
        "_Sources will appear here once retrieval finishes._",
        "_SQL query will appear here when applicable._",
        "_Retrieved document chunks will appear here when applicable._",
    )


def complete_queued_question(
    history: list[dict[str, str]] | None,
    pending_question: str,
) -> tuple[list[dict[str, str]], str, str, str, str, str]:
    """Replace the pending assistant message with the final router answer."""
    history = normalize_chat_history(history)
    question = str(pending_question or "").strip()
    if not question:
        return (
            history,
            "",
            "### Route\n\n_Ask a question to begin._",
            "_Sources will appear here._",
            "_SQL query will appear here when applicable._",
            "_Retrieved document chunks will appear here._",
        )

    settings = load_settings()
    try:
        result = get_router().answer_question(question)
        answer, route_md, sources_md, sql_md, context_md = format_router_response(result)
    except LLMConnectionError:
        answer = (
            "I could not reach the local LLM server. Start LM Studio's local server "
            f"and confirm it is reachable at `{settings.llm_base_url}`, then try again."
        )
        route_md = "**Route:** `ERROR`\n\n**Reason:** Local LLM server is not reachable."
        sources_md = "_No sources available._"
        sql_md = "_No SQL query available._"
        context_md = "_No retrieved context available._"
    except Exception as exc:
        answer = (
            "Something went wrong while answering the question. "
            f"Details: {exc}"
        )
        route_md = "**Route:** `ERROR`\n\n**Reason:** The assistant could not complete this request."
        sources_md = "_No sources available._"
        sql_md = "_No SQL query available._"
        context_md = "_No retrieved context available._"

    completed_history = [*history]
    if completed_history and completed_history[-1].get("role") == "assistant":
        completed_history[-1] = {"role": "assistant", "content": answer}
    else:
        completed_history.append({"role": "assistant", "content": answer})
    return completed_history, "", route_md, sources_md, sql_md, context_md


def create_app() -> gr.Blocks:
    """Create the Gradio Blocks interface."""
    with gr.Blocks(
        title="Business Intelligence AI Assistant",
        fill_width=True,
    ) as demo:
        gr.HTML(
            """
<section class="bi-hero">
  <h1>Business Intelligence AI Assistant</h1>
  <p>Local-first RAG + SQL assistant for synthetic FinSight PayOps data. Ask KPI, policy, segmentation, or analytical questions and inspect the route, sources, and SQL trail.</p>
</section>
"""
        )
        pending_question = gr.State("")

        with gr.Row():
            with gr.Column(scale=7, min_width=620):
                chatbot = gr.Chatbot(
                    label="Assistant",
                    height=620,
                    buttons=["copy", "copy_all"],
                    elem_classes=["bi-chat", "bi-panel"],
                    latex_delimiters=[
                        {"left": "$$", "right": "$$", "display": True},
                        {"left": "$", "right": "$", "display": False},
                    ],
                )
                question = gr.Textbox(
                    label="Question",
                    placeholder="Ask a KPI, policy, SQL analytics, or hybrid question...",
                    lines=2,
                    elem_classes=["bi-input"],
                )
                with gr.Row():
                    submit = gr.Button("Ask", variant="primary")
                    clear = gr.Button("Clear")

                example_choice = gr.Dropdown(
                    choices=EXAMPLE_CHOICES,
                    label="Example questions",
                    value=None,
                    interactive=True,
                )

            with gr.Column(scale=3, min_width=360, elem_classes=["bi-details"]):
                route_metadata = gr.Markdown(
                    "### Route\n\n_Waiting for a question._",
                    elem_classes=["bi-panel", "bi-meta"],
                )
                with gr.Accordion("Sources", open=True):
                    sources = gr.Markdown("_Sources will appear here._")
                with gr.Accordion("SQL query", open=True):
                    sql_query = gr.Markdown("_SQL query will appear here when applicable._")
                with gr.Accordion("Retrieved context", open=False):
                    retrieved_context = gr.Markdown(
                        "_Retrieved document chunks will appear here._",
                        elem_classes=["bi-context", "bi-panel"],
                        elem_id="retrieved-context-output",
                    )

        example_choice.change(strip_example_prefix, inputs=example_choice, outputs=question)
        submit_event = submit.click(
            queue_user_question,
            inputs=[question, chatbot],
            outputs=[
                chatbot,
                question,
                pending_question,
                route_metadata,
                sources,
                sql_query,
                retrieved_context,
            ],
            show_progress="hidden",
        )
        submit_event.then(
            complete_queued_question,
            inputs=[chatbot, pending_question],
            outputs=[
                chatbot,
                pending_question,
                route_metadata,
                sources,
                sql_query,
                retrieved_context,
            ],
            show_progress="hidden",
        )
        text_event = question.submit(
            queue_user_question,
            inputs=[question, chatbot],
            outputs=[
                chatbot,
                question,
                pending_question,
                route_metadata,
                sources,
                sql_query,
                retrieved_context,
            ],
            show_progress="hidden",
        )
        text_event.then(
            complete_queued_question,
            inputs=[chatbot, pending_question],
            outputs=[
                chatbot,
                pending_question,
                route_metadata,
                sources,
                sql_query,
                retrieved_context,
            ],
            show_progress="hidden",
        )
        clear.click(
            lambda: ([], "", "", "### Route\n\n_Waiting for a question._", "", "", ""),
            outputs=[
                chatbot,
                question,
                pending_question,
                route_metadata,
                sources,
                sql_query,
                retrieved_context,
            ],
        )

    return demo


def main() -> None:
    """Launch the Gradio demo app."""
    app = create_app()
    theme = gr.themes.Soft(primary_hue="blue", neutral_hue="slate")
    app.launch(server_name="127.0.0.1", server_port=7860, theme=theme, css=CUSTOM_CSS)


if __name__ == "__main__":
    main()
