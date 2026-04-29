"""Question router for SQL, RAG, and hybrid workflows."""


class QuestionRouter:
    """Routes a user question to the appropriate assistant workflow.

    TODO: Classify requests as document-only, data-only, or hybrid.
    TODO: Add confidence scoring and fallback behavior.
    """

    def route(self, question: str) -> str:
        """Return the planned route for a question."""
        raise NotImplementedError("Question routing is not implemented yet.")
