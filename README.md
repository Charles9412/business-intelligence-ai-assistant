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
