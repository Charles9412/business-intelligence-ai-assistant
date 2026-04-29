"""Manual smoke test for the safe SQL agent."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.sql_agent import SQLAgent

QUESTIONS = [
    "Show total payment amount by provider.",
    "Which month had the highest number of failed payments?",
    "List the top 10 clients by total payment amount.",
    "Show payment success rate by provider.",
    "How many active clients are there by region?",
]


def main() -> None:
    """Print schema, generated SQL, and answers for sample questions."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    agent = SQLAgent()
    print(agent.get_schema())

    for question in QUESTIONS:
        print("=" * 80)
        print(f"Question: {question}")
        sql = agent.generate_sql(question)
        print("\nGenerated SQL:")
        print(sql)
        dataframe = agent.execute_sql(sql)
        print("\nFinal answer:")
        print(agent.synthesize_answer(question, sql, dataframe))
        print()


if __name__ == "__main__":
    main()
