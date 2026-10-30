# DocuDialog

Chat with answers grounded in your project documents. DocuDialog is a project-scoped document chatbot built with FastAPI, LangChain, LangGraph, plain HTML/CSS/JavaScript, and PostgreSQL with `pgvector`.

Users will be able to create projects, upload documents into them, select a project, and ask questions answered from that project's indexed documents with source citations.

## Project documents

- [Roadmap](roadmap.md) — planned delivery phases and completion criteria.
- [Architecture](architecture.md) — components, data model, API outline, and security boundaries.
- [Repository guidance](AGENTS.md) — conventions and implementation constraints for contributors and coding agents.

## Current status

The local FastAPI application is available with environment-based configuration, health endpoints, and a small landing page. Project management, document ingestion, database integration, and chat are planned in the roadmap and are not implemented yet.

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
