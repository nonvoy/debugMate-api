> [!WARNING]
> **Work in Progress**
>
> DebugMate is currently under active development. Features, APIs, data models, and architecture may change as the project evolves. The current implementation represents an early MVP focused on event ingestion, event processing, incident detection, and AI-assisted incident analysis.

## About DebugMate

DebugMate is an AI-powered observability assistant designed to help engineers understand production issues faster.

Modern distributed systems generate a large volume of logs, infrastructure events, and deployment notifications. DebugMate collects these events, normalizes and groups similar occurrences, detects potential incidents, and generates concise summaries to help engineers identify the most likely root causes.

The project is currently being developed as a collection of microservices:

- **debugMate-api** — Event ingestion API built with FastAPI.
- **debugMate-worker** — Background processing service responsible for event normalization, fingerprint generation, grouping, incident detection, and AI-powered analysis.

## debugMate-api

`debugMate-api` is the FastAPI service that sits at the front of the pipeline. It accepts events over HTTP, publishes them onto a Celery broker for the worker to process, and exposes read endpoints to retrieve processed events and detected incidents.

The API itself does not normalize events or detect incidents — that work is done by `debugMate-worker`. The API only **publishes** events to the broker and **reads** the results the worker has persisted (events in OpenSearch, incidents in PostgreSQL).

### Workflow

```text
Application logs
        |
        v
   debugMate-api  (publish)
        |
        v
   Celery broker
   Redis locally / SQS outside local
        |
        v
 debugMate-worker
        |
        +--> OpenSearch: normalized events
        |
        +--> PostgreSQL: incidents and event associations
        |
        v
   debugMate-api  (read)
        |
        +--> GET events     (from OpenSearch)
        +--> GET incidents  (from PostgreSQL)
```

On the publish path, the API assigns each event a UUID, stamps a publish timestamp, and sends a Celery task (named by `CELERY__TASK_NAME`, default `process_events`) carrying the event payload. Batch publishes also share a generated `batch_id`, used as the Celery `task_id`.

On the read path, the API queries OpenSearch for events (by event ID or batch ID) and PostgreSQL for incidents (by ID, or filtered and paginated). The OpenSearch and SQLModel models in this service are treated as read-only; the worker owns writes to those stores.

## API Endpoints

### Health

| Method | Path            | Description                                                              |
| ------ | --------------- | ------------------------------------------------------------------------ |
| GET    | `/health/live`  | Liveness check. Returns `{"status": "OK"}` if the app is running.        |
| GET    | `/health/ready` | Readiness check. Pings Celery workers; returns `503` if none respond.    |

### Events (`/api/v1/events`)

| Method | Path                       | Description                                                                 |
| ------ | -------------------------- | --------------------------------------------------------------------------- |
| POST   | `/api/v1/events/`          | Publish a single event to the Celery queue. Returns `202` with the event.   |
| POST   | `/api/v1/events/batch`     | Publish a batch of events under a shared `batch_id`. Returns `202`.          |
| GET    | `/api/v1/events/{event_id}`| Retrieve a processed event from OpenSearch by its UUID.                      |
| GET    | `/api/v1/events/batch/{batch_id}` | Retrieve all processed events for a batch from OpenSearch.            |

An event payload includes:

- **service** — the service that generated the event (e.g. `auth-service`).
- **severity** — one of `debug`, `info`, `warning`, `error`, `critical`.
- **message** — a descriptive message about the event.
- **environment** — (optional) where the event occurred, defaults to `unknown`.
- **event_type** — (optional) the type of event, defaults to `unknown`.
- **metadata** — (optional) arbitrary key/value context.
- **timestamp** — when the event occurred (ISO 8601).

String fields (`service`, `severity`, `environment`, `event_type`) are stripped and lowercased on input. Events read back from OpenSearch additionally expose worker-populated fields such as `normalized_message`, `fingerprint`, `received_at`, and `updated_at`, which are only set after processing.

### Incidents (`/api/v1/incidents`)

| Method | Path                          | Description                                               |
| ------ | ----------------------------- | -------------------------------------------------------- |
| GET    | `/api/v1/incidents/{incident_id}` | Retrieve a single incident (with associated event IDs).  |
| GET    | `/api/v1/incidents/`          | Retrieve a paginated, filterable list of incidents.      |

The list endpoint accepts the following query parameters:

- **service**, **environment**, **status** — exact-match filters.
- **start_time_from**, **start_time_to** — filter by incident start time.
- **page** (default `1`), **page_size** (default `20`, max `100`) — pagination.

Responses are wrapped in a paginated envelope (`items`, `total`, `page`, `page_size`, `pages`). Incidents are ordered by creation time (newest first).

Interactive API docs are available at `/docs` (Swagger UI) and `/redoc` once the app is running.

## Project Layout

```text
main.py                              FastAPI app and router registration
debug_worker.py                      Local stub Celery worker for testing the publish path
src/config/                          Pydantic settings and logging
src/models/incident.py               SQLModel tables for incidents (read-only here)
src/routes/events.py                 Event publish and retrieval endpoints
src/routes/incidents.py              Incident retrieval endpoints
src/routes/liveness.py               Liveness and readiness endpoints
src/routes/schemas/                  Request/response Pydantic models and pagination
src/services/celery/client.py        Celery client factory (Redis or SQS)
src/services/db/db_client.py         PostgreSQL read client
src/services/search/open_search_client.py  OpenSearch read client
tests/routes/                        Endpoint tests
dependencies/                        Runtime dependency pins (base/local/prod)
dependencies/dev/                    Development dependency pins
dev/Dockerfile                       Production image
dev/local/                           Local Docker Compose and images
```

## Configuration

Configuration is loaded from environment variables, with `.env` support via `pydantic-settings`. Nested settings use `__` as the delimiter.

Start from `.env.example`:

```bash
cp .env.example .env
```

Required settings (no defaults):

```text
DB_URL=postgresql://user:password@localhost:5432/mydatabase
OPENSEARCH__URL=http://localhost:9200
```

Common settings:

```text
DEBUG=false
ENVIRONMENT=local
LOG_LEVEL=INFO

OPENSEARCH__USERNAME=admin
OPENSEARCH__PASSWORD=admin
OPENSEARCH__VERIFY_CERTS=false

CELERY__APP_NAME=debugmate-worker
CELERY__TASK_NAME=process_events
CELERY__QUEUE_NAME=debugmate-queue
CELERY__BROKER_URL=redis://localhost:6379/0
```

When `ENVIRONMENT=local`, Celery uses Redis as the broker (`CELERY__BROKER_URL`). For non-local environments, Celery uses SQS and expects AWS credentials plus queue settings such as `AWS__ACCESS_KEY_ID`, `AWS__SECRET_ACCESS_KEY`, `AWS__REGION`, `CELERY__QUEUE_NAME`, and `CELERY__QUEUE_URL`.

## Local Setup

Create a virtual environment and install local plus development dependencies:

```bash
python3.13 -m venv venv
source venv/bin/activate
pip install -r dependencies/requirements-local.txt
pip install -r dependencies/dev/requirements-dev.txt
```

The API expects reachable OpenSearch and PostgreSQL instances for its read endpoints, and a reachable Celery broker (Redis in local mode) for publishing.

Run the API:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Local stub worker

`debug_worker.py` is a lightweight Celery worker that consumes the tasks published by the API and returns a debug report. It is useful for exercising the publish path without running the full `debugMate-worker`:

```bash
celery -A debug_worker.celery_app worker --loglevel=info
```

Note that this stub does not write to OpenSearch or PostgreSQL, so the event/incident read endpoints still require the real data stores (and the real worker) to return data.

## Dependencies

Dependency pins are split by target:

```text
dependencies/requirements-base.txt   Shared runtime deps (FastAPI, Pydantic, OpenSearch, SQLModel, psycopg2)
dependencies/requirements-local.txt  Base + Celery with Redis broker
dependencies/requirements-prod.txt   Base + Celery with SQS broker (boto3)
dependencies/dev/requirements-dev.txt Tooling (pytest, ruff, mypy, pre-commit)
```

## Development Checks

Run formatting and linting:

```bash
ruff check .
ruff format .
```

Run type checking:

```bash
mypy
```

Run tests:

```bash
pytest tests
```

The current test suite covers the event and incident endpoints and the health checks, using FastAPI's `TestClient` with a SQLite database and fake/overridden service clients.

Or install and run the configured pre-commit hooks:

```bash
pre-commit install
pre-commit run --all-files
```

## Docker

Production image:

```bash
docker build -f dev/Dockerfile -t debugmate-api .
```

Local stack (API, stub worker, and Redis) via Docker Compose:

```bash
docker compose -f dev/local/docker-compose.yaml up --build
```

The API is exposed on `http://localhost:8000`.
