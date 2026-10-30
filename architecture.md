# DocuDialog Architecture

## Overview

DocuDialog is a project-scoped retrieval-augmented chatbot. A user selects a project in the browser and submits a question. The API verifies access to that project, invokes a LangGraph RAG workflow, and returns an answer with citations drawn only from documents indexed for that project.

```text
Browser (HTML / CSS / JavaScript)
        | JSON API / optional streaming
        v
FastAPI routes -> application services -> repositories -> PostgreSQL + pgvector
                         |                     
                         +-> LangGraph workflow -> retrieval -> model provider

Upload API -> file storage -> ingestion worker -> extract / chunk / embed -> PostgreSQL
```

## Technology choices

- **API:** FastAPI, with versioned REST endpoints and OpenAPI documentation.
- **RAG orchestration:** LangChain components for loaders, text splitting, embeddings, and model integrations; LangGraph for an explicit, observable multi-step chat workflow.
- **UI:** plain HTML, CSS, and JavaScript served from `frontend/` (initially through FastAPI static/template support).
- **Database:** PostgreSQL with `pgvector`; SQLAlchemy for persistence and Alembic for schema migrations.
- **Configuration:** environment-based settings, loaded through `python-dotenv` for local development. Secrets must not be committed.
- **File storage:** storage interface with a local development implementation; production backend is configurable independently of database metadata.

The repository already declares FastAPI, LangChain, LangGraph, OpenAI integration, and dotenv. Database, migration, and vector-store dependencies should be added when implementation begins, with versions selected and locked together.

FastAPI starts from `app/main.py`. Settings live in `app/core/config.py` and are loaded from environment variables plus an optional root `.env` file. Local documentation is enabled when `DEBUG=true`. Database sessions are synchronous SQLAlchemy sessions using Psycopg 3; the initial Alembic migration installs `vector` and creates the user, project, and document tables.

## Main components

### Web client

The browser provides project selection, project/document management, upload progress, and a chat view. It sends the selected `project_id` with each chat request. The client value is a selector only; it is never trusted as authorization.

### FastAPI application

Routes validate requests and responses, authenticate the caller, verify project access, and delegate business logic to services. API routers are versioned under `/api/v1`. Upload and chat endpoints must enforce size, content, and rate limits appropriate to deployment.

### Application services and repositories

Services own workflows and transactions; repositories encapsulate database reads/writes. Project scoping is explicit in repository methods. Do not expose a generic unscoped document/vector search operation to API handlers.

### Ingestion worker

The upload request stores the file and creates a document record with a queued status, then hands work to a worker. The worker extracts text, splits it into chunks with source metadata, creates embeddings, and upserts chunks. Document status moves through `queued`, `processing`, `ready`, or `failed`. Retries should be safe and remove or replace stale chunks atomically where practical.

The current upload implementation validates an extension allowlist (PDF, DOCX, TXT, Markdown, CSV), enforces configurable per-file and request limits, writes through generated storage keys, and commits metadata for all files in a request together. A database failure triggers rollback and cleanup of the staged files. Ingestion queue/worker execution is not implemented yet; uploaded documents remain `queued`.

### LangGraph chat workflow

Suggested graph stages:

1. Validate the question and the caller's access to the selected project.
2. Retrieve candidate chunks using a mandatory project filter.
3. Optionally rerank or trim context to the model limit.
4. Generate an answer constrained to the retrieved evidence.
5. Return citations mapped to document and page/section metadata.

The workflow should return an explicit insufficient-evidence response when the retrieved context does not support an answer. Conversation history, if enabled, is contextual input and must not weaken project filtering.

## Data model

- **User:** identity and account metadata (or external identity subject).
- **Project:** owner/creator, name, timestamps, and optional description.
- **Project membership:** optional future relation for shared projects and roles. Until sharing exists, enforce creator ownership.
- **Document:** project ID, original display name, storage key, media type, byte size, checksum, ingestion status, error summary, and timestamps.
- **Chunk:** document ID, project ID, ordinal, text, source metadata (page/section), embedding vector, and timestamps.
- **Conversation / message:** optional persistence for chat sessions; every conversation belongs to a project and its owner.

Use foreign keys and indexes for ownership, project/document relations, document status, and vector search. Keeping `project_id` on chunks supports efficient filtering, but integrity must ensure it matches the parent document. Use cascade or explicit cleanup rules for document/project deletion.

## API outline

All paths below are under `/api/v1`.

- `GET/POST /projects`, `GET/PATCH/DELETE /projects/{project_id}`
- `GET/POST /projects/{project_id}/documents`
- `DELETE /projects/{project_id}/documents/{document_id}`
- `POST /projects/{project_id}/documents/{document_id}/retry`
- `POST /projects/{project_id}/chat` (optionally streaming)
- `GET /healthz` and `/readyz` for liveness and database readiness

Every nested resource operation verifies that the project belongs to or is shared with the caller. Document operations also verify the document is inside that project. Chat retrieval always applies both authorization and the selected project filter.

Project CRUD and basic document upload/list/delete are implemented. Local file storage defaults to `storage/uploads`, and upload limits are configured with `MAX_UPLOAD_BYTES`, `MAX_UPLOAD_TOTAL_BYTES`, and `MAX_UPLOAD_FILES`. Until an authentication provider is selected, local development uses one fixed local user configured by `LOCAL_USER_EMAIL`; the identity dependency fails closed outside `ENVIRONMENT=local` and must be replaced by real authentication before deployment.

## Security and reliability

- Treat uploaded files as untrusted: allowlist formats, cap size, sanitize display names, generate storage keys, and never use a user filename as a filesystem path.
- Keep file bytes outside the database; keep metadata and vectors in PostgreSQL. Avoid exposing storage keys or local paths to clients.
- Enforce authorization server-side on every project, document, conversation, and chat operation. Never rely on a client-supplied project ID alone.
- Apply project filters inside the vector query itself. Test cross-project isolation, including empty or malformed filters.
- Keep secrets in environment/secret management, not source control or logs. Avoid logging raw document content or sensitive prompts.
- Use transaction boundaries and idempotency around ingestion; provide timeouts and bounded retries for external model calls.
- Separate health checks from readiness checks and avoid reporting secrets or sensitive configuration.

## Repository layout

```text
app/
  api/v1/       HTTP routes and dependency wiring
  core/         settings, security, logging, shared errors
  db/           engine, sessions, base metadata
  models/       SQLAlchemy persistence models
  schemas/      request/response models
  repositories/ scoped database access
  services/     project, document, chat application logic
  ingestion/    extraction, chunking, embedding pipeline
  rag/          retrieval, prompts, model adapters, citations
  workflows/    LangGraph graph construction and state
  workers/      background job entry points
frontend/       templates and static HTML/CSS/JavaScript
migrations/     Alembic configuration and revisions
storage/        local development uploads (ignored by Git)
tests/          unit and integration tests
scripts/        developer and maintenance commands
```

## Deployment shape

Run the FastAPI web process, a background worker, and PostgreSQL as separate services. In development, a local PostgreSQL instance with the `vector` extension and local file storage is sufficient. Production can replace local storage with object storage and add a durable queue without changing the API or RAG boundaries. Configure database backups, file retention, and deletion behavior together so metadata and stored files do not drift.
