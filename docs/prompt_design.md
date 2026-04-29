# Prompt Design

This project separates prompt design by workflow. Phase 4 implements only the document RAG prompt strategy; SQL generation, routing, and UI prompts remain future work.

## RAG Grounding Strategy

The document RAG workflow retrieves the most relevant markdown chunks from `data/documents/` and passes only those chunks to the local LLM. The model is instructed to answer from the provided context, avoid invention, and say clearly when the documents do not contain enough information.

Each retrieved chunk includes its source filename and chunk index. The answer prompt asks the model to mention source filenames, and the RAG pipeline appends a short `Sources` section if the model omits one.

The RAG answer style should be concise and business-friendly. It should explain definitions, policies, and segmentation rules in operational language rather than exposing implementation details.

The RAG prompt should not ask the model to query the SQLite database. Questions that require numeric aggregation from `business_data.sqlite` belong to a later SQL agent phase.

## SQL Generation Strategy

The SQL agent receives a schema string extracted directly from the SQLite database. The prompt instructs the model to use only that schema, avoid invented columns, return one SQLite-compatible `SELECT` query, and omit markdown, explanations, comments, and semicolons.

Schema grounding keeps the model focused on the actual `clients`, `providers`, and `payments` tables. The schema includes column names, basic column types, primary-key hints, and declared foreign-key relationships so the model can prefer explicit joins.

The generated SQL is validated before execution. The validator allows only a single read-only `SELECT` query, rejects semicolons and comments, and blocks dangerous keywords such as `DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `CREATE`, `REPLACE`, `TRUNCATE`, `PRAGMA`, `ATTACH`, `DETACH`, and `VACUUM`.

Dangerous SQL is blocked because the assistant should never modify, attach to, or administer the local database. Even though the data is synthetic, the read-only habit is important for portfolio-quality BI tooling and for future use with more sensitive environments.

## Router And Hybrid Grounding

The question router uses deterministic keyword rules before any model-based routing. This keeps routing predictable, testable, and easy to debug while the project is still local-first and portfolio-oriented.

Document questions route to RAG when they ask about definitions, policies, rules, thresholds, explanations, or interpretation. Analytical questions route to SQL when they ask for counts, totals, averages, rankings, trends, grouped results, or direct database calculations. Mixed questions route to hybrid when they combine documented rules with calculations, such as applying KPI definitions, segmentation rules, or policy thresholds to the database.

Hybrid answers retrieve relevant document chunks first, then pass that document context into SQL generation so the query can reflect documented thresholds or definitions. The SQL is validated exactly like normal SQL-agent queries: only one read-only `SELECT` statement is allowed.

The final hybrid prompt combines document context, the SQL query, and the SQL result table. It asks the model to explain the documented rule briefly, explain the calculated result briefly, avoid invention, and state caveats when the documents or data are insufficient.
