# Backend Architecture

## Active Runtime

```text
Flutter App
  -> FastAPI Public API (`stringsense_backend/`)
      -> SQLAlchemy + Alembic managed database
      -> In-process recommendation and AI helper modules
```

- The frontend now calls the Python backend directly.
- `stringsense_backend/` owns public business routes, auth, profiles, strings, bookings, admin operations, and recommendation logging.
- AI recommendation logic now runs in process instead of crossing an internal NestJS-to-FastAPI HTTP boundary.
- `nest-api/` and `archive/python_business_backend/` are reference code only.

## Ownership Boundaries

### Unified Backend (`stringsense_backend/`)

The unified backend owns:

- authentication and JWT issuance
- users and profiles
- strings catalog seeding and admin maintenance
- bookings and booking status transitions
- recommendation generation and logging
- admin reporting endpoints
- frontend-facing validation, error shaping, and OpenAPI docs

### Reused AI Logic (`ai_service/`)

`ai_service/` is no longer the active public runtime. Its value is now:

- reusable recommendation/review-analysis reference logic
- fallback data-loading utilities
- compatibility tests around recommendation primitives

The active public API does not require `x-internal-api-key`.

## Configuration and Startup

- The unified backend loads `backend/.env` through `pydantic-settings`.
- Relative `APPROVED_STRINGS_SOURCE_PATH` values resolve from the backend root.
- `DATABASE_URL` now uses SQLAlchemy semantics; the default example points to a local SQLite file in `/tmp`.
- `AUTO_CREATE_SCHEMA=true` is intended for local development and tests. Production should use Alembic migrations explicitly.
- Privileged seed users remain opt-in. If `SEED_ADMIN_ENABLED` or `SEED_VENDOR_ENABLED` is true, the matching username, phone number, and password must all be provided.

## Core Flows

### Auth Flow

1. Client authenticates with `phone_number + password`.
2. FastAPI validates credentials against SQLAlchemy-managed users.
3. FastAPI issues JWT bearer tokens.
4. Optional seed admin users are created during startup only when explicitly enabled.

### Recommendation Flow

1. Frontend calls the Python backend directly.
2. The backend uses either the stored profile or a direct preview payload.
3. The active string catalog is scored in process by the unified recommendation module.
4. The backend stores request and result snapshots in `recommendation_logs`.

### Strings Flow

1. Startup seeds strings from the approved catalog when the table is empty.
2. Admin string write operations must still map to approved catalog entries.
3. The same string records are used by both public catalog routes and recommendation scoring.

## Booking Workflow

Allowed status values:

- `awaiting_dropoff`
- `in_progress`
- `ready_for_collection`
- `completed`
- `cancelled`
- `rejected`

Allowed transitions:

- `awaiting_dropoff -> in_progress | rejected | cancelled`
- `in_progress -> ready_for_collection | cancelled`
- `ready_for_collection -> completed`
- `completed`, `cancelled`, and `rejected` are terminal

## Maintainability Rules

- Keep shared settings, auth, error handling, and serialization in `stringsense_backend/core/`.
- Keep ORM models, seed logic, and migrations in `stringsense_backend/db/` plus `migrations/`.
- Keep feature routers and domain logic grouped by module under `stringsense_backend/modules/`.
- Prefer direct in-process service calls over internal HTTP between backend components.
- Update tests and docs whenever runtime behavior or config rules change.

## Validation Contract

Primary validation commands:

```bash
cd backend
./.venv/bin/ruff check .
./.venv/bin/ruff format --check .
./.venv/bin/pytest -v
```
