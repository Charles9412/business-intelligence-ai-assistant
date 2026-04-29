"""Question router for document RAG, SQL, and hybrid workflows."""

from __future__ import annotations

from dataclasses import dataclass

from app.llm_client import LLMClient
from app.prompts import HYBRID_ANSWER_PROMPT_TEMPLATE
from app.rag import RAGPipeline, RetrievedChunk
from app.sql_agent import SQLAgent

VALID_ROUTES = {"rag", "sql", "hybrid"}

RAG_KEYWORDS = (
    "definition",
    "define",
    "policy",
    "rules",
    "rule",
    "explain",
    "interpret",
    "interpretation",
    "threshold",
    "what is",
    "what does",
    "what counts as",
    "how are clients classified",
    "classified",
    "classification",
    "segmentation",
    "reviewed",
)

SQL_KEYWORDS = (
    "count",
    "counts",
    "total",
    "average",
    "avg",
    "top",
    "ranking",
    "rank",
    "highest",
    "lowest",
    "highest number",
    "number of",
    "trend",
    "trends",
    "grouped",
    "show",
    "list",
    "calculate",
    "how many",
    "by provider",
    "by region",
    "by month",
    "from the database",
    "database",
)

HYBRID_PHRASES = (
    "according to the definition",
    "using the kpi definition",
    "using the definition",
    "according to the segmentation rules",
    "based on the policy threshold",
    "using the documents and database",
    "documents and database",
    "documented rule",
    "based on the provider failure-rate threshold",
    "according to the client segmentation rules",
)


@dataclass(frozen=True)
class RouteDecision:
    """Routing decision for a user question."""

    route: str
    confidence: float
    reason: str

    def __post_init__(self) -> None:
        """Validate route decisions at construction time."""
        if self.route not in VALID_ROUTES:
            raise ValueError(f"route must be one of {sorted(VALID_ROUTES)}")


class AssistantRouter:
    """Deterministic router that dispatches questions to RAG, SQL, or hybrid flows."""

    def __init__(
        self,
        rag_pipeline: RAGPipeline | None = None,
        sql_agent: SQLAgent | None = None,
        llm_client: LLMClient | None = None,
    ) -> None:
        """Create a router with optional injected dependencies for tests."""
        self.llm_client = llm_client or LLMClient()
        self.rag_pipeline = rag_pipeline or RAGPipeline(llm_client=self.llm_client)
        self.sql_agent = sql_agent or SQLAgent(llm_client=self.llm_client)

    def route_question(self, question: str) -> RouteDecision:
        """Route a question using deterministic keyword and intent rules."""
        normalized = question.strip().lower()
        if not normalized:
            raise ValueError("question must not be blank")

        rag_hits = self._count_hits(normalized, RAG_KEYWORDS)
        sql_hits = self._count_hits(normalized, SQL_KEYWORDS)
        hybrid_hits = self._count_hits(normalized, HYBRID_PHRASES)

        if hybrid_hits or (rag_hits and sql_hits):
            confidence = 0.90 if hybrid_hits else 0.78
            return RouteDecision(
                route="hybrid",
                confidence=confidence,
                reason="Question combines documented rules or definitions with database analysis.",
            )

        if sql_hits > rag_hits:
            return RouteDecision(
                route="sql",
                confidence=0.82,
                reason="Question asks for counts, totals, rankings, grouped results, or calculations.",
            )

        if rag_hits:
            return RouteDecision(
                route="rag",
                confidence=0.82,
                reason="Question asks about definitions, policies, rules, thresholds, or interpretation.",
            )

        return RouteDecision(
            route="rag",
            confidence=0.55,
            reason="Defaulting to document retrieval because no clear analytical database intent was found.",
        )

    def answer_question(self, question: str) -> dict[str, object]:
        """Route and answer a question, returning answer metadata."""
        decision = self.route_question(question)

        if decision.route == "rag":
            answer = self.rag_pipeline.answer_question(question)
            chunks = self.rag_pipeline.retrieve(question, top_k=4)
            return {
                "question": question,
                "route": decision.route,
                "route_reason": decision.reason,
                "answer": answer,
                "sources": self._sources_from_chunks(chunks),
                "sql_query": None,
                "retrieved_context": self._context_payload(chunks),
            }

        if decision.route == "sql":
            answer = self.sql_agent.answer_question(question)
            return {
                "question": question,
                "route": decision.route,
                "route_reason": decision.reason,
                "answer": answer,
                "sources": [],
                "sql_query": getattr(self.sql_agent, "last_sql", None),
                "retrieved_context": [],
            }

        return self.answer_hybrid_question(question, decision=decision)

    def answer_hybrid_question(
        self, question: str, decision: RouteDecision | None = None
    ) -> dict[str, object]:
        """Answer a question using retrieved document context and SQL results."""
        decision = decision or RouteDecision(
            route="hybrid",
            confidence=0.80,
            reason="Hybrid answer requested directly.",
        )
        chunks = self.rag_pipeline.retrieve(question, top_k=4)
        document_context = self._format_context(chunks)
        sql = self.sql_agent.generate_sql(question, extra_context=document_context)
        dataframe = self.sql_agent.execute_sql(sql)
        result_markdown = self.sql_agent._dataframe_to_markdown(dataframe)
        answer = self.llm_client.chat(
            [
                {
                    "role": "system",
                    "content": "You combine documented business rules with SQL results.",
                },
                {
                    "role": "user",
                    "content": HYBRID_ANSWER_PROMPT_TEMPLATE.format(
                        document_context=document_context or "No document context retrieved.",
                        question=question,
                        sql=sql,
                        result_markdown=result_markdown,
                    ),
                },
            ],
            temperature=0.2,
            max_tokens=900,
        )

        sources = self._sources_from_chunks(chunks)
        if sources and "sources" not in answer.lower():
            answer = f"{answer.rstrip()}\n\nSources: {', '.join(sources)}"
        answer = f"{answer.rstrip()}\n\n## SQL Query Used\n\n```sql\n{sql}\n```"

        return {
            "question": question,
            "route": decision.route,
            "route_reason": decision.reason,
            "answer": answer,
            "sources": sources,
            "sql_query": sql,
            "retrieved_context": self._context_payload(chunks),
        }

    def route(self, question: str) -> str:
        """Backward-compatible route helper returning only the route name."""
        return self.route_question(question).route

    def _count_hits(self, text: str, phrases: tuple[str, ...]) -> int:
        """Count phrase hits in normalized question text."""
        return sum(1 for phrase in phrases if phrase in text)

    def _format_context(self, chunks: list[RetrievedChunk]) -> str:
        """Format retrieved chunks for hybrid prompting."""
        sections = []
        for idx, chunk in enumerate(chunks, start=1):
            sections.append(
                f"[{idx}] Source: {chunk.source}, chunk {chunk.chunk_index}\n{chunk.text}"
            )
        return "\n\n".join(sections)

    def _sources_from_chunks(self, chunks: list[RetrievedChunk]) -> list[str]:
        """Return sorted unique source filenames from retrieved chunks."""
        return sorted({chunk.source for chunk in chunks})

    def _context_payload(self, chunks: list[RetrievedChunk]) -> list[dict[str, object]]:
        """Return retrieved context as dictionaries for callers and scripts."""
        return [
            {
                "text": chunk.text,
                "source": chunk.source,
                "chunk_index": chunk.chunk_index,
                "distance": chunk.distance,
                "score": chunk.score,
            }
            for chunk in chunks
        ]


# Backward-compatible alias for the initial scaffold name.
QuestionRouter = AssistantRouter
