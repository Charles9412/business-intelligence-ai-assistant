"""Manual document RAG smoke test."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.rag import RAGPipeline

QUESTIONS = [
    "What is payment success rate?",
    "How are failed payments reviewed?",
    "How are high-value clients classified?",
]


def main() -> None:
    """Retrieve context and answer a few document-only questions."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    pipeline = RAGPipeline()

    for question in QUESTIONS:
        print("=" * 80)
        print(f"Question: {question}")
        print("\nRetrieved chunks:")
        chunks = pipeline.retrieve(question, top_k=3)
        for chunk in chunks:
            score = f"{chunk.score:.3f}" if chunk.score is not None else "n/a"
            preview = " ".join(chunk.text.split())[:260]
            print(f"- {chunk.source} chunk {chunk.chunk_index} score={score}")
            print(f"  {preview}...")

        print("\nAnswer:")
        print(pipeline.answer_question(question, top_k=3))
        print()


if __name__ == "__main__":
    main()
