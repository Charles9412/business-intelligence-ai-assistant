"""Retrieval-Augmented Generation helpers for local markdown documents."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import chromadb
from sentence_transformers import SentenceTransformer

from app.config import PROJECT_ROOT, Settings, load_settings
from app.llm_client import LLMClient
from app.prompts import RAG_ANSWER_PROMPT_TEMPLATE, RAG_SYSTEM_PROMPT

COLLECTION_NAME = "business_docs"
DEFAULT_EMBEDDING_MODEL = "all-MiniLM-L6-v2"


@dataclass(frozen=True)
class SourceDocument:
    """Markdown document loaded from the local document corpus."""

    text: str
    source: str
    path: Path


@dataclass(frozen=True)
class DocumentChunk:
    """Text chunk with source metadata for vector indexing."""

    text: str
    source: str
    chunk_index: int


@dataclass(frozen=True)
class RetrievedChunk:
    """Retrieved context returned from the vector store."""

    text: str
    source: str
    chunk_index: int
    distance: float | None

    @property
    def score(self) -> float | None:
        """Return a simple similarity-like score derived from Chroma distance."""
        if self.distance is None:
            return None
        return 1.0 / (1.0 + self.distance)


class RAGPipeline:
    """Local markdown RAG pipeline backed by sentence-transformers and ChromaDB."""

    def __init__(
        self,
        settings: Settings | None = None,
        documents_path: str | Path | None = None,
        embedding_model_name: str = DEFAULT_EMBEDDING_MODEL,
        llm_client: LLMClient | None = None,
    ) -> None:
        """Create a RAG pipeline with lazy embedding model initialization."""
        self.settings = settings or load_settings()
        self.documents_path = self._resolve_path(documents_path or "data/documents")
        self.vector_store_path = self._resolve_path(self.settings.vector_store_path)
        self.embedding_model_name = embedding_model_name
        self.llm_client = llm_client
        self.documents: list[SourceDocument] = []
        self.chunks: list[DocumentChunk] = []
        self._embedding_model: SentenceTransformer | None = None
        self._chroma_client: Any | None = None
        self._collection: Any | None = None

    def load_documents(self) -> list[SourceDocument]:
        """Load all markdown documents and preserve source filenames as metadata."""
        if not self.documents_path.exists():
            raise FileNotFoundError(f"Document directory not found: {self.documents_path}")

        documents: list[SourceDocument] = []
        for path in sorted(self.documents_path.glob("*.md")):
            text = path.read_text(encoding="utf-8").strip()
            if text:
                documents.append(SourceDocument(text=text, source=path.name, path=path))

        self.documents = documents
        return documents

    def chunk_documents(
        self, chunk_size: int = 800, chunk_overlap: int = 120
    ) -> list[DocumentChunk]:
        """Split loaded documents into readable overlapping chunks."""
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than zero")
        if chunk_overlap < 0:
            raise ValueError("chunk_overlap cannot be negative")
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")
        if not self.documents:
            self.load_documents()

        chunks: list[DocumentChunk] = []
        for document in self.documents:
            parts = self._split_text(document.text, chunk_size, chunk_overlap)
            for index, text in enumerate(parts):
                chunks.append(
                    DocumentChunk(
                        text=text,
                        source=document.source,
                        chunk_index=index,
                    )
                )

        self.chunks = chunks
        return chunks

    def build_vector_store(self, reset: bool = True) -> int:
        """Embed chunks and persist them in a ChromaDB collection."""
        if not self.chunks:
            self.chunk_documents()

        self.vector_store_path.mkdir(parents=True, exist_ok=True)
        client = self._get_chroma_client()
        if reset:
            try:
                client.delete_collection(COLLECTION_NAME)
            except Exception:
                pass

        collection = client.get_or_create_collection(name=COLLECTION_NAME)
        if self.chunks:
            texts = [chunk.text for chunk in self.chunks]
            embeddings = self._embed(texts)
            ids = [f"{chunk.source}:{chunk.chunk_index}" for chunk in self.chunks]
            metadatas = [
                {"source": chunk.source, "chunk_index": chunk.chunk_index}
                for chunk in self.chunks
            ]

            if not reset:
                existing = set(collection.get(ids=ids).get("ids", []))
                keep_indexes = [idx for idx, chunk_id in enumerate(ids) if chunk_id not in existing]
                ids = [ids[idx] for idx in keep_indexes]
                texts = [texts[idx] for idx in keep_indexes]
                embeddings = [embeddings[idx] for idx in keep_indexes]
                metadatas = [metadatas[idx] for idx in keep_indexes]

            if ids:
                collection.add(
                    ids=ids,
                    documents=texts,
                    embeddings=embeddings,
                    metadatas=metadatas,
                )

        self._collection = collection
        return len(self.chunks)

    def retrieve(self, query: str, top_k: int = 4) -> list[RetrievedChunk]:
        """Return the most relevant chunks for a query."""
        if not query.strip():
            raise ValueError("query must not be blank")
        if top_k <= 0:
            raise ValueError("top_k must be greater than zero")

        collection = self._get_collection()
        query_embedding = self._embed([query])[0]
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        retrieved: list[RetrievedChunk] = []
        for text, metadata, distance in zip(documents, metadatas, distances):
            metadata = metadata or {}
            retrieved.append(
                RetrievedChunk(
                    text=text,
                    source=str(metadata.get("source", "unknown")),
                    chunk_index=int(metadata.get("chunk_index", 0)),
                    distance=float(distance) if distance is not None else None,
                )
            )
        return retrieved

    def answer_question(self, question: str, top_k: int = 4) -> str:
        """Answer a question using only retrieved document context."""
        chunks = self.retrieve(question, top_k=top_k)
        if not chunks:
            return "I do not know based on the provided documents.\n\nSources: none"

        context = self._format_context(chunks)
        prompt = RAG_ANSWER_PROMPT_TEMPLATE.format(context=context, question=question)
        llm_client = self.llm_client or LLMClient(self.settings)
        answer = llm_client.chat(
            [
                {"role": "system", "content": RAG_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=800,
        )

        sources = sorted({chunk.source for chunk in chunks})
        if "sources" not in answer.lower():
            answer = f"{answer.rstrip()}\n\nSources: {', '.join(sources)}"
        return answer

    def _resolve_path(self, path: str | Path) -> Path:
        """Resolve project-relative paths against the repository root."""
        candidate = Path(path)
        return candidate if candidate.is_absolute() else PROJECT_ROOT / candidate

    def _get_embedding_model(self) -> SentenceTransformer:
        """Load the local embedding model on first use."""
        if self._embedding_model is None:
            self._embedding_model = SentenceTransformer(self.embedding_model_name)
        return self._embedding_model

    def _embed(self, texts: list[str]) -> list[list[float]]:
        """Embed text using the configured sentence-transformers model."""
        embeddings = self._get_embedding_model().encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return embeddings.tolist()

    def _get_chroma_client(self) -> Any:
        """Return a persistent Chroma client."""
        if self._chroma_client is None:
            self.vector_store_path.mkdir(parents=True, exist_ok=True)
            self._chroma_client = chromadb.PersistentClient(path=str(self.vector_store_path))
        return self._chroma_client

    def _get_collection(self) -> Any:
        """Return the persisted document collection."""
        if self._collection is None:
            self._collection = self._get_chroma_client().get_or_create_collection(
                name=COLLECTION_NAME
            )
        return self._collection

    def _split_text(
        self, text: str, chunk_size: int, chunk_overlap: int
    ) -> list[str]:
        """Split text into chunks while preferring paragraph and word boundaries."""
        normalized = re.sub(r"\n{3,}", "\n\n", text.strip())
        paragraphs = [part.strip() for part in re.split(r"\n\s*\n", normalized) if part.strip()]
        chunks: list[str] = []
        current = ""

        for paragraph in paragraphs:
            if len(paragraph) > chunk_size:
                if current:
                    chunks.append(current.strip())
                    current = ""
                chunks.extend(self._split_long_paragraph(paragraph, chunk_size, chunk_overlap))
                continue

            candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
            if len(candidate) <= chunk_size:
                current = candidate
            else:
                chunks.append(current.strip())
                current = self._overlap_prefix(chunks[-1], chunk_overlap, paragraph)

        if current:
            chunks.append(current.strip())

        return chunks

    def _split_long_paragraph(
        self, paragraph: str, chunk_size: int, chunk_overlap: int
    ) -> list[str]:
        """Split a long paragraph by words with overlap."""
        words = paragraph.split()
        chunks: list[str] = []
        current_words: list[str] = []

        for word in words:
            candidate = " ".join([*current_words, word])
            if current_words and len(candidate) > chunk_size:
                chunk = " ".join(current_words)
                chunks.append(chunk)
                overlap_words = self._last_words_for_overlap(chunk, chunk_overlap)
                current_words = [*overlap_words, word]
            else:
                current_words.append(word)

        if current_words:
            chunks.append(" ".join(current_words))
        return chunks

    def _overlap_prefix(self, previous: str, chunk_overlap: int, next_text: str) -> str:
        """Prefix a new chunk with trailing words from the previous chunk."""
        overlap = " ".join(self._last_words_for_overlap(previous, chunk_overlap))
        return f"{overlap}\n\n{next_text}".strip() if overlap else next_text

    def _last_words_for_overlap(self, text: str, chunk_overlap: int) -> list[str]:
        """Return trailing words up to the requested overlap character budget."""
        if chunk_overlap == 0:
            return []
        selected: list[str] = []
        total = 0
        for word in reversed(text.split()):
            next_total = total + len(word) + (1 if selected else 0)
            if next_total > chunk_overlap:
                break
            selected.append(word)
            total = next_total
        return list(reversed(selected))

    def _format_context(self, chunks: list[RetrievedChunk]) -> str:
        """Format retrieved chunks for the grounded answer prompt."""
        sections = []
        for idx, chunk in enumerate(chunks, start=1):
            sections.append(
                f"[{idx}] Source: {chunk.source}, chunk {chunk.chunk_index}\n{chunk.text}"
            )
        return "\n\n".join(sections)


# Backward-compatible alias for the initial scaffold name.
RagEngine = RAGPipeline
