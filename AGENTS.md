# Repository guidance

## Product context

This repository is a project-scoped RAG chatbot. Users create projects, upload documents into a project, select a project in the chat UI, and ask questions grounded in that project's documents. Read `roadmap.md` and `architecture.md` before making structural changes.

## Architecture rules

- Keep HTTP handling in `app/api`, business workflows in `app/services`, and persistence access in scoped `app/repositories`.
- Every document, conversation, and retrieval operation must be authorized against the caller and its project. Do not trust a project ID supplied by the browser.
- The fixed local development identity is only for `ENVIRONMENT=local`; never enable it in shared or production deployments. Replace it with a real identity provider before exposing project APIs.
- Every vector search must include the authorized project filter in the database query. Never retrieve globally and filter after results are returned.
- Keep LangGraph orchestration in `app/workflows`; keep retrieval, prompts, and provider adapters in `app/rag`.
- Keep parsing and embedding work out of synchronous upload requests. Track ingestion state and make retries safe.
- Validate uploaded content and size, use generated storage keys, and do not use client filenames as paths.
- Keep secrets and user document contents out of source control and routine logs.
- Use Alembic migrations for database schema changes; do not rely on ad hoc startup DDL.
- Keep the initial frontend plain HTML, CSS, and JavaScript unless the project direction is deliberately updated.

## Code conventions

- Use type hints and small, focused modules.
- Keep request/response schemas separate from persistence models.
- Make project scope explicit in service and repository method signatures.
- Use configuration from environment variables; provide safe local defaults only for non-secret settings.
- Return clear validation and domain errors without exposing internal paths, secrets, or provider details.
- Update `architecture.md` when a lasting architectural decision changes and update `roadmap.md` when phase scope or completion criteria change.

## Verification

- For implementation changes, run the relevant formatter, static checks, and focused tests when available; report what was run and any failures.
- Run the unit test suite after every change with `uv run python -m pytest tests/unit`.
- Add regression coverage for authorization/project isolation, ingestion state transitions, and retrieval citations when changing those paths.
- Do not claim a behavior is verified unless it was exercised.

## Local development

- The project uses `uv` and declares dependencies in `pyproject.toml` with `uv.lock` as the lockfile.
- Keep local uploads, environment files, credentials, and generated artifacts out of Git.
- Document required environment variables and setup commands in the README as the application is implemented.
