"""FastAPI app exposing the assistant router for the React UI."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import load_settings
from app.llm_client import LLMConnectionError
from app.router import AssistantRouter
from backend.schemas import ChatRequest, ChatResponse

app = FastAPI(title="Business Intelligence AI Assistant API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@lru_cache(maxsize=1)
def get_router() -> AssistantRouter:
    """Create and cache the assistant router."""
    return AssistantRouter()


@app.get("/health")
def health() -> dict[str, bool]:
    """Simple readiness endpoint."""
    return {"ok": True}


@app.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    """Answer a question using the existing assistant router."""
    question = payload.question.strip()
    if not question:
        return ChatResponse(
            question="",
            answer="Please enter a question.",
            error="question must not be blank",
        )

    try:
        result = get_router().answer_question(question)
        return ChatResponse(
            question=str(result.get("question", question)),
            route=_to_optional_str(result.get("route")),
            route_reason=_to_optional_str(result.get("route_reason")),
            answer=str(result.get("answer") or "No answer returned."),
            sources=_to_sources(result.get("sources")),
            sql_query=_to_optional_str(result.get("sql_query")),
            retrieved_context=_to_context(result.get("retrieved_context")),
            error=None,
        )
    except LLMConnectionError:
        settings = load_settings()
        return ChatResponse(
            question=question,
            route="error",
            route_reason="Local LLM connection failed.",
            answer=(
                "I could not reach the local LLM server. Start LM Studio (or another "
                f"OpenAI-compatible server) and confirm it is reachable at {settings.llm_base_url}."
            ),
            error="local_llm_unreachable",
        )
    except Exception as exc:
        return ChatResponse(
            question=question,
            route="error",
            route_reason="Unexpected backend error.",
            answer="Something went wrong while answering your question.",
            error=str(exc),
        )


def _to_optional_str(value: Any) -> str | None:
    """Return string values as-is and map empty values to None."""
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _to_sources(value: Any) -> list[str]:
    """Normalize source list values."""
    if not value:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    return [str(value)]


def _to_context(value: Any) -> list[dict[str, Any]]:
    """Normalize retrieved context payload values."""
    if not value:
        return []
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    return []


def main() -> None:
    """Run the API server locally."""
    uvicorn.run("backend.api:app", host="127.0.0.1", port=8000, reload=False)


if __name__ == "__main__":
    main()

