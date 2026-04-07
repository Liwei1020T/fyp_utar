# StringSense Backend

StringSense now runs on a unified Python backend:

- `app/` is the active public backend runtime organized in clean architecture layers.
- `ai_service/` remains as reusable AI logic and compatibility reference, but the active backend now calls AI logic in process instead of over internal HTTP.

## Active Structure

```text
backend/
  app/
  ai_service/
  migrations/
  data/raw/
  docs/
```

## Environment

Copy values from [.env.example](./.env.example) into `backend/.env`.

Key variables:

- `DATABASE_URL`: SQLAlchemy database URL for the unified Python backend
- `JWT_SECRET_KEY`: signing key for bearer tokens
- `APPROVED_STRINGS_SOURCE_PATH`: approved real catalog source; relative paths resolve from the backend root
- `SEED_ADMIN_*`: optional admin seed controls
- `AUTO_CREATE_SCHEMA`: optional dev/test convenience toggle for local schema creation

In this unified workspace, `AI_MATRIX_CSV_PATH` and `AI_REVIEW_ASPECT_CSV_PATH` should normally point at `../ml/nlp-workbench/outputs/`.

Legacy AI env vars such as `AI_INTERNAL_API_KEY` are only needed if you still run `ai_service/` directly for standalone compatibility checks.

## Local Postgres

Start the local development database from the workspace root:

```bash
docker compose up -d postgres
```

Use this backend connection string:

```env
DATABASE_URL=postgresql+psycopg://admin:admin@127.0.0.1:55432/stringsense
```

The Compose service stores data in the `stringsense_postgres_data` Docker volume.

## Run

1. Install Python dependencies:

```bash
cd backend
uv sync --extra dev
```

2. Apply migrations for the unified backend:

```bash
cd backend
./.venv/bin/alembic upgrade head
```

3. Start the unified backend:

```bash
cd backend
./.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 3001 --reload
```

The API base URL is `http://127.0.0.1:3001/api`.
FastAPI docs are available at `http://127.0.0.1:3001/docs`.

## Verify

```bash
cd backend
./.venv/bin/ruff check .
./.venv/bin/ruff format --check .
./.venv/bin/mypy app ai_service tests
./.venv/bin/pytest -v
```

## API Summary

Public unified Python endpoints:

- `GET /health`
- `GET /api/health`
- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/forgot-password/request-code`
- `POST /api/auth/forgot-password/reset`
- `GET /api/auth/me`
- `GET /api/profile`
- `PUT /api/profile`
- `GET /api/strings`
- `GET /api/strings/{id}`
- `POST /api/bookings`
- `GET /api/bookings`
- `GET /api/bookings/{id}`
- `POST /api/recommendations/preview`
- `POST /api/recommendations/profile`
- `GET /api/admin/strings`
- `POST /api/admin/strings`
- `PUT /api/admin/strings/{id}`
- `DELETE /api/admin/strings/{id}`
- `GET /api/admin/inventory/strings`
- `GET /api/admin/inventory/strings/{id}`
- `PATCH /api/admin/inventory/strings/{id}`
- `GET /api/admin/bookings`
- `GET /api/admin/bookings/{id}`
- `PATCH /api/admin/bookings/{id}/status`
- `GET /api/admin/business-hours`
- `PUT /api/admin/business-hours`
- `GET /api/slots`
- `GET /api/admin/slots`
- `GET /api/admin/check-in/lookup`
- `POST /api/admin/check-in`
- `GET /api/admin/service-queue`
- `GET /api/admin/store-settings`
- `PUT /api/admin/store-settings`
- `GET /api/admin/analytics/summary`
- `GET /api/admin/analytics/popular-strings`
- `GET /api/admin/recommendations/logs`

More detail is in [docs/architecture.md](./docs/architecture.md), [docs/api-contract.md](./docs/api-contract.md), and [docs/database.md](./docs/database.md).
