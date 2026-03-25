# Healthcare Document Intelligence System (RAG-based)

Production-ready, domain-specific Retrieval-Augmented Generation (RAG) platform for healthcare teams that need fast, explainable answers from patient records, clinical notes, and compliance PDFs.

## Problem Statement

Healthcare operations are slowed by fragmented documents and manual search:
- patient histories distributed across multiple files
- discharge summaries with inconsistent structure
- compliance policies that are hard to query quickly

Keyword search misses semantic intent, and generic chat can hallucinate.  
This system grounds every answer in retrieved source chunks from uploaded healthcare documents.

## Solution Overview

This project delivers:
- FastAPI backend for ingestion, retrieval, and answer generation
- React + Tailwind web UI for upload and conversational querying
- Source-grounded responses with top retrieved chunks
- Caching, logging, runtime metrics, and a simple evaluation runner

## Architecture

```text
[PDF Upload]
   |
   v
[Text Extraction] -> [Chunking (configurable)] -> [Embeddings]
   |
   v
[FAISS + Metadata Persistence]
   |
   v
[Hybrid Retrieval: Keyword shortlist + Vector search + Re-rank]
   |
   v
[Threshold filter + Cache]
   |
   v
[LLM generation (or strict fallback)]
   |
   v
[Answer + source chunks + latency]
```

## Updated Folder Structure

```text
app/
  main.py
  api/
    upload.py
    query.py
    metrics.py
  core/
    config.py
  services/
    embedding.py
    ingestion.py
    retriever.py
    generator.py
    cache.py
    metrics.py
  db/
    vector_store.py
  utils/
    pdf_loader.py
  evaluation/
    run_evaluation.py
frontend/
  package.json
  vite.config.js
  tailwind.config.js
  postcss.config.js
  vercel.json
  src/
    App.jsx
    api.js
    main.jsx
    index.css
test/
  ...
render.yaml
requirements.txt
README.md
```

## Tech Stack

### Backend
- FastAPI
- FAISS
- SentenceTransformers
- PyPDF
- OpenAI API (optional)

### Frontend
- React (Vite)
- Tailwind CSS

### Evaluation & Quality
- pytest + pytest-asyncio + httpx
- custom evaluation runner (`app/evaluation/run_evaluation.py`)

## Core Features

- Healthcare-oriented PDF ingestion and indexing
- Configurable chunking (`CHUNK_SIZE`, `CHUNK_OVERLAP`)
- Hybrid retrieval (keyword + vector + re-ranking)
- Query controls (`top_k`, `threshold`)
- Retrieval toggle (`use_retrieval`) for baseline comparison
- In-memory response caching with TTL
- Structured observability logs (query, latency, sources)
- Metrics endpoint (`/metrics`)
- Source display for explainable answers in UI

## Backend Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Create `.env` in project root:

```env
PROJECT_NAME=Healthcare Document Intelligence System
PROJECT_VERSION=2.0.0
PROJECT_DESCRIPTION=RAG platform for patient records, clinical notes, and compliance documents.
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
EMBEDDING_MODEL=all-MiniLM-L6-v2
DATA_DIR=data
TOP_K=5
SIMILARITY_THRESHOLD=0.7
CHUNK_SIZE=500
CHUNK_OVERLAP=100
QUERY_CACHE_TTL_SECONDS=300
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

Run backend:

```bash
uvicorn app.main:app --reload
```

Endpoints:
- API: `http://127.0.0.1:8000`
- Swagger: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## Frontend Setup (React + Tailwind)

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on `http://localhost:5173`.

Optional frontend env:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## API Reference

### `POST /upload`
Ingest healthcare PDFs (patient records, clinical notes, compliance docs).

### `POST /query`
Request:

```json
{
  "question": "What medications is the patient taking?"
}
```

Optional query params:
- `top_k`
- `threshold`
- `use_retrieval` (`true` or `false`)
- `bypass_cache` (`true` or `false`, useful for evaluation)

Response:

```json
{
  "answer": "...",
  "retrieved_chunks": [
    {
      "text": "...",
      "source": "patient_record_001.pdf",
      "chunk_id": 17,
      "score": 0.62,
      "similarity": 0.81,
      "keyword_score": 0.33,
      "rerank_score": 0.71
    }
  ],
  "response_time_ms": 34.7
}
```

### `GET /metrics`

```json
{
  "total_queries": 120,
  "avg_response_time": 28.6,
  "cache_hits": 45,
  "cache_misses": 75
}
```

## Domain Example Queries

- What medications is the patient currently taking?
- Summarize discharge notes for this patient.
- What allergies are documented in the record?
- What follow-up visits are recommended?
- What does the compliance policy say about data retention?

## Evaluation Module (Latency + Qualitative Accuracy)

Run:

```bash
python -m app.evaluation.run_evaluation --base-url http://127.0.0.1:8000 --top-k 5 --threshold 0.7
```

Evaluation script behavior:
- executes 12 predefined healthcare-style questions
- compares responses with retrieval vs without retrieval
- reports:
  - average latency
  - qualitative accuracy (keyword overlap score)
- stores output JSON in:
  - `test/results/healthcare_eval_metrics.json`

## Deployment

### Backend (Render)

`render.yaml` is provided. Default start command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Set required env vars in Render dashboard (`OPENAI_API_KEY`, retrieval/chunk settings, etc.).

### Frontend (Vercel)

`frontend/vercel.json` is included for Vite SPA deployment.

Recommended Vercel settings:
- Root directory: `frontend`
- Build command: `npm run build`
- Output directory: `dist`
- Environment variable: `VITE_API_BASE_URL=<your-backend-url>`

## Screenshots Placeholders

Add polished product screenshots to:
- `docs/screenshots/healthcare-chat.png`
- `docs/screenshots/source-evidence-panel.png`
- `docs/screenshots/upload-flow.png`

Current API verification screenshots:

![Swagger Overview](test/results/screenshots/swagger_overview.png)
![Swagger Query CO2 Result](test/results/screenshots/swagger_query_co2_result.png)
![Swagger Query Romulus Result](test/results/screenshots/swagger_query_romulus_result.png)

## Production Notes

- no hardcoded secrets; env-driven configuration
- answer grounding via retrieved source chunks
- query cache and metrics are thread-safe
- modular architecture ready for auth, audit logs, PHI redaction, and EHR connectors
# Healthcare Document Intelligence System (RAG-based)

Production-ready, domain-specific Retrieval-Augmented Generation (RAG) platform for healthcare teams that need fast, explainable answers from patient records, clinical notes, and compliance PDFs.

## Problem Statement

Healthcare operations are slowed by fragmented documents and manual search:
- patient histories distributed across multiple files
- discharge summaries with inconsistent structure
- compliance policies that are hard to query quickly

Keyword search misses semantic intent, and generic chat can hallucinate.  
This system grounds every answer in retrieved source chunks from uploaded healthcare documents.

## Solution Overview

<<<<<<< HEAD
---
## UI Screenshots

Swagger overview:

![Swagger Overview](test/results/screenshots/swagger_overview.png)

`POST /query` execution with question:
`What was the global CO2 concentration in 2023?`

![Swagger Query CO2 Result](test/results/screenshots/swagger_query_co2_result.png)

`POST /query` execution with question:
`When was Romulus Augustulus deposed?`

![Swagger Query Romulus Result](test/results/screenshots/swagger_query_romulus_result.png)
## Project Structure
=======
This project delivers:
- FastAPI backend for ingestion, retrieval, and answer generation
- React + Tailwind web UI for upload and conversational querying
- Source-grounded responses with top retrieved chunks
- Caching, logging, runtime metrics, and a simple evaluation runner

## Architecture
>>>>>>> e2e4522 (Transform project into a healthcare-focused document intelligence platform.)

```text
[PDF Upload]
   |
   v
[Text Extraction] -> [Chunking (configurable)] -> [Embeddings]
   |
   v
[FAISS + Metadata Persistence]
   |
   v
[Hybrid Retrieval: Keyword shortlist + Vector search + Re-rank]
   |
   v
[Threshold filter + Cache]
   |
   v
[LLM generation (or strict fallback)]
   |
   v
[Answer + source chunks + latency]
```

## Updated Folder Structure

```text
app/
  main.py
  api/
    upload.py
    query.py
    metrics.py
  core/
    config.py
  services/
    embedding.py
    ingestion.py
    retriever.py
    generator.py
    cache.py
    metrics.py
  db/
    vector_store.py
  utils/
    pdf_loader.py
  evaluation/
    run_evaluation.py
frontend/
  package.json
  vite.config.js
  tailwind.config.js
  postcss.config.js
  vercel.json
  src/
    App.jsx
    api.js
    main.jsx
    index.css
test/
  ...
render.yaml
requirements.txt
README.md
```

## Tech Stack

### Backend
- FastAPI
- FAISS
- SentenceTransformers
- PyPDF
- OpenAI API (optional)

### Frontend
- React (Vite)
- Tailwind CSS

### Evaluation & Quality
- pytest + pytest-asyncio + httpx
- custom evaluation runner (`app/evaluation/run_evaluation.py`)

## Core Features

- Healthcare-oriented PDF ingestion and indexing
- Configurable chunking (`CHUNK_SIZE`, `CHUNK_OVERLAP`)
- Hybrid retrieval (keyword + vector + re-ranking)
- Query controls (`top_k`, `threshold`)
- Retrieval toggle (`use_retrieval`) for baseline comparison
- In-memory response caching with TTL
- Structured observability logs (query, latency, sources)
- Metrics endpoint (`/metrics`)
- Source display for explainable answers in UI

## Backend Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Create `.env` in project root:

```env
PROJECT_NAME=Healthcare Document Intelligence System
PROJECT_VERSION=2.0.0
PROJECT_DESCRIPTION=RAG platform for patient records, clinical notes, and compliance documents.
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
EMBEDDING_MODEL=all-MiniLM-L6-v2
DATA_DIR=data
TOP_K=5
SIMILARITY_THRESHOLD=0.7
CHUNK_SIZE=500
CHUNK_OVERLAP=100
QUERY_CACHE_TTL_SECONDS=300
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

Run backend:

```bash
uvicorn app.main:app --reload
```

Endpoints:
- API: `http://127.0.0.1:8000`
- Swagger: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## Frontend Setup (React + Tailwind)

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on `http://localhost:5173`.

Optional frontend env:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## API Reference

### `POST /upload`
Ingest healthcare PDFs (patient records, clinical notes, compliance docs).

### `POST /query`
Request:

```json
{
  "question": "What medications is the patient taking?"
}
```

Optional query params:
- `top_k`
- `threshold`
- `use_retrieval` (`true` or `false`)

Response:

```json
{
  "answer": "...",
  "retrieved_chunks": [
    {
      "text": "...",
      "source": "patient_record_001.pdf",
      "chunk_id": 17,
      "score": 0.62,
      "similarity": 0.81,
      "keyword_score": 0.33,
      "rerank_score": 0.71
    }
  ],
  "response_time_ms": 34.7
}
```

### `GET /metrics`

```json
{
  "total_queries": 120,
  "avg_response_time": 28.6,
  "cache_hits": 45,
  "cache_misses": 75
}
```

## Domain Example Queries

- What medications is the patient currently taking?
- Summarize discharge notes for this patient.
- What allergies are documented in the record?
- What follow-up visits are recommended?
- What does the compliance policy say about data retention?

## Evaluation Module (Latency + Qualitative Accuracy)

Run:

```bash
python -m app.evaluation.run_evaluation --base-url http://127.0.0.1:8000 --top-k 5 --threshold 0.7
```

Evaluation script behavior:
- executes 12 predefined healthcare-style questions
- compares responses with retrieval vs without retrieval
- reports:
  - average latency
  - qualitative accuracy (keyword overlap score)
- stores output JSON in:
  - `test/results/healthcare_eval_metrics.json`

## Deployment

### Backend (Render)

`render.yaml` is provided. Default start command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Set required env vars in Render dashboard (`OPENAI_API_KEY`, retrieval/chunk settings, etc.).

### Frontend (Vercel)

`frontend/vercel.json` is included for Vite SPA deployment.

Recommended Vercel settings:
- Root directory: `frontend`
- Build command: `npm run build`
- Output directory: `dist`
- Environment variable: `VITE_API_BASE_URL=<your-backend-url>`

## Screenshots Placeholders

Add polished product screenshots to:
- `docs/screenshots/healthcare-chat.png`
- `docs/screenshots/source-evidence-panel.png`
- `docs/screenshots/upload-flow.png`

Current API verification screenshots:

![Swagger Overview](test/results/screenshots/swagger_overview.png)
![Swagger Query CO2 Result](test/results/screenshots/swagger_query_co2_result.png)
![Swagger Query Romulus Result](test/results/screenshots/swagger_query_romulus_result.png)

## Production Notes

<<<<<<< HEAD
- **Persistence** — FAISS index and chunk metadata are written to `DATA_DIR` (`data/` by default) on each upload and reloaded on startup.
- **Caching** — In-memory, keyed by normalised query string, evicted after `QUERY_CACHE_TTL_SECONDS`.
- **Retrieval tuning** — Hybrid retrieval (keyword → vector → rerank) balances precision and recall. Raise `threshold` to tighten answers; lower `top_k` to reduce latency.
- **Scaling** — For high-throughput ingestion, consider an async task queue (Celery, ARQ). Add authentication and rate limiting before exposing the API publicly.
- **No API key** — The extractive fallback selects the highest-scoring retrieved chunk as the answer, so the system remains functional without OpenAI access.

---


=======
- no hardcoded secrets; env-driven configuration
- answer grounding via retrieved source chunks
- query cache and metrics are thread-safe
- modular architecture ready for auth, audit logs, PHI redaction, and EHR connectors
>>>>>>> e2e4522 (Transform project into a healthcare-focused document intelligence platform.)
