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
./scripts/alembic upgrade head
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
./.venv/bin/mypy app tests
./.venv/bin/pytest -v
```

## 4. Catalog and Recommendation Notes

- The unified backend seeds the normalized catalog from `APPROVED_STRINGS_SOURCE_PATH` when the catalog is empty.
- Relative `APPROVED_STRINGS_SOURCE_PATH` values resolve from the backend root.
- The default approved source is `backend/data/string_catalog_db_ready.json`.
- Relative `RECOMMENDATION_MATRIX_SOURCE_PATH` values also resolve from the backend root.
- The default NLP review matrix source is `../ml/nlp-workbench-latest/output/latest_macbert_review_matrix_system12.xlsx`; V9 remains separate.
- Recommendation generation uses `(0.75 * PreferenceMatch + 0.15 * RuleFit) / 0.90`
  as its base score with fixed official/NLP fusion and no confidence or
  review-count weighting. It blends racket-scoped CF only after the three-user
  exact-model support gate; otherwise the base score is final.
- Complete profile saves and `POST /api/recommendations/generate` persist raw 1-to-10 scores plus normalized weights in `user_preference_matrix` with `source_layer='profile'`.
- Generated profile recommendations are cached in `recommendation_score_cache` and can be inspected through `GET /api/recommendations/{user_id}` and `GET /api/recommendations/{user_id}/{catalog_id}`.
- Startup seeding imports the independent MacBERT workbook into `string_recommendation_matrix` with `source_layer='nlp_review'` whenever the workbook exists. A missing workbook does not prevent startup: persisted matrix rows remain usable, and health reports `catalog_fallback` only when no NLP rows exist.
- Re-import compares scoring values and evidence notes. Any content change clears all recommendation cache rows; an unchanged import preserves them.
- Import requires matching metadata plus all nine runtime features: `repulsion` (from source `attack`), `comfort`, `control`, `durability`, `elasticity`, `sound`, `string_movement`, `tension_retention`, and `value_for_money`.
- `value_for_money` is the ninth weighted preference feature; catalog price is descriptive and is not scored.
- Structured gauge and official feel categories are soft RuleFit inputs and never remove candidates.
- Admin string write operations still require approved catalog membership.
- Startup filters the 33-item catalog source through `config/approved_string_cohort_v1.csv`; only the 12 approved strings, their inventory, and their matrix rows are seeded. Non-approved source records are not runtime catalog rows.
- NLP-derived scores should be loaded into `string_recommendation_matrix`, not into `strings` or `string_official_performance`.
- Admin debug support:
  - `GET /api/admin/strings/{id}/recommendation-matrix` shows effective scores plus raw matrix rows grouped by source layer.
  - `POST /api/admin/recommendation-matrix/import` safely re-imports the configured CSV or XLSX artifact and reports matched, inserted, updated, and unmatched counts.
- Admin OpenWA notification delivery commits `pending` before provider I/O, then
  persists and returns the final provider outcome (`sent` or `failed`) from a
  separate session. A provider failure is recorded as `failed`; it is not
  retried by a queue.
- Alembic is the sole runtime schema owner. Run `./scripts/alembic upgrade head` before starting the backend after pulling schema changes.
- Privileged seed users stay disabled unless `SEED_ADMIN_ENABLED=true` is
  configured with a non-empty username/password and a valid 9-to-15-digit
  companion phone number. Seed credentials belong in local process/env state,
  never in mobile source or committed documentation.
- Password-reset codes use the configured OpenWA session and are committed
  before provider I/O. Keep `PASSWORD_RESET_DEV_PREVIEW_ENABLED=false` outside
  controlled local development. Do not claim live delivery until the OpenWA
  session is connected and a real phone receipt has been verified.

## 5. Commerce Boundary

- Admin uploads the active shop QR from Store Settings. New top-ups and external
  booking payments use `qr_transfer` with a validated screenshot or `cash`
  without a screenshot. Both remain `pending` until an administrator verifies
  the transfer evidence or confirms cash receipt.
- Wallet top-ups credit the append-only ledger exactly once after verification.
- `wallet_balance` booking payments complete immediately after the server checks
  the persisted balance and do not require a screenshot.
- A future payment-provider webhook must replace manual verification for that
  provider; it must not create a second payment ledger.
