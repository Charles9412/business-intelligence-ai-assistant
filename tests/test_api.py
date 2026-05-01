"""Tests for FastAPI backend endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient

from backend import api
from app.llm_client import LLMConnectionError


class StubRouter:
    """Router test double with deterministic payload."""

    def answer_question(self, question: str) -> dict[str, object]:
        return {
            "question": question,
            "route": "hybrid",
            "route_reason": "Combined intent.",
            "answer": "Final answer",
            "sources": ["kpi_definitions.md"],
            "sql_query": "SELECT 1",
            "retrieved_context": [{"source": "kpi_definitions.md", "text": "KPI info"}],
        }


class FailingRouter:
    """Router that simulates local LLM connectivity issues."""

    def answer_question(self, question: str) -> dict[str, object]:
        raise LLMConnectionError("offline")


def test_health_returns_ok() -> None:
    client = TestClient(api.app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_chat_returns_router_payload(monkeypatch) -> None:
    client = TestClient(api.app)
    monkeypatch.setattr(api, "get_router", lambda: StubRouter())

    response = client.post("/chat", json={"question": "test question"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["question"] == "test question"
    assert payload["route"] == "hybrid"
    assert payload["route_reason"] == "Combined intent."
    assert payload["answer"] == "Final answer"
    assert payload["sources"] == ["kpi_definitions.md"]
    assert payload["sql_query"] == "SELECT 1"
    assert payload["error"] is None


def test_chat_returns_friendly_llm_error(monkeypatch) -> None:
    client = TestClient(api.app)
    monkeypatch.setattr(api, "get_router", lambda: FailingRouter())

    response = client.post("/chat", json={"question": "hello"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["route"] == "error"
    assert payload["error"] == "local_llm_unreachable"
    assert "could not reach the local llm server" in payload["answer"].lower()
