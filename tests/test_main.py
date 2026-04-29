"""Tests for Gradio UI formatting helpers."""

from __future__ import annotations

from app.main import (
    format_retrieved_context,
    format_route_metadata,
    format_router_response,
    format_sources,
    format_sql_query,
    extract_message_text,
    normalize_chat_history,
    normalize_markdown,
    queue_user_question,
    strip_example_prefix,
)


def test_strip_example_prefix() -> None:
    assert strip_example_prefix("SQL - Show total payment amount by provider.") == (
        "Show total payment amount by provider."
    )
    assert strip_example_prefix("What is payment success rate?") == "What is payment success rate?"


def test_format_sources() -> None:
    assert "`kpi_definitions.md`" in format_sources(["kpi_definitions.md"])
    assert "No document sources" in format_sources([])


def test_format_sql_query() -> None:
    formatted = format_sql_query("SELECT COUNT(*) FROM payments")

    assert formatted.startswith("```sql")
    assert "SELECT COUNT(*) FROM payments" in formatted


def test_normalize_markdown_converts_display_math_delimiters() -> None:
    normalized = normalize_markdown("\\[\\text{Rate}=1\\]")

    assert normalized == "$$\\text{Rate}=1$$"


def test_format_retrieved_context() -> None:
    formatted = format_retrieved_context(
        [
            {
                "source": "kpi_definitions.md",
                "chunk_index": 2,
                "score": 0.75,
                "text": "Payment Success Rate is defined here.",
            }
        ]
    )

    assert "kpi_definitions.md" in formatted
    assert "0.750" in formatted
    assert "Payment Success Rate" in formatted


def test_format_route_metadata() -> None:
    formatted = format_route_metadata({"route": "hybrid", "route_reason": "Mixed intent."})

    assert "`HYBRID`" in formatted
    assert "Mixed intent." in formatted


def test_format_router_response() -> None:
    answer, route, sources, sql, context = format_router_response(
        {
            "answer": "Done.",
            "route": "sql",
            "route_reason": "Analytics question.",
            "sources": [],
            "sql_query": "SELECT 1",
            "retrieved_context": [],
        }
    )

    assert answer == "Done."
    assert "`SQL`" in route
    assert "No document sources" in sources
    assert "SELECT 1" in sql
    assert "No retrieved document context" in context


def test_normalize_chat_history_accepts_tuple_history() -> None:
    history = normalize_chat_history([["hello", "hi there"]])

    assert history == [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi there"},
    ]


def test_normalize_chat_history_extracts_gradio_content_blocks() -> None:
    history = normalize_chat_history(
        [
            {
                "role": "user",
                "content": [{"text": "Using the KPI definition", "type": "text"}],
            }
        ]
    )

    assert history == [{"role": "user", "content": "Using the KPI definition"}]


def test_extract_message_text_handles_nested_text_blocks() -> None:
    text = extract_message_text([{"text": [{"text": "hello", "type": "text"}]}])

    assert text == "hello"


def test_queue_user_question_returns_pending_state() -> None:
    history, textbox, pending, route, sources, sql, context = queue_user_question(
        "What is payment success rate?",
        [],
    )

    assert textbox == ""
    assert pending == "What is payment success rate?"
    assert history[-1]["content"] == "Working on it..."
    assert "`PROCESSING`" in route
    assert "retrieval finishes" in sources
    assert "SQL query" in sql
    assert "Retrieved document" in context
