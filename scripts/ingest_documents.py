"""Ingest markdown documents into the local vector store."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.rag import RAGPipeline


def main() -> None:
    """Build the persistent ChromaDB index for local business documents."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    pipeline = RAGPipeline()
    documents = pipeline.load_documents()
    chunks = pipeline.chunk_documents()
    indexed_count = pipeline.build_vector_store(reset=True)

    print(f"Loaded documents: {len(documents)}")
    print(f"Indexed chunks: {indexed_count}")
    print(f"Vector store path: {pipeline.vector_store_path}")
    print("Document ingestion completed successfully.")


if __name__ == "__main__":
    main()
