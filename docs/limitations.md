# Limitations

This project is a local portfolio demo, not a production BI platform.

## Synthetic Data Only

All business data and documents are synthetic. The FinSight PayOps domain, clients, providers, payments, policies, and segmentation rules are fictional and should not be interpreted as real operational guidance.

## Local LLM Variability

Answer quality depends on the local model selected in LM Studio or another OpenAI-compatible server. Smaller or heavily quantized models may produce weaker SQL, less consistent summaries, or less reliable instruction following.

## SQL Generation Risk

SQL generation is constrained to SQLite `SELECT` queries and validated before execution. The validator blocks dangerous keywords, comments, semicolons, and multiple statements. Even so, generated SQL should be evaluated before production use, especially for financial or operational decision-making.

## Not Production Hardened

The demo does not include authentication, authorization, monitoring, alerting, rate limiting, audit logs, or robust secrets management. It should not be exposed directly to untrusted users.

## Retrieval Maintenance

The vector store must be rebuilt after document changes:

```powershell
python scripts/ingest_documents.py
```

If documents change and ingestion is not rerun, RAG answers may use stale context.

## Evaluation Gaps

The project includes unit tests for core plumbing, validation, routing, and formatting. It does not yet include a full semantic evaluation suite for retrieval quality, SQL correctness, or answer faithfulness.

## UI Scope

The Gradio UI is designed for local demonstration. It is not a complete dashboarding environment and does not support user accounts, saved sessions, advanced visualizations, or collaborative workflows.
