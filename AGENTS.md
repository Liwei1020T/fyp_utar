# AGENTS.md - StringSence

## Scope

- This file applies to this directory and all children.
- Deeper `AGENTS.md` files override this file in subdirectories.

## Project Context

- Mission: keep StringSence as one delivery workspace that integrates the Expo mobile app, the unified Python backend, and the notebook-based NLP pipeline.
- Primary users: the FYP team building the demo, badminton players using the mobile flow, and the single shop admin managing operations.
- Non-goals: splitting the project back into separate repos, rewriting the NLP notebook into a production service by default, or introducing production infrastructure beyond FYP needs.

## Validation Commands

- Local Postgres: `docker compose up -d postgres`
- Full local Docker stack: `DOCKER_BUILDKIT=0 COMPOSE_DOCKER_CLI_BUILD=1 docker compose -p stringsence -f compose.yaml -f compose.local.yaml up -d --build postgres migrate backend frontend`
- Mobile setup: `cd mobile && nvm use && npm install`
- Mobile typecheck: `cd mobile && npx tsc --noEmit`
- Mobile web smoke: `cd mobile && EXPO_PUBLIC_API_BASE_URL=http://127.0.0.1:3001/api npm run web`
- Mobile Expo Go smoke: start backend with `--host 0.0.0.0`, then `cd mobile && EXPO_PUBLIC_API_BASE_URL=http://<MAC_WIFI_IP>:3001/api npm run start -- --lan`
- Backend setup: `cd backend && uv sync --extra dev`
- Backend migrations: `cd backend && ./scripts/alembic upgrade head`
- Backend full validation: `cd backend && ./.venv/bin/ruff check . && ./.venv/bin/ruff format --check . && ./.venv/bin/mypy app tests && ./.venv/bin/pytest -v`
- NLP setup: `cd ml/nlp-workbench-latest && ./scripts/bootstrap.sh`
- NLP fast validation: `cd ml/nlp-workbench-latest && .venv/bin/python -m pytest -q tests`
- NLP reproducibility run: `cd ml/nlp-workbench-latest && .venv/bin/python scripts/run_experiment.py --run-id <experiment-id> --repeat 2`

## Architecture Map

- Entry points:
  - Mobile app: `mobile/app/_layout.tsx`
  - Public backend: `backend/app/main.py`
  - NLP workbench: `ml/nlp-workbench-latest/stringsense_complete_absa_pipeline_notebook_latest.ipynb`
- Core modules:
  - `mobile/`: Expo Router app for player and admin flows
  - `backend/`: FastAPI + SQLAlchemy backend plus in-process AI logic
  - `ml/nlp-workbench-latest/`: canonical notebook, datasets, and generated recommendation artifacts
  - `docs/`: workspace-level orientation docs
  - `config/approved_string_cohort_v1.csv`: the 12-string system catalog boundary shared by backend runtime and BERT preparation
- Critical paths:
  - player login and recommendation flow: `mobile` -> `backend` -> in-process AI scoring
  - recommendation learning loop: weighted-preference v13 ranking -> bounded feedback calibration -> gated exact-racket CF inherited from v11, with the calibrated base fallback below three independent supporters
  - FYP-scoped player Agent: four-question guided selection, two-or-three-string comparison, exact-run explanation, verified in-stock alternatives, and live store information -> authenticated `/api/agent/query` -> DeepSeek V4 Flash; V13 remains the only ranking owner
  - admin catalog and booking operations: `mobile` admin screens -> `backend`
  - admin Agent operations: read-only current-operations summary plus booking and inventory searches; write handlers remain preserved but inactive
  - NLP artifact handoff: independent 12-string MacBERT workbook in `ml/nlp-workbench-latest/output/latest_macbert_review_matrix_system12.xlsx` -> backend `RECOMMENDATION_MATRIX_SOURCE_PATH`; legacy V9 remains separate
- State/data boundaries:
  - `backend/` owns runtime data, auth, bookings, notification preferences, commerce ledgers, and recommendation logs
  - `mobile/` is API-only at runtime: every route page uses backend or backend-derived records and no seeded mock session exists
  - `ml/nlp-workbench-latest/` is offline experimentation and artifact generation, not a public service
  - catalog, inventory, booking selection, and recommendation APIs expose only the 12 approved cohort IDs; other persisted strings remain hidden for historical-reference integrity

## Change Rules

1. Prefer minimal diffs that solve the requested scope.
2. Keep cross-workspace wiring explicit in docs and env examples.
3. Do not commit secrets, local `.env` files, DB files, build artifacts, or notebook outputs.
4. Update this file when workspace commands, structure, or ownership boundaries change.

## Graphify Workflow

- For every code-change task, call Graphify before editing relevant functions or fields with `graphify query`, `graphify explain`, or `graphify path` to inspect callers and dependencies; call it again after editing to verify affected relationships.
- Query the existing `graphify-out/graph.json` for relationship checks. Do not rebuild `graphify-out` for every edit; use an incremental update only when the graph must include newly changed source, and keep generated graph output out of functional commits unless explicitly requested.

## Definition of Done

1. Requested workspace behavior is implemented.
2. Relevant checks pass or are explicitly marked `unverified`.
3. Cross-workspace paths and docs stay consistent.
4. Risks, assumptions, and follow-ups are documented in the final update.

## High-Risk Changes (Ask Before Proceeding)

- Destructive operations (`rm -rf`, hard reset, history rewrite, force push)
- Irreversible data/schema migrations
- Production auth/security/infra changes
- Large dependency/tooling upgrades

## Quick Start

- Full Docker stack: `DOCKER_BUILDKIT=0 COMPOSE_DOCKER_CLI_BUILD=1 docker compose -p stringsence -f compose.yaml -f compose.local.yaml up -d --build postgres migrate backend frontend`
- Docker frontend: `http://127.0.0.1:8081`; Docker backend health: `http://127.0.0.1:3001/health`

- Local Postgres:
  - `docker compose up -d postgres`
- Backend:
  - `cd backend && cp .env.example .env`
  - `cd backend && uv sync --extra dev`
  - `cd backend && ./scripts/alembic upgrade head`
  - Browser-only local run: `cd backend && ./.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 3001 --reload`
  - Expo Go phone run: `cd backend && ./.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 3001 --reload`
- Mobile:
  - `cd mobile && nvm use`
  - `cd mobile && npm install`
  - Browser web: `cd mobile && EXPO_PUBLIC_API_BASE_URL=http://127.0.0.1:3001/api npm run web`
  - Expo Go: run `ifconfig en0`, copy the `inet` Wi-Fi IP, then `cd mobile && EXPO_PUBLIC_API_BASE_URL=http://<MAC_WIFI_IP>:3001/api npm run start -- --lan`
  - Do not use `localhost` or `127.0.0.1` for Expo Go on a physical phone; those point to the phone, not the Mac.
- NLP:
  - `cd ml/nlp-workbench-latest && ./scripts/bootstrap.sh`
  - Run `.venv/bin/python scripts/run_experiment.py --run-id <experiment-id> --repeat 2`; do not reuse run IDs.
  - Generated files stay under `output/runs/<run-id>/` with `promotion.status=not_promoted`.
  - Never open `data/archive_latest.zip`; use only the extracted JSON input.
  - Do not overwrite `data/*_latest.csv`, `output/latest_practical_string_feature_matrix_v9_v8dict.xlsx`, or `output/latest_macbert_review_matrix_system12.xlsx` without a separate approved promotion task.
