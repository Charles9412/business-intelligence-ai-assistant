# Business Intelligence AI Assistant

A local-first Python project skeleton for a Retrieval-Augmented Generation (RAG) and SQL business intelligence assistant. The assistant uses synthetic FinSight PayOps payment operations data to answer operational, KPI, segmentation, and policy questions without relying on private production data.

## Goal

Build a business intelligence assistant that can:

- Answer natural-language questions about payment operations KPIs.
- Retrieve relevant policy and metric-definition context from local documents.
- Query a local SQLite database containing synthetic client, provider, and payment data.
- Route questions between RAG, SQL, or combined workflows.
- Run locally with configurable OpenAI-compatible LLM endpoints.

## Planned Architecture

```text
User Question
    |
    v
app/router.py
    |-- RAG path -> app/rag.py -> vector_store/
    |-- SQL path -> app/sql_agent.py -> data/business_data.sqlite
    |-- Hybrid path -> retrieved context + SQL results
    v
app/llm_client.py
    v
Answer with sources, assumptions, and query notes
```

## Synthetic Dataset And Documents

Phase 2 adds a fictional FinSight PayOps dataset for local analytics development:

- `clients`: 500 synthetic clients with type, region, status, and risk level.
- `providers`: 20 synthetic payment providers across Card, Bank Transfer, Cash, Wallet, and SPEI channels.
- `payments`: 10,000 synthetic payment attempts across the 24 months before the fixed reference date `2026-04-01`.

The generated data includes seasonal payment variation, client-type-based amount differences, payment statuses, and failure reasons only for failed payments. All names, records, and operational rules are synthetic.

The markdown documents in `data/documents/` define KPI formulas, payment operations policy, and client segmentation rules. They are intended to become the first local RAG corpus in a later phase.

## Project Layout

- `app/`: application code and orchestration modules.
- `data/documents/`: synthetic business documentation used for RAG.
- `data/raw/`: generated raw synthetic data files.
- `data/processed/`: cleaned datasets ready for database loading.
- `data/business_data.sqlite`: local SQLite database.
- `scripts/`: one-off setup and ingestion scripts.
- `vector_store/`: local vector database files.
- `docs/`: design notes, data dictionary, prompts, and demo questions.
- `tests/`: early unit-test placeholders.

## Setup

1. Create and activate a virtual environment.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies.

```powershell
pip install -r requirements.txt
```

3. Create a local environment file.

```powershell
Copy-Item .env.example .env
```

4. Edit `.env` with your local OpenAI-compatible endpoint and model settings. Do not commit `.env`.


## Local LLM Setup

This project uses the `openai` Python package against an OpenAI-compatible local server. For LM Studio:

1. Open LM Studio and load a chat model.
2. Go to the Developer or Local Server section.
3. Start the local server.
4. Confirm the server is reachable at `http://localhost:1234` and that the model identifier matches your `.env` value.

Create your local environment file from the example:

```powershell
Copy-Item .env.example .env
```

For the LM Studio server shown in the screenshot, the relevant settings are:

```text
LLM_BASE_URL=http://localhost:1234/v1
LLM_API_KEY=lm-studio
LLM_MODEL=openai/gpt-oss-20b
```

`LLM_API_KEY` is required by the OpenAI client, but LM Studio usually accepts any non-empty placeholder value for local use. Do not commit real API keys or private credentials.

Test the connection from the repository root:

```powershell
python -m app.llm_client
python scripts/test_llm_connection.py
```

## Document RAG Setup

Build the local document vector store after installing dependencies and configuring `.env`:

```powershell
python scripts/ingest_documents.py
```

Then run a small document-only RAG smoke test:

```powershell
python scripts/test_rag_query.py
```

The ingestion script reads markdown files from `data/documents/`, chunks them, embeds them with `all-MiniLM-L6-v2`, and stores the persistent ChromaDB index under `vector_store/`. Generated vector database files are ignored by git; keep `vector_store/.gitkeep` in the repository.

## Generate Data And Build The Database

Run these commands from the repository root:

```powershell
python scripts/generate_synthetic_data.py
python scripts/build_database.py
```

The first command writes `clients.csv`, `providers.csv`, and `payments.csv` to `data/raw/`. The second command replaces `data/business_data.sqlite` and loads the three tables with primary keys, foreign keys, checks, and useful indexes.

## Initial Workflow

The full assistant is intentionally not implemented yet. The expected next milestones are:

1. Ingest markdown documents into ChromaDB.
2. Implement SQL-safe question answering.
3. Implement RAG over policy and KPI documents.
4. Add routing logic for SQL, RAG, and hybrid questions.
5. Add a lightweight Gradio interface.

## Privacy

This repository must not include private client data, payment credentials, API keys, or production database exports. All demo data should be synthetic and clearly labeled as such.
