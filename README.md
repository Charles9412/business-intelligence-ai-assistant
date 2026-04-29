# Business Intelligence AI Assistant

A local-first Python project skeleton for a Retrieval-Augmented Generation (RAG) and SQL business intelligence assistant. The assistant will use synthetic payment operations data to answer operational, KPI, segmentation, and policy questions without relying on private production data.

## Goal

Build a business intelligence assistant that can:

- Answer natural-language questions about payment operations KPIs.
- Retrieve relevant policy and metric-definition context from local documents.
- Query a local SQLite database containing synthetic transaction, client, merchant, and operations data.
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

## Project Layout

- `app/`: application code and orchestration modules.
- `data/documents/`: synthetic business documentation used for RAG.
- `data/raw/`: generated raw synthetic data files.
- `data/processed/`: cleaned datasets ready for database loading.
- `data/business_data.sqlite`: local SQLite database placeholder.
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

## Initial Workflow

The full system is intentionally not implemented yet. The expected next milestones are:

1. Generate synthetic payment operations datasets.
2. Build the SQLite schema and load processed data.
3. Ingest markdown documents into ChromaDB.
4. Implement SQL-safe question answering.
5. Implement RAG over policy and KPI documents.
6. Add routing logic for SQL, RAG, and hybrid questions.
7. Add a lightweight Gradio interface.

## Privacy

This repository must not include private client data, payment credentials, API keys, or production database exports. All demo data should be synthetic and clearly labeled as such.
