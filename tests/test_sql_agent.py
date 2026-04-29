"""Tests for the safe SQL assistant workflow."""

from __future__ import annotations

import sqlite3

import pandas as pd
import pytest

from app.config import Settings
from app.sql_agent import SQLAgent


class FakeLLMClient:
    """Simple fake LLM client for SQL agent tests."""

    def __init__(self, response: str = "SELECT COUNT(*) AS row_count FROM clients") -> None:
        self.response = response

    def chat(self, messages, temperature=0.2, max_tokens=800):
        return self.response


@pytest.fixture()
def test_database(tmp_path):
    """Create a small SQLite database with the project table shape."""
    path = tmp_path / "business_data.sqlite"
    with sqlite3.connect(path) as connection:
        connection.executescript(
            """
            PRAGMA foreign_keys = ON;
            CREATE TABLE clients (
                client_id TEXT PRIMARY KEY,
                client_name TEXT NOT NULL,
                region TEXT NOT NULL,
                status TEXT NOT NULL
            );
            CREATE TABLE providers (
                provider_id TEXT PRIMARY KEY,
                provider_name TEXT NOT NULL
            );
            CREATE TABLE payments (
                payment_id TEXT PRIMARY KEY,
                client_id TEXT NOT NULL,
                provider_id TEXT NOT NULL,
                amount REAL NOT NULL,
                status TEXT NOT NULL,
                FOREIGN KEY (client_id) REFERENCES clients (client_id),
                FOREIGN KEY (provider_id) REFERENCES providers (provider_id)
            );
            INSERT INTO clients VALUES ('C001', 'Client One', 'North', 'Active');
            INSERT INTO providers VALUES ('P001', 'Provider One');
            INSERT INTO payments VALUES ('PMT001', 'C001', 'P001', 125.50, 'Successful');
            """
        )
    return path


def make_agent(database_path) -> SQLAgent:
    """Create a SQL agent with a fake LLM and test database."""
    return SQLAgent(
        settings=Settings(database_path=str(database_path)),
        database_path=database_path,
        llm_client=FakeLLMClient(),
    )


def test_schema_extraction_includes_tables_columns_and_relationships(test_database) -> None:
    agent = make_agent(test_database)

    schema = agent.get_schema()

    assert "Table: clients" in schema
    assert "client_id" in schema
    assert "Table: payments" in schema
    assert "payments.client_id -> clients.client_id" in schema


def test_validate_sql_accepts_select(test_database) -> None:
    agent = make_agent(test_database)

    assert agent.validate_sql("SELECT client_id FROM clients") is True


@pytest.mark.parametrize("keyword", ["DELETE", "DROP", "UPDATE", "INSERT"])
def test_validate_sql_rejects_dangerous_keywords(test_database, keyword) -> None:
    agent = make_agent(test_database)

    with pytest.raises(ValueError):
        agent.validate_sql(f"{keyword} FROM clients")


def test_validate_sql_rejects_multiple_statements(test_database) -> None:
    agent = make_agent(test_database)

    with pytest.raises(ValueError, match="semicolons|multiple"):
        agent.validate_sql("SELECT * FROM clients; SELECT * FROM payments")


def test_execute_sql_returns_dataframe(test_database) -> None:
    agent = make_agent(test_database)

    dataframe = agent.execute_sql("SELECT client_id, client_name FROM clients")

    assert isinstance(dataframe, pd.DataFrame)
    assert list(dataframe.columns) == ["client_id", "client_name"]
    assert dataframe.iloc[0]["client_id"] == "C001"


def test_synthesize_answer_appends_deterministic_result_table(test_database) -> None:
    agent = SQLAgent(
        settings=Settings(database_path=str(test_database)),
        database_path=test_database,
        llm_client=FakeLLMClient("Summary only."),
    )
    dataframe = pd.DataFrame(
        {
            "client_id": ["C001", "C002"],
            "total_amount": [125.50, 99.00],
        }
    )

    answer = agent.synthesize_answer(
        "List clients by amount.",
        "SELECT client_id, total_amount FROM clients",
        dataframe,
    )

    assert "Summary only." in answer
    assert "## Query Result" in answer
    assert "| client_id | total_amount |" in answer
    assert "| C001 | 125.5 |" in answer
    assert "## SQL Query Used" in answer
