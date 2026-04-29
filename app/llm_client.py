"""OpenAI-compatible LLM client wrapper for local model servers."""

from __future__ import annotations

from typing import Any

from openai import APIConnectionError, APIStatusError, APITimeoutError, OpenAI

from app.config import Settings, load_settings

DEFAULT_SYSTEM_MESSAGE = "You are a concise business intelligence assistant."


class LLMConnectionError(RuntimeError):
    """Raised when the configured local LLM server cannot be reached."""


class LLMClient:
    """Small wrapper around the OpenAI chat completions API.

    The client is configured through `Settings`, so it can connect to LM Studio,
    Ollama's OpenAI-compatible endpoint, or another local server using the same
    API shape.
    """

    def __init__(self, settings: Settings | None = None, client: OpenAI | None = None) -> None:
        """Create an LLM client from settings or an injected test client."""
        self.settings = settings or load_settings()
        self._client = client or OpenAI(
            base_url=self.settings.llm_base_url,
            api_key=self.settings.llm_api_key,
            timeout=30.0,
        )

    def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 800,
    ) -> str:
        """Send chat messages to the configured model and return response text."""
        if not messages:
            raise ValueError("messages must contain at least one chat message")

        try:
            response = self._client.chat.completions.create(
                model=self.settings.llm_model,
                messages=messages,  # type: ignore[arg-type]
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except APIConnectionError as exc:
            raise LLMConnectionError(
                "Could not connect to the local LLM server. Confirm LM Studio's "
                f"local server is running and reachable at {self.settings.llm_base_url}."
            ) from exc
        except APITimeoutError as exc:
            raise LLMConnectionError(
                "The local LLM server did not respond before the request timed out. "
                "Check whether the model is loaded and the server is healthy."
            ) from exc
        except APIStatusError as exc:
            raise RuntimeError(
                f"Local LLM server returned HTTP {exc.status_code}. "
                "Check the configured model name and server logs."
            ) from exc
        except Exception as exc:  # pragma: no cover - defensive wrapper for provider quirks.
            raise RuntimeError(f"Unexpected LLM client error: {exc}") from exc

        content = response.choices[0].message.content if response.choices else None
        if not content:
            raise RuntimeError("Local LLM server returned an empty response.")
        return content.strip()

    def simple_chat(self, prompt: str) -> str:
        """Send a single user prompt with a short default system message."""
        return self.chat(
            [
                {"role": "system", "content": DEFAULT_SYSTEM_MESSAGE},
                {"role": "user", "content": prompt},
            ]
        )

    def health_check(self) -> bool:
        """Return True when the configured LLM server responds to a tiny prompt."""
        try:
            response = self.chat(
                [{"role": "user", "content": "Reply with exactly: ok"}],
                temperature=0.0,
                max_tokens=100,
            )
        except Exception:
            return False
        return bool(response)


def _main() -> int:
    """Run a small command-line connection check."""
    import sys

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    settings = load_settings()
    client = LLMClient(settings)
    print(f"Testing local LLM connection at {settings.llm_base_url}")
    print(f"Model: {settings.llm_model}")

    try:
        response = client.simple_chat("Reply with exactly: LLM connection successful.")
    except Exception as exc:
        print(f"LLM connection failed: {exc}")
        return 1

    print(response)
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
