# Architecture

Business Intelligence AI Assistant is a local-first RAG + SQL application for synthetic payment operations analysis. It combines a small document knowledge base, a local SQLite database, a safe SQL agent, and a local OpenAI-compatible LLM.

## End-To-End Flow

```text
User Question
-> Assistant Router
-> Route Decision: RAG / SQL / Hybrid
-> Document RAG Pipeline and/or SQL Agent
-> Retrieved Context and/or SQL Result
-> Local LLM Answer Synthesis
-> Final Answer + Sources + SQL Trace
```

## Main Components

### Gradio UI

`app/main.py` provides a local demo interface. It accepts user questions and displays the final answer, selected route, route reason, document sources, generated SQL, and retrieved context.

### Assistant Router

`app/router.py` classifies each question as:

- `rag`: document-only questions about definitions, policies, rules, and interpretation.
- `sql`: database-only questions about counts, totals, rankings, averages, and grouped analysis.
- `hybrid`: questions that need both a documented rule and a database calculation.

Routing is deterministic and rule-based so behavior is easy to inspect and test.

### Document RAG Pipeline

`app/rag.py` loads markdown files from `data/documents/`, chunks them, embeds them with `all-MiniLM-L6-v2`, and stores vectors in ChromaDB under `vector_store/`.

At query time, the RAG pipeline retrieves relevant chunks and asks the local LLM to answer only from the retrieved context.

### SQL Agent

`app/sql_agent.py` extracts the SQLite schema, asks the local LLM for a single SQLite `SELECT` query, validates the query, executes it with pandas, and renders deterministic result tables.

The SQL agent validates all generated SQL before execution and blocks write/admin operations.

### Local LLM Client

`app/llm_client.py` wraps the OpenAI Python SDK and points it at a configurable OpenAI-compatible endpoint such as LM Studio.

## Data Stores

- `data/business_data.sqlite`: synthetic SQLite database for clients, providers, and payments.
- `data/documents/`: synthetic markdown knowledge base.
- `vector_store/`: generated ChromaDB persistence directory. Generated files are ignored by git.

## Hybrid Answer Strategy

Hybrid questions retrieve relevant document chunks first. That context is passed into SQL generation so documented rules and thresholds can guide the query. The generated SQL is validated exactly like any SQL-only query. Final answer synthesis receives:

- retrieved document context
- SQL query
- SQL result table
- source filenames

The final response includes both the business explanation and traceability artifacts.
