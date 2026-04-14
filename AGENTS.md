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
- Mobile setup: `cd mobile && nvm use && npm install`
- Mobile typecheck: `cd mobile && npx tsc --noEmit`
- Mobile web smoke: `cd mobile && EXPO_PUBLIC_API_BASE_URL=http://127.0.0.1:3001/api npm run web`
- Backend setup: `cd backend && uv sync --extra dev`
- Backend migrations: `cd backend && ./.venv/bin/alembic upgrade head`
- Backend full validation: `cd backend && ./.venv/bin/ruff check . && ./.venv/bin/ruff format --check . && ./.venv/bin/mypy app ai_service tests && ./.venv/bin/pytest -v`
- NLP notebook setup: `cd ml/nlp-workbench && python3 -m pip install -r requirements.txt`
- NLP notebook run: `cd ml/nlp-workbench && jupyter lab`

## Architecture Map

- Entry points:
  - Mobile app: `mobile/app/_layout.tsx`
  - Public backend: `backend/app/main.py`
  - NLP workbench: `ml/nlp-workbench/stringsense_complete_absa_pipeline_notebook.ipynb`
- Core modules:
  - `mobile/`: Expo Router app for player and admin flows
  - `backend/`: FastAPI + SQLAlchemy backend plus in-process AI logic
  - `ml/nlp-workbench/`: notebook, datasets, and generated CSV artifacts for recommendation signals
  - `docs/`: workspace-level orientation docs
- Critical paths:
  - player login and recommendation flow: `mobile` -> `backend` -> in-process AI scoring
  - admin catalog and booking operations: `mobile` admin screens -> `backend`
  - NLP artifact handoff: default runtime workbook in `ml/nlp-workbench-latest/output/latest_practical_string_feature_matrix_v9_v8dict.xlsx` -> backend `RECOMMENDATION_MATRIX_SOURCE_PATH`
  - legacy AI-service artifact handoff: `ml/nlp-workbench/outputs/` -> backend `AI_*_PATH` config
- State/data boundaries:
  - `backend/` owns runtime data, auth, bookings, recommendation logs, and recommendation run history
  - `mobile/` stays hybrid: live FYP1 player/admin core flow plus hidden/mock-first FYP2 domains
  - `ml/nlp-workbench/` is offline experimentation and artifact generation, not a public service

## Change Rules

1. Prefer minimal diffs that solve the requested scope.
2. Keep cross-workspace wiring explicit in docs and env examples.
3. Do not commit secrets, local `.env` files, DB files, build artifacts, or notebook outputs.
4. Update this file when workspace commands, structure, or ownership boundaries change.

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

- Local Postgres:
  - `docker compose up -d postgres`
- Backend:
  - `cd backend && cp .env.example .env`
  - `cd backend && uv sync --extra dev`
  - `cd backend && ./.venv/bin/alembic upgrade head`
  - `cd backend && ./.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 3001 --reload`
- Mobile:
  - `cd mobile && nvm use`
  - `cd mobile && npm install`
  - `cd mobile && EXPO_PUBLIC_API_BASE_URL=http://127.0.0.1:3001/api npm run web`
- NLP:
  - `cd ml/nlp-workbench && python3 -m pip install -r requirements.txt`
  - Run the notebook top-to-bottom to populate `ml/nlp-workbench/outputs/` (legacy AI-service compatibility artifacts)
  - Unified backend default matrix source uses `ml/nlp-workbench-latest/output/latest_practical_string_feature_matrix_v9_v8dict.xlsx`
