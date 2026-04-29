"""Safe SQL question-answering utilities for the synthetic business database."""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path

import pandas as pd

from app.config import PROJECT_ROOT, Settings, load_settings
from app.llm_client import LLMClient
from app.prompts import (
    SQL_AGENT_SYSTEM_PROMPT,
    SQL_ANSWER_PROMPT_TEMPLATE,
    SQL_GENERATION_PROMPT_TEMPLATE,
)

DANGEROUS_SQL_KEYWORDS = (
    "DROP",
    "DELETE",
    "UPDATE",
    "INSERT",
    "ALTER",
    "CREATE",
    "REPLACE",
    "TRUNCATE",
    "PRAGMA",
    "ATTACH",
    "DETACH",
    "VACUUM",
)


class SQLAgent:
    """Generate, validate, execute, and summarize read-only SQLite queries."""

    def __init__(
        self,
        settings: Settings | None = None,
        llm_client: LLMClient | None = None,
        database_path: str | Path | None = None,
    ) -> None:
        """Create a SQL agent for the configured SQLite database."""
        self.settings = settings or load_settings()
        self.database_path = self._resolve_path(database_path or self.settings.database_path)
        self.llm_client = llm_client or LLMClient(self.settings)
        self.last_sql: str | None = None

    def get_schema(self) -> str:
        """Inspect the SQLite database and return a clear schema string."""
        if not self.database_path.exists():
            raise FileNotFoundError(f"SQLite database not found: {self.database_path}")

        lines = ["SQLite database schema:"]
        with sqlite3.connect(self.database_path) as connection:
            tables = [
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master "
                    "WHERE type = 'table' AND name NOT LIKE 'sqlite_%' "
                    "ORDER BY name"
                )
            ]

            for table in tables:
                lines.append(f"\nTable: {table}")
                columns = list(
                    connection.execute(f"PRAGMA table_info({self._quote_identifier(table)})")
                )
                for _, name, column_type, not_null, default, primary_key in columns:
                    details = [column_type or "TEXT"]
                    if primary_key:
                        details.append("primary key")
                    if not_null:
                        details.append("not null")
                    if default is not None:
                        details.append(f"default {default}")
                    lines.append(f"- {name}: {', '.join(details)}")

                examples = self._categorical_examples(connection, table, columns)
                if examples:
                    lines.append("  Example values:")
                    for column_name, values in examples.items():
                        lines.append(f"  - {column_name}: {', '.join(values)}")

            relationships: list[str] = []
            for table in tables:
                foreign_keys = connection.execute(
                    f"PRAGMA foreign_key_list({self._quote_identifier(table)})"
                )
                for row in foreign_keys:
                    relationships.append(
                        f"- {table}.{row[3]} -> {row[2]}.{row[4]}"
                    )

        if relationships:
            lines.append("\nRelationships:")
            lines.extend(relationships)
        else:
            lines.append("\nRelationships: none declared")

        return "\n".join(lines)

    def generate_sql(self, question: str) -> str:
        """Use the LLM to generate a SQLite SELECT query for a question."""
        if not question.strip():
            raise ValueError("question must not be blank")

        base_prompt = SQL_GENERATION_PROMPT_TEMPLATE.format(
            schema=self.get_schema(),
            question=question.strip(),
        )
        prompt = base_prompt
        last_error: ValueError | None = None

        for attempt in range(2):
            raw_sql = self.llm_client.chat(
                [
                    {"role": "system", "content": SQL_AGENT_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,
                max_tokens=500,
            )
            sql = self._clean_generated_sql(raw_sql)
            try:
                self.validate_sql(sql)
                self._ensure_query_prepares(sql)
            except ValueError as exc:
                last_error = exc
                if attempt == 1:
                    break
                prompt = (
                    f"{base_prompt}\n\nThe previous SQL was invalid.\n"
                    f"Previous SQL:\n{sql}\n\n"
                    f"SQLite or validation error:\n{exc}\n\n"
                    "Return a corrected single SQLite SELECT query only."
                )
                continue

            self.last_sql = sql
            return sql

        raise ValueError(f"Could not generate valid SQL: {last_error}")

    def validate_sql(self, sql: str) -> bool:
        """Validate that SQL is a single read-only SELECT statement."""
        normalized = sql.strip()
        if not normalized:
            raise ValueError("SQL query is empty")
        if ";" in normalized:
            raise ValueError("SQL query must not contain semicolons or multiple statements")
        if "--" in normalized or "/*" in normalized or "*/" in normalized:
            raise ValueError("SQL comments are not allowed")
        if not re.match(r"^\s*SELECT\b", normalized, flags=re.IGNORECASE):
            raise ValueError("Only read-only SELECT queries are allowed")

        for keyword in DANGEROUS_SQL_KEYWORDS:
            if re.search(rf"\b{keyword}\b", normalized, flags=re.IGNORECASE):
                raise ValueError(f"Dangerous SQL keyword is not allowed: {keyword}")

        return True

    def execute_sql(self, sql: str, max_rows: int = 50) -> pd.DataFrame:
        """Validate and execute a read-only SQL query, returning a DataFrame."""
        if max_rows <= 0:
            raise ValueError("max_rows must be greater than zero")
        self.validate_sql(sql)

        with sqlite3.connect(self.database_path) as connection:
            connection.execute("PRAGMA query_only = ON")
            try:
                dataframe = pd.read_sql_query(sql, connection)
            except Exception as exc:
                raise ValueError(f"SQL execution failed: {exc}") from exc

        return dataframe.head(max_rows)

    def answer_question(self, question: str) -> str:
        """Generate SQL, execute it, and synthesize a concise business answer."""
        sql = self.generate_sql(question)
        dataframe = self.execute_sql(sql)
        return self.synthesize_answer(question, sql, dataframe)

    def synthesize_answer(self, question: str, sql: str, dataframe: pd.DataFrame) -> str:
        """Use the LLM to summarize a validated query result."""
        self.validate_sql(sql)
        result_markdown = self._dataframe_to_markdown(dataframe)

        answer = self.llm_client.chat(
            [
                {"role": "system", "content": "You summarize SQL results for business users."},
                {
                    "role": "user",
                    "content": SQL_ANSWER_PROMPT_TEMPLATE.format(
                        question=question.strip(),
                        sql=sql,
                        result_markdown=result_markdown,
                    ),
                },
            ],
            temperature=0.2,
            max_tokens=700,
        )

        return f"{answer.strip()}\n\n## SQL Query Used\n\n```sql\n{sql}\n```"

    def answer(self, question: str) -> str:
        """Backward-compatible alias for `answer_question`."""
        return self.answer_question(question)

    def _resolve_path(self, path: str | Path) -> Path:
        """Resolve project-relative paths against the repository root."""
        candidate = Path(path)
        return candidate if candidate.is_absolute() else PROJECT_ROOT / candidate

    def _clean_generated_sql(self, sql: str) -> str:
        """Remove common LLM formatting while preserving the SQL statement."""
        cleaned = sql.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:sql|sqlite)?\s*", "", cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r"\s*```$", "", cleaned)
        cleaned = cleaned.strip()
        if cleaned.endswith(";") and cleaned.count(";") == 1:
            cleaned = cleaned[:-1].strip()
        return cleaned

    def _dataframe_to_markdown(self, dataframe: pd.DataFrame) -> str:
        """Convert query results to markdown without requiring tabulate."""
        if dataframe.empty:
            return "_No rows returned._"

        headers = [str(column) for column in dataframe.columns]
        lines = [
            "| " + " | ".join(headers) + " |",
            "| " + " | ".join(["---"] * len(headers)) + " |",
        ]
        for _, row in dataframe.iterrows():
            values = [self._format_cell(row[column]) for column in dataframe.columns]
            lines.append("| " + " | ".join(values) + " |")
        return "\n".join(lines)

    def _format_cell(self, value: object) -> str:
        """Format a DataFrame cell for a markdown table."""
        if pd.isna(value):
            return ""
        text = str(value)
        return text.replace("|", "\\|").replace("\n", " ")

    def _ensure_query_prepares(self, sql: str) -> None:
        """Ask SQLite to prepare the query without running it."""
        with sqlite3.connect(self.database_path) as connection:
            connection.execute("PRAGMA query_only = ON")
            try:
                connection.execute(f"EXPLAIN QUERY PLAN {sql}")
            except sqlite3.Error as exc:
                raise ValueError(f"SQL query could not be prepared: {exc}") from exc

    def _categorical_examples(
        self,
        connection: sqlite3.Connection,
        table: str,
        columns: list[tuple[object, ...]],
    ) -> dict[str, list[str]]:
        """Return distinct example values for small text columns."""
        examples: dict[str, list[str]] = {}
        for _, name, column_type, *_ in columns:
            if "TEXT" not in str(column_type).upper():
                continue
            quoted_table = self._quote_identifier(table)
            quoted_column = self._quote_identifier(str(name))
            rows = connection.execute(
                f"SELECT DISTINCT {quoted_column} FROM {quoted_table} "
                f"WHERE {quoted_column} IS NOT NULL AND {quoted_column} != '' "
                f"ORDER BY {quoted_column} LIMIT 12"
            ).fetchall()
            values = [str(row[0]) for row in rows]
            if 1 < len(values) <= 10:
                examples[str(name)] = values
        return examples

    def _quote_identifier(self, identifier: str) -> str:
        """Safely quote a SQLite identifier from introspected metadata."""
        return '"' + identifier.replace('"', '""') + '"'


# Backward-compatible alias for the initial scaffold name.
SqlAgent = SQLAgent
