# Prompt Design

This project separates prompt design by workflow. Phase 4 implements only the document RAG prompt strategy; SQL generation, routing, and UI prompts remain future work.

## RAG Grounding Strategy

The document RAG workflow retrieves the most relevant markdown chunks from `data/documents/` and passes only those chunks to the local LLM. The model is instructed to answer from the provided context, avoid invention, and say clearly when the documents do not contain enough information.

Each retrieved chunk includes its source filename and chunk index. The answer prompt asks the model to mention source filenames, and the RAG pipeline appends a short `Sources` section if the model omits one.

The RAG answer style should be concise and business-friendly. It should explain definitions, policies, and segmentation rules in operational language rather than exposing implementation details.

The RAG prompt should not ask the model to query the SQLite database. Questions that require numeric aggregation from `business_data.sqlite` belong to a later SQL agent phase.
