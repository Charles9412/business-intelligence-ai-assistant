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
  --bi-bg: #0b1220;
  --bi-panel: #172235;
  --bi-panel-strong: #111a2b;
  --bi-border: #34445c;
  --bi-muted: #9aa8bb;
  --bi-text: #eef3f8;
  --bi-blue: #2563eb;
}

.gradio-container {
  max-width: 1500px !important;
  margin: 0 auto !important;
  color: var(--bi-text);
  background: var(--bi-bg) !important;
}

.bi-hero {
  padding: 18px 4px 12px;
}

.bi-hero h1 {
  margin: 0 0 6px;
  font-size: 30px;
  line-height: 1.15;
}

.bi-hero p {
  margin: 0;
  color: var(--bi-muted);
  font-size: 15px;
}

.bi-panel {
  border: 1px solid var(--bi-border) !important;
  border-radius: 10px !important;
  background: var(--bi-panel) !important;
  color: var(--bi-text) !important;
}

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
  background: var(--bi-panel) !important;
  color: var(--bi-text) !important;
  border-color: var(--bi-border) !important;
  max-width: 100% !important;
  min-width: 0 !important;
}

.bi-details details {
  border-radius: 8px !important;
  overflow: hidden !important;
}

.bi-details summary {
  font-weight: 650 !important;
}

.bi-details h3 {
  margin-top: 0;
}

.bi-meta code {
  white-space: pre-wrap !important;
}

.bi-context {
  box-sizing: border-box !important;
  width: 100% !important;
  max-width: 100% !important;
  max-height: 360px;
  overflow: auto;
  overflow-x: hidden;
  overflow-wrap: anywhere;
  word-break: normal;
  background: var(--bi-panel-strong) !important;
  color: var(--bi-text) !important;
  padding: 10px 12px !important;
  border-radius: 8px !important;
}

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
  margin: 12px 0 6px;
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
  line-height: 1.45;
  max-width: 100% !important;
}

.bi-chat .message,
.bi-chat .message p,
.bi-chat .message li {
  font-size: 15px !important;
  line-height: 1.55 !important;
}

.bi-chat pre,
.bi-details pre,
.bi-context pre {
  border-radius: 8px !important;
  border: 1px solid var(--bi-border) !important;
  max-width: 100% !important;
  overflow-x: hidden !important;
  white-space: pre-wrap !important;
}

.bi-details pre code,
.bi-context pre code,
.bi-chat pre code {
  background: transparent !important;
  white-space: pre-wrap !important;
  overflow-wrap: anywhere !important;
}

.bi-details p code,
.bi-details li code,
.bi-context p code,
.bi-context li code,
.bi-chat p code,
.bi-chat li code {
  white-space: pre-wrap !important;
  overflow-wrap: anywhere !important;
  background: #0d1728 !important;
  color: #f8fafc !important;
}

.bi-input textarea {
  font-size: 15px !important;
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
