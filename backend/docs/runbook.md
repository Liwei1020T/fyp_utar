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

- The unified backend seeds the normalized catalog from `APPROVED_STRINGS_SOURCE_PATH` when the catalog is empty.
- Relative `APPROVED_STRINGS_SOURCE_PATH` values resolve from the backend root.
- The default approved source is `backend/data/string_catalog_db_ready.json`.
- Relative `RECOMMENDATION_MATRIX_SOURCE_PATH` values also resolve from the backend root.
- The default NLP review matrix source is `../ml/nlp-workbench-latest/output/latest_practical_string_feature_matrix_v9_v8dict.xlsx`.
- Recommendation generation uses `0.60 * PreferenceMatch + 0.15 * RuleFit + 0.15 * BudgetFit + 0.10 * ConfidenceScore`.
- Complete profile saves and `POST /api/recommendations/generate` persist raw 1-to-10 scores plus normalized weights in `user_preference_matrix` with `source_layer='profile'`.
- Generated profile recommendations are cached in `recommendation_score_cache` and can be inspected through `GET /api/recommendations/{user_id}` and `GET /api/recommendations/{user_id}/{catalog_id}`.
- Startup seeding imports the V9 workbook into `string_recommendation_matrix` with `source_layer='nlp_review'` and keeps it separate from official performance data.
- Re-import compares artifact provenance, including `source_generated_at`, so a stale timestamp is repaired even when feature values are unchanged.
- Import first sanitizes the workbook to the live runtime whitelist: matching metadata plus `repulsion` (from source `attack`), `comfort`, `control`, `durability`, `elasticity`, `sound`, `string_movement`, and `tension_retention`.
- `BudgetFit` follows the saved budget range directly; missing price falls back to a neutral budget score.
- Structured catalog data such as gauge is used for RuleFit and filtering, not direct PreferenceMatch scoring.
- Admin string write operations still require approved catalog membership.
- Official performance rows are seeded as `pending_manual_fill` and can be updated later through admin endpoints.
- NLP-derived scores should be loaded into `string_recommendation_matrix`, not into `strings` or `string_official_performance`.
- Admin debug support:
  - `GET /api/admin/strings/{id}/recommendation-matrix` shows effective scores plus raw matrix rows grouped by source layer.
  - `POST /api/admin/recommendation-matrix/import` safely re-imports the CSV and reports matched, inserted, updated, and unmatched counts.
- `AUTO_CREATE_SCHEMA=true` is meant for local development and tests; use Alembic migrations explicitly for controlled environments.
- `AUTO_CREATE_SCHEMA=true` only creates missing tables from the ORM metadata. It does not repair drift inside existing tables, so local environments should still run `./.venv/bin/alembic upgrade head` after pulling schema changes.
- Privileged seed users stay disabled unless `SEED_ADMIN_ENABLED=true` is configured with companion credentials.

## 5. Optional Compatibility Component

This component still exists for compatibility checks and local experimentation:
- `ai_service/` standalone HTTP entrypoint

It is not imported by the unified FastAPI startup and is not the active public runtime path.
