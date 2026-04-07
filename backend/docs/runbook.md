# Local Development Flow

## 1. Prepare Environment

From the workspace root, start the local Postgres service:

```bash
docker compose up -d postgres
```

Then prepare the backend environment:

```bash
cd backend
uv sync --extra dev
./.venv/bin/alembic upgrade head
```

## 2. Start the Unified Backend

```bash
cd backend
./.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 3001 --reload
```

FastAPI docs:

```text
http://127.0.0.1:3001/docs
```

## 3. Validation Commands

```bash
cd backend
./.venv/bin/ruff check .
./.venv/bin/ruff format --check .
./.venv/bin/mypy app ai_service tests
./.venv/bin/pytest -v
```

## 4. Catalog and Recommendation Notes

- The unified backend seeds strings from `APPROVED_STRINGS_SOURCE_PATH` when the table is empty.
- Relative `APPROVED_STRINGS_SOURCE_PATH` values resolve from the backend root.
- Recommendation scoring now uses the active DB-backed string catalog in process.
- Admin string write operations still require approved catalog membership.
- `AUTO_CREATE_SCHEMA=true` is meant for local development and tests; use Alembic migrations explicitly for controlled environments.
- Privileged seed users stay disabled unless `SEED_ADMIN_ENABLED=true` is configured with companion credentials.

## 5. Optional Compatibility Component

This component still exists for compatibility checks and local experimentation:
- `ai_service/` standalone HTTP entrypoint

They are not the active public runtime path anymore.
