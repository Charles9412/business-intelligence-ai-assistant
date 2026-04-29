"""Manual smoke test for the configured local LLM connection."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import load_settings
from app.llm_client import LLMClient


def main() -> None:
    """Send a simple prompt and print the model response."""
    settings = load_settings()
    client = LLMClient(settings)
    response = client.simple_chat("Reply with exactly: LLM connection successful.")
    print(response)


if __name__ == "__main__":
    main()
