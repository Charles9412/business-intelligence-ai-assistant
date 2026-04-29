"""Retrieval-Augmented Generation helpers for local markdown documents."""


class RagEngine:
    """Local document retriever and answer composer.

    TODO: Load ChromaDB collections from `VECTOR_STORE_PATH`.
    TODO: Retrieve relevant chunks from KPI, policy, and segmentation documents.
    """

    def query(self, question: str) -> str:
        """Answer a document-grounded question."""
        raise NotImplementedError("RAG querying is not implemented yet.")
