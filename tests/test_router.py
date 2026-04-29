"""Tests for question routing and dispatch."""

from __future__ import annotations

import pandas as pd
import pytest

from app.rag import RetrievedChunk
from app.router import AssistantRouter
from app.sql_agent import SQLAgent


class FakeRAGPipeline:
    """Mock RAG pipeline for router tests."""

    def __init__(self) -> None:
        self.answered = []
        self.retrieved = []

    def answer_question(self, question: str) -> str:
        self.answered.append(question)
        return "rag answer"

    def retrieve(self, question: str, top_k: int = 4):
        self.retrieved.append((question, top_k))
        return [
            RetrievedChunk(
                text="Payment Success Rate is Successful payments / Total attempts.",
                source="kpi_definitions.md",
                chunk_index=0,
                distance=0.12,
            )
        ]


class FakeSQLAgent:
    """Mock SQL agent for router tests."""

    def __init__(self) -> None:
        self.last_sql = None
        self.answered = []
        self.generated = []

    def answer_question(self, question: str, extra_context: str | None = None) -> str:
        self.answered.append((question, extra_context))
        self.last_sql = "SELECT COUNT(*) AS count FROM payments"
        return "sql answer"

    def generate_sql(self, question: str, extra_context: str | None = None) -> str:
        self.generated.append((question, extra_context))
        self.last_sql = "SELECT COUNT(*) AS count FROM payments"
        return self.last_sql

    def execute_sql(self, sql: str):
        return pd.DataFrame({"count": [10]})

    def _dataframe_to_markdown(self, dataframe: pd.DataFrame) -> str:
        return "| count |\n| --- |\n| 10 |"


class FakeLLMClient:
    """Mock LLM client for hybrid answer synthesis."""

    def __init__(self) -> None:
        self.messages = []

    def chat(self, messages, temperature=0.2, max_tokens=800):
        self.messages.append(messages)
        return "hybrid answer"


def make_router() -> AssistantRouter:
    """Create a router with fake dependencies."""
    return AssistantRouter(
        rag_pipeline=FakeRAGPipeline(),
        sql_agent=FakeSQLAgent(),
        llm_client=FakeLLMClient(),
    )


def test_route_question_returns_rag_for_document_definition_question() -> None:
    router = make_router()

    decision = router.route_question("What is payment success rate?")

    assert decision.route == "rag"


def test_route_question_returns_sql_for_analytical_database_question() -> None:
    router = make_router()

    decision = router.route_question("Show total payment amount by provider.")

    assert decision.route == "sql"


def test_route_question_returns_sql_for_highest_failed_payment_month() -> None:
    router = make_router()

    decision = router.route_question("Which month had the highest number of failed payments?")

    assert decision.route == "sql"


def test_route_question_returns_hybrid_for_mixed_document_and_calculation_question() -> None:
    router = make_router()

    decision = router.route_question(
        "Using the KPI definition, calculate the payment success rate from the database."
    )

    assert decision.route == "hybrid"


def test_answer_question_dispatches_to_rag() -> None:
    router = make_router()

    result = router.answer_question("How are failed payments reviewed?")

    assert result["route"] == "rag"
    assert result["answer"] == "rag answer"
    assert result["sources"] == ["kpi_definitions.md"]


def test_answer_question_dispatches_to_sql() -> None:
    router = make_router()

    result = router.answer_question("List the top 10 clients by total payment amount.")

    assert result["route"] == "sql"
    assert result["answer"] == "sql answer"
    assert result["sql_query"] == "SELECT COUNT(*) AS count FROM payments"


def test_answer_question_dispatches_to_hybrid() -> None:
    router = make_router()

    result = router.answer_question(
        "Based on the provider failure-rate threshold in the policy, which providers should be reviewed?"
    )

    assert result["route"] == "hybrid"
    assert result["answer"].startswith("hybrid answer")
    assert result["sources"] == ["kpi_definitions.md"]
    assert result["sql_query"] == "SELECT COUNT(*) AS count FROM payments"


@pytest.mark.parametrize("sql", ["DELETE FROM payments", "DROP TABLE clients"])
def test_dangerous_sql_validation_is_still_enforced(sql: str) -> None:
    agent = SQLAgent.__new__(SQLAgent)

    with pytest.raises(ValueError):
        agent.validate_sql(sql)
