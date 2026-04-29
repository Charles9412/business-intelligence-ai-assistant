"""Tests for the local LLM client wrapper using mocked OpenAI clients."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.config import Settings
from app.llm_client import LLMClient


class FakeCompletions:
    """Minimal fake for `client.chat.completions.create`."""

    def __init__(self, content: str = "ok") -> None:
        self.content = content
        self.last_request = None

    def create(self, **kwargs):
        self.last_request = kwargs
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=self.content))]
        )


class FakeOpenAIClient:
    """Minimal fake OpenAI client for unit tests."""

    def __init__(self, content: str = "ok") -> None:
        self.completions = FakeCompletions(content)
        self.chat = SimpleNamespace(completions=self.completions)


def test_chat_returns_content_and_uses_settings() -> None:
    settings = Settings(llm_model="demo-model", llm_api_key="test-key")
    fake_client = FakeOpenAIClient("hello")
    client = LLMClient(settings=settings, client=fake_client)

    response = client.chat([{"role": "user", "content": "Say hello"}], temperature=0.1, max_tokens=12)

    assert response == "hello"
    assert fake_client.completions.last_request["model"] == "demo-model"
    assert fake_client.completions.last_request["temperature"] == 0.1
    assert fake_client.completions.last_request["max_tokens"] == 12


def test_chat_rejects_empty_messages() -> None:
    client = LLMClient(settings=Settings(), client=FakeOpenAIClient())

    with pytest.raises(ValueError, match="messages"):
        client.chat([])


def test_health_check_returns_true_for_response() -> None:
    client = LLMClient(settings=Settings(), client=FakeOpenAIClient("ok"))

    assert client.health_check() is True
