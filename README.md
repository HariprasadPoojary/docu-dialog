# DocuDialog

Chat with answers grounded in your project documents. DocuDialog is a project-scoped document chatbot built with FastAPI, LangChain, LangGraph, plain HTML/CSS/JavaScript, and PostgreSQL with `pgvector`.

Users will be able to create projects, upload documents into them, select a project, and ask questions answered from that project's indexed documents with source citations.

## Project documents

- [Roadmap](roadmap.md) — planned delivery phases and completion criteria.
- [Architecture](architecture.md) — components, data model, API outline, and security boundaries.
- [Repository guidance](AGENTS.md) — conventions and implementation constraints for contributors and coding agents.

## Current status

The local FastAPI application is available with environment-based configuration, health endpoints, project and document management endpoints, and a browser workspace. Background document ingestion is implemented; project-scoped chat is the next roadmap phase.

## Run locally

Requirements: Python 3.14 and [`uv`](https://docs.astral.sh/uv/).

```powershell
uv sync
Copy-Item .env.example .env
docker compose up -d db
uv run alembic upgrade head
uv run fastapi dev app/main.py
```

Open <http://127.0.0.1:8000> for the landing page, <http://127.0.0.1:8000/docs> for the API docs, and <http://127.0.0.1:8000/api/v1/healthz> for the liveness check.

Settings are loaded from environment variables and an optional `.env` file. See `.env.example` for the current options. The Compose service uses the official pgvector PostgreSQL image and persists data in a local Docker volume. The readiness endpoint checks the configured PostgreSQL connection.

Project endpoints are under `/api/v1/projects` and support create, list, read, update, and delete. Document endpoints are under `/api/v1/projects/{project_id}/documents` and support multi-file upload, listing, and deletion. Uploads accept PDF, DOCX, TXT, Markdown, and CSV; defaults allow 20 MB per file, 50 MB total per request, and 10 files per request. Values are configurable in `.env`.

Until an authentication provider is selected, these endpoints use one fixed local development user when `ENVIRONMENT=local`; they return an error in other environments. This local identity is for development only and does not authenticate real users. Uploaded files use generated storage keys under `storage/uploads` and are recorded as `queued`.

To start indexing, set `OPENAI_API_KEY` in `.env` and run this command in a second terminal:

```powershell
uv run python -m app.workers.ingest
```

The worker uses `text-embedding-3-small` with 1,536 dimensions, stores source-aware chunks in `pgvector`, retries failures up to the configured limit, and marks exhausted jobs as failed. Failed documents can be retried from the project page. The worker polls PostgreSQL directly; run one or more worker processes without needing a separate broker.
