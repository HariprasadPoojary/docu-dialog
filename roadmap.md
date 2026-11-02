# DocuDialog Roadmap

## Product goal

Let a user create projects, upload multiple documents to each project, and ask questions in a chatbot after selecting a project. Answers must be grounded in documents belonging to that selected project and show useful source references.

## Current progress

- [x] FastAPI local setup, environment configuration, PostgreSQL sessions, and Alembic baseline with `pgvector` enabled.
- [x] Project CRUD and local multi-file upload/list/delete with project ownership checks and upload limits.
- [x] Document extraction, chunking, embeddings, and a database-backed background ingestion worker.
- [ ] Project-scoped chat workflow and cited answers.

## Delivery phases

### 1. Foundation and architecture

- Set up the FastAPI application, configuration, database session, migrations, and local development environment.
- Create the PostgreSQL schema with `pgvector`; establish user, project, document, chunk, and conversation relationships.
- Build the HTML/CSS/JavaScript application shell and project selector.
- Define API conventions, error handling, logging, and the project-level access boundary.

**Done when:** the application starts locally, connects to PostgreSQL, and the initial schema can be migrated.

### 2. Projects and document management

- Add project create/list/read/update/delete flows, scoped to the authenticated user.
- Add multi-file upload, validation (type, size, and safe filenames), document status, and delete/retry operations.
- Store file metadata in PostgreSQL and document bytes in a configured storage backend (local storage in development; object storage can be added later).

**Done when:** a user can manage projects and upload documents without seeing another user's data.

### 3. Ingestion and indexing

- Create an asynchronous ingestion path with queued/running/ready/failed states.
- Extract text from supported document types, normalize it, split it into overlapping chunks, and retain page/section metadata.
- Generate embeddings and persist chunks and vectors with their project and document identifiers.
- Make retries idempotent and expose ingestion progress to the UI.

**Done when:** uploaded documents become searchable, failures are visible and retryable, and deleting a document removes its indexed chunks.

### 4. Project-scoped chat

- Implement retrieval that always filters by the selected project and checks the user's access to that project before querying vectors.
- Build a LangGraph workflow for query preparation, retrieval, context assembly, answer generation, and citation formatting.
- Return source document names and page/section references with the answer; handle insufficient evidence without inventing an answer.
- Add conversation history and a streaming response path if needed by the UI.

**Done when:** questions retrieve only from the selected project, answers cite sources, and no-evidence cases are handled clearly.

### 5. User experience and hardening

- Complete the chat UI, project/document views, loading and error states, and responsive layout.
- Add authentication and authorization appropriate to the deployment, request limits, upload protections, structured logs, and health/readiness endpoints.
- Add automated unit and integration coverage for project isolation, ingestion, retrieval, and citations.
- Document configuration, migrations, local setup, operations, backups, and retention behavior.

**Done when:** the core workflows are usable end to end and security-critical boundaries have regression coverage.

## Initial scope choices

- PostgreSQL is the source of truth for users/projects/documents and stores chunk embeddings through `pgvector`.
- Long-running parsing and embedding work runs outside the request/response path; start with a simple worker and add a broker when deployment needs require it.
- Keep the first UI as plain HTML, CSS, and JavaScript served as static assets; no frontend build system is required initially.
- Treat project membership/access checks and project filters as mandatory at every document and retrieval boundary.

## Open decisions for implementation

- Authentication provider and whether projects need sharing/membership beyond their creator.
- Chat model provider, cost limits, and retention policy for documents and vectors.
- Production file storage and background-job broker.
- Whether chat history is persisted and whether responses stream token-by-token.
