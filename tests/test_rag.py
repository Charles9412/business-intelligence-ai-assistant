"""Tests for document loading and chunking."""

from __future__ import annotations

from app.config import Settings
from app.rag import RAGPipeline


def test_load_documents_preserves_source_metadata(tmp_path) -> None:
    """Markdown files are loaded with filename metadata."""
    docs_path = tmp_path / "documents"
    docs_path.mkdir()
    (docs_path / "alpha.md").write_text("# Alpha\n\nPayment success rate.", encoding="utf-8")
    (docs_path / "notes.txt").write_text("Ignored", encoding="utf-8")

    pipeline = RAGPipeline(
        settings=Settings(vector_store_path=str(tmp_path / "vector_store")),
        documents_path=docs_path,
    )

    documents = pipeline.load_documents()

    assert len(documents) == 1
    assert documents[0].source == "alpha.md"
    assert "Payment success rate" in documents[0].text


def test_chunk_documents_keeps_metadata_and_readable_chunks(tmp_path) -> None:
    """Chunking keeps source metadata and avoids oversized chunks."""
    docs_path = tmp_path / "documents"
    docs_path.mkdir()
    text = (
        "# KPI Definitions\n\n"
        "Payment success rate measures successful payments divided by attempts. "
        "It should be reviewed by provider and channel.\n\n"
        "Failure rate measures failed payments divided by attempts. "
        "It should be monitored for operational thresholds."
    )
    (docs_path / "kpi_definitions.md").write_text(text, encoding="utf-8")

    pipeline = RAGPipeline(
        settings=Settings(vector_store_path=str(tmp_path / "vector_store")),
        documents_path=docs_path,
    )
    pipeline.load_documents()

    chunks = pipeline.chunk_documents(chunk_size=120, chunk_overlap=30)

    assert len(chunks) >= 2
    assert all(chunk.source == "kpi_definitions.md" for chunk in chunks)
    assert [chunk.chunk_index for chunk in chunks] == list(range(len(chunks)))
    assert all(len(chunk.text) <= 150 for chunk in chunks)
