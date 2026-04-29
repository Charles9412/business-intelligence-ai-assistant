"""Demo the question router across RAG, SQL, and hybrid questions."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.router import AssistantRouter

QUESTIONS = [
    "What is payment success rate?",
    "How are failed payments reviewed?",
    "How are high-value clients classified?",
    "Show total payment amount by provider.",
    "Which month had the highest number of failed payments?",
    "List the top 10 clients by total payment amount.",
    "Using the KPI definition, calculate the payment success rate from the database.",
    "According to the client segmentation rules, how many high-value clients do we have?",
    "Based on the provider failure-rate threshold in the policy, which providers should be reviewed?",
]


def main() -> None:
    """Run the router demo and print route metadata with answers."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    router = AssistantRouter()
    for question in QUESTIONS:
        result = router.answer_question(question)
        print("=" * 80)
        print(f"Question: {result['question']}")
        print(f"Route: {result['route']}")
        print(f"Reason: {result['route_reason']}")
        if result.get("sql_query"):
            print("\nSQL query:")
            print(result["sql_query"])
        if result.get("sources"):
            print("\nSources:")
            print(", ".join(result["sources"]))
        print("\nFinal answer:")
        print(result["answer"])
        print()


if __name__ == "__main__":
    main()
