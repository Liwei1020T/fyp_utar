# StringSence Workspace

StringSence now lives as one integrated workspace that combines the mobile app, the unified Python backend, and the notebook-based NLP pipeline used to generate recommendation artifacts.

## Workspace Layout

- `mobile/`: Expo Router React Native app for player and admin flows
- `backend/`: FastAPI + SQLAlchemy backend with the canonical in-process scorer at `backend/app/domain/recommendation/scoring.py`
- `ml/nlp-workbench-latest/`: canonical notebook package, datasets, and recommendation artifacts
- `docs/`: workspace-level documentation index

## Quick Start

### 1. Start Postgres

```bash
rtk docker compose up -d postgres
```

### 2. Start the backend

For browser-only testing on the same Mac, `127.0.0.1` is enough. For Expo Go on a phone, the backend must listen on `0.0.0.0` so the phone can reach it through the Mac Wi-Fi IP.

```bash
cd backend
cp .env.example .env
rtk uv sync --extra dev
rtk ./.venv/bin/alembic upgrade head
rtk ./.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 3001 --reload
```

### 3. Start the mobile app in a browser

```bash
cd mobile
nvm use
npm install
EXPO_PUBLIC_API_BASE_URL=http://127.0.0.1:3001/api npm run web
```

The mobile workspace pins Node `24.18.0` via `mobile/.nvmrc` and `mobile/package.json` allows the Node `24.x` LTS line.

### 4. Start the mobile app on Expo Go

Find the Mac Wi-Fi IP first. On this machine it usually appears as the `inet` value under `en0`.

```bash
rtk ifconfig en0
```

Then start Expo in LAN mode. Replace `<MAC_WIFI_IP>` with the IP from the previous command, for example `192.168.0.80`.

```bash
cd mobile
nvm use
EXPO_PUBLIC_API_BASE_URL=http://<MAC_WIFI_IP>:3001/api npm run start -- --lan
```

Open Expo Go on the phone and scan the QR code. The phone and Mac must be on the same Wi-Fi. Do not use `localhost` or `127.0.0.1` for Expo Go, because on a phone those addresses point to the phone itself, not the Mac.

### 5. Run the NLP workbench when you need fresh recommendation artifacts

```bash
cd ml/nlp-workbench-latest
./scripts/bootstrap.sh
.venv/bin/python -m pytest -q tests
.venv/bin/python scripts/run_experiment.py --run-id <experiment-id> --repeat 2
```

The runner executes labeling and the complete pipeline in order and writes only to immutable `output/runs/<run-id>/` directories. It fails on data leakage, protected-input changes, or non-reproducible metrics/CSV outputs.

Experiment outputs are never promoted automatically. The unified backend default recommendation source remains `ml/nlp-workbench-latest/output/latest_practical_string_feature_matrix_v9_v8dict.xlsx` until a separate human-approved promotion task.

## Backend and NLP Integration

- `backend/.env.example` sets `RECOMMENDATION_MATRIX_SOURCE_PATH` to `../ml/nlp-workbench-latest/output/latest_practical_string_feature_matrix_v9_v8dict.xlsx`
- The unified FastAPI app does not import the legacy AI adapters or `ai_service` during startup
- Standalone `ai_service` compatibility CSV settings use the canonical latest output directory when that package is run explicitly
- If those generated files do not exist yet, the backend can still fall back to `backend/data/raw/badminton_strings_recommender.jsonl`

## Validation

- Mobile: `cd mobile && nvm use && npx tsc --noEmit && npm run lint -- --max-warnings=0`
- Backend: `cd backend && ./.venv/bin/ruff check . && ./.venv/bin/ruff format --check . && ./.venv/bin/mypy app ai_service tests && ./.venv/bin/pytest -v`
- NLP: `cd ml/nlp-workbench-latest && .venv/bin/python -m pytest -q tests && .venv/bin/python scripts/run_experiment.py --run-id <experiment-id> --repeat 2`

More detail lives in [docs/README.md](./docs/README.md), [mobile/README.md](./mobile/README.md), and [backend/README.md](./backend/README.md). The current mock-data remediation status is recorded in [docs/plans/mock-page-remediation.md](./docs/plans/mock-page-remediation.md), and the latest complete customer and administrator browser evidence is in [docs/customer-admin-acceptance-2026-07-24.md](./docs/customer-admin-acceptance-2026-07-24.md). The earlier administrator-only acceptance remains in [docs/admin-acceptance-2026-07-23.md](./docs/admin-acceptance-2026-07-23.md), and the pre-FYP2 remediation gate remains preserved in [docs/plans/fyp2-readiness/04-remediation-results-and-readiness.md](./docs/plans/fyp2-readiness/04-remediation-results-and-readiness.md).
