"""Pydantic schemas for backend API payloads."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Incoming chat request payload."""

    question: str = Field(..., min_length=1, description="User question.")


class ChatResponse(BaseModel):
    """Structured assistant response payload."""

    question: str
    route: str | None = None
    route_reason: str | None = None
    answer: str
    sources: list[str] = Field(default_factory=list)
    sql_query: str | None = None
    retrieved_context: list[dict[str, Any]] = Field(default_factory=list)
    error: str | None = None

