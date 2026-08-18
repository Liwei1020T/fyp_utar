# StringSense Backend

StringSense now runs on a unified Python backend:

- `app/` is the active public backend runtime organized in clean architecture layers.
- `app/domain/recommendation/scoring.py` is the single active public recommendation implementation.
- `ai_service/` remains a standalone compatibility reference and is not imported by unified FastAPI startup.

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
- `APPROVED_STRINGS_SOURCE_PATH`: approved normalized catalog source; relative paths resolve from the backend root
- `RECOMMENDATION_MATRIX_SOURCE_PATH`: NLP/review recommendation matrix source file (`.csv` or `.xlsx`); relative paths resolve from the backend root
- `EXPO_PUSH_ENABLED`: enables remote Expo delivery after device registration
- `EXPO_ACCESS_TOKEN`: server-only Expo access token used with enhanced push
  security; it is mandatory when push is enabled in production
- `OPENWA_ENABLED`: uses a self-hosted OpenWA session as the remote WhatsApp
  notification channel; do not enable it together with Expo push
- `OPENWA_BASE_URL`, `OPENWA_SESSION_ID`, `OPENWA_API_KEY`: OpenWA REST endpoint
  and session-scoped operator credential
- `AGENT_ENABLED`, `AGENT_API_KEY`: enable the authenticated FYP-scoped player
  Agent and read-only admin summary, using a server-only DeepSeek credential
- `AGENT_MODEL`: defaults to the selected `deepseek-v4-flash` model
- `SEED_ADMIN_*`: optional admin seed controls; enabling them requires a valid
  username, 9-to-15-digit phone number, and password

In this unified workspace, the public runtime recommendation source is `RECOMMENDATION_MATRIX_SOURCE_PATH` (default: `../ml/nlp-workbench-latest/output/latest_macbert_review_matrix_system12.xlsx`).

The active catalog and recommendation boundary is the versioned 12-string list
in `../config/approved_string_cohort_v1.csv`. Other master-data rows remain
persisted for historical booking and audit references, but catalog, inventory,
editing, booking selection, and recommendation APIs do not expose them.

`AI_MATRIX_CSV_PATH` and `AI_REVIEW_ASPECT_CSV_PATH` remain for standalone `ai_service/` compatibility and use CSV artifacts under `../ml/nlp-workbench-latest/output/`.

Legacy AI env vars such as `AI_INTERNAL_API_KEY` are only needed if you still run `ai_service/` directly for standalone compatibility checks.

Keep `EXPO_ACCESS_TOKEN` in the deployment secret store or untracked
`backend/.env`. Never put it in the mobile app or use an `EXPO_PUBLIC_*` name.
The same server-only rule applies to `OPENWA_API_KEY` and `AGENT_API_KEY`; never
expose either through an `EXPO_PUBLIC_*` mobile variable.

For an FYP-only WhatsApp channel, run the self-hosted OpenWA `v0.11.1`, create
and connect one session in its dashboard, mint a session-scoped operator key,
then set `OPENWA_ENABLED=true`. StringSense sends only the notification title
and body, or a time-limited password-reset code, to
`POST /api/sessions/{sessionId}/messages/send-text`. The in-app notification
remains the audit source of truth if OpenWA is unavailable. Player category
preferences apply to both the in-app feed and OpenWA notification delivery;
security codes are account messages and are not controlled by those preferences.

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
./scripts/alembic upgrade head
```

Alembic is the sole runtime schema owner. ORM `create_all` remains available
only to isolated test fixtures.

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
- `GET /api/media/{media_path}`
- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/forgot-password/request-code`
- `POST /api/auth/forgot-password/reset`
- `GET /api/auth/me`
- `GET /api/profile`
- `PUT /api/profile`
- `GET /api/notifications`
- `PATCH /api/notifications/read`
- `GET /api/notifications/preferences`
- `PUT /api/notifications/preferences`
- `GET /api/conversations`
- `POST /api/bookings/{id}/support`
- `GET /api/conversations/{id}`
- `POST /api/conversations/{id}/messages`
- `POST /api/conversations/{id}/read`
- `GET /api/rackets`
- `POST /api/rackets`
- `GET /api/rackets/{id}`
- `PATCH /api/rackets/{id}`
- `GET /api/bookings/{id}/feedback`
- `POST /api/bookings/{id}/feedback`
- `GET /api/strings`
- `GET /api/strings/{id}`
- `POST /api/bookings`
- `GET /api/bookings`
- `GET /api/bookings/{id}`
- `POST /api/bookings/{id}/updates`
- `GET /api/payments`
- `GET /api/payments/bookings/{id}/quote`
- `POST /api/payments/bookings/{id}`
- `GET /api/wallet`
- `POST /api/wallet/top-ups`
- `POST /api/recommendations/preview`
- `POST /api/recommendations/profile`
- `POST /api/recommendations/generate`
- `GET /api/recommendations/{user_id}`
- `GET /api/recommendations/{user_id}/{catalog_id}`
- `POST /api/agent/query`
- `GET /api/admin/strings`
- `POST /api/admin/strings`
- `PUT /api/admin/strings/{id}`
- `DELETE /api/admin/strings/{id}`
- `POST /api/admin/strings/{id}/image`
- `DELETE /api/admin/strings/{id}/image`
- `GET /api/admin/inventory/strings`
- `GET /api/admin/inventory/strings/{id}`
- `PATCH /api/admin/inventory/strings/{id}`
- `PUT /api/admin/inventory/strings/{id}/editor` (atomic catalog, official-performance, and inventory update)
- `GET /api/admin/inventory/strings/{id}/movements`
- `GET /api/admin/strings/{id}/official-performance`
- `PUT /api/admin/strings/{id}/official-performance`
- `GET /api/admin/strings/{id}/recommendation-matrix`
- `POST /api/admin/recommendation-matrix/import`
- `GET /api/admin/bookings`
- `GET /api/admin/bookings/{id}`
- `PATCH /api/admin/bookings/{id}/status`
- `POST /api/admin/bookings/{id}/updates`
- `POST /api/admin/bookings/{id}/photos`
- `GET /api/admin/business-hours`
- `PUT /api/admin/business-hours`
- `GET /api/slots`
- `GET /api/store-settings`
- `GET /api/admin/slots`
- `GET /api/admin/check-in/lookup`
- `POST /api/admin/check-in`
- `GET /api/admin/service-queue`
- `GET /api/admin/store-settings`
- `PUT /api/admin/store-settings`
- `GET /api/admin/analytics/summary`
- `GET /api/admin/analytics/popular-strings`
- `GET /api/admin/payments`
- `PATCH /api/admin/payments/{id}`
- `GET /api/admin/conversations`
- `GET /api/admin/conversations/{id}`
- `POST /api/admin/conversations/{id}/messages`
- `POST /api/admin/conversations/{id}/read`
- `POST /api/admin/conversations/{id}/resolve`
- `POST /api/admin/conversations/{id}/close`
- `GET /api/admin/recommendations/logs`
- `GET /api/admin/recommendations/runs`
- `GET /api/admin/recommendations/runs/{run_id}`

More detail is in [docs/architecture.md](./docs/architecture.md), [docs/api-contract.md](./docs/api-contract.md), and [docs/database.md](./docs/database.md).

## Catalog Refactor Notes

- Master catalog data now lives in normalized `brands` and `strings` tables.
- Community metrics/tags, official performance, inventory, and recommendation matrix data are separated into their own tables.
- The default seed source is `backend/data/string_catalog_db_ready.json`.
- The default recommendation matrix source is `../ml/nlp-workbench-latest/output/latest_macbert_review_matrix_system12.xlsx`; the protected V9 workbook remains separate.
- Official performance rows are created as `pending_manual_fill`; missing values are intentionally not guessed.
- Recommendation-derived aspect scores now belong in `string_recommendation_matrix`, not in the master catalog table.
- The backend imports the canonical recommendation artifact into `string_recommendation_matrix` with `source_layer='nlp_review'`; each import fully replaces that source layer and records a SHA-256 source version.

## Recommendation Refactor Notes

The current design review found that the backend already had the right normalized tables, but the live recommender was still mostly a rule/content scorer. The active flow now preserves the existing architecture while making `user_preference_matrix` and `recommendation_score_cache` runtime tables.

Final score:

```text
FinalScore = (0.75 * PreferenceMatch + 0.15 * RuleFit) / 0.90
```

- `PreferenceMatch` compares normalized 1-to-10 user priorities against effective item features.
- Effective item features use official performance when available and NLP/review matrix values as enrichment.
- Structured catalog fields such as gauge are excluded from direct PreferenceMatch and are used only by RuleFit, filtering, and display.
- `RuleFit` applies badminton-specific logic such as beginner thin-gauge support, high-tension/high-frequency thick-gauge support, and attacking/control bonuses.
- NLP/review signals are imported from the independent 12-by-9 MacBERT workbook into `string_recommendation_matrix` with `source_layer='nlp_review'`; they are not copied into `strings`, `string_official_performance`, or the protected V9 workbook.
- Matrix rows contain only scoring values and optional evidence notes; confidence, review-count, reference, and per-row artifact metadata are not persisted.
- `POST /api/recommendations/generate` generates and caches profile recommendations; the older `/preview` and `/profile` routes remain for compatibility.
