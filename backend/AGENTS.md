# AGENTS.md - backend

## Scope

- This file applies to this directory and all children.
- Deeper `AGENTS.md` overrides this file in subdirectories.

## Project Context

- Mission: Keep StringSense’s public business backend in Python with a maintainable FastAPI + SQLAlchemy architecture and in-process AI capabilities.
- Primary users: `customer`, `admin`
- Non-goals: reintroducing a second public backend stack, introducing queue/event infrastructure, or overengineering beyond FYP needs

## Validation Commands

- Local Postgres from workspace root: `docker compose up -d postgres`
- Python lint: `./.venv/bin/ruff check .`
- Python format check: `./.venv/bin/ruff format --check .`
- Python typecheck: `./.venv/bin/mypy app ai_service tests`
- Python tests: `./.venv/bin/pytest -v`
- Alembic upgrade: `./scripts/alembic upgrade head`
- Fast loop for touched areas first, then run the relevant full checks before completion.
- Ruff excludes generated and inactive paths such as `.venv/`, caches, and AppleDouble sidecar files, so repo-wide Python checks should stay green without narrowing the command scope.

## Architecture Map

- Entry points:
  - Unified FastAPI backend: `app/main.py`
  - Legacy AI-only service reference: `ai_service/main.py`
- Core modules:
  - `app/`: FastAPI entrypoints, use cases, domain, ports, DTOs, and adapters for the unified backend
  - `ai_service/`: reusable recommendation, review analysis, and RAG-style logic
  - `migrations/`: active migration history for the unified backend
- Critical paths:
  - phone-first auth (`phone_number + password`)
  - booking state transition enforcement
  - recommendation flow: frontend -> unified Python backend -> in-process AI module
  - admin string CRUD/import
  - commerce flow: player payment/top-up request -> admin verification -> persisted payment and wallet ledger
- Config/runtime rules:
  - Unified backend reads `.env` through `pydantic-settings`
  - relative `APPROVED_STRINGS_SOURCE_PATH` values resolve from the backend root
  - default recommendation matrix source is `../ml/nlp-workbench-latest/output/latest_practical_string_feature_matrix_v9_v8dict.xlsx`
  - compatibility `AI_MATRIX_CSV_PATH` and `AI_REVIEW_ASPECT_CSV_PATH` values point to CSV artifacts under `../ml/nlp-workbench-latest/output/`
  - Alembic is the sole runtime schema owner; ORM `create_all` is test-fixture only
  - `SEED_ADMIN_ENABLED` defaults to `false`; enabling it requires explicit companion credentials
- State/data boundaries:
  - SQLAlchemy + Alembic own the active core business tables
  - the unified Python backend owns workflow writes
  - booking support, player feedback, and derived notifications reuse persisted booking updates/history
  - payment status and wallet balance come only from `payments` and `wallet_transactions`
  - recommendation logs remain business-owned data

## Change Rules

1. Prefer minimal diffs that solve requested scope.
2. Reuse existing patterns before introducing new abstractions.
3. Prefer shared helpers for path resolution, env validation, serialization, and DTO-to-persistence mapping before adding duplicate logic.
4. Keep frontend-facing APIs in `app/entrypoints/` and prefer in-process service calls over internal HTTP.
5. Update docs/tests when behavior changes.
6. Never commit secrets or private credentials.
7. If simplifying code, preserve behavior exactly and reduce duplication before introducing broader refactors.

## Definition of Done

1. Requested behavior is implemented.
2. Relevant checks pass or are explicitly marked `unverified` with reason.
3. No known regressions are introduced.
4. Risks, assumptions, and follow-ups are documented in the final update.

## High-Risk Changes (Ask Before Proceeding)

- Destructive operations (`rm -rf`, hard reset, history rewrite, force push)
- Irreversible data/schema migrations
- Production auth/security/infra changes
- Large dependency/tooling upgrades

## Quick Start

- Local Postgres:
  - from workspace root, run `docker compose up -d postgres`
- Setup:
  - `uv sync --extra dev`
  - `./scripts/alembic upgrade head`
- Environment:
  - copy `.env.example` to `.env`
  - only set `SEED_ADMIN_*` when the matching seed flag is explicitly enabled
- Run locally:
  - Unified backend: `./.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 3001 --reload`
- Test locally:
  - `./.venv/bin/ruff check . && ./.venv/bin/ruff format --check . && ./.venv/bin/mypy app ai_service tests && ./.venv/bin/pytest -v`
- Release/deploy:
  - Deploy the unified Python backend as the public backend.
