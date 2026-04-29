"""SQL question-answering utilities for the synthetic business database."""


class SqlAgent:
    """Converts business questions into safe SQLite queries.

    TODO: Inspect database schema before generating SQL.
    TODO: Restrict execution to read-only SELECT statements.
    TODO: Return query results with assumptions and caveats.
    """

    def answer(self, question: str) -> str:
        """Answer a question using the local SQLite database."""
        raise NotImplementedError("SQL agent is not implemented yet.")
